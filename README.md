# Wispr Actions

Voice-controlled gateway for productivity apps using the Model Context Protocol (MCP).

## What This Does

Speak natural language commands and execute actions across multiple apps without writing integration code for each one. Built on MCP (Model Context Protocol) to demonstrate O(1) integration scaling.

**Example commands:**
- "list files on desktop"
- "read test.txt"
- "search for pdf files"

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   python main.py
   ```

3. **First-time setup:**
   - You'll be prompted for your OpenAI API key
   - Configuration is saved to `.env`

## Controls

- **V** - Hold to record voice (release to process)
- **Q** - Quit

## Architecture Overview

**Voice → Action Pipeline:**
```
Voice Input
    ↓
[Audio Capture] → PyAudio buffers audio while V is held
    ↓
[Whisper API] → Transcribes to text
    ↓
[GPT-4 + MCP Tool Catalog] → Parses intent into structured function call
    ↓
[MCP Gateway] → Routes to correct MCP server
    ↓
[MCP Server] → Executes the action (filesystem, GitHub, etc.)
    ↓
[Terminal UI] → Shows result
```

## Why MCP?

Traditional approach: Write custom integration for each service (Slack, Gmail, Notion, etc.)
- **Problem:** N integrations = N × maintenance cost
- **Problem:** Every API change breaks your code

MCP approach: Connect to standard MCP servers that service providers maintain
- **Benefit:** Add new services via config only (no code changes)
- **Benefit:** Service providers maintain their own MCP servers
- **Benefit:** As MCP ecosystem grows, system gets more powerful automatically

**Adding a new service:**
```json
// Just add to mcp_config.json
{
  "name": "slack",
  "display_name": "Slack",
  "icon": "💬",
  "enabled": true,
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": {
    "SLACK_TOKEN": "${SLACK_TOKEN}"
  }
}
```

That's it. No code changes needed.

## Project Structure

```
flow-action-gateway/
├── main.py                    # Entry point with onboarding
├── mcp_config.json            # MCP server configuration
├── src/
│   ├── gateway/
│   │   ├── mcp_gateway.py     # MCP connection manager
│   │   ├── mcp_config.py      # Config loader
│   │   └── intent_parser.py   # GPT-4 intent understanding
│   ├── voice/
│   │   ├── capture.py         # Audio recording
│   │   └── transcription.py   # Whisper integration
│   └── ui/
│       └── app.py             # Textual terminal UI
├── docs/
│   ├── PROMPT.md              # Interview challenge prompt
│   ├── ABSTRACT.md            # Architecture rationale
│   └── ARCHITECTURE.md        # Technical deep dive
└── requirements.txt
```

## Key Design Decisions

**Terminal UI instead of web/native app:**
- Focus on demonstrating the MCP gateway architecture
- Same backend can power any frontend later
- Faster to build, easier to demo core functionality

**OpenAI Whisper + GPT-4:**
- Single provider (simpler setup)
- GPT-4 function calling is excellent for structured outputs
- Proven reliability

**MCP Gateway Pattern:**
- O(1) integration effort per service (vs O(N) for custom APIs)
- Leverage community-built MCP servers
- Future-proof as ecosystem grows

## Current Limitations

- **Latency:** ~4-6 seconds per command (Whisper API + GPT-4 API calls)
  - Could be improved with local Whisper (faster-whisper) + GPT-4o-mini
- **UI:** Basic terminal interface (sufficient for demo)
- **Services:** Currently filesystem + GitHub (more can be added via config)

## Development

Built for the Wispr full-stack engineering challenge. Demonstrates:
- Scalable architecture (MCP gateway pattern)
- LLM integration (GPT-4 function calling for intent parsing)
- Voice processing pipeline (Whisper → GPT-4 → MCP → Action)
- Clean abstractions and separation of concerns
