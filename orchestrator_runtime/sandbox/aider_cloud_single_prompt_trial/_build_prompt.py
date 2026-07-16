import json

# Read frozen input
with open('orchestrator_runtime/sandbox/aider_cloud_single_prompt_trial/scan_canonical.json') as f:
    data = json.load(f)

findings = data['findings']
n = len(findings)
print(f"Total findings: {n}")

# Build the prompt
lines = []
lines.append("Create a new file `single_prompt_output.json` in the current directory.")
lines.append("The file must contain ONLY valid JSON — no preamble, no markdown, no explanation.")
lines.append("")
lines.append(f"Classify these {n} findings (indices 1 to {n}) with severity:")
lines.append("HIGH=security/data-loss/auth, MEDIUM=functionality/correctness/performance, LOW=docs/style/cleanup")
lines.append("")
lines.append("FINDINGS (include ALL, invent NONE):")

for i, f in enumerate(findings):
    idx = i + 1
    ftype = f['type']
    filepath = f['file']
    line = f['line']
    text = f['text']
    ctx_before = f.get('context_before', '')
    ctx_after = f.get('context_after', '')
    
    # Build context string (same format as chunk prompts)
    if ctx_before and ctx_after:
        context = f"context: \"{ctx_before}\""
    elif ctx_before:
        context = f"context: \"{ctx_before}\""
    elif ctx_after:
        context = f"context: \"{ctx_after}\""
    else:
        context = ""
    
    # Escape quotes in text
    text_escaped = text.replace('"', '\\"')
    
    if context:
        lines.append(f"#{idx} [{ftype}] {filepath}:{line} \"{text_escaped}\"  {context}")
    else:
        lines.append(f"#{idx} [{ftype}] {filepath}:{line} \"{text_escaped}\"")

lines.append("")
lines.append("Required JSON structure for `single_prompt_output.json`:")
lines.append("{")
lines.append('  "prompt_id": 1,')
lines.append('  "start_index": 1,')
lines.append(f'  "end_index": {n},')
lines.append(f'  "finding_count": {n},')
lines.append('  "findings": [')
lines.append('    {')
lines.append('      "index": <number>,')
lines.append('      "file": "<file path>",')
lines.append('      "line": <number>,')
lines.append('      "type": "<TODO|FIXME|XXX>",')
lines.append('      "severity": "<LOW|MEDIUM|HIGH>",')
lines.append('      "text": "<exact text>",')
lines.append('      "context": "<context>"')
lines.append('    }')
lines.append('  ]')
lines.append("}")
lines.append("")
lines.append(f"Every finding index from 1 to {n} MUST appear exactly once.")
lines.append("Do not add findings that are not in the list above.")

prompt = "\n".join(lines)

with open('orchestrator_runtime/sandbox/aider_cloud_single_prompt_trial/single_prompt_instruction.txt', 'w', encoding='utf-8') as f:
    f.write(prompt)

# Print stats
print(f"Prompt length: {len(prompt)} chars")
print(f"Prompt lines: {len(lines)}")
print(f"First 3 lines:")
for l in lines[:3]:
    print(f"  {l}")
print(f"Last 3 lines:")
for l in lines[-3:]:
    print(f"  {l}")