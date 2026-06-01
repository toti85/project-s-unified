#!/usr/bin/env python3
"""
Project-S RAG Query Interface V1
==================================
Searches the BGE-M3 indexed Project-S documents using cosine similarity.

Usage:
    python query_index.py "Mi a Project-S jelenlegi active focus?"
    python query_index.py --top 5 "Milyen lokalis modellek vannak a DL380-on?"
"""

import json, sys, argparse
import numpy as np
import requests
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
EMBED_URL     = "http://127.0.0.1:8099/v1/embeddings"
INDEX_DIR     = Path("F:/ModelVault/rag/project_s_index_v1")
VECTORS_FILE  = INDEX_DIR / "vectors.npy"
METADATA_FILE = INDEX_DIR / "metadata.jsonl"


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_index():
    vectors = np.load(str(VECTORS_FILE))
    metadata = []
    with open(METADATA_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                metadata.append(json.loads(line))
    return vectors, metadata


def get_embedding(text: str) -> np.ndarray:
    r = requests.post(
        EMBED_URL,
        json={"model": "bge-m3", "input": text},
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    r.raise_for_status()
    return np.array(r.json()["data"][0]["embedding"], dtype=np.float32)


def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Vectorized cosine similarity: query (1024,) vs matrix (N, 1024)."""
    q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    m_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    m_normed = matrix / m_norms
    return m_normed @ q_norm  # (N,)


def search(query: str, top_k: int = 3) -> list:
    vectors, metadata = load_index()
    q_vec = get_embedding(query)
    scores = cosine_similarity(q_vec, vectors)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for rank, idx in enumerate(top_indices):
        meta = metadata[idx].copy()
        meta["score"] = float(scores[idx])
        meta["rank"] = rank + 1
        results.append(meta)
    return results


def print_results(query: str, results: list):
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")
    for r in results:
        print(f"\n[Rank {r['rank']} | score={r['score']:.4f}]")
        print(f"  File  : {r['file_path']}")
        print(f"  Type  : {r['chunk_type']}")
        label = r.get("header") or r.get("label") or r.get("name") or ""
        if label:
            print(f"  Label : {label}")
        print(f"  Lines : {r['start_line']}–{r['end_line']}")
        preview = r.get("text_preview") or r.get("text", "")[:150]
        print(f"  Preview: {preview[:200]}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Project-S RAG Query V1")
    parser.add_argument("query", nargs="?", help="Query string")
    parser.add_argument("--top", type=int, default=3, help="Number of results (default: 3)")
    parser.add_argument("--batch", action="store_true", help="Run predefined smoke queries")
    args = parser.parse_args()

    if args.batch:
        smoke_queries = [
            "Mi a Project-S jelenlegi active focus?",
            "Mi a GAP_031 statusza?",
            "Milyen lokalis modellek vannak a DL380-on?",
            "Hol van az Interactive Layer router?",
            "Mi a kovetkezo Project-S fejlesztesi irany?",
        ]
        print("Loading index...")
        vectors, metadata = load_index()
        print(f"Index loaded: {len(metadata)} chunks, vectors {vectors.shape}")

        for q in smoke_queries:
            try:
                q_vec = get_embedding(q)
                scores = cosine_similarity(q_vec, vectors)
                top_indices = np.argsort(scores)[::-1][:3]
                results = []
                for rank, idx in enumerate(top_indices):
                    meta = metadata[idx].copy()
                    meta["score"] = float(scores[idx])
                    meta["rank"] = rank + 1
                    results.append(meta)
                print_results(q, results)
            except Exception as e:
                print(f"ERROR on query '{q}': {e}")
        return

    if not args.query:
        parser.print_help()
        return

    results = search(args.query, args.top)
    print_results(args.query, results)


if __name__ == "__main__":
    main()
