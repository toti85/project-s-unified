# Project-S Interactive Layer — V1 Screen Plan

**Date:** 2026-05-17
**Type:** Screen/layout design for v1
**Status:** Design only, NO implementation yet

---

## 1. Layout Overview

### 1.1 Single-Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER BAR                                                      │
│  Session: abc-123  Mission: running  Elapsed: 2:34  Model: Q3.6 │
├─────────────────────────────────────────────────────────────────┤
│  MAIN AREA (flex: 1, scrollable)                                 │
│  ┌──────────────────────┬──────────────────────────────────────┐│
│  │                      │                                      ││
│  │  CHAT PANEL          │  MISSION PANEL                       ││
│  │  (60% width)         │  (40% width)                         ││
│  │                      │                                      ││
│  │  ┌────────────────┐  │  ┌──────────────────────────────┐   ││
│  │  │ Messages       │  │  │ Mission Status               │   ││
│  │  │ (scrollable)   │  │  │ ● Running: web_search        │   ││
│  │  │                │  │  │ ○ web_scraper                │   ││
│  │  │ User: ...      │  │  │ ○ synthesis                  │   ││
│  │  │ AI: ...        │  │  │                              │   ││
│  │  │ User: ...      │  │  │ Progress                     │   ││
│  │  │ AI: ...        │  │  │ [████████░░░░] 65%          │   ││
│  │  │                │  │  │                              │   ││
│  │  │                │  │  │ Current Tool                 │   ││
│  │  │                │  │  │ web_search                   │   ││
│  │  │                │  │  │ Duration: 1:23               │   ││
│  │  │                │  │  │                              │   ││
│  │  │                │  │  │ Tool Events                  │   ││
│  │  │                │  │  │ [14:23] web_search start    │   ││
│  │  │                │  │  │ [14:24] web_search complete │   ││
│  │  │                │  │  │ [14:24] web_scraper start   │   ││
│  │  │                │  │  │                              │   ││
│  │  │                │  │  │ Evidence (collapsible)       │   ││
│  │  │                │  │  │ [▼ Show last 5 entries]     │   ││
│  │  └────────────────┘  │  └──────────────────────────────┘   ││
│  │                      │                                      ││
│  │  ┌────────────────┐  │                                      ││
│  │  │ Input: [_____] │  │                                      ││
│  │  │        [Send]  │  │                                      ││
│  │  └────────────────┘  │                                      ││
│  └──────────────────────┴──────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  FOOTER BAR                                                      │
│  Files: [upload]  Reports: [list]  Evidence: [query]           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Responsive Behavior

- **Desktop (≥1200px):** Two-panel layout (chat 60% / mission 40%)
- **Tablet (768-1199px):** Two-panel layout, narrower mission panel
- **Mobile (<768px):** Stacked layout (chat on top, mission below) — NOT prioritized

---

## 2. Screen 1: Main Chat

### 2.1 Purpose

Primary interaction point. User types tasks, AI responds with results.

### 2.2 Components

| Component | Description |
|-----------|-------------|
| **Message list** | Scrollable list of user/AI messages, ordered chronologically |
| **Message input** | Textarea + Send button |
| **Message types** | User text, AI text, AI report link, AI error, AI system |

### 2.3 Message Format

```
User message:
┌─────────────────────────────────────────────┐
│ You                                          │
│ 2026-05-17 21:30:15                         │
│                                             │
│ Research the current state of local LLM     │
│ deployment on consumer hardware.            │
└─────────────────────────────────────────────┘

AI message:
┌─────────────────────────────────────────────┐
│ Project-S     ⏱ 3:45                        │
│ 2026-05-17 21:34:00                         │
│                                             │
│ Research complete. Key findings:            │
│                                             │
│ 1. Qwen3.6-35B-A3B runs on 13-24GB VRAM   │
│ 2. Quantized versions available             │
│ 3. Local inference: 120-190 tok/sec        │
│                                             │
│ Full report: [download report.md]           │
└─────────────────────────────────────────────┘

AI message with error:
┌─────────────────────────────────────────────┐
│ Project-E     ❌ FAILED                     │
│ 2026-05-17 21:30:45                         │
│                                             │
│ Mission failed: browser automation timeout  │
│ after 180 seconds.                          │
│                                             │
│ [Retry mission]  [View error details]       │
└─────────────────────────────────────────────┘

System message:
┌─────────────────────────────────────────────┐
│ System                                      │
│ 2026-05-17 21:30:15                         │
│                                             │
│ Mission started: "Research..."              │
│ Model: qwen/qwen3.6-35b-a3b                │
│ Timeout: 600s                               │
└─────────────────────────────────────────────┘
```

