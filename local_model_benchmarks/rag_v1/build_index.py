#!/usr/bin/env python3
"""
Project-S RAG Indexer V1 — BGE-M3 powered
==========================================
Indexes Project-S source documents into a JSONL + numpy vector store.

Usage (on DL380):
    python build_index.py

Reads from:  F:\ModelVault\rag\project_s_docs\
Writes to:   F:\ModelVault\rag\project_s_index_v1\
Embeds via:  http://127.0.0.1:8099/v1/embeddings
"""

import json, os, re, sys, time
import numpy as np
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────
EMBED_URL  = "http://127.0.0.1:8099/v1/embeddings"
DOCS_DIR   = Path("F:/ModelVault/rag/project_s_docs")
INDEX_DIR  = Path("F:/ModelVault/rag/project_s_index_v1")
VECTORS_FILE  = INDEX_DIR / "vectors.npy"
METADATA_FILE = INDEX_DIR / "metadata.jsonl"
MANIFEST_FILE = INDEX_DIR / "index_manifest.json"

CHUNK_MAX_CHARS = 2048   # ~512 tokens
CHUNK_OVERLAP   = 200    # ~50 tokens


# ── Embedding ───────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list:
    text = text[:8000]  # BGE-M3 max
    r = requests.post(
        EMBED_URL,
        json={"model": "bge-m3", "input": text},
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


# ── Chunkers ────────────────────────────────────────────────────────────────

def chunk_by_size(text: str, file_path: str, chunk_type: str = "text") -> list:
    """Fallback: fixed-size sliding-window chunks."""
    lines = text.splitlines(keepends=True)
    chunks = []
    current = ""
    start_line = 1

    for line_num, line in enumerate(lines, 1):
        current += line
        if len(current) >= CHUNK_MAX_CHARS:
            t = current.strip()
            if t:
                chunks.append({
                    "file_path": file_path,
                    "chunk_type": chunk_type,
                    "start_line": start_line,
                    "end_line": line_num,
                    "text": t,
                })
            # keep overlap tail
            current = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else ""
            start_line = line_num

    t = current.strip()
    if t:
        chunks.append({
            "file_path": file_path,
            "chunk_type": chunk_type,
            "start_line": start_line,
            "end_line": len(lines),
            "text": t,
        })
    return chunks


def chunk_markdown(text: str, file_path: str) -> list:
    """Split markdown by #/##/### section headers."""
    lines = text.splitlines(keepends=True)
    chunks = []
    current_text = ""
    current_header = "(preamble)"
    start_line = 1

    for line_num, line in enumerate(lines, 1):
        is_header = re.match(r'^#{1,3} ', line)
        if is_header and current_text.strip():
            t = current_text.strip()
            if len(t) > 80:
                chunks.append({
                    "file_path": file_path,
                    "chunk_type": "markdown_section",
                    "start_line": start_line,
                    "end_line": line_num - 1,
                    "text": f"[{current_header}]\n{t}",
                    "header": current_header,
                })
            # oversized section → sub-chunk
            elif len(t) > CHUNK_MAX_CHARS * 2:
                for sub in chunk_by_size(current_text, file_path, "markdown_subsection"):
                    sub["header"] = current_header
                    chunks.append(sub)
            current_text = line
            current_header = line.strip().lstrip("#").strip()
            start_line = line_num
        else:
            current_text += line

    # last section
    t = current_text.strip()
    if t and len(t) > 80:
        if len(t) > CHUNK_MAX_CHARS * 2:
            for sub in chunk_by_size(current_text, file_path, "markdown_subsection"):
                sub["header"] = current_header
                chunks.append(sub)
        else:
            chunks.append({
                "file_path": file_path,
                "chunk_type": "markdown_section",
                "start_line": start_line,
                "end_line": len(lines),
                "text": f"[{current_header}]\n{t}",
                "header": current_header,
            })

    if not chunks:
        return chunk_by_size(text, file_path, "markdown_text")
    return chunks


def chunk_python(text: str, file_path: str) -> list:
    """Split Python by top-level class/def boundaries."""
    lines = text.splitlines(keepends=True)
    chunks = []
    current_text = ""
    current_name = "(module_top)"
    start_line = 1

    for line_num, line in enumerate(lines, 1):
        m = re.match(r'^(class |def )(\w+)', line)
        if m and current_text.strip() and line_num > start_line + 3:
            kind = m.group(1).strip()
            t = current_text.strip()
            if len(t) > 50:
                chunks.append({
                    "file_path": file_path,
                    "chunk_type": f"python_{kind}",
                    "start_line": start_line,
                    "end_line": line_num - 1,
                    "text": t,
                    "name": current_name,
                })
            current_text = line
            current_name = f"{m.group(1).strip()} {m.group(2)}"
            start_line = line_num
        else:
            current_text += line

        # flush oversized accumulation mid-file
        if len(current_text) > CHUNK_MAX_CHARS * 3:
            t = current_text.strip()
            chunks.append({
                "file_path": file_path,
                "chunk_type": "python_block",
                "start_line": start_line,
                "end_line": line_num,
                "text": t,
                "name": current_name,
            })
            current_text = ""
            start_line = line_num + 1

    t = current_text.strip()
    if t and len(t) > 50:
        chunks.append({
            "file_path": file_path,
            "chunk_type": "python_block",
            "start_line": start_line,
            "end_line": len(lines),
            "text": t,
            "name": current_name,
        })

    if not chunks:
        return chunk_by_size(text, file_path, "python_text")
    return chunks


def chunk_self_state(text: str, file_path: str) -> list:
    """Semantic chunking for self_state.json — milestones + current_state + gaps."""
    try:
        data = json.loads(text)
    except Exception:
        return chunk_by_size(text, file_path, "json_text")

    chunks = []

    def add(label, obj):
        t = json.dumps(obj, indent=2, ensure_ascii=False)
        if len(t) > CHUNK_MAX_CHARS * 2:
            # split large objects into size chunks
            for sub in chunk_by_size(t, file_path, "json_section"):
                sub["label"] = label
                chunks.append(sub)
        else:
            chunks.append({
                "file_path": file_path,
                "chunk_type": "json_section",
                "start_line": 0,
                "end_line": 0,
                "text": f"[{label}]\n{t}",
                "label": label,
            })

    # Current state — key RAG target
    if "current_state" in data:
        add("current_state", data["current_state"])

    # Each milestone individually
    for m in data.get("milestones", []):
        mid = m.get("id", "?")
        mtitle = m.get("title", "")
        add(f"milestone_{mid}: {mtitle}", m)

    # Gaps (batch by 4)
    gaps = data.get("gaps", [])
    for i in range(0, len(gaps), 4):
        batch = gaps[i:i+4]
        ids = [g.get("gap_id", "?") for g in batch]
        add(f"gaps_{ids[0]}_to_{ids[-1]}", batch)

    # b2_strategy section
    if "b2_strategy" in data:
        add("b2_strategy", data["b2_strategy"])

    # Fallback: dump full if nothing extracted
    if not chunks:
        return chunk_by_size(text, file_path, "json_text")
    return chunks


# ── File dispatcher ─────────────────────────────────────────────────────────

def chunk_file(path: Path) -> list:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  SKIP (read error): {e}")
        return []

    if not text.strip():
        return []

    file_str = str(path).replace("\\", "/")
    name = path.name.lower()

    if name == "self_state.json":
        return chunk_self_state(text, file_str)
    elif name.endswith(".json"):
        return chunk_by_size(text, file_str, "json_text")
    elif name.endswith(".md"):
        return chunk_markdown(text, file_str)
    elif name.endswith(".py"):
        return chunk_python(text, file_str)
    else:
        return chunk_by_size(text, file_str, "text")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Project-S RAG Indexer V1")
    print(f"{'='*50}")
    print(f"Docs dir  : {DOCS_DIR}")
    print(f"Index dir : {INDEX_DIR}")
    print(f"Embed URL : {EMBED_URL}")
    print()

    # Collect source files
    if not DOCS_DIR.exists():
        print(f"ERROR: DOCS_DIR not found: {DOCS_DIR}")
        sys.exit(1)

    source_files = sorted(DOCS_DIR.rglob("*"))
    source_files = [f for f in source_files if f.is_file() and not f.name.startswith(".")]
    print(f"Found {len(source_files)} source files")

    # Chunk all files
    all_chunks = []
    files_indexed = 0
    for fpath in source_files:
        rel = fpath.relative_to(DOCS_DIR)
        print(f"  Chunking: {rel}")
        chunks = chunk_file(fpath)
        print(f"    → {len(chunks)} chunks")
        all_chunks.extend(chunks)
        if chunks:
            files_indexed += 1

    print(f"\nTotal chunks to embed: {len(all_chunks)}")

    # Assign chunk IDs + text_preview
    for i, chunk in enumerate(all_chunks):
        chunk["chunk_id"] = i
        preview = chunk["text"][:150].replace("\n", " ").strip()
        chunk["text_preview"] = preview

    # Embed all chunks
    print(f"\nEmbedding {len(all_chunks)} chunks via BGE-M3...")
    vectors = []
    failed = 0
    for i, chunk in enumerate(all_chunks):
        try:
            emb = get_embedding(chunk["text"])
            vectors.append(emb)
            if (i + 1) % 10 == 0 or i == len(all_chunks) - 1:
                print(f"  [{i+1}/{len(all_chunks)}] embedded")
        except Exception as e:
            print(f"  ERROR chunk {i}: {e}")
            vectors.append([0.0] * 1024)  # zero vector placeholder
            failed += 1

    # Save vectors
    arr = np.array(vectors, dtype=np.float32)
    np.save(str(VECTORS_FILE), arr)
    print(f"\nVectors saved: {arr.shape} → {VECTORS_FILE}")

    # Save metadata (without full text to keep it lightweight)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            meta = {k: v for k, v in chunk.items() if k != "text"}
            meta["text"] = chunk["text"]  # keep full text for retrieval
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    print(f"Metadata saved: {METADATA_FILE}")

    # Save manifest
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embed_url": EMBED_URL,
        "embed_model": "bge-m3-Q4_K_M",
        "embed_dim": 1024,
        "vector_store": "numpy_jsonl",
        "files_indexed": files_indexed,
        "total_files": len(source_files),
        "total_chunks": len(all_chunks),
        "embed_failures": failed,
        "vectors_file": str(VECTORS_FILE),
        "metadata_file": str(METADATA_FILE),
        "source_files": [str(f.relative_to(DOCS_DIR)) for f in source_files if f.is_file()],
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest saved: {MANIFEST_FILE}")

    print(f"\n{'='*50}")
    print(f"Index built:")
    print(f"  Files indexed : {files_indexed}")
    print(f"  Total chunks  : {len(all_chunks)}")
    print(f"  Embed failures: {failed}")
    print(f"  Vector shape  : {arr.shape}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
