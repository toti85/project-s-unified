import os

REPORT = r'C:\ProjectS-Unified\reports\PROJECT_S_STRATEGIC_POSITIONING_REALITY_CHECK_20260514.md'
with open(REPORT, encoding='utf-8') as f:
    content = f.read()

SECTION_CHECKS = {
    'Executive Verdict':              lambda c: '## 1.' in c and ('verdict' in c.lower() or 'direction' in c.lower()),
    'Current Capabilities section':   lambda c: '## 2.' in c and ('pipeline' in c.lower() or 'tool' in c.lower()),
    'External Reality Check':         lambda c: '## 3.' in c and ('market' in c.lower() or 'landscape' in c.lower() or 'crowded' in c.lower()),
    'Candidate Directions (>=5)':     lambda c: '## 4.' in c and c.lower().count('direction') >= 3,
    'Comparative Decision Table':     lambda c: '## 5.' in c and '|' in c and 'verdict' in c.lower(),
    'Final Recommendation':           lambda c: '## 6.' in c and ('recommend' in c.lower() or 'primary' in c.lower()),
    '30-Day Use Plan':                lambda c: '## 7.' in c and ('week' in c.lower() or 'day' in c.lower()),
    'What NOT To Do':                 lambda c: '## 8.' in c and 'not' in c.lower() and ('do not fall back' in c.lower() or 'not fall back' in c.lower()),
    'Confirmed Facts vs Assumptions': lambda c: '## 9.' in c and ('assumption' in c.lower() or 'fact' in c.lower()),
    'Sources section':                lambda c: '## 10.' in c or 'sources' in c.lower(),
    'Cites internal docs':            lambda c: any(kw in c.lower() for kw in ['self_state', 'project_s_overview', 'overview.md', 'meta_evidence', 'witness layer', '403k', 'evidence trail', '22 gaps', '21 resolved']),
    'Cites external URLs':            lambda c: 'http' in c.lower() or 'https' in c.lower(),
    'No bounty/exploit content':      lambda c: ('non-bounty' in c.lower() or 'bounty' not in c.lower()) and 'exploit' not in c.lower() and 'pentest' not in c.lower(),
    'Not a raw tool dump':            lambda c: 'tool executed successfully' not in c.lower() and 'web_search result' not in c.lower(),
}

results = {name: fn(content) for name, fn in SECTION_CHECKS.items()}
passed = sum(1 for v in results.values() if v)
total = len(results)

for name, ok in results.items():
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}")

print(f"\nScore: {passed}/{total}")
print(f"File size: {os.path.getsize(REPORT):,} bytes")
verdict = "PASS" if passed >= 10 else "PARTIAL" if passed >= 6 else "FAIL"
print(f"Verdict: {verdict}")
