"""GAP_031 Phase 1 — Chat smoke test helper.

Usage (run from repo root):
    python -m interactive_layer._debug_gap031_chat_smoke

Steps:
1. POST /api/sessions  → create a real session
2. POST /api/chat      → TEST_1 prompt
3. Print: status code, response body, any error details

Designed as a standalone file, NOT an inline python -c snippet.
"""
from __future__ import annotations

import json
import sys
import traceback
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"
TEST_PROMPT = "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció."


def _post(path: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return exc.code, parsed


def main() -> None:
    print("=" * 60)
    print("GAP_031 Phase 1 — Chat smoke test (TEST_1)")
    print("=" * 60)

    # ── Step 1: create session ──────────────────────────────────
    print("\n[1] POST /api/sessions ...")
    status, body = _post("/api/sessions", {"user_id": "toti"})
    print(f"    status : {status}")
    print(f"    body   : {json.dumps(body, ensure_ascii=False, indent=2)}")

    if status != 200:
        print("\n!! Session creation failed — aborting smoke test.")
        sys.exit(1)

    session_id = body["session_id"]
    print(f"    session_id = {session_id}")

    # ── Step 2: POST /api/chat ──────────────────────────────────
    print(f"\n[2] POST /api/chat ...")
    print(f"    prompt : {TEST_PROMPT!r}")
    chat_status, chat_body = _post(
        "/api/chat",
        {
            "user_id": "toti",
            "session_id": session_id,
            "message": TEST_PROMPT,
        },
    )
    print(f"    status : {chat_status}")
    print(f"    body   : {json.dumps(chat_body, ensure_ascii=False, indent=2)}")

    # ── Step 3: evaluate ────────────────────────────────────────
    print("\n" + "=" * 60)
    if chat_status == 200:
        print("RESULT : PASS — HTTP 200")
        mission_id = chat_body.get("mission_id", "N/A")
        route = chat_body.get("response", "")
        print(f"  mission_id : {mission_id}")
        print(f"  response   : {route[:120]}")
        sys.exit(0)
    else:
        print(f"RESULT : FAIL — HTTP {chat_status}")
        if "detail" in chat_body:
            print(f"  error detail : {chat_body['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(3)
