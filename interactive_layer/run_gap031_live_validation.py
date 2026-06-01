#!/usr/bin/env python3
"""GAP_031 Phase 1 — Live Acceptance Validation.

Runs the 8-test acceptance matrix against the live Interactive Layer server
with Phase 1 router implementation active.

Usage:
    python run_gap031_live_validation.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

# 8-test acceptance matrix prompts (from architecture design)
TESTS = [
    {
        "id": 1,
        "name": "Direct simple answer",
        "prompt": "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
        "expected_route": "DIRECT_LIGHTWEIGHT_RESPONSE",
    },
    {
        "id": 2,
        "name": "Self-state retrieval",
        "prompt": "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
        "expected_route": "INTERNAL_PROJECT_DOC_REASONING",
    },
    {
        "id": 3,
        "name": "Strategic recommendation",
        "prompt": "Készíts rövid döntési memót: a Project-S következő UI-fejlesztése.",
        "expected_route": "FULL_AGENTIC_META_CONTROLLER",
    },
    {
        "id": 4,
        "name": "Diagnostic advice",
        "prompt": "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
        "expected_route": "DIRECT_LIGHTWEIGHT_RESPONSE",
    },
    {
        "id": 5,
        "name": "External research",
        "prompt": "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM.",
        "expected_route": "EXTERNAL_RESEARCH_SYNTHESIS",
    },
    {
        "id": 6,
        "name": "Internal-doc reasoning",
        "prompt": "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.",
        "expected_route": "INTERNAL_PROJECT_DOC_REASONING",
    },
    {
        "id": 7,
        "name": "Output-format compliance",
        "prompt": "Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel. Téma: mi működik most jól a Project-S-ben.",
        "expected_route": "DIRECT_LIGHTWEIGHT_RESPONSE",
    },
    {
        "id": 8,
        "name": "Truthfulness / impossible prediction",
        "prompt": "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
        "expected_route": "TRUTHFUL_UNCERTAINTY_RESPONSE",
    },
]


def api_post(path: str, data: dict) -> tuple[int, dict]:
    """POST to the API and return (status, body)."""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def api_get(path: str) -> tuple[int, dict]:
    """GET from the API and return (status, body)."""
    url = f"{BASE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def run_test(test: dict) -> dict:
    """Run a single acceptance test and return results."""
    tid = test["id"]
    prompt = test["prompt"]
    expected_route = test["expected_route"]

    print(f"\n{'='*70}")
    print(f"TEST_{tid}: {test['name']}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"Expected route: {expected_route}")
    print(f"{'='*70}")

    start = time.time()

    # Step 1: Create session
    status, session = api_post("/api/sessions", {"user_id": "toti"})
    if status != 200:
        return {"id": tid, "status": "ERROR", "error": "Failed to create session"}
    session_id = session.get("session_id", "")

    # Step 2: Submit prompt via /api/chat
    status, chat_resp = api_post("/api/chat", {
        "user_id": "toti",
        "session_id": session_id,
        "message": prompt,
    })
    if status != 200:
        return {"id": tid, "status": "ERROR", "error": f"Chat API returned {status}"}

    mission_id = chat_resp.get("mission_id", "")
    print(f"  Mission ID: {mission_id}")

    # Step 3: Poll mission status until terminal or timeout
    max_wait = 120  # 120s observation window
    poll_interval = 2
    terminal_states = {"COMPLETE", "FAILED", "TIMEOUT"}
    final_state = "QUEUED"
    final_result = ""
    route_type = ""
    route_confidence = 0.0
    route_rationale = ""
    route_matched_rules = []

    for _ in range(max_wait // poll_interval):
        time.sleep(poll_interval)
        elapsed = time.time() - start

        # Get mission details
        status, mission = api_get(f"/api/missions/{mission_id}")
        if status == 200:
            final_state = mission.get("state", "UNKNOWN")
            final_result = mission.get("result", "") or ""
            route_type = mission.get("route_type", "")
            route_confidence = mission.get("route_confidence", 0.0)
            route_rationale = mission.get("route_rationale", "")
            route_matched_rules = mission.get("route_matched_rules", [])

            if final_state in terminal_states:
                break

            print(f"  [{elapsed:.0f}s] State: {final_state}")

    elapsed = time.time() - start

    # Step 4: Determine PASS/PARTIAL/FAIL
    metacontroller_bypassed = route_type in (
        "DIRECT_LIGHTWEIGHT_RESPONSE",
        "TRUTHFUL_UNCERTAINTY_RESPONSE",
        "INTERNAL_PROJECT_DOC_REASONING",
    )

    # Check if result is non-empty and reasonable
    result_ok = len(final_result) > 20 if final_result else False

    # Check if route matches expected
    route_matches = route_type == expected_route

    if final_state == "COMPLETE" and result_ok:
        if route_matches:
            verdict = "PASS"
        else:
            verdict = "PARTIAL"  # Completed but wrong route
    elif final_state in ("FAILED", "TIMEOUT"):
        verdict = "FAIL"
    else:
        verdict = "FAIL"  # Not terminal within observation window

    # Truncate result for display
    result_display = final_result[:200] if final_result else "(empty)"

    return {
        "id": tid,
        "name": test["name"],
        "prompt": prompt[:100],
        "expected_route": expected_route,
        "actual_route": route_type,
        "route_confidence": route_confidence,
        "route_rationale": route_rationale,
        "route_matched_rules": route_matched_rules,
        "terminal_state": final_state,
        "elapsed_seconds": round(elapsed, 1),
        "result": result_display,
        "verdict": verdict,
        "metacontroller_bypassed": metacontroller_bypassed,
    }


def main():
    """Run the full 8/8 acceptance matrix."""
    print("=" * 70)
    print("GAP_031 Phase 1 — Live Acceptance Validation")
    print(f"Server: {BASE_URL}")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Tests: {len(TESTS)}")
    print("=" * 70)

    # Health check
    status, health = api_get("/health")
    if status != 200:
        print(f"ERROR: Server not healthy. Status: {status}")
        sys.exit(1)
    print(f"Server health: {health}")

    results = []
    for test in TESTS:
        try:
            r = run_test(test)
            results.append(r)
        except Exception as e:
            results.append({
                "id": test["id"],
                "name": test["name"],
                "error": str(e),
                "verdict": "FAIL",
            })

    # Summary
    print(f"\n{'='*70}")
    print("ACCEPTANCE MATRIX RESULTS")
    print(f"{'='*70}")

    pass_count = 0
    partial_count = 0
    fail_count = 0

    for r in results:
        tid = r["id"]
        verdict = r.get("verdict", "FAIL")
        actual = r.get("actual_route", "N/A")
        elapsed = r.get("elapsed_seconds", 0)
        state = r.get("terminal_state", "N/A")

        if verdict == "PASS":
            pass_count += 1
        elif verdict == "PARTIAL":
            partial_count += 1
        else:
            fail_count += 1

        icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}.get(verdict, "❓")
        print(f"  TEST_{tid}: {icon} {verdict} | route={actual} | state={state} | {elapsed}s")

    print(f"\n{'='*70}")
    print(f"SUMMARY: {pass_count} PASS, {partial_count} PARTIAL, {fail_count} FAIL")
    print(f"{'='*70}")

    # Detailed results for report
    return results


if __name__ == "__main__":
    results = main()

    # Write JSON results for report generation
    output_path = Path(__file__).parent.parent / "reports" / "GAP_031_LIVE_VALIDATION_RESULTS_20260520.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "server": BASE_URL,
            "total": len(results),
            "pass": sum(1 for r in results if r.get("verdict") == "PASS"),
            "partial": sum(1 for r in results if r.get("verdict") == "PARTIAL"),
            "fail": sum(1 for r in results if r.get("verdict") == "FAIL"),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {output_path}")