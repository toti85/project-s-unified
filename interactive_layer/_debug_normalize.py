#!/usr/bin/env python3
"""Debug: check what normalize_text produces for key prompts."""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

from prompt_router import normalize_text, normalize_hungarian
import re

prompts = [
    "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
    "Mondd meg biztosan, hogy mi lesz holnap.",
    "Adj egy pontosan 4 soros választ.",
    "Keress információt a piacról.",
    "Mi a Project-S státusza?",
]

for p in prompts:
    norm = normalize_text(p)
    print(f"ORIGINAL: {p[:70]}")
    print(f"NORMAL:   {norm}")
    print()

# Test specific patterns
print("=" * 60)
print("PATTERN MATCH TESTS")
print("=" * 60)

test_norm = normalize_text("Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.")
patterns_to_test = [
    (r"irj\s+\d+.*?mondat", "irj_mondat"),
    (r"irj\s+\d+.*?sort", "irj_sort"),
    (r"fogalmazd\s+meg", "fogalmazd_meg"),
    (r"summazd.*?r(ö|o)vlden", "summazd_roviden"),
    (r"adj.*?r(ö|o)vlden.*?valasz", "adj_rovid_valasz"),
    (r"r(ö|o)vlden.*?irj", "roviden_irj"),
    (r"valaszolj.*?r(ö|o)vlden", "valaszolj_roviden"),
    (r"biztosan\s", "biztosan"),
    (r"garant", "garant"),
    (r"pontosan\s+mennyi", "pontosan_mennyi"),
]

for pat, name in patterns_to_test:
    match = re.search(pat, test_norm)
    print(f"  Pattern '{name}' ({pat}): {'MATCH' if match else 'NO MATCH'} -> {match.group() if match else ''}")

print()
print("Testing 'biztosan' prompt:")
biztosan_norm = normalize_text("Mondd meg biztosan, hogy mi lesz holnap.")
for pat, name in patterns_to_test:
    match = re.search(pat, biztosan_norm)
    print(f"  Pattern '{name}' ({pat}): {'MATCH' if match else 'NO MATCH'} -> {match.group() if match else ''}")