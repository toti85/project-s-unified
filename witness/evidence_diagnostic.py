"""
witness/evidence_diagnostic.py
-------------------------------
Egymenetes diagnosztikai elemzés a meta_evidence.jsonl felett.

NEM módosítja:
  - meta_evidence.jsonl
  - self_state.json

Csak Python stdlib. Streaming olvasás — nem tölt be mindent memóriába.
Kimenet: Markdown riport a witness/reports/ mappába.

Futtatás:
  python -m witness.evidence_diagnostic
"""

import json
import os
import random
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

# --- Útvonalak ---
REPO_ROOT = Path(__file__).parent.parent
META_EVIDENCE_PATH = REPO_ROOT / "memory" / "intelligence" / "meta_evidence.jsonl"
REPORTS_DIR = REPO_ROOT / "witness" / "reports"

KNOWN_EVENTS = [
    "goal_started",
    "plan_selected",
    "execution_done",
    "validation_done",
    "replan_triggered",
    "goal_completed",
    "goal_failed",
]

RESERVOIR_SIZE = 100
INC_PS_SAMPLE = 20          # incidens-nap plan_selected mintaméret
INCIDENT_DATE = "2026-01-14" # az ismert "bumm" nap


def run_diagnostic():
    scan_start = time.monotonic()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── a) Napi eloszlás ──────────────────────────────────────────────────────
    # defaultdict: day -> {total, goal_started, goal_completed, goal_failed}
    daily: dict = {}

    # ── b) Goal ID minták ─────────────────────────────────────────────────────
    completed_goal_ids: list = []          # mind (max ~37 várható)
    reservoir: list = []                    # 100 véletlenszerű goal_id
    reservoir_total = 0                     # hány goal_id-t láttunk összesen

    # ── c) Mezők az első 1000 sorból ─────────────────────────────────────────
    first_1000_top_keys: dict = {}
    first_1000_data_keys: dict = {}
    first_1000_sources: dict = {}

    # ── d) Életciklus párosítás (szekvenciális kontextus) ────────────────────
    # Mivel plan_selected, execution_done stb. nem tartalmaz goal_id-t az adatokban,
    # a legutóbbi goal_started goal_id-ját rendeljük hozzájuk.
    current_goal_id: str | None = None     # aktív goal_id kontextus

    # Egyedi goal_id halmazok fázisonként
    gs_ids: set = set()     # goal_started
    ps_ids: set = set()     # plan_selected
    ed_ids: set = set()     # execution_done
    vd_ids: set = set()     # validation_done
    gc_ids: set = set()     # goal_completed
    gf_ids: set = set()     # goal_failed

    # ── e) Utolsó 100 rekord ─────────────────────────────────────────────────
    last_100: deque = deque(maxlen=100)

    # ── Általános számlálók ───────────────────────────────────────────────────
    total_records = 0
    parse_errors = 0
    event_counts: dict = {}

    # ── f) Execution-done timeline — új szekció ──────────────────────────────
    ed_records: list = []           # teljes lista (max ~40 elem várható)
    gs_timestamps: dict = {}        # goal_id -> ts (goal_started)
    gc_timestamps: dict = {}        # goal_id -> ts (goal_completed)
    gf_timestamps: dict = {}        # goal_id -> ts (goal_failed)
    inc_ps_reservoir: list = []     # incidens-nap plan_selected minta
    inc_ps_count: int = 0

    # ═════════════════════════════════════════════════════════════════════════
    # EGYMENETES BEOLVASÁS
    # ═════════════════════════════════════════════════════════════════════════
    with open(META_EVIDENCE_PATH, encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue

            total_records += 1

            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                last_100.append({"_parse_error": True, "raw": raw_line[:300]})
                continue

            last_100.append(rec)

            ts: str = rec.get("timestamp") or ""
            day: str = ts[:10] if ts else "unknown"
            event_type: str = rec.get("event_type") or "<missing>"
            data = rec.get("data") or {}
            if not isinstance(data, dict):
                data = {}

            # ── Napi számlálók ────────────────────────────────────────────
            if day not in daily:
                daily[day] = {"total": 0, "goal_started": 0,
                               "goal_completed": 0, "goal_failed": 0}
            daily[day]["total"] += 1
            if event_type in ("goal_started", "goal_completed", "goal_failed",
                               "execution_done", "validation_done"):
                daily[day][event_type] = daily[day].get(event_type, 0) + 1

            # ── Event számlálók ───────────────────────────────────────────
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # ── Goal ID kinyerés ─────────────────────────────────────────
            # Elsőbbség: data.goal_id; ha nincs, szekvenciális kontextus
            explicit_gid: str | None = data.get("goal_id") or None

            if event_type == "goal_started" and explicit_gid:
                current_goal_id = explicit_gid
                gs_timestamps[explicit_gid] = ts

            effective_gid: str | None = explicit_gid or current_goal_id

            # ── Reservoir sampling ───────────────────────────────────────
            if effective_gid:
                reservoir_total += 1
                if len(reservoir) < RESERVOIR_SIZE:
                    reservoir.append(effective_gid)
                else:
                    j = random.randint(0, reservoir_total - 1)
                    if j < RESERVOIR_SIZE:
                        reservoir[j] = effective_gid

            # ── Életciklus halmazok ──────────────────────────────────────
            if effective_gid:
                if event_type == "goal_started":
                    gs_ids.add(effective_gid)
                elif event_type == "plan_selected":
                    ps_ids.add(effective_gid)
                elif event_type == "execution_done":
                    ed_ids.add(effective_gid)
                elif event_type == "validation_done":
                    vd_ids.add(effective_gid)
                elif event_type == "goal_completed":
                    gc_ids.add(effective_gid)
                    completed_goal_ids.append(effective_gid)
                    gc_timestamps[effective_gid] = ts
                elif event_type == "goal_failed":
                    gf_ids.add(effective_gid)
                    gf_timestamps[effective_gid] = ts

            # execution_done rekord gyűjtés (teljes rekord, max ~40 elem)
            if event_type == "execution_done" and effective_gid:
                ed_records.append({
                    "ts": ts, "goal_id": effective_gid, "day": day,
                    "status": data.get("execution_status"),
                    "exec_time_ms": data.get("execution_time_ms"),
                    "iteration": data.get("iteration"),
                })

            # Incidens-nap plan_selected reservoir (20 véletlen minta)
            if event_type == "plan_selected" and day == INCIDENT_DATE and effective_gid:
                inc_ps_count += 1
                if len(inc_ps_reservoir) < INC_PS_SAMPLE:
                    inc_ps_reservoir.append(effective_gid)
                else:
                    j = random.randint(0, inc_ps_count - 1)
                    if j < INC_PS_SAMPLE:
                        inc_ps_reservoir[j] = effective_gid

            # Terminal event → kontextus reset
            if event_type in ("goal_completed", "goal_failed"):
                current_goal_id = None

            # ── Első 1000 rekord mezőelemzés ─────────────────────────────
            if total_records <= 1000:
                for k in rec.keys():
                    first_1000_top_keys[k] = first_1000_top_keys.get(k, 0) + 1
                for k in data.keys():
                    first_1000_data_keys[k] = first_1000_data_keys.get(k, 0) + 1
                # source-típusú mezők
                for field in ("source", "module", "script", "origin", "caller", "agent"):
                    val = rec.get(field) or data.get(field)
                    if val:
                        src_key = f"{field}={val}"
                        first_1000_sources[src_key] = first_1000_sources.get(src_key, 0) + 1

    scan_duration = time.monotonic() - scan_start

    # ═════════════════════════════════════════════════════════════════════════
    # ANALÍZIS
    # ═════════════════════════════════════════════════════════════════════════

    # Top-10 nap
    sorted_days = sorted(daily.items(), key=lambda x: x[1]["total"], reverse=True)
    top_10_days = sorted_days[:10]

    # Goal-ID prefix analízis a reservoir alapján
    prefix_counts: dict = {}
    for gid in reservoir:
        parts = gid.split("_")
        if parts and not parts[0].isdigit():
            pfx = parts[0]
        else:
            pfx = "<date_based>"
        prefix_counts[pfx] = prefix_counts.get(pfx, 0) + 1

    # Életciklus lánc (Venn-szerű: hány GS-hez van PS stb.)
    gs_with_ps     = len(gs_ids & ps_ids)
    ps_with_ed     = len(ps_ids & ed_ids)
    ed_with_vd     = len(ed_ids & vd_ids)
    vd_with_term   = len(vd_ids & (gc_ids | gf_ids))
    gs_with_term   = len(gs_ids & (gc_ids | gf_ids))

    def pct(n: int, d: int) -> str:
        return f"{n / d * 100:.1f}%" if d else "—"

    # ═════════════════════════════════════════════════════════════════════════
    # RIPORT ÖSSZEÁLLÍTÁSA
    # ═════════════════════════════════════════════════════════════════════════
    L: list = []

    def h(text: str) -> None:
        L.append(text)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    h(f"# Evidence Diagnostic Report")
    h(f"")
    h(f"**Generálva:** {now_str}")
    h(f"**Forrás:** `{META_EVIDENCE_PATH}`")
    h(f"**Scan idő:** {scan_duration:.2f} s")
    h(f"")

    # ── Összesítő ─────────────────────────────────────────────────────────────
    h(f"## Összesítő")
    h(f"")
    h(f"| Metrika | Érték |")
    h(f"|---------|-------|")
    h(f"| Összes rekord | {total_records:,} |")
    h(f"| Parse hibák | {parse_errors:,} |")
    h(f"| Összes napok száma | {len(daily):,} |")
    h(f"")
    h(f"### Event típusok")
    h(f"")
    h(f"| Event típus | Db |")
    h(f"|-------------|-----|")
    for et in KNOWN_EVENTS:
        h(f"| `{et}` | {event_counts.get(et, 0):,} |")
    # egyéb event típusok
    others = [(k, v) for k, v in sorted(event_counts.items(), key=lambda x: -x[1]) if k not in KNOWN_EVENTS]
    if others:
        h(f"| — | — |")
        for et, cnt in others:
            h(f"| `{et}` | {cnt:,} |")
    h(f"")

    # ── a) Időbeli eloszlás ───────────────────────────────────────────────────
    h(f"## a) Időbeli Eloszlás")
    h(f"")
    h(f"### Top 10 nap (rekordszám szerint)")
    h(f"")
    h(f"| Nap | Összes | goal_started | goal_completed | goal_failed |")
    h(f"|-----|--------|:------------:|:--------------:|:-----------:|")
    for day, c in top_10_days:
        h(f"| {day} | {c['total']:,} | {c.get('goal_started', 0):,} | {c.get('goal_completed', 0):,} | {c.get('goal_failed', 0):,} |")
    h(f"")
    h(f"### Teljes napi bontás (kronológiai sorrendben)")
    h(f"")
    h(f"| Nap | Összes | goal_started | goal_completed | goal_failed |")
    h(f"|-----|--------|:------------:|:--------------:|:-----------:|")
    for day, c in sorted(daily.items()):
        h(f"| {day} | {c['total']:,} | {c.get('goal_started', 0):,} | {c.get('goal_completed', 0):,} | {c.get('goal_failed', 0):,} |")
    h(f"")

    # ── b) Goal ID mintázat ───────────────────────────────────────────────────
    h(f"## b) Goal ID Mintázat")
    h(f"")
    h(f"**Összes goal_id-t érintő esemény:** {reservoir_total:,}")
    h(f"**Reservoir mérete:** {len(reservoir)} (véletlenszerű minta)")
    h(f"")
    h(f"### Prefix eloszlás a mintában")
    h(f"")
    h(f"| Prefix | Minta-db |")
    h(f"|--------|----------|")
    for pfx, cnt in sorted(prefix_counts.items(), key=lambda x: -x[1]):
        h(f"| `{pfx}` | {cnt} |")
    h(f"")

    # Reservoir minta
    h(f"### Mintavételezett goal_id-k ({len(reservoir)} db)")
    h(f"")
    h(f"```")
    for gid in reservoir:
        h(gid)
    h(f"```")
    h(f"")

    # Completed goal_ids — mind
    h(f"### A {len(completed_goal_ids)} db goal_completed goal_id-je (valódi sikerek)")
    h(f"")
    if completed_goal_ids:
        h(f"```")
        for gid in completed_goal_ids:
            h(gid)
        h(f"```")
    else:
        h(f"*Nem találtunk goal_completed eseményt.*")
    h(f"")

    # ── c) Source-alapú bontás ────────────────────────────────────────────────
    h(f"## c) Source-alapú Bontás (első 1000 rekord)")
    h(f"")
    h(f"### Top-level kulcsok")
    h(f"")
    h(f"| Kulcs | Előfordulás |")
    h(f"|-------|-------------|")
    for k, cnt in sorted(first_1000_top_keys.items(), key=lambda x: -x[1]):
        h(f"| `{k}` | {cnt} |")
    h(f"")
    h(f"### `data.*` kulcsok")
    h(f"")
    if first_1000_data_keys:
        h(f"| data.kulcs | Előfordulás |")
        h(f"|------------|-------------|")
        for k, cnt in sorted(first_1000_data_keys.items(), key=lambda x: -x[1]):
            h(f"| `{k}` | {cnt} |")
    else:
        h(f"*Nem találhatók data.* kulcsok az első 1000 rekordban.*")
    h(f"")
    h(f"### Source / module / script / origin értékek")
    h(f"")
    if first_1000_sources:
        h(f"| Mező=Érték | Előfordulás |")
        h(f"|------------|-------------|")
        for src, cnt in sorted(first_1000_sources.items(), key=lambda x: -x[1]):
            h(f"| `{src}` | {cnt} |")
    else:
        h(f"*Nem található `source`, `module`, `script`, `origin`, `caller`, `agent` mező "
          f"az első 1000 rekordban.*")
    h(f"")

    # ── d) Életciklus párosítás ───────────────────────────────────────────────
    h(f"## d) Goal Életciklus Párosítás")
    h(f"")
    h(f"> Megjegyzés: a `plan_selected`, `execution_done`, `validation_done` eseményekben "
      f"nincs `goal_id` mező — a párosítás szekvenciális kontextussal történt "
      f"(utolsó `goal_started` goal_id-ja).")
    h(f"")
    h(f"```")
    h(f"goal_started              : {len(gs_ids):>8,}")
    h(f"  ↳ kapott plan_selected  : {gs_with_ps:>8,}  ({pct(gs_with_ps, len(gs_ids))} of started)")
    h(f"")
    h(f"plan_selected (egyedi id) : {len(ps_ids):>8,}")
    h(f"  ↳ kapott execution_done : {ps_with_ed:>8,}  ({pct(ps_with_ed, len(ps_ids))} of planned)")
    h(f"")
    h(f"execution_done (egyedi)   : {len(ed_ids):>8,}")
    h(f"  ↳ kapott validation_done: {ed_with_vd:>8,}  ({pct(ed_with_vd, len(ed_ids))} of executed)")
    h(f"")
    h(f"validation_done (egyedi)  : {len(vd_ids):>8,}")
    h(f"  ↳ terminal állapotba ért: {vd_with_term:>8,}  ({pct(vd_with_term, len(vd_ids))} of validated)")
    h(f"")
    h(f"goal_completed (egyedi)   : {len(gc_ids):>8,}")
    h(f"goal_failed    (egyedi)   : {len(gf_ids):>8,}")
    h(f"összes terminal           : {len(gc_ids | gf_ids):>8,}")
    h(f"  ebből goal_started-ból  : {gs_with_term:>8,}  ({pct(gs_with_term, len(gs_ids))} of started)")
    h(f"```")
    h(f"")

    # Pipeline vízesés tábla
    h(f"### Pipeline drop-off vízesés")
    h(f"")
    stages = [
        ("goal_started",               len(gs_ids)),
        ("plan_selected",              len(ps_ids)),
        ("execution_done",             len(ed_ids)),
        ("validation_done",            len(vd_ids)),
        ("terminal (completed|failed)", len(gc_ids | gf_ids)),
    ]
    h(f"| Fázis | Egyedi goal_id-k | Δ az előzőhöz |")
    h(f"|-------|:---------------:|:--------------:|")
    prev_count = None
    for name, count in stages:
        delta = pct(count, prev_count) if prev_count else "—"
        h(f"| `{name}` | {count:,} | {delta} |")
        prev_count = count
    h(f"")
    h(f"**Magyarázat:** Ha a `plan_selected` << `goal_started`, akkor a célok nagy része "
      f"tervezési fázisban omlik le (pl. consensus hiba).")
    h(f"")

    # ── e) Utolsó 100 rekord ─────────────────────────────────────────────────
    h(f"## e) Az Utolsó 100 Rekord")
    h(f"")
    last_list = list(last_100)
    h(f"| # | timestamp | event_type | goal_id |")
    h(f"|---|-----------|------------|---------|")
    for i, rec in enumerate(last_list):
        if not isinstance(rec, dict) or rec.get("_parse_error"):
            h(f"| {i+1} | PARSE_ERROR | — | — |")
            continue
        ts  = (rec.get("timestamp") or "")[:19]
        et  = rec.get("event_type") or "<missing>"
        d   = rec.get("data") or {}
        gid = (d.get("goal_id") or "—") if isinstance(d, dict) else "—"
        h(f"| {i+1} | {ts} | `{et}` | {gid} |")
    h(f"")

    h(f"### Utolsó 10 rekord — teljes tartalom")
    h(f"")
    h(f"```json")
    for rec in last_list[-10:]:
        try:
            h(json.dumps(rec, ensure_ascii=False)[:600])
        except Exception:
            h(str(rec)[:600])
    h(f"```")
    h(f"")

    # ── f) EXECUTION_DONE TIMELINE — új szekció ─────────────────────────────
    h(f"## f) EXECUTION_DONE TIMELINE")
    h(f"")

    # Napi bontás: execution_done és terminal
    h(f"### execution_done és terminal események napi bontásban")
    h(f"")
    h(f"| Nap | execution_done | validation_done | goal_completed | goal_failed |")
    h(f"|-----|:--------------:|:---------------:|:--------------:|:-----------:|")
    for day_k, c in sorted(daily.items()):
        h(f"| {day_k} "
          f"| {c.get('execution_done', 0)} "
          f"| {c.get('validation_done', 0)} "
          f"| {c.get('goal_completed', 0)} "
          f"| {c.get('goal_failed', 0)} |")
    h(f"")

    # Teljes execution_done lista párosítással
    h(f"### Mind a {len(ed_records)} execution_done rekord — párosítva goal_started és terminal eseménnyel")
    h(f"")
    h(f"| # | Nap | goal_id | started_ts | exec_ts | terminal_ts | terminal | duration_s | iter | status |")
    h(f"|---|-----|---------|-----------|---------|-------------|----------|:----------:|:----:|--------|")
    for i, er in enumerate(ed_records, 1):
        gid = er["goal_id"] or "—"
        started = gs_timestamps.get(gid, "—")
        terminal_ts = gc_timestamps.get(gid) or gf_timestamps.get(gid) or "—"
        terminal_ev = ("completed" if gid in gc_timestamps
                       else ("failed" if gid in gf_timestamps else "—"))
        # Időtartam: exec_ts - started_ts (másodperc)
        dur = "—"
        if started != "—" and er["ts"]:
            try:
                t0 = datetime.fromisoformat(started.replace("Z", "+00:00").replace("+00:00", ""))
                t1 = datetime.fromisoformat(er["ts"].replace("Z", "+00:00").replace("+00:00", ""))
                dur = f"{(t1 - t0).total_seconds():.1f}"
            except Exception:
                pass
        h(f"| {i} | {er['day']} | {gid} "
          f"| {(started or '—')[:19]} "
          f"| {(er['ts'] or '—')[:19]} "
          f"| {(terminal_ts or '—')[:19]} "
          f"| {terminal_ev} | {dur} | {er.get('iteration') or '—'} | {er.get('status') or '—'} |")
    h(f"")

    # Incidens-nap vizsgálat
    inc_with_ed   = sum(1 for g in inc_ps_reservoir if g in ed_ids)
    inc_with_vd   = sum(1 for g in inc_ps_reservoir if g in vd_ids)
    inc_with_gc   = sum(1 for g in inc_ps_reservoir if g in gc_ids)
    inc_with_gf   = sum(1 for g in inc_ps_reservoir if g in gf_ids)

    h(f"### Incidens-nap ({INCIDENT_DATE}) plan_selected mintája ({len(inc_ps_reservoir)} véletlen goal_id)")
    h(f"")
    h(f"> Összes plan_selected ezen a napon: {inc_ps_count:,}")
    h(f"")
    h(f"| goal_id | execution_done? | validation_done? | goal_completed? | goal_failed? |")
    h(f"|---------|:--------------:|:----------------:|:---------------:|:------------:|")
    for g in inc_ps_reservoir:
        has_ed = "✅" if g in ed_ids else "❌"
        has_vd = "✅" if g in vd_ids else "❌"
        has_gc = "✅" if g in gc_ids else "❌"
        has_gf = "✅" if g in gf_ids else "❌"
        h(f"| {g} | {has_ed} | {has_vd} | {has_gc} | {has_gf} |")
    h(f"")
    h(f"**Összesítve a {len(inc_ps_reservoir)} mintából:**")
    h(f"- execution_done-ig eljutott: **{inc_with_ed}** ({pct(inc_with_ed, len(inc_ps_reservoir))})")
    h(f"- validation_done-ig: **{inc_with_vd}**")
    h(f"- goal_completed: **{inc_with_gc}**")
    h(f"- goal_failed: **{inc_with_gf}**")
    h(f"")

    # Konklúzió
    incident_ed_count = sum(1 for r in ed_records if r["day"] == INCIDENT_DATE)
    post_inc_ed_count = sum(1 for r in ed_records if r["day"] > INCIDENT_DATE)
    h(f"### Konklúzió")
    h(f"")
    h(f"```")
    h(f"execution_done az incidens napján ({INCIDENT_DATE}) : {incident_ed_count}")
    h(f"execution_done az incidens UTÁN                     : {post_inc_ed_count}")
    h(f"")
    if incident_ed_count == 0:
        h(f"▶ Az incidens-nap ({INCIDENT_DATE}) ~{event_counts.get('goal_started',0):,} goal_started-jéből")
        h(f"  EGYETLEN EGY sem jutott el execution_done-ig.")
        h(f"  Diagnosis: plan_selected után a dispatcher EGYÁLTALÁN NEM indított végrehajtást.")
        h(f"  Ez NEM fejlesztési zaj — strukturális dispatcher bug 2026-01-14-én.")
    else:
        h(f"▶ Az incidens-napon {incident_ed_count} goal eljutott execution-ig.")
        h(f"  Az incidens részleges volt — egyes goal-ok végrehajtódtak.")
    h(f"")
    if post_inc_ed_count > 0:
        h(f"▶ Az incidens UTÁN indított goal-ok normálisan futottak le (execution_done: {post_inc_ed_count}).")
        h(f"  A pipeline önmagában helyes — a hiba lokalizált az incidens-napra.")
    h(f"```")
    h(f"")

    h(f"---")
    h(f"*Riport generálva: `witness/evidence_diagnostic.py` — csak olvasás, "
      f"sem `meta_evidence.jsonl`, sem `self_state.json` nem módosult.*")

    report_text = "\n".join(L)

    # ── Mentés ────────────────────────────────────────────────────────────────
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"evidence_diagnostic_{today_str}.md"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    return report_text, report_path, scan_duration


def main() -> None:
    print("=== Evidence Diagnostic ===")
    print(f"Forrás : {META_EVIDENCE_PATH}")
    print(f"Méret  : {META_EVIDENCE_PATH.stat().st_size / 1_048_576:.1f} MB")
    print("Scanning...\n")

    if not META_EVIDENCE_PATH.exists():
        print(f"HIBA: {META_EVIDENCE_PATH} nem található!", file=sys.stderr)
        sys.exit(1)

    report_text, report_path, scan_duration = run_diagnostic()

    report_lines = report_text.split("\n")
    print("─" * 60)
    print("RIPORT (első 50 sor):")
    print("─" * 60)
    for line in report_lines[:50]:
        print(line)
    if len(report_lines) > 50:
        print(f"... ({len(report_lines) - 50} további sor)")

    print()
    print("─" * 60)
    print(f"Riport mentve : {report_path}")
    print(f"Scan idő      : {scan_duration:.2f} s")
    print("─" * 60)


if __name__ == "__main__":
    main()
