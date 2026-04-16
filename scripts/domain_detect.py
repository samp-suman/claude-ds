#!/usr/bin/env python3
"""
DataForge — Domain Auto-Detection

Detects the business domain of a dataset by analyzing column names,
filename patterns, and value patterns. Returns the most likely domain
with a confidence score.

Usage:
    python domain_detect.py --data <path> --profile <profile.json> --output <domain.json>

Supported domains: healthcare, finance, marketing, retail, social, manufacturing
Falls back to "general" if confidence < 0.5.

Exit codes: 0 = success, 1 = warning, 2 = fatal error
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Domain keyword dictionaries — column name patterns
DOMAIN_KEYWORDS = {
    "real_estate": [
        "property", "real_estate", "realestate", "price", "bedRoom", "bedroom",
        "bathroom", "bathrm", "bathrooms", "balcony", "area", "sqft", "square_feet",
        "facing", "location", "address", "nearby", "floor", "floorNum", "property_type",
        "agent", "broker", "listing", "sale", "rent", "lease", "tenant", "landlord",
        "mortgage", "loan", "interest_rate", "possession", "agePossession", "building",
        "apartment", "flat", "house", "villa", "bungalow", "commercial", "residential",
        "amenity", "parking", "garden", "pool", "security", "lift", "maintenance",
        "builder", "developer", "society", "colony", "neighborhood", "locality",
        "landmark", "metro", "station", "school", "hospital", "market", "restaurant",
    ],
    "healthcare": [
        "patient", "diagnosis", "icd", "cpt", "hba1c", "bmi", "blood_pressure",
        "vitals", "dosage", "prescription", "admission", "discharge", "readmission",
        "lab_result", "hemoglobin", "cholesterol", "glucose", "heart_rate", "oxygen",
        "symptom", "treatment", "clinical", "medical", "hospital", "nurse", "doctor",
        "surgery", "medication", "allergy", "chronic", "acute", "prognosis",
        "survival", "mortality", "morbidity", "comorbidity", "biopsy", "pathology",
        "radiology", "imaging", "ecg", "ekg", "mri", "ct_scan", "ultrasound",
    ],
    "finance": [
        "balance", "credit", "debit", "transaction", "loan", "interest_rate", "apr",
        "fico", "risk_score", "default", "fraud", "pnl", "revenue", "portfolio",
        "maturity", "yield", "exposure", "collateral", "mortgage", "equity",
        "dividend", "stock", "bond", "asset", "liability", "capital", "leverage",
        "volatility", "sharpe", "drawdown", "return", "spread", "coupon", "notional",
        "settlement", "clearing", "margin", "hedge", "derivative", "option", "futures",
        "credit_score", "debt", "income", "expense", "budget", "account",
    ],
    "marketing": [
        "campaign", "click", "impression", "ctr", "conversion", "bounce", "session",
        "channel", "utm", "clv", "ltv", "churn", "email_open", "unsubscribe",
        "cohort", "attribution", "acquisition", "retention", "engagement",
        "lead", "funnel", "landing_page", "ab_test", "variant", "control",
        "segment", "persona", "journey", "touchpoint", "brand", "awareness",
        "newsletter", "subscriber", "opt_in", "opt_out", "referral", "affiliate",
        "ad_spend", "roas", "cpc", "cpm", "cpa", "roi", "organic", "paid",
    ],
    "retail": [
        "product", "sku", "price", "quantity", "order", "cart", "category",
        "inventory", "discount", "shipping", "return", "basket", "store", "aisle",
        "shelf", "barcode", "upc", "ean", "supplier", "vendor", "warehouse",
        "fulfillment", "delivery", "purchase", "sale", "receipt", "checkout",
        "promotion", "clearance", "markup", "margin", "cost_of_goods", "cogs",
        "stock", "reorder", "backorder", "demand", "forecast", "seasonal",
        "customer_id", "loyalty", "reward", "coupon_code", "gift_card",
    ],
    "social": [
        "post", "like", "share", "comment", "follower", "engagement", "sentiment",
        "hashtag", "mention", "reach", "impression", "retweet", "view", "subscriber",
        "content", "media", "video", "image", "story", "reel", "live", "stream",
        "influencer", "creator", "audience", "community", "viral", "trending",
        "bot", "spam", "troll", "report", "flag", "moderate", "ban",
        "reaction", "emoji", "thread", "reply", "dm", "message", "notification",
        "profile", "bio", "handle", "username", "verified", "platform",
    ],
    "manufacturing": [
        "sensor", "temperature", "pressure", "vibration", "rpm", "cycle_time",
        "defect", "yield", "batch", "lot", "tolerance", "thickness", "viscosity",
        "spc", "control_chart", "cpk", "ppk", "oee", "downtime", "uptime",
        "maintenance", "failure", "mtbf", "mttr", "reliability", "wear",
        "calibration", "inspection", "quality", "reject", "scrap", "rework",
        "machine", "tool", "fixture", "jig", "assembly", "weld", "coating",
        "humidity", "flow_rate", "torque", "force", "displacement", "acceleration",
    ],
}

# Filename patterns
FILENAME_PATTERNS = {
    "real_estate": r"(property|realestate|real_estate|housing|apartment|flat|house|price|rental|estate)",
    "healthcare": r"(patient|clinical|medical|hospital|health|diagnosis|pharma|drug)",
    "finance": r"(transaction|credit|loan|fraud|bank|financ|stock|portfolio|risk)",
    "marketing": r"(campaign|market|churn|customer|lead|email|ad_|advertis|crm)",
    "retail": r"(product|order|sales|store|inventory|retail|ecommerce|shop|basket)",
    "social": r"(social|tweet|post|comment|sentiment|engag|content|influenc|reddit)",
    "manufacturing": r"(sensor|manufactur|factory|machine|quality|defect|mainten|iot)",
}


def score_column_names(columns, domain):
    """Score domain match based on column name keywords."""
    keywords = DOMAIN_KEYWORDS[domain]
    col_lower = [c.lower().replace(" ", "_") for c in columns]
    matches = []
    for kw in keywords:
        for col in col_lower:
            if kw in col:
                matches.append(col)
                break
    if not keywords:
        return 0.0, []
    return min(len(matches) / 5.0, 1.0), list(set(matches))


def score_filename(filename, domain):
    """Score domain match based on filename pattern."""
    pattern = FILENAME_PATTERNS.get(domain, "")
    if not pattern:
        return 0.0
    return 1.0 if re.search(pattern, filename.lower()) else 0.0


def score_value_patterns(profile, domain):
    """Score domain match based on value patterns in the profile."""
    if not profile or "column_profiles" not in profile:
        return 0.0

    score = 0.0
    col_profiles = profile.get("column_profiles", {})

    if domain == "real_estate":
        for col, info in col_profiles.items():
            col_lower = col.lower()
            # Price-like numeric columns suggest real estate
            if col_lower in ("price", "price_numeric", "price_sqft", "priceperunit") and info.get("dtype", "").startswith(("float", "int")):
                score += 0.3
            # Bedroom/bathroom counts
            if col_lower in ("bedroom", "bedRoom", "bathroom", "bathrm", "bathrooms", "balcony"):
                score += 0.2
            # Location/area features
            if col_lower in ("area", "facing", "location", "address", "nearby", "floorNum", "floor"):
                score += 0.2
            # Property type categorical
            if col_lower in ("property_type", "property_type_name", "type"):
                sample_values = info.get("sample_values", [])
                sample_str = " ".join(str(v).lower() for v in sample_values)
                if any(x in sample_str for x in ("apartment", "flat", "house", "villa")):
                    score += 0.25

    elif domain == "healthcare":
        for col, info in col_profiles.items():
            sample_values = info.get("sample_values", [])
            sample_str = " ".join(str(v) for v in sample_values)
            if re.search(r"[A-Z]\d{2}\.\d", sample_str):  # ICD codes
                score += 0.4
            if info.get("dtype") == "float64" and col.lower() in ("bmi", "hba1c", "glucose"):
                score += 0.2

    elif domain == "finance":
        for col, info in col_profiles.items():
            sample_values = info.get("sample_values", [])
            sample_str = " ".join(str(v) for v in sample_values)
            if re.search(r"[\$\u20ac\u00a3]", sample_str):  # Currency symbols
                score += 0.3
            if col.lower() in ("amount", "balance", "credit", "debit"):
                score += 0.2

    elif domain == "manufacturing":
        # Many numeric columns with high-frequency timestamps = sensor data
        n_numeric = sum(1 for info in col_profiles.values()
                        if info.get("dtype", "").startswith(("float", "int")))
        if n_numeric > 10:
            score += 0.4

    elif domain == "social":
        for col, info in col_profiles.items():
            sample_values = info.get("sample_values", [])
            sample_str = " ".join(str(v) for v in sample_values)
            if re.search(r"https?://", sample_str):
                score += 0.2
            if re.search(r"@\w+", sample_str):
                score += 0.2

    return min(score, 1.0)


def detect_domain(data_path, profile_path):
    """Detect the most likely domain for the dataset."""
    # Load profile
    profile = None
    if profile_path and Path(profile_path).exists():
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

    # Get column names
    columns = []
    if profile and "columns" in profile:
        columns = profile["columns"]
    elif profile and "column_profiles" in profile:
        columns = list(profile["column_profiles"].keys())

    # Get filename
    filename = Path(data_path).stem if data_path else ""

    # Score each domain
    scores = {}
    matched_signals = {}

    for domain in DOMAIN_KEYWORDS:
        col_score, col_matches = score_column_names(columns, domain)
        file_score = score_filename(filename, domain)
        value_score = score_value_patterns(profile, domain)

        # Feature type distribution score
        type_score = 0.0
        if profile and "column_profiles" in profile:
            n_cols = len(profile["column_profiles"])
            n_numeric = sum(1 for info in profile["column_profiles"].values()
                            if info.get("dtype", "").startswith(("float", "int")))
            n_binary = sum(1 for info in profile["column_profiles"].values()
                           if info.get("n_unique", 0) == 2)
            if domain == "manufacturing" and n_cols > 0 and n_numeric / max(n_cols, 1) > 0.8:
                type_score = 0.5
            elif domain in ("healthcare", "finance") and n_binary > 3:
                type_score = 0.3

        # Weighted composite
        composite = (col_score * 0.4) + (file_score * 0.2) + (value_score * 0.3) + (type_score * 0.1)
        scores[domain] = composite

        if composite > 0:
            signals = {}
            if col_matches:
                signals["column_names"] = col_matches[:10]
            if file_score > 0:
                signals["filename"] = filename
            if value_score > 0:
                signals["value_patterns"] = True
            matched_signals[domain] = signals

    # Rank
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain = ranked[0][0]
    best_score = ranked[0][1]
    runner_up = ranked[1][0] if len(ranked) > 1 else "general"
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0

    # Threshold: need >= 0.5 to activate domain expert
    if best_score < 0.5:
        best_domain = "general"
        best_score = 1.0 - max(scores.values())

    return {
        "domain": best_domain,
        "confidence": round(best_score, 3),
        "runner_up": runner_up,
        "runner_up_confidence": round(runner_up_score, 3),
        "matched_signals": matched_signals.get(best_domain if best_domain != "general" else ranked[0][0], {}),
        "all_scores": {k: round(v, 3) for k, v in scores.items()},
    }


def main():
    parser = argparse.ArgumentParser(description="DataForge domain auto-detection")
    parser.add_argument("--data", required=True, help="Path to raw dataset")
    parser.add_argument("--profile", default=None, help="Path to profile.json")
    parser.add_argument("--output", required=True, help="Output path for domain.json")
    args = parser.parse_args()

    try:
        result = detect_domain(args.data, args.profile)

        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        # Print JSON result as last line
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        error_result = {"domain": "general", "confidence": 0.0, "error": str(e)}
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
