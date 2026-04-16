---
name: df-rag-orchestrator
description: Build production RAG (Retrieval-Augmented Generation) systems for semantic search and Q&A. Semantic chunking, hybrid retrieval, reranking, and citation accuracy. Consolidated from 5 RAG skills (data-ingestion, chunking-strategy, embedding-selection, vector-indexing, retrieval-optimization).
---

# RAG Orchestrator

## Purpose

Build end-to-end RAG systems: ingest documents → chunk semantically → embed → index → retrieve → rank → generate cited answers.

## RAG Pipeline

```
Documents (PDF, HTML, MD)
    ↓ [Ingestion & Parsing]
Structured text
    ↓ [Semantic Chunking]
Chunks (512 tokens, 10% overlap)
    ↓ [Embedding]
Dense vectors (1536-dim)
    ↓ [Vector Index]
Pinecone / FAISS / Weaviate
    ↓ [User Query]
    ↓ [Hybrid Retrieval]
    ├─ BM25 (sparse): keywords
    ├─ Dense (embedding): semantic
    └─ Rerank (cross-encoder)
    ↓ [Top 5 Results]
    ↓ [Context Assembly]
    ↓ [LLM Generation]
    ↓ [Cited Answer]
```

## Phase 1: Document Ingestion

**Preserve document structure:**

```python
import PyPDF2
import markdown

def ingest_pdf(filepath):
    """Extract text while preserving structure (sections, tables)."""
    reader = PyPDF2.PdfReader(filepath)
    pages = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        pages.append({
            "page": page_num + 1,
            "text": text,
            "content_type": "text"  # or "table", "image"
        })
    
    return pages

def ingest_markdown(filepath):
    """Parse markdown preserving headers (sections)."""
    with open(filepath, 'r') as f:
        text = f.read()
    
    # Extract headers as section boundaries
    sections = []
    current_section = None
    
    for line in text.split('\n'):
        if line.startswith('#'):
            if current_section:
                sections.append(current_section)
            current_section = {"heading": line, "content": []}
        elif current_section:
            current_section["content"].append(line)
    
    return sections
```

## Phase 2: Semantic Chunking

**Preserve boundaries, not fixed sizes:**

```python
def semantic_chunk(text, chunk_size=512, overlap=50):
    """
    Split by semantic boundaries (sentences, paragraphs)
    not arbitrary token counts.
    """
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        tokens = len(sentence.split())
        
        if current_size + tokens > chunk_size:
            # Start new chunk
            chunks.append('. '.join(current_chunk) + '.')
            # Overlap: last sentence repeats in next chunk
            current_chunk = [sentence]
            current_size = tokens
        else:
            current_chunk.append(sentence)
            current_size += tokens
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks
```

**Why not fixed-size chunks?**
```
Bad: Split at 512 tokens exactly
  → Chunks mid-sentence, losing context
  → Boundaries arbitrary

Good: Split at sentence boundaries
  → Preserves meaning
  → Natural chunk sizes (450-550 tokens)
```

## Phase 3: Embedding Selection

**Choose model based on use case:**

```python
# Dense embedding (semantic similarity)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, lightweight
# OR
model = SentenceTransformer('all-mpnet-base-v2')  # Slower, more accurate
# OR
embeddings = OpenAI embeddings (API-based, 1536-dim)
```

**Model comparison:**

| Model | Dim | Speed | Accuracy | Cost |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | 384 | Fast | Good | Free |
| all-mpnet-base-v2 | 768 | Medium | Better | Free |
| text-embedding-3-small | 1536 | API | Excellent | $0.02/1M |
| text-embedding-3-large | 3072 | API | Excellent | $0.02/1M |

**Decision:**
```
If cost-sensitive OR large corpus:
  → all-MiniLM-L6-v2 (fast, good enough)

If accuracy critical:
  → text-embedding-3-large (best, slightly expensive)

If hybrid search (BM25 + dense):
  → Either (dense retrieval less critical if BM25 pre-filters)
```

## Phase 4: Vector Indexing

**Store embeddings with metadata:**

```python
import pinecone

# Initialize
pinecone.init(api_key="...", environment="us-west1-gcp")
index = pinecone.Index("documents")

# Upsert vectors with metadata
index.upsert(vectors=[
    {
        "id": "doc-123-chunk-5",
        "values": [0.1, 0.2, ..., 0.9],  # 1536-dim embedding
        "metadata": {
            "document": "research_paper.pdf",
            "page": 5,
            "section": "Methods",
            "text": "The experiment used 100 samples..."
        }
    },
    ...
])

# Query
results = index.query(
    vector=[0.1, 0.2, ...],  # Query embedding
    top_k=20,
    include_metadata=True,
    filter={"document": "research_paper.pdf"}  # Optional filtering
)
```

## Phase 5: Hybrid Retrieval

**Combine sparse (BM25) + dense (embedding) + rerank:**

