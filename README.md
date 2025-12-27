# Wispr Actions

Voice-controlled gateway combining **fast voice input** with **rich visual output** for productivity apps.

## What This Does

Speak natural language → Get structured visual results. No custom integration code per app.

**Example commands:**
- "list files on desktop" → Visual file browser with icons and metadata
- "search github for react repos" → Cards with stars, language, clickable links
- "search for AI news" → Formatted results with titles and sources

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

First run prompts for OpenAI API key (saved to `.env`).

**Controls:**
- **V** - Hold to record, release to process
- **Q** - Quit

## Architecture

Solves two fundamental challenges:

### Challenge 1: Application Integration at Scale

**Problem:** Building custom integrations for thousands of apps = N × maintenance cost.

**Solution:** MCP Gateway routes to app-maintained MCP servers. Add services via config only—zero code changes.

### Challenge 2: Information Display at Scale

**Problem:** Building custom UI for every function in every app = N×M maintenance nightmare.

**Solution:** Auto data binder maps any JSON response to UI components using heuristics. New tools work automatically.

### Complete Pipeline

```
Voice Input
    ↓
[Audio Capture] → PyAudio records audio
    ↓
[Whisper API] → Transcribes to text
    ↓
[GPT-4] → Parses intent into function call
    ↓
[MCP Gateway] → Routes to correct MCP server
    ↓
[MCP Server] → Executes action (filesystem, GitHub, etc.)
    ↓
[Auto Data Binder] → Maps JSON → UI components
    ↓
[Terminal UI] → Displays visual result
```

## Why This Scales

**Input (MCP Gateway):**
- O(1) integration: Add services via config, not code
- Leverage community MCP servers
- Zero maintenance (providers maintain servers)

**Output (Auto Data Binder):**
- O(1) UI generation: Works with any tool automatically
- Heuristic mapping: Lists → cards, objects → metadata, strings → banners
- Field processing: HTML stripping, truncation, filtering IDs/timestamps/booleans

**Adding a service:**
```json
{
  "name": "slack",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": {"SLACK_TOKEN": "${SLACK_TOKEN}"}
}
```

That's it. No code changes.

## Project Structure

```
flow-action-gateway/
├── main.py                    # Entry point
├── mcp_config.json            # MCP server configuration
├── src/
│   ├── gateway/
│   │   ├── mcp_gateway.py     # MCP connection manager
│   │   ├── mcp_config.py      # Config loader
│   │   └── intent_parser.py   # GPT-4 intent parsing
│   ├── voice/
│   │   ├── capture.py         # Audio recording
│   │   └── transcription.py   # Whisper integration
│   └── ui/
│       ├── app.py             # Textual TUI
│       ├── auto_data_binder.py # Automatic JSON → UI mapping
│       └── components/         # Reusable UI primitives
├── tests/
│   ├── unit/                   # Function tests
│   └── functional/             # Application flow tests
└── docs/
    ├── ABSTRACT.md             # Architecture rationale
    └── ARCHITECTURE.md         # Technical details
```

## Key Decisions

**MCP Gateway:**
- Routes to app-maintained servers instead of custom integrations
- Scales O(1): Adding services = config change only

**Auto Data Binder:**
- Automatically maps any JSON to UI components
- No custom code per tool
- Good enough for 80% of cases

**Terminal UI:**
- Focus on architecture, not frontend polish
- Same backend works with any frontend

**OpenAI Whisper + GPT-4:**
- Single provider (simpler)
- GPT-4 function calling handles ambiguity well

## Testing

```bash
cd tests && python run_all_tests.py
```

- **Unit tests**: HTML processing, field filtering
- **Functional tests**: Data binding, APIs, voice pipeline

## Scope

**In scope:** Proving O(1) scaling architecture via MCP gateway + auto data binder

**Out of scope (not demo focus):**
- Latency optimization (current: 4-6s, production: <500ms with Wispr streaming ASR)
- Production UX polish (terminal UI → web/native frontend)
- Auth/security (production needs OAuth, secure storage)
- Error recovery (production needs retry logic, graceful degradation)

## Development

Built for Wispr full-stack engineering challenge. Demonstrates:
- **Dual O(1) Scaling:** MCP Gateway + Auto Data Binder
- **Voice → Visual Pipeline:** Fast input, efficient comprehension
- **Protocol-Based Integration:** Leverage MCP ecosystem
- **Clean Abstractions:** Modular, extensible architecture
