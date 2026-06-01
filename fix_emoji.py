#!/usr/bin/env python3
# Fix emoji characters to ASCII
import sys

file_path = r'c:\1225\project_s_super_core\test_real_multi_tool_task.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace emojis
replacements = {
    '✅': '[OK]',
    '❌': '[FAIL]',
    '🚀': '[START]',
    '🔍': '[SEARCH]',
    '📁': '[DIR]',
    '📊': '[CHART]',
}

for emoji, ascii_char in replacements.items():
    content = content.replace(emoji, ascii_char)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed! Emojis replaced with ASCII characters.")
