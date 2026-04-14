#!/usr/bin/env python3
"""
DataForge - Project Type (Track) Detection

Inspects an input path and decides which DataForge execution track should
handle it: tabular, dl, or rag. Also emits a subtype hint where possible.

Detection rules (see plan v0.4.0):
    - .csv / .parquet / .xlsx / .xls / .feather / .tsv  -> tabular
    - directory of images (.png/.jpg/.jpeg/.webp/.bmp/.tif/.tiff) -> dl (cv-*)
    - directory of audio (.wav/.mp3/.flac/.ogg/.m4a)             -> dl (audio)
    - directory of plain text + label file                       -> dl (nlp-*)
    - directory of pdf/md/html/docx/rst                          -> rag (text-rag)
    - mixed text + images                                        -> dl multimodal
                                                                    or rag multimodal
                                                                    (caller picks)
    - ambiguous / unknown                                        -> tabular fallback
                                                                    with low confidence
                                                                    so router can ask

This script ships in v0.4.0 even though only the tabular branch is implemented,
so v0.5/v0.6 do not need to retrofit detection.

Usage:
    python project_type_detect.py --input <path> [--output <out.json>]
                                   [--type-override tabular|dl|rag]

Exit codes: 0 = decision emitted (any confidence), 2 = path not found.
"""
import argparse
import json
import os
import sys
from pathlib import Path


TABULAR_EXTS = {".csv", ".parquet", ".pq", ".xlsx", ".xls", ".feather", ".tsv", ".json", ".jsonl"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
TEXT_DOC_EXTS = {".pdf", ".md", ".markdown", ".html", ".htm", ".docx", ".rst", ".txt", ".epub"}
RAG_HEAVY_EXTS = {".pdf", ".docx", ".epub", ".html", ".htm"}
LABEL_FILENAMES = {"labels.csv", "labels.json", "train.csv", "metadata.csv", "annotations.json", "annotations.csv"}

# Cap how deep / how many files we sniff to keep this fast on large folders.
MAX_FILES_SCAN = 2000
MAX_DEPTH = 4


def _iter_files(root: Path):
    """Walk root up to MAX_DEPTH, yielding files until MAX_FILES_SCAN."""
    count = 0
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).parts) - root_depth
        if depth > MAX_DEPTH:
            dirnames[:] = []
            continue
        # Skip noisy hidden/build dirs
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {"__pycache__", "node_modules", ".git"}]
        for fn in filenames:
            yield Path(dirpath) / fn
            count += 1
            if count >= MAX_FILES_SCAN:
                return


def _classify_directory(path: Path) -> dict:
    """Inspect a directory, return a counts breakdown by file family."""
    counts = {
        "tabular": 0,
        "image": 0,
        "audio": 0,
        "video": 0,
        "text_doc": 0,
        "rag_heavy": 0,
        "label_file": 0,
        "other": 0,
        "total": 0,
    }
    for f in _iter_files(path):
        ext = f.suffix.lower()
        name = f.name.lower()
        counts["total"] += 1
        if name in LABEL_FILENAMES:
            counts["label_file"] += 1
        if ext in TABULAR_EXTS:
            counts["tabular"] += 1
        elif ext in IMAGE_EXTS:
            counts["image"] += 1
        elif ext in AUDIO_EXTS:
            counts["audio"] += 1
        elif ext in VIDEO_EXTS:
            counts["video"] += 1
        elif ext in TEXT_DOC_EXTS:
            counts["text_doc"] += 1
            if ext in RAG_HEAVY_EXTS:
                counts["rag_heavy"] += 1
        else:
            counts["other"] += 1
    return counts


