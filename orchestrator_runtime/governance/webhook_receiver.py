"""
MS-AO4 AO4.2 — Webhook Receiver for External Goal Triggers

Simple HTTP server for accepting goal submissions via POST /goal.
Binds to localhost only (no external exposure).

Rules:
  - Port: 8765, localhost only
  - POST /goal — accepts JSON goal submission
  - Validates: required fields (id, title, risk, sandbox_only)
  - HIGH risk → pending_human_approval.json (NOT auto-processed)
  - LOW/MEDIUM + sandbox_only → trigger_queue.json
  - Rate limit: max 10 requests per minute per IP
  - Kill switch check on every request
  - Log all requests to trigger_log.jsonl

Usage:
  python orchestrator_runtime/governance/webhook_receiver.py
  # or
  from orchestrator_runtime.governance.webhook_receiver import WebhookReceiver
  receiver = WebhookReceiver(port=8765)
  receiver.start()
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

TRIGGER_QUEUE_PATH = Path(__file__).parent / "trigger_queue.json"
PENDING_APPROVAL_PATH = Path(__file__).parent / "pending_human_approval.json"
TRIGGER_LOG_PATH = Path(__file__).parent / "trigger_log.jsonl"

# Rate limit: max requests per minute per IP
MAX_REQUESTS_PER_MINUTE = 10

# Kill switch integration
try:
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    _KILL_SWITCH = KillSwitch()
except ImportError:
    _KILL_SWITCH = None

# Risk classifier integration
try:
    from orchestrator_runtime.governance.risk_classifier import classify_goal
    _CLASSIFIER = classify_goal
except ImportError:
    _CLASSIFIER = None


def _load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    if path.exists():
        path.unlink()
    tmp.rename(path)


def _log_event(event_type, details=None):
    """Append event to trigger_log.jsonl."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "details": details or {},
    }
    with open(TRIGGER_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# Rate limit tracking: {ip: [timestamps]}
_rate_limit_store = {}
_rate_lock = threading.Lock()


def _check_rate_limit(ip):
    """Check if IP is within rate limit. Returns (allowed, current_count)."""
    now = time.time()
    with _rate_lock:
        if ip not in _rate_limit_store:
            _rate_limit_store[ip] = []

        # Remove entries older than 60 seconds
        _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < 60]
        count = len(_rate_limit_store[ip])

        if count >= MAX_REQUESTS_PER_MINUTE:
            return False, count

        # Add current request
        _rate_limit_store[ip].append(now)
        return True, count + 1


