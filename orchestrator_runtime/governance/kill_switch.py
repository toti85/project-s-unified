"""
MS-AO2 Kill Switch — AO2.3

File-based kill switch for autonomous governance loops.
If orchestrator_runtime/governance/KILL_SWITCH exists → all loops stop.

Usage:
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    ks = KillSwitch()
    ks.is_active()  # bool
    ks.activate("Budget exhausted")
    ks.deactivate()
    ks.status()
"""

import json
from pathlib import Path
from datetime import datetime, timezone

KILL_SWITCH_PATH = Path(__file__).parent / "KILL_SWITCH"


class KillSwitch:
    def __init__(self):
        pass

    def is_active(self):
        """Check if kill switch is engaged."""
        return KILL_SWITCH_PATH.exists()

    def activate(self, reason=""):
        """Engage kill switch. Creates flag file with reason + timestamp."""
        data = {
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason or "Manual kill switch activation",
        }
        with open(KILL_SWITCH_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data

    def deactivate(self):
        """Disengage kill switch. Removes flag file."""
        if KILL_SWITCH_PATH.exists():
            KILL_SWITCH_PATH.unlink()
            return {"status": "DEACTIVATED", "timestamp": datetime.now(timezone.utc).isoformat()}
        return {"status": "ALREADY_INACTIVE"}

    def status(self):
        """Return kill switch status."""
        if KILL_SWITCH_PATH.exists():
            with open(KILL_SWITCH_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "status": "ACTIVE",
                "activated_at": data.get("activated_at", ""),
                "reason": data.get("reason", ""),
            }
        return {"status": "INACTIVE"}


if __name__ == "__main__":
    import sys
    ks = KillSwitch()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "activate":
            reason = sys.argv[2] if len(sys.argv) > 2 else ""
            ks.activate(reason)
            print("Kill switch ACTIVATED")
        elif cmd == "deactivate":
            ks.deactivate()
            print("Kill switch DEACTIVATED")
        elif cmd == "status":
            print(json.dumps(ks.status(), indent=2))
        else:
            print(f"Unknown command: {cmd}")
    else:
        print(json.dumps(ks.status(), indent=2))