### 2.4 Input Behavior

- **Single-line input:** Press Enter to send
- **Multi-line input:** Shift+Enter for newline
- **Max input length:** 4000 characters
- **Send button:** Always visible next to input
- **Loading state:** Send button disabled while mission running

---

## 3. Screen 2: Mission Progress

### 3.1 Purpose

Real-time visibility into what the AI is doing.

### 3.2 Components

| Component | Description |
|-----------|-------------|
| **Status indicator** | Current mission status (idle/running/synthesizing/completed/failed) |
| **Progress bar** | Visual progress (0-100%) |
| **Tool queue** | List of tools in execution order |
| **Current tool** | Highlighted tool currently executing |
| **Tool events** | Timestamped log of tool start/complete/error |
| **Elapsed time** | How long the mission has been running |
| **Estimated time** | Based on average tool durations |

### 3.3 Status States

| State | Color | Progress | Description |
|-------|-------|----------|-------------|
| **idle** | Gray | N/A | No mission running |
| **pending** | Blue | 0% | Mission queued |
| **running** | Blue | 1-99% | Tool execution in progress |
| **synthesizing** | Purple | 90-99% | LLM synthesis in progress |
| **complete** | Green | 100% | Mission finished |
| **failed** | Red | N/A | Mission failed |

### 3.4 Tool Event Log Format

```
[14:23:01] ● web_search start
[14:23:15] ✓ web_search complete (14s)
[14:23:15] ● web_scraper start
[14:23:28] ✓ web_scraper complete (13s)
[14:23:28] ● file_writer start
[14:23:29] ✓ file_writer complete (1s)
[14:23:29] ● synthesis start (Qwen3.6)
[14:24:12] ✓ synthesis complete (43s)
[14:24:12] ✓ mission complete (71s)
```

---

## 4. Screen 3: Evidence/Log Viewer

### 4.1 Purpose

View the Witness layer evidence trail.

### 4.2 Components

| Component | Description |
|-----------|-------------|
| **Evidence list** | Table of recent evidence entries |
| **Filter** | Filter by source, tool, success |
| **Sort** | Sort by timestamp, source |
| **Entry detail** | Click to view full entry JSON |
| **Total count** | Total evidence entries in JSONL |

### 4.3 Evidence Table Format

| Timestamp | Source | Tool | Success | Duration |
|-----------|--------|------|---------|----------|
| 21:30:15 | super_intelligent_ai | web_search | ✓ | 14s |
| 21:30:28 | super_intelligent_ai | web_scraper | ✓ | 13s |
| 21:30:45 | super_intelligent_ai | file_writer | ✓ | 1s |
| 21:31:28 | super_intelligent_ai | synthesis | ✓ | 43s |

### 4.4 Entry Detail View

When clicking a row, show the full JSON:

```json
{
  "timestamp": "2026-05-17T21:30:15.123Z",
  "source": "super_intelligent_ai",
  "tool": "web_search",
  "success": true,
  "duration_ms": 14234,
  "params": {"query": "local LLM deployment", "max_results": 10},
  "result_summary": "Found 10 results from DuckDuckGo"
}
```

---

## 5. Screen 4: File Manager

### 5.1 Purpose

Upload files to the server, download generated reports.

### 5.2 Components

| Component | Description |
|-----------|-------------|
| **Upload area** | Drag-and-drop or click to upload |
| **Upload list** | List of uploaded files for current session |
| **Output list** | List of generated reports |
| **Download buttons** | One per output file |
| **File info** | Size, timestamp, type |

### 5.3 Upload Area

```
┌─────────────────────────────────────────────┐
│  Upload files                               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │                                     │   │
│  │   Drag files here or click to       │   │
│  │   browse                            │   │
│  │                                     │   │
│  │   Max file size: 10MB               │   │
│  │   Accepted: any text file           │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 5.4 File Lists

**Uploaded files:**
```
┌─────────────────────────────────────────────┐
│  Uploaded files                             │
│  ┌────────────────┬────────┬──────────────┐ │
│  │ Name           │ Size   │ Uploaded     │ │
│  ├────────────────┼────────┼──────────────┤ │
│  │ research.txt   │ 2.3KB  │ 21:30:15     │ │
│  │ data.csv       │ 15.7KB │ 21:28:42     │ │
│  └────────────────┴────────┴──────────────┘ │
└─────────────────────────────────────────────┘
```

**Generated reports:**
```
┌─────────────────────────────────────────────┐
│  Generated reports                          │
│  ┌────────────────┬────────┬──────────────┐ │
│  │ Name           │ Size   │ Generated    │ │
│  ├────────────────┼────────┼──────────────┤ │
│  │ report_001.md  │ 3.5KB  │ 21:34:00     │ │ [Download]│
│  │ report_002.md  │ 12.1KB │ 21:20:15     │ │ [Download]│
│  └────────────────┴────────┴──────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 6. Screen 5: Report Viewer

