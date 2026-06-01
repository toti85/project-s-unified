#!/usr/bin/env python3
"""Initialize decisions.jsonl with Phase 1 decision records."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge.knowledge_manager import KnowledgeManager

km = KnowledgeManager()

# Log Phase 1 decisions
km.log_decision('architecture', 'Archive v2_architecture', 'Two codebases caused confusion; consolidate to one', 'success', 0.95)
km.log_decision('architecture', 'Deduplicate AIClient to 1 copy', '4 identical copies caused maintenance risk', 'success', 0.95)
km.log_decision('architecture', 'Consolidate config to 3 files', '6+ config files were scattered and outdated', 'success', 0.9)
km.log_decision('architecture', 'Update models.yaml to real models', 'Config had GPT-4 + Claude 3 Opus but system uses Qwen3 + DeepSeek + GPT-4o-mini', 'success', 0.9)
km.log_decision('strategy', 'Phase 2 starts with Knowledge Layer', 'Biggest recurring pain point: manual context setup per AI session', None, 0.85)

print('✅ Logged 5 Phase 1 decisions')
for d in km.get_recent_decisions(5):
    print(f'  [{d["category"]}] {d["decision"]}')