def _decide_from_counts(counts: dict) -> dict:
    total = counts["total"]
    if total == 0:
        return {
            "track": "tabular",
            "subtype": None,
            "confidence": 0.0,
            "reason": "Empty directory; defaulting to tabular with zero confidence",
            "ambiguous": True,
        }

    image_frac = counts["image"] / total
    audio_frac = counts["audio"] / total
    text_doc_frac = counts["text_doc"] / total
    rag_heavy_frac = counts["rag_heavy"] / total
    tabular_frac = counts["tabular"] / total

    # Strong single-family signals
    if image_frac >= 0.6:
        if text_doc_frac >= 0.2:
            return {
                "track": "dl",
                "subtype": "multimodal",
                "confidence": 0.7,
                "reason": f"Images dominate ({image_frac:.0%}) with non-trivial text ({text_doc_frac:.0%}); multimodal DL",
                "ambiguous": True,
            }
        return {
            "track": "dl",
            "subtype": "cv-classification",
            "confidence": 0.85,
            "reason": f"Image files dominate ({image_frac:.0%})",
            "ambiguous": False,
        }
    if audio_frac >= 0.6:
        return {
            "track": "dl",
            "subtype": "audio",
            "confidence": 0.85,
            "reason": f"Audio files dominate ({audio_frac:.0%})",
            "ambiguous": False,
        }
    if rag_heavy_frac >= 0.4 or (text_doc_frac >= 0.6 and counts["rag_heavy"] > 0):
        return {
            "track": "rag",
            "subtype": "text-rag",
            "confidence": 0.85,
            "reason": f"PDF/HTML/DOCX-style documents dominate ({rag_heavy_frac:.0%} heavy, {text_doc_frac:.0%} text)",
            "ambiguous": False,
        }
    if text_doc_frac >= 0.6:
        # Plain text + maybe a labels file -> NLP DL, otherwise text-rag
        if counts["label_file"] > 0:
            return {
                "track": "dl",
                "subtype": "nlp-classification",
                "confidence": 0.75,
                "reason": "Text files with a labels file present; NLP supervised DL",
                "ambiguous": False,
            }
        return {
            "track": "rag",
            "subtype": "text-rag",
            "confidence": 0.6,
            "reason": "Plain text documents without labels; defaulting to RAG",
            "ambiguous": True,
        }
    if tabular_frac >= 0.6:
        return {
            "track": "tabular",
            "subtype": None,
            "confidence": 0.85,
            "reason": f"Tabular files dominate ({tabular_frac:.0%})",
            "ambiguous": False,
        }

    # Mixed bag - pick the largest family but flag ambiguous
    largest = max(
        ("tabular", counts["tabular"]),
        ("image", counts["image"]),
        ("audio", counts["audio"]),
        ("text_doc", counts["text_doc"]),
        key=lambda x: x[1],
    )
    family_to_track = {
        "tabular": ("tabular", None),
        "image": ("dl", "cv-classification"),
        "audio": ("dl", "audio"),
        "text_doc": ("rag", "text-rag"),
    }
    track, subtype = family_to_track[largest[0]]
    return {
        "track": track,
        "subtype": subtype,
        "confidence": 0.4,
        "reason": f"Mixed contents; largest family is {largest[0]} ({largest[1]}/{total})",
        "ambiguous": True,
    }


def detect(input_path: str, type_override: str = None) -> dict:
    p = Path(input_path).expanduser()
    if not p.exists():
        return {
            "input_path": str(p),
            "track": None,
            "subtype": None,
            "confidence": 0.0,
            "reason": f"Path does not exist: {p}",
            "ambiguous": True,
            "error": "path_not_found",
        }

    if type_override:
        return {
            "input_path": str(p),
            "track": type_override,
            "subtype": None,
            "confidence": 1.0,
            "reason": f"User override via --type-override {type_override}",
            "ambiguous": False,
            "overridden": True,
        }

    if p.is_file():
        ext = p.suffix.lower()
        if ext in TABULAR_EXTS:
            return {
                "input_path": str(p),
                "track": "tabular",
                "subtype": None,
                "confidence": 0.95,
                "reason": f"Single tabular file ({ext})",
                "ambiguous": False,
            }
        if ext in IMAGE_EXTS:
            return {
                "input_path": str(p),
                "track": "dl",
                "subtype": "cv-classification",
                "confidence": 0.6,
                "reason": "Single image file - DL track but unusual to run on one image",
                "ambiguous": True,
            }
        if ext in AUDIO_EXTS:
            return {
                "input_path": str(p),
                "track": "dl",
                "subtype": "audio",
                "confidence": 0.6,
                "reason": "Single audio file",
                "ambiguous": True,
            }
        if ext in TEXT_DOC_EXTS:
            return {
                "input_path": str(p),
                "track": "rag",
                "subtype": "text-rag",
                "confidence": 0.6,
                "reason": f"Single document file ({ext}); RAG track",
                "ambiguous": True,
            }
        return {
            "input_path": str(p),
            "track": "tabular",
            "subtype": None,
            "confidence": 0.0,
            "reason": f"Unknown file extension {ext}; defaulting to tabular with zero confidence",
            "ambiguous": True,
        }

    # Directory
    counts = _classify_directory(p)
    decision = _decide_from_counts(counts)
    decision["input_path"] = str(p)
    decision["counts"] = counts
    return decision


def main():
    ap = argparse.ArgumentParser(description="Detect DataForge execution track for an input path")
    ap.add_argument("--input", required=True, help="Path to dataset file or directory")
    ap.add_argument("--output", help="Optional path to write JSON result")
    ap.add_argument("--type-override", choices=["tabular", "dl", "rag"], help="Force a specific track")
    args = ap.parse_args()

    result = detect(args.input, args.type_override)

    out_text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out_text, encoding="utf-8")
    print(out_text)

    if result.get("error") == "path_not_found":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
