# Wispr Actions

Voice-controlled gateway that combines **fast voice input** with **rich visual output** for productivity apps.

## What This Does

Speak natural language commands → Get beautiful, structured visual results. No custom integration code needed for each app.

**Why voice + visual?**
- **Voice input**: Fastest way to communicate (as fast as you can think)
- **Visual output**: Most efficient way to comprehend information (layouts > text > audio)

**Example commands:**
- "list files on desktop" → Visual file browser with icons and metadata
- "search github for react repos" → Cards showing repos with stars, language, and clickable links
- "search for AI news" → Formatted search results with titles, descriptions, and sources

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

This system solves two fundamental challenges:

### Challenge 1: Application Integration at Scale → MCP Gateway

**Traditional approach fails:** Building custom integrations for thousands of apps (Linear, Notion, GitHub, Slack, etc.) = N × maintenance cost. Every API change breaks your code.

**MCP Gateway solution:** One gateway that routes to app-maintained MCP servers. O(1) integration effort. As MCP ecosystem grows, system automatically gets more powerful—no code changes needed.

### Challenge 2: Information Display at Scale → Component Library + Data Bindings

**Traditional approach fails:** Building custom UI for every function in every app = N×M maintenance nightmare.

**Component Library solution:** Reusable UI primitives (cards, lists, key-value pairs, links) cover 80%+ of use cases. Declarative data bindings map MCP responses → UI components. Future: LLM-assisted binding generation with caching—once ANY user executes a function, we generate the optimal UI for all future users.

**Complete Pipeline:**
```
Voice Input (fast communication)
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
[Data Binding Router] → Maps response → UI components
    ↓
[Terminal UI] → Rich visual output (efficient comprehension)
```

## Why This Architecture?

**Input Side: MCP Gateway for O(1) Scaling**
- **Problem:** ~200 apps with 100M+ users, plus long tail of niche tools. Covering 80% of workflows = thousands of custom integrations.
- **Solution:** ONE gateway that dynamically routes to MCP servers maintained by app providers themselves.
- **Result:** Add new services via config only. Zero maintenance burden. Automatic ecosystem benefits.

**Output Side: Component Library for O(1) Scaling**
- **Problem:** Voice input is fastest (as fast as thinking), but visual comprehension is most efficient. Millions of engineers work on UI/UX for a reason—layouts, components, and styling communicate nuanced information better than text or audio.
- **Solution:** Reusable component library + declarative data bindings. Post-process with LLM to generate bindings, cache for all users.
- **Result:** Build UI components once, map any function to them. Network effects—first execution generates binding for everyone.

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
│       ├── app.py             # Textual terminal UI
│       └── components/        # Reusable UI components
│           ├── github.py      # GitHub data bindings
│           └── search.py      # Search results data bindings
├── docs/
│   ├── PROMPT.md              # Interview challenge prompt
│   ├── ABSTRACT.md            # Architecture rationale
│   └── ARCHITECTURE.md        # Technical deep dive
└── requirements.txt
```

## Key Design Decisions

**Dual O(1) Scaling Strategy:**
- **Input:** MCP Gateway handles application integration without custom code per app
- **Output:** Component Library + Data Bindings handle UI without custom components per function
- Both sides scale independently as ecosystem grows

**Terminal UI instead of web/native app:**
- Focus on demonstrating core architecture (MCP gateway + component bindings)
- Same backend can power any frontend later
- Faster to build, easier to demo dual-scaling concept

**OpenAI Whisper + GPT-4:**
- Single provider (simpler setup)
- GPT-4 function calling is excellent for structured outputs
- Proven reliability for voice → structured intent

**Component-Based Output:**
- Reusable UI primitives (cards, lists, key-value displays)
- Declarative data bindings separate from component logic
- Easy to extend—add new binding without touching component code

## Current Limitations

- **Latency:** ~2.6-5.5 seconds per command
  - Whisper API: 1.5-3s (network RTT)
  - GPT-4 Intent Parsing: 1-2s (network RTT)
  - MCP Execution: 0.1-0.5s (local IPC)
  - Sequential bottleneck: Cannot parallelize ASR → Intent → Execution
  - Potential improvements: Intent caching, tool filtering, faster models (GPT-4o-mini)
- **UI Components:** Basic terminal components (cards, lists, key-value pairs)
  - Sufficient for demo, can be extended to web/native later
- **Data Bindings:** Manual for now (GitHub, Brave Search)
  - Future: LLM-assisted binding generation with caching
- **Services:** Currently filesystem, GitHub, Brave Search
  - More can be added via config only (no code changes)

## Testing

Run the test suite:
```bash
cd tests && python run_all_tests.py
```

**Test structure:**
- **Unit tests**: Individual functions (HTML processing, field filtering)
- **Functional tests**: Full application flows (data binding, APIs, voice pipeline)

Tests automatically skip components that aren't available (e.g., API keys, audio drivers).

## Development

Built for the Wispr full-stack engineering challenge. Demonstrates:
- **Dual O(1) Scaling:** MCP Gateway (input) + Component Library (output)
- **Voice → Visual Pipeline:** Fast input meets efficient comprehension
- **LLM Integration:** GPT-4 function calling for intent parsing
- **Declarative UI:** Data bindings separate from component logic
- **Clean Abstractions:** Modular architecture for easy extension
