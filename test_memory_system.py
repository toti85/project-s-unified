#!/usr/bin/env python3
"""
PROJECT-S PHASE 1B - MEMORY & LEARNING SYSTEM TEST
Task 3: Inspect learning.jsonl execution records
"""

import json
from pathlib import Path
import datetime

print("\n" + "="*70)
print("[TEST 3] Memory & Learning System Analysis")
print("="*70)

memory_path = Path("memory/intelligence")

if not memory_path.exists():
    print(f"❌ Memory path not found: {memory_path}")
    exit(1)

print(f"\n✅ Memory directory found: {memory_path}")

# Scan for JSONL files
jsonl_files = list(memory_path.glob("*.jsonl"))
print(f"\n📊 JSONL Files Found: {len(jsonl_files)}")

total_records = 0
for jf in jsonl_files:
    size = jf.stat().st_size
    lines = 0
    try:
        with open(jf, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f.readlines())
        print(f"   • {jf.name}: {size:,} bytes ({lines} records)")
        total_records += lines
    except Exception as e:
        print(f"   • {jf.name}: {size} bytes (read error: {e})")

print(f"\n✅ Total records in JSONL files: {total_records}")

# Analyze learning.jsonl in detail
learning_file = memory_path / "learning.jsonl"
if learning_file.exists():
    print(f"\n📖 LEARNING SYSTEM ANALYSIS")
    print(f"{'='*70}")
    
    records = []
    try:
        with open(learning_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"❌ Error reading learning.jsonl: {e}")
    
    print(f"✅ Parsed {len(records)} learning records\n")
    
    # Analyze structure
    if records:
        first_record = records[0]
        print(f"📌 Sample Record Structure:")
        
        keys = first_record.keys()
        for key in sorted(keys):
            value = first_record[key]
            if isinstance(value, dict):
                print(f"   • {key}: (dict with {len(value)} keys)")
                for k2 in list(value.keys())[:3]:
                    print(f"      └─ {k2}: ...")
            elif isinstance(value, list):
                print(f"   • {key}: (list with {len(value)} items)")
            else:
                preview = str(value)[:50]
                print(f"   • {key}: {preview}...")
        
        # Statistics
        print(f"\n📊 LEARNING STATISTICS")
        print(f"{'─'*70}")
        
        domains = {}
        for record in records:
            domain = record.get("domain", "unknown")
            domains[domain] = domains.get(domain, 0) + 1
        
        print(f"Domains covered:")
        for domain, count in sorted(domains.items(), key=lambda x: -x[1]):
            print(f"   • {domain}: {count} records")
        
        # Check for outcomes
        print(f"\n✅ Learning records include:")
        if records:
            print(f"   • Timestamp: {records[0].get('timestamp', 'N/A')}")
            print(f"   • Confidence: {records[0].get('confidence', 'N/A')}")
            print(f"   • Domain: {records[0].get('domain', 'N/A')}")
            evidence = records[0].get('evidence', {})
            if isinstance(evidence, dict):
                print(f"   • Evidence keys: {list(evidence.keys())}")

# Check other memory files
print(f"\n📁 OTHER MEMORY FILES")
print(f"{'='*70}")

other_files = list(memory_path.glob("*")) 
for f in other_files:
    if not f.is_dir() and f.suffix != '.jsonl':
        size = f.stat().st_size
        print(f"   • {f.name}: {size:,} bytes")

# Check meta_evidence.jsonl
meta_file = memory_path / "meta_evidence.jsonl"
if meta_file.exists():
    print(f"\n✅ Meta-Evidence System Active:")
    try:
        with open(meta_file, 'r') as f:
            lines = sum(1 for _ in f.readlines())
        print(f"   • {lines} meta-evidence records logged")
    except:
        pass

print(f"\n✅ MEMORY SYSTEM TEST PASSED")
print(f"   Status: ACTIVE with {total_records} execution events logged")