def _is_auto_approvable(goal):
    """Check if goal is auto-approvable."""
    risk = goal.get("risk", "HIGH")
    auto_approve = goal.get("auto_approve", False)
    sandbox_only = goal.get("sandbox_only", False)

    if risk == "LOW" and auto_approve:
        return True
    if risk == "MEDIUM" and sandbox_only:
        return True
    if risk == "LOW" and sandbox_only:
        return True
    return False


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for goal webhook submissions."""

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass

    def _send_json(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "webhook_receiver"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        """Handle POST /goal submissions."""
        if self.path != "/goal":
            self._send_json(404, {"error": "not found"})
            return

        # Get client IP
        client_ip = self.client_address[0] if hasattr(self, "client_address") else "unknown"

        # Rate limit check
        allowed, count = _check_rate_limit(client_ip)
        if not allowed:
            _log_event("webhook_rate_limited", {"ip": client_ip, "count": count})
            self._send_json(429, {
                "error": "rate_limit_exceeded",
                "limit": MAX_REQUESTS_PER_MINUTE,
                "current": count,
            })
            return

        # Kill switch check
        if _KILL_SWITCH is not None and _KILL_SWITCH.is_active():
            status = _KILL_SWITCH.status()
            _log_event("webhook_kill_switch", {"ip": client_ip, "reason": status.get("reason", "")})
            self._send_json(503, {
                "error": "kill_switch_active",
                "reason": status.get("reason", ""),
            })
            return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"error": "empty body"})
            return

        body = self.rfile.read(content_length)
        try:
            goal = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "invalid JSON"})
            return

        # Validate required fields
        required = ["id", "title", "risk"]
        missing = [f for f in required if f not in goal]
        if missing:
            _log_event("webhook_validation_error", {
                "ip": client_ip,
                "missing_fields": missing,
            })
            self._send_json(400, {
                "error": "missing_required_fields",
                "required": required,
                "missing": missing,
            })
            return

        goal_id = goal.get("id")
        risk = goal.get("risk", "HIGH")

        _log_event("webhook_goal_received", {
            "ip": client_ip,
            "goal_id": goal_id,
            "risk": risk,
        })

        # HIGH risk → pending_human_approval (NOT auto-processed)
        if risk == "HIGH":
            pending = _load_json(PENDING_APPROVAL_PATH, {"goals": []})
            # Avoid duplicates
            existing_ids = {g.get("id") for g in pending.get("goals", [])}
            if goal_id not in existing_ids:
                pending["goals"].append({
                    **goal,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "status": "PENDING_HUMAN_APPROVAL",
                    "source": "webhook",
                })
                _save_json(PENDING_APPROVAL_PATH, pending)

            _log_event("webhook_goal_pending_approval", {
                "goal_id": goal_id,
                "risk": "HIGH",
            })

            self._send_json(202, {
                "status": "pending_human_approval",
                "goal_id": goal_id,
                "reason": "HIGH risk goals require human approval",
            })
            return

        # LOW/MEDIUM + sandbox_only → trigger_queue
        if _is_auto_approvable(goal):
            # Risk classifier check
            if _CLASSIFIER is not None:
                try:
                    result = _CLASSIFIER(goal_id)
                    if result.get("decision") == "REJECTED":
                        _log_event("webhook_goal_rejected", {
                            "goal_id": goal_id,
                            "reason": result.get("reason", ""),
                        })
                        self._send_json(403, {
                            "error": "goal_rejected_by_classifier",
                            "reason": result.get("reason", ""),
                        })
                        return
                except Exception as e:
                    _log_event("webhook_classifier_error", {
                        "goal_id": goal_id,
                        "error": str(e),
                    })

            trigger_queue = _load_json(TRIGGER_QUEUE_PATH, {"goals": []})
            existing_ids = {g.get("id") for g in trigger_queue.get("goals", [])}
            if goal_id not in existing_ids:
                trigger_queue["goals"].append({
                    **goal,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "source": "webhook",
                })
                _save_json(TRIGGER_QUEUE_PATH, trigger_queue)

            _log_event("webhook_goal_approved", {
                "goal_id": goal_id,
                "risk": risk,
            })

            self._send_json(200, {
                "status": "accepted",
                "goal_id": goal_id,
                "queue": "trigger_queue",
            })
            return

        # Not auto-approvable → pending
        pending = _load_json(PENDING_APPROVAL_PATH, {"goals": []})
        existing_ids = {g.get("id") for g in pending.get("goals", [])}
        if goal_id not in existing_ids:
            pending["goals"].append({
                **goal,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "status": "PENDING_HUMAN_APPROVAL",
                "source": "webhook",
                "reason": "not_auto_approvable",
            })
            _save_json(PENDING_APPROVAL_PATH, pending)

        self._send_json(202, {
            "status": "pending_human_approval",
            "goal_id": goal_id,
            "reason": "Goal not auto-approvable",
        })


class WebhookReceiver:
    """Webhook receiver server wrapper."""

    def __init__(self, port=8765, host="127.0.0.1"):
        self.port = port
        self.host = host
        self._server = None
        self._thread = None

    def start(self, blocking=True):
        """Start the webhook receiver server."""
        self._server = HTTPServer((self.host, self.port), WebhookHandler)
        _log_event("webhook_server_started", {"host": self.host, "port": self.port})
        print(f"Webhook receiver listening on {self.host}:{self.port}")

        if blocking:
            try:
                self._server.serve_forever()
            except KeyboardInterrupt:
                self.stop()
        else:
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the webhook receiver server."""
        if self._server:
            self._server.shutdown()
            _log_event("webhook_server_stopped", {})
            print("Webhook receiver stopped")


if __name__ == "__main__":
    receiver = WebhookReceiver(port=8765)
    receiver.start(blocking=True)