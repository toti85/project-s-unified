import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SYMBOLS = [
    "cognitive_registry",
    "EnhancedCognitiveProcessor",
    "AdvancedIntentAnalyzer",
    "SemanticReasoningEngine",
    "CognitiveContext",
    "CognitiveResult",
    "IntentMatch",
    "TaskDecomposition",
]

SEARCH_PATHS = [
    (r"C:\1225\project_s_super_core", r"C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core"),
    (r"C:\Users\Admin\project_s_super_core", r"C:\Users\Admin\project_s_super_core"),
    (r"C:\ProjectS\project-s-code", r"C:\ProjectS\project-s-code"),
    (r"C:\ProjectS-Snapshot-Staging", r"C:\ProjectS-Snapshot-Staging"),
    (r"C:\project-s-clean", r"C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean"),
    (r"C:\0703\v2_architecture", r"C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture"),
    (r"C:\0725\v2_architecture", r"C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture"),
]

EXCLUDED = {"venv", ".venv", "node_modules", "__pycache__", ".git", "site-packages"}
MAX_SIZE = 500 * 1024
OUTS = [
    Path(r"C:\ProjectS-Unified\orchestrator_runtime\sandbox\sz_t13_cwi_symbol_archaeology.md"),
    Path(r"C:\ProjectS-Unified\reports\MS_AO5_AO5_T13_CWI_SYMBOL_HUNT_20260610.md"),
]


def kind_for(line, symbol):
    stripped = line.strip()
    if re.match(rf"class\s+{re.escape(symbol)}\b", stripped):
        return "class definition"
    if re.match(rf"(?:async\s+)?def\s+{re.escape(symbol)}\b", stripped):
        return "function definition"
    if re.match(rf"{re.escape(symbol)}\s*=", stripped):
        return "instance/variable definition"
    return "reference"


def definition_span(lines, start_index):
    base_indent = len(lines[start_index]) - len(lines[start_index].lstrip())
    end = start_index + 1
    while end < len(lines):
        line = lines[end]
        if not line.strip():
            end += 1
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= base_indent and not line.lstrip().startswith(("#", "@")):
            break
        end += 1
    return max(1, end - start_index)


results = {symbol: [] for symbol in SYMBOLS}
scope = []
for requested, actual in SEARCH_PATHS:
    root = Path(actual)
    scope.append({"requested": requested, "actual": actual, "exists": root.is_dir(), "relocated": requested.lower() != actual.lower()})
    if not root.is_dir():
        continue
    for current, dirs, files in os.walk(root):
        dirs[:] = [directory for directory in dirs if directory not in EXCLUDED]
        for filename in files:
            if not filename.endswith(".py"):
                continue
            path = Path(current) / filename
            try:
                stat = path.stat()
                if stat.st_size > MAX_SIZE:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            present = [symbol for symbol in SYMBOLS if symbol in text]
            if not present:
                continue
            lines = text.splitlines()
            for symbol in present:
                for index, line in enumerate(lines):
                    if symbol not in line:
                        continue
                    kind = kind_for(line, symbol)
                    results[symbol].append({
                        "path": str(path),
                        "line": index + 1,
                        "kind": kind,
                        "snippet": line.strip()[:240],
                        "file_lines": len(lines),
                        "definition_lines": definition_span(lines, index) if "definition" in kind else 0,
                        "mtime": datetime.fromtimestamp(stat.st_mtime),
                        "codebase": actual,
                        "requested_codebase": requested,
                    })

# Prefer concrete definitions; then production-looking src/core/cognitive files; then recency/completeness.
def best_score(hit):
    definition = 1 if "definition" in hit["kind"] else 0
    production = 1 if "src\\core\\cognitive" in hit["path"].lower() else 0
    return (definition, production, hit["mtime"].timestamp(), hit["definition_lines"], hit["file_lines"])

best = {symbol: max(hits, key=best_score) if hits else None for symbol, hits in results.items()}
definition_codebases = defaultdict(set)
all_hit_codebases = set()
for symbol, hits in results.items():
    for hit in hits:
        all_hit_codebases.add(hit["codebase"])
        if "definition" in hit["kind"]:
            definition_codebases[hit["codebase"]].add(symbol)

best_codebase = max(definition_codebases, key=lambda path: (len(definition_codebases[path]), path == SEARCH_PATHS[0][1])) if definition_codebases else None
found_count = sum(bool(results[symbol]) for symbol in SYMBOLS)
definition_count = sum(any("definition" in hit["kind"] for hit in results[symbol]) for symbol in SYMBOLS)
all_same = bool(best_codebase) and len(definition_codebases[best_codebase]) == 8
feasibility = "SIMPLE" if definition_count == 8 and all_same else ("MODERATE" if definition_count >= 6 else "COMPLEX")

