import sys
sys.path.insert(0, 'src')

try:
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    print("[1] Import successful")
    
    registry = ToolRegistry()
    print("[2] ToolRegistry instantiated")
    print(f"[3] default_paths exists: {hasattr(registry, 'default_paths')}")
    print(f"[4] tools dict: {list(registry.tools.keys())}")
    print(f"[5] web_api_call in tools: {'web_api_call' in registry.tools}")
except Exception as e:
    import traceback
    print(f"[ERROR] {e}")
    traceback.print_exc()
