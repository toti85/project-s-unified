#!/usr/bin/env python3
"""Célzott titokellenőrzés: hiba, ha a vizsgált fájlokban API-kulcsnak tűnő érték van. Az értéket nem írja ki.
Használat: python3 scripts/check_no_secrets.py [--staged]   (alapértelmezés: minden verziókezelt fájl)"""
import re, subprocess, sys
MINTAK = {"OpenRouter": rb"sk-or-v1-[0-9a-f]{64}", "OpenAI": rb"sk-(proj-)?[A-Za-z0-9_-]{40,}",
          "Anthropic": rb"sk-ant-[A-Za-z0-9_-]{40,}", "GitHub": rb"gh[opsur]_[A-Za-z0-9]{36,}",
          "privát kulcs": rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"}
arg = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if "--staged" in sys.argv else ["git", "ls-files"]
hiba = 0
for f in subprocess.run(arg, capture_output=True, text=True).stdout.split("\n"):
    if not f:
        continue
    try:
        b = open(f, "rb").read()
    except OSError:
        continue
    for nev, m in MINTAK.items():
        n = len(re.findall(m, b))
        if n:
            print(f"TITOK GYANÚ: {f}: {nev} ({n} db) – az érték nincs kiírva")
            hiba = 1
sys.exit(hiba)
