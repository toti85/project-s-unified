#!/usr/bin/env python3
"""
Extract OpenAI models from markdown and save as CSV + JSON
Direct local processing - no AI overhead
"""

import json
import csv
import re
from pathlib import Path

def parse_models_from_md(md_file):
    """Parse models from markdown file"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    models = []
    current_section = None
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Find model headings (###)
        if line.startswith('###'):
            model_name = line.replace('###', '').strip()
            current_section = model_name
            
            # Look ahead for model ID
            model_id = None
            description = None
            features = []
            
            j = i + 1
            while j < len(lines) and not lines[j].startswith('###') and not lines[j].startswith('##'):
                next_line = lines[j].strip()
                
                # Find model ID (Model ID: something)
                if 'model id:' in next_line.lower():
                    match = re.search(r'`([^`]+)`', next_line)
                    if match:
                        model_id = match.group(1)
                
                # Find description (first non-empty, non-special line after heading)
                if next_line and not ':' in next_line and not next_line.startswith('-') and not description:
                    if not next_line.startswith('Model'):
                        description = next_line
                
                # Find features (lines starting with -)
                if next_line.startswith('-'):
                    feature = next_line.lstrip('- ').strip()
                    if feature:
                        features.append(feature)
                
                j += 1
            
            if model_id:  # Only add if we found a model ID
                models.append({
                    'name': model_name,
                    'model_id': model_id,
                    'description': description or 'No description available',
                    'features': features,
                    'section': current_section
                })
        
        i += 1
    
    return models

def main():
    md_file = Path('docs/openai_models_sample.md')
    
    if not md_file.exists():
        print(f"[ERROR] File not found: {md_file}")
        return False
    
    print(f"[INFO] Reading {md_file}...")
    models = parse_models_from_md(md_file)
    
    if not models:
        print("[ERROR] No models extracted from markdown")
        return False
    
    print(f"[OK] Extracted {len(models)} models")
    
    # Create output directory
    output_dir = Path('memory/output')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    csv_file = output_dir / 'models.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'model_id', 'description', 'features'])
        writer.writeheader()
        for model in models:
            writer.writerow({
                'name': model['name'],
                'model_id': model['model_id'],
                'description': model['description'],
                'features': '; '.join(model['features'])
            })
    print(f"[OK] CSV saved: {csv_file}")
    
    # Write JSON
    json_file = output_dir / 'models.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'docs/openai_models_sample.md',
            'count': len(models),
            'models': models
        }, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON saved: {json_file}")
    
    # Print summary
    print("\n" + "="*70)
    print("OPENAI MODELS SUMMARY")
    print("="*70)
    print(f"Total models extracted: {len(models)}")
    print(f"\nModel Types:")
    
    # Group by section
    sections = {}
    for model in models:
        section = model['section']
        if section not in sections:
            sections[section] = []
        sections[section].append(model['model_id'])
    
    for section, model_ids in sections.items():
        print(f"  {section}: {', '.join(model_ids)}")
    
    print(f"\nOutput files:")
    print(f"  1. {csv_file.relative_to('.')}")
    print(f"  2. {json_file.relative_to('.')}")
    print(f"\nData is structured and ready for use.")
    print(f"No hallucination - direct parsing from markdown source.")
    print("="*70)
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