### 6.1 Purpose

View generated reports inline (not just download).

### 6.2 Components

| Component | Description |
|-----------|-------------|
| **Report list** | List of available reports |
| **Report viewer** | Markdown-rendered report content |
| **Raw view** | Toggle between rendered and raw markdown |
| **Download button** | Download the report file |

### 6.3 Report Viewer Format

```
┌─────────────────────────────────────────────┐
│  report_001.md                    [Raw] [↓] │
├─────────────────────────────────────────────┤
│                                             │
│  # Research Report                          │
│                                             │
│  ## Executive Summary                       │
│                                             │
│  Local LLM deployment on consumer hardware  │
│  is feasible with Qwen3.6-35B-A3B...       │
│                                             │
│  ## Key Findings                            │
│                                             │
│  1. VRAM requirements: 13-24GB              │
│  2. Inference speed: 120-190 tok/sec        │
│  3. Quantization available: 4-bit, 8-bit    │
│                                             │
│  ...                                        │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 7. Navigation

### 7.1 Tab-Based Navigation

```
┌─────────────────────────────────────────────────────────────────┐
│  [Chat] [Mission] [Evidence] [Files] [Reports]                 │
└─────────────────────────────────────────────────────────────────┘
```

- **Chat:** Default view, always visible
- **Mission:** Shows mission progress (auto-opens when mission starts)
- **Evidence:** Evidence viewer
- **Files:** File manager
- **Reports:** Report viewer

### 7.2 Auto-Open Behavior

- When a mission starts → Mission tab auto-opens
- When a report is generated → Reports tab auto-opens (briefly)
- When an error occurs → Chat shows error with link to Mission tab

---

## 8. Color Scheme

### 8.1 Theme: Dark (Operational)

| Element | Color |
|---------|-------|
| **Background** | #1a1a2e (dark navy) |
| **Panel background** | #16213e (slightly lighter) |
| **Text** | #e0e0e0 (light gray) |
| **Accent** | #0f3460 (blue) |
| **Success** | #00c853 (green) |
| **Error** | #ff1744 (red) |
| **Warning** | #ff9100 (orange) |
| **Info** | #2979ff (blue) |
| **Synthesis** | #aa00ff (purple) |
| **Border** | #2a2a4e (dark gray-blue) |

### 8.2 Status Colors

| Status | Color |
|--------|-------|
| idle | #808080 (gray) |
| pending | #2979ff (blue) |
| running | #2979ff (blue, animated pulse) |
| synthesizing | #aa00ff (purple) |
| complete | #00c853 (green) |
| failed | #ff1744 (red) |

---

## 9. Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| **Header** | System sans-serif | 14px | 600 |
| **Message text** | System sans-serif | 14px | 400 |
| **Message timestamp** | System monospace | 11px | 400 |
| **Code** | System monospace | 13px | 400 |
| **Mission events** | System monospace | 12px | 400 |
| **Evidence table** | System monospace | 12px | 400 |
| **Report content** | System sans-serif | 14px | 400 |

---

## 10. What's NOT in V1

1. **Dark/light theme toggle** — Dark only for v1
2. **Custom font support** — System fonts only
3. **Message reactions** — Not needed for operational interface
4. **Voice input** — Not needed
5. **Image display** — Reports are text/markdown only
6. **Collaborative editing** — Single user only
7. **Keyboard shortcuts** — Enter to send is enough for v1
8. **Notification sounds** — Not needed
9. **Push notifications** — Local dev only
10. **PWA/install support** — Local dev only

---

## 11. Screen Sizes Target

| Size | Resolution | Behavior |
|------|-----------|----------|
| **Desktop** | ≥1200px | Full two-panel layout |
| **Laptop** | 900-1199px | Two-panel, narrower mission |
| **Tablet** | 768-899px | Two-panel, smaller fonts |
| **Mobile** | <768px | Stacked layout (deferred) |

Target: Desktop only for v1. Mobile layout can be added in Phase 2 if needed.

---

*End of screen plan document.*
*Next: Implementation sequence (PROJECT_S_INTERACTIVE_LAYER_IMPLEMENTATION_SEQUENCE_20260517.md)*