```python
def hybrid_retrieve(query_text, top_k=5):
    # Step 1: Sparse retrieval (BM25)
    bm25_results = bm25_index.retrieve(query_text, top_k=100)
    
    # Step 2: Dense retrieval (embedding)
    query_embedding = model.encode(query_text)
    dense_results = vector_index.query(query_embedding, top_k=100)
    
    # Step 3: Combine and deduplicate
    combined = {}
    for result in bm25_results:
        combined[result["id"]] = {
            "score_bm25": result["score"],
            "text": result["text"],
            "metadata": result["metadata"]
        }
    
    for result in dense_results:
        if result["id"] in combined:
            combined[result["id"]]["score_dense"] = result["score"]
        else:
            combined[result["id"]] = {
                "score_dense": result["score"],
                "text": result["text"],
                "metadata": result["metadata"]
            }
    
    # Step 4: Rerank top-K candidates
    candidates = list(combined.values())[:50]
    
    from sentence_transformers import CrossEncoder
    reranker = CrossEncoder('cross-encoder/mmarco-MiniLMv2-L12')
    scores = reranker.predict([
        [query_text, c["text"]] for c in candidates
    ])
    
    # Sort by rerank scores
    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    return [c[0] for c in ranked[:top_k]]
```

**Why hybrid?**
```
BM25 alone:
  ✓ Fast, keyword-based
  ✗ Misses semantic similarity

Dense alone:
  ✓ Semantic, catches synonyms
  ✗ Can miss exact keywords

Hybrid:
  ✓ Best of both: keywords + semantics
  ✓ Rerank improves quality
```

## Phase 6: Context Assembly

**Merge chunks, add citations:**

```python
def assemble_context(retrieved_chunks):
    """Merge overlapping chunks, add citations."""
    
    # Sort by original document position
    sorted_chunks = sorted(
        retrieved_chunks,
        key=lambda x: (x["metadata"]["document"], x["metadata"]["page"])
    )
    
    # Merge overlapping chunks (from same section)
    merged = []
    current = None
    
    for chunk in sorted_chunks:
        if current and is_overlapping(current, chunk):
            # Merge
            current["text"] += " " + chunk["text"]
        else:
            if current:
                merged.append(current)
            current = chunk
    
    if current:
        merged.append(current)
    
    # Add citations
    context = []
    for chunk in merged:
        citation = f"[{chunk['metadata']['document']}:{chunk['metadata']['page']}:{chunk['metadata']['section']}]"
        context.append(f"{chunk['text']} {citation}")
    
    return "\n\n".join(context)
```

## Quality Metrics

```python
# Recall: % of relevant documents in top-K
relevant_docs = set(...)  # Known relevant docs
retrieved_docs = set([r["id"] for r in results[:10]])
recall = len(relevant_docs & retrieved_docs) / len(relevant_docs)
print(f"Recall@10: {recall:.1%}")  # Goal: > 90%

# MRR: Mean Reciprocal Rank
mrr = 0
for rank, result in enumerate(results, 1):
    if is_relevant(result):
        mrr = 1 / rank
        break
print(f"MRR: {mrr:.3f}")  # Goal: > 0.8

# Citation accuracy: % of claims with correct source
claims_vs_sources = validate_claims(answer, retrieved_chunks)
citation_accuracy = claims_vs_sources["correct"] / claims_vs_sources["total"]
print(f"Citation accuracy: {citation_accuracy:.1%}")  # Goal: > 95%

# Latency: p99 retrieval + rerank time
latencies = [...]
p99_latency = np.percentile(latencies, 99)
print(f"Latency p99: {p99_latency:.0f}ms")  # Goal: < 500ms
```

---

## Memory Tracking

```json
{
  "run_id": "2026-04-17_rag_001",
  "corpus": "100 research papers (500MB text)",
  "chunking": "semantic, 512 tokens, 10% overlap",
  "embedding_model": "all-mpnet-base-v2",
  "vector_index": "Pinecone (50k vectors)",
  "retrieval_strategy": "hybrid (BM25 + dense + rerank)",
  "quality_metrics": {
    "recall@10": 0.92,
    "mrr": 0.87,
    "citation_accuracy": 0.98,
    "latency_p99_ms": 350
  },
  "outcomes": "Production-ready RAG; 92% recall, 350ms latency",
  "next_time": "Semantic chunking + hybrid retrieval optimal; scale this pattern"
}
```

---

## Implementation Checklist

- [ ] Ingest documents (PDF, HTML, markdown)
- [ ] Parse structure (preserve sections, tables)
- [ ] Semantic chunking (sentence boundaries, overlap)
- [ ] Select embedding model (cost vs accuracy tradeoff)
- [ ] Create vector index (Pinecone / FAISS / Weaviate)
- [ ] Implement BM25 index (sparse retrieval)
- [ ] Implement dense retrieval (embedding similarity)
- [ ] Implement reranking (cross-encoder)
- [ ] Merge overlapping chunks (context assembly)
- [ ] Add citations (source attribution)
- [ ] Measure quality (recall, MRR, citation accuracy)
- [ ] Monitor latency (p99 < 500ms)

