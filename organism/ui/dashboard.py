"""
Dashboard - Web interface for organism observations and proposals.

Simple HTTP server (standard library only) that visualizes:
- Recent observations
- Top priorities
- Generated proposals
- Decision history

Accessible at http://localhost:8765
"""

import json
import http.server
import socketserver
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional

from ..core.loop import DevOrganism


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for the organism dashboard."""
    
    # Share state with handler instances
    organism = None
    evidence_dir = None
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self._render_dashboard().encode())
            
            elif path == '/api/observe':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.organism.run_once(top_n=5)
                self.wfile.write(json.dumps(result, indent=2, default=str).encode())
            
            elif path == '/api/proposals':
                self.send_response(200)
                self.send_header('Content-type', 'text/markdown')
                self.end_headers()
                proposals_file = self.evidence_dir / "top_proposals.md"
                if proposals_file.exists():
                    self.wfile.write(proposals_file.read_bytes())
                else:
                    self.wfile.write(b"No proposals generated yet.")
            
            elif path == '/api/decisions':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                stats = self.organism.taste_model.get_decision_stats()
                self.wfile.write(json.dumps(stats, indent=2).encode())
            
            elif path == '/api/observations':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                obs = self.organism.observer.observe()
                self.wfile.write(json.dumps(obs.to_dict(), indent=2, default=str).encode())
            
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Not found")
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Server error: {e}".encode())
    
    def do_POST(self):
        """Handle POST requests for decisions."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            if path == '/api/decide':
                task_id = data.get('task_id')
                action = data.get('action')
                
                if not task_id or action not in ['approve', 'reject', 'defer']:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Invalid input'}).encode())
                    return
                
                self.organism.record_decision(task_id, action)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok', 'task_id': task_id, 'action': action}).encode())
            
            else:
                self.send_response(404)
                self.end_headers()
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Server error: {e}".encode())
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def _render_dashboard(self) -> str:
        """Render the main dashboard HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Dev Organism Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            border-bottom: 1px solid #30363d;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #58a6ff;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #8b949e;
            font-size: 14px;
        }
        .section {
            margin-bottom: 40px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
        }
        .section h2 {
            color: #79c0ff;
            margin-bottom: 15px;
            font-size: 18px;
            border-bottom: 1px solid #30363d;
            padding-bottom: 10px;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        button {
            background: #238636;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        button:hover {
            background: #2ea043;
        }
        button.secondary {
            background: #30363d;
            color: #c9d1d9;
        }
        button.secondary:hover {
            background: #484f58;
        }
        .loading {
            color: #8b949e;
            font-style: italic;
        }
        .error {
            color: #f85149;
            padding: 10px;
            background: #16131d;
            border-left: 3px solid #f85149;
            border-radius: 3px;
            margin: 10px 0;
        }
        .success {
            color: #3fb950;
            padding: 10px;
            background: #0d3d1d;
            border-left: 3px solid #3fb950;
            border-radius: 3px;
            margin: 10px 0;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #0d1117;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #30363d;
        }
        .stat-label {
            color: #8b949e;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .stat-value {
            color: #58a6ff;
            font-size: 24px;
            font-weight: bold;
        }
        .proposal-item {
            background: #0d1117;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 3px solid #58a6ff;
            border-radius: 3px;
        }
        .proposal-title {
            color: #79c0ff;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .proposal-meta {
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 8px;
        }
        .proposal-actions {
            display: flex;
            gap: 8px;
        }
        .proposal-actions button {
            padding: 6px 12px;
            font-size: 12px;
        }
        .risk-low { color: #3fb950; }
        .risk-medium { color: #d29922; }
        .risk-high { color: #f85149; }
        code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 3px;
            color: #79c0ff;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        }
        .code-block {
            background: #0d1117;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #30363d;
            overflow-x: auto;
            margin: 10px 0;
        }
        .code-block code {
            background: none;
            padding: 0;
            color: #79c0ff;
        }
        .api-endpoint {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            color: #79c0ff;
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 Dev Organism Dashboard</h1>
            <p class="subtitle">Living development environment. Observes, prioritizes, proposes. You decide.</p>
        </header>
        
        <div class="section">
            <h2>⚡ Quick Actions</h2>
            <div class="button-group">
                <button onclick="runObservation()">🔍 Run Observation Cycle</button>
                <button class="secondary" onclick="reloadProposals()">📋 Reload Proposals</button>
                <button class="secondary" onclick="showStats()">📊 Show Stats</button>
            </div>
            <div id="status"></div>
        </div>
        
        <div class="section">
            <h2>📊 Statistics</h2>
            <div id="stats-container" class="stats">
                <div class="stat-card">
                    <div class="stat-label">Total Decisions</div>
                    <div class="stat-value" id="stat-total">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Approved</div>
                    <div class="stat-value" id="stat-approved">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Rejected</div>
                    <div class="stat-value" id="stat-rejected">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Approval Rate</div>
                    <div class="stat-value" id="stat-rate">-</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Top Proposals</h2>
            <div id="proposals-container" class="loading">Loading proposals...</div>
        </div>
        
        <div class="section">
            <h2>📖 API Documentation</h2>
            <p>Interact with the organism programmatically:</p>
            <div class="code-block">
                <code># Get fresh observations<br>
curl http://localhost:8765/api/observe<br>
<br>
# Get top proposals<br>
curl http://localhost:8765/api/proposals<br>
<br>
# Record a decision<br>
curl -X POST http://localhost:8765/api/decide \\<br>
&nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
&nbsp;&nbsp;-d '{"task_id": "todo_0", "action": "approve"}'<br>
<br>
# Get decision stats<br>
curl http://localhost:8765/api/decisions
                </code>
            </div>
        </div>
        
        <div class="section">
            <h2>ℹ️ About</h2>
            <p>
                The <strong>Dev Organism</strong> is a research fork of <strong>Project-S</strong>.<br>
                It creates a "living development environment" that:
            </p>
            <ul style="margin-left: 20px; margin-top: 10px;">
                <li><strong>Observes:</strong> Git changes, TODOs, terminal patterns</li>
                <li><strong>Prioritizes:</strong> Multi-metric scoring (impact, learning, EV, effort)</li>
                <li><strong>Proposes:</strong> Human-readable actionable recommendations</li>
                <li><strong>Learns:</strong> Taste model adapts to user decisions</li>
            </ul>
            <p style="margin-top: 15px;">
                <em>Important: The organism is NOT autonomous. All actions require explicit human approval.</em>
            </p>
        </div>
    </div>
    
    <script>
        async function runObservation() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<span class="loading">Running observation cycle...</span>';
            
            try {
                const response = await fetch('/api/observe');
                const data = await response.json();
                
                statusDiv.innerHTML = `
                    <div class="success">✓ Cycle complete<br>
                    Tasks: ${data.tasks_collected} | Proposals: ${data.top_proposals.length}</div>
                `;
                
                setTimeout(() => reloadProposals(), 500);
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }
        
        async function reloadProposals() {
            const container = document.getElementById('proposals-container');
            container.innerHTML = '<span class="loading">Loading proposals...</span>';
            
            try {
                const response = await fetch('/api/proposals');
                const text = await response.text();
                
                container.innerHTML = `<pre style="background: #0d1117; padding: 15px; border-radius: 6px; overflow-x: auto;">${escapeHtml(text)}</pre>`;
            } catch (error) {
                container.innerHTML = `<div class="error">Failed to load proposals: ${error.message}</div>`;
            }
        }
        
        async function showStats() {
            try {
                const response = await fetch('/api/decisions');
                const stats = await response.json();
                
                document.getElementById('stat-total').textContent = stats.total;
                document.getElementById('stat-approved').textContent = stats.approved;
                document.getElementById('stat-rejected').textContent = stats.rejected;
                document.getElementById('stat-rate').textContent = (stats.approval_rate * 100).toFixed(0) + '%';
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Load stats on page load
        window.addEventListener('load', () => {
            showStats();
            reloadProposals();
        });
    </script>
</body>
</html>
"""


class Dashboard:
    """Simple HTTP dashboard for organism observations."""
    
    def __init__(self, organism: DevOrganism, port: int = 8765):
        """
        Initialize dashboard.
        
        Args:
            organism: DevOrganism instance
            port: Port to listen on
        """
        self.organism = organism
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start dashboard server in background thread."""
        # Share organism with handler
        DashboardHandler.organism = self.organism
        DashboardHandler.evidence_dir = self.organism.evidence_dir
        
        self.server = socketserver.TCPServer(("", self.port), DashboardHandler)
        
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        print(f"\n🌐 Dashboard running at http://localhost:{self.port}")
        print("   Press Ctrl+C to stop\n")
    
    def stop(self):
        """Stop dashboard server."""
        if self.server:
            self.server.shutdown()


def run_dashboard(repo_root: str = '.', port: int = 8765):
    """
    Convenience function to start the dashboard.
    
    Args:
        repo_root: Path to git repository
        port: Port to listen on
    """
    organism = DevOrganism(repo_root, str(Path(repo_root) / 'organism' / 'evidence'))
    dashboard = Dashboard(organism, port)
    dashboard.start()
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        dashboard.stop()


if __name__ == '__main__':
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    run_dashboard(repo)