lines = [
    "# AO5_T13 Parallel CWI Symbol Hunt",
    "",
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "",
    "> Correction: legacy paths moved during disk cleanup were resolved under `C:\\_cleanup_quarantine\\audit_forks_20260609`. The quarantine was read only.",
    "",
    "## Scan Scope Status",
]
for item in scope:
    state = "OK (relocated to quarantine)" if item["exists"] and item["relocated"] else ("OK" if item["exists"] else "MISSING")
    lines.append(f"- {state}: requested `{item['requested']}`; scanned `{item['actual']}`")

lines += ["", "## 1. Summary Table (8 Missing Symbols)", "| Symbol | Found? | Definition location(s) | Type | Definition size |", "|---|---|---|---|---:|"]
for symbol in SYMBOLS:
    definitions = [hit for hit in results[symbol] if "definition" in hit["kind"]]
    if not results[symbol]:
        lines.append(f"| {symbol} | no | - | - | - |")
        continue
    locations = "; ".join(f"{hit['path']}:{hit['line']}" for hit in definitions[:4]) or "references only"
    if len(definitions) > 4:
        locations += f" (+{len(definitions)-4} more definitions)"
    types = ", ".join(sorted({hit["kind"] for hit in definitions})) or "reference"
    sizes = ", ".join(str(hit["definition_lines"]) for hit in definitions[:4]) if definitions else "-"
    lines.append(f"| {symbol} | yes | {locations} | {types} | {sizes} lines |")

lines += ["", "## 2. Per-Symbol Detail"]
for symbol in SYMBOLS:
    lines.append(f"### {symbol}")
    definitions = sorted([hit for hit in results[symbol] if "definition" in hit["kind"]], key=best_score, reverse=True)
    references = [hit for hit in results[symbol] if hit["kind"] == "reference"]
    if not results[symbol]:
        lines.append("- Not found.")
        continue
    for hit in definitions:
        lines.append(f"- Definition: `{hit['path']}:{hit['line']}` | {hit['kind']} | approx. {hit['definition_lines']} lines | file {hit['file_lines']} lines | mtime {hit['mtime']:%Y-%m-%d %H:%M:%S}")
        lines.append(f"  - `{hit['snippet']}`")
    lines.append(f"- Additional reference hits: {len(references)}")
    selected = best[symbol]
    lines.append(f"- Best source: `{selected['path']}:{selected['line']}`")
    lines.append("")

lines += ["## 3. Best-Source Recommendation"]
for symbol in SYMBOLS:
    hit = best[symbol]
    if hit:
        lines.append(f"- **{symbol}**: `{hit['path']}:{hit['line']}` ({hit['kind']}, approx. {hit['definition_lines']} definition lines)")
    else:
        lines.append(f"- **{symbol}**: NOT FOUND")

lines += [
    "",
    "### Recommended source module set",
    f"- Primary codebase: `{best_codebase}`",
    "- `src/core/cognitive/base_cognitive.py`: registry and shared data models/base contracts.",
    "- `src/core/cognitive/enhanced_processor.py`: EnhancedCognitiveProcessor.",
    "- `src/core/cognitive/advanced_analyzer.py`: AdvancedIntentAnalyzer.",
    "- `src/core/cognitive/semantic_reasoning.py`: SemanticReasoningEngine.",
    "- `src/core/cognitive/__init__.py`: expected public re-export surface.",
    "",
    "## 4. Reconstruction Feasibility Verdict",
    f"- A. Symbols found: **{found_count}/8**; concrete definitions found: **{definition_count}/8**.",
    f"- B. All 8 occur together: **{'YES' if all_same else 'NO'}** in `{best_codebase}`.",
    f"- C. Most likely original codebase: `{best_codebase}` ({len(definition_codebases.get(best_codebase, set()))}/8 concrete symbols).",
    f"- D. Reconstruction feasibility: **{feasibility}**.",
    "- E. Dependency risk: **MEDIUM-HIGH**. The symbols span four implementation modules plus package exports; copying one file is insufficient, and module-level singleton registration can create import-order/circular-import risk.",
    "- Recommended next action: compare the legacy `src/core/cognitive/__init__.py` and four implementation modules against Unified, then restore only the missing export contract with guarded import smoke tests.",
    "- Files modified outside Unified: **NO**.",
    "",
    "## Codebases With Hits",
]
for codebase in sorted(all_hit_codebases):
    concrete = len(definition_codebases.get(codebase, set()))
    lines.append(f"- `{codebase}`: {concrete}/8 concrete definitions")

report = "\n".join(lines) + "\n"
for output in OUTS:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print("WROTE", output)
print("FOUND", found_count, "DEFINITIONS", definition_count)
print("BEST", best_codebase)
print("FEASIBILITY", feasibility)
print("CODEBASES", len(all_hit_codebases))
