#!/usr/bin/env python
"""
Startup helper for Project-S Interactive Layer.

Ensures UTF-8 encoding for Windows console logging,
then launches the FastAPI server via uvicorn.

Usage:
    python interactive_layer/start_server.py
    python -m interactive_layer.start_server
"""

import os
import sys
import io
from pathlib import Path

# ── Add parent directory to sys.path for uvicorn imports ─────────────
# This is critical when running via Start-Process or when CWD != project root.
_REPO_ROOT = str(Path(__file__).parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ── UTF-8 encoding fix (GAP_028) ──────────────────────────────────────
# Windows console uses cp1251 by default, which cannot encode Hungarian
# characters like "Í", "ö", "ü", "á", "é", "ű", "ó".
# Set PYTHONIOENCODING before any logging occurs.

os.environ["PYTHONIOENCODING"] = "utf-8"

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── Launch server ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "interactive_layer.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
