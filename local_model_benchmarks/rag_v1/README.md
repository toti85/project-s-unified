# Project-S RAG Indexer V1 — BGE-M3

Local vector search over Project-S documentation and source code.

## Architecture

```
F:\ModelVault\rag\project_s_index_v1\
├── build_index.py      — indexes source docs → vectors.npy + metadata.jsonl
├── query_index.py      — cosine search over the index
├── index_manifest.json — build metadata (chunks, files, timestamp)
├── vectors.npy         — (N × 1024) float32 numpy array
├── metadata.jsonl      — one JSON line per chunk (text + metadata)
└── README.md

F:\ModelVault\rag\project_s_docs\
└── (source documents copied from C:\ProjectS-Unified)
```

## Embedding Model

- Model: `BAAI/bge-m3` (Q4_K_M GGUF via gpustack)
- Endpoint: `http://127.0.0.1:8099/v1/embeddings`
- Dimension: 1024
- Multilingual: EN / HU / UK and 100+ languages

## Vector Store

JSONL + numpy cosine similarity (no external vector DB required).
- `vectors.npy` — float32 matrix shape (N, 1024)
- `metadata.jsonl` — one JSON per line: file_path, chunk_id, chunk_type, start_line, end_line, text, text_preview

## Source Documents

| Path | Type | Chunks |
|------|------|--------|
| self_state.json | JSON semantic | ~40+ |
| PROJECT_S_OVERVIEW.md | Markdown sections | varies |
| PROJECT_S_STATUS_AND_JOURNAL.md | Markdown sections | varies |
| docs/*.md (13 files) | Markdown sections | varies |
| interactive_layer/*.py | Python functions | varies |
| src/core/*.py | Python functions | varies |

## Usage

### Build index (on DL380 — BGE-M3 must be running on port 8099)
```powershell
cd F:\ModelVault\rag\project_s_index_v1
python build_index.py
```

### Query
```powershell
python query_index.py "Mi a Project-S jelenlegi active focus?"
python query_index.py --top 5 "Milyen lokalis modellek vannak a DL380-on?"

# All smoke queries
python query_index.py --batch
```

## Chunking Strategy

| File type | Strategy |
|-----------|----------|
| `self_state.json` | Semantic: current_state, each milestone, gap batches, b2_strategy |
| `*.md` | H1/H2/H3 section boundaries |
| `*.py` | `class`/`def` top-level boundaries |
| Fallback | 512-token (~2048 char) sliding window, 50-token overlap |

## Smoke Query Results (2026-05-22)

See: `C:\ProjectS-Unified\reports\PROJECT_S_RAG_INDEXER_V1_BGE_M3_PROOF_20260522.md`

## Next Steps

1. SSH tunnel port 8099 for external query access
2. ChromaDB/FAISS migration when index exceeds ~10k chunks
3. MS-OQ1-A integration: pipe retrieved chunks as context to Qwen2.5-Coder-14B/Qwen3.6-35B
4. Incremental indexing (track file mtimes in manifest)
