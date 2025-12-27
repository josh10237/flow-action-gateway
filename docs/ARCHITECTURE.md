# Architecture - Wispr Actions

## System Overview

Voice-controlled gateway connecting users to multiple productivity applications through natural language using the Model Context Protocol (MCP).

## Data Flow

```
Voice Input (hold V)
    ↓
[AudioCapture] → PyAudio streams mic input
    ↓
[Whisper API] → Converts audio to text
    ↓
[GPT-4] → Parses intent → Structured function call
    ↓
[MCPGateway] → Routes to correct MCP server
    ↓
[MCP Server] → Executes action
    ↓
[Auto Data Binder] → Maps JSON → UI components
    ↓
[Terminal UI] → Displays rich visual result
```

**Total latency: ~4-6 seconds**

---

## Core Components

### 1. Audio Capture (`src/voice/capture.py`)

```python
class AudioCapture:
    def start_recording()      # PyAudio blocking mode, 16kHz
    def get_volume_level()     # Returns 0-100 for waveform
    def get_audio_data()       # Returns buffered audio bytes
```

**Key decisions:**
- Blocking mode (simpler with Textual async)
- Volume calculated during recording (live waveform)
- 16kHz sample rate (optimal for Whisper)

### 2. Transcription (`src/voice/transcription.py`)

```python
class Transcriber:
    def transcribe(audio_data, sample_rate) -> str
        # Convert PCM → WAV
        # Call Whisper API
        # Filter hallucinations ("you", "thank you")
        # Return cleaned text
```

**Why API:** Faster than CPU inference, no model management

### 3. Intent Parser (`src/gateway/intent_parser.py`)

```python
class IntentParser:
    def parse(transcript: str) -> Dict
        # Call GPT-4 with function calling
        # System prompt: working directory, path resolution
        # Returns: {"function": "tool_name", "arguments": {...}}
```

**Example:**
```
"list files on desktop"
    → {"function": "list_directory", "arguments": {"path": "/Users/joshbenson/Desktop"}}
```

### 4. MCP Gateway (`src/gateway/mcp_gateway.py`)

**Connection Management:**
```python
class MCPGateway:
    sessions: Dict[str, ClientSession]     # Active MCP connections
    tools_cache: Dict[str, List]           # Tools per server
    tool_to_server: Dict[str, str]         # Routing table

    async def connect_server(config)
        # Start stdio subprocess
        # Maintain connection in background task
        # Cache tools, build routing table

    async def execute_tool(tool_name, args)
        # O(1) lookup: tool_name → server_name
        # Route to correct session
        # Return result
```

**Key insight:** GPT-4 sees unified tool catalog from all servers. Gateway handles routing transparently.

### 5. Auto Data Binder (`src/ui/auto_data_binder.py`)

**Automatically maps any JSON → UI components without custom code.**

```python
def bind_data(data: List[TextContent]) -> Component:
    # Parse JSON from MCP response
    # Apply heuristics
    # Return optimal UI component
```

**Mapping Rules:**
1. List with `items`/`results` array → `ListComponent` of cards
2. Single large object (≥5 fields) → `CardComponent` with metadata
3. Single small object (<5 fields) → `CardComponent` with key-values
4. Array of primitives → `BannerComponent`
5. String → `BannerComponent`

**Field Processing:**
- HTML stripping: `<p>text</p>` → `text`, `&#x27;` → `'`
- Text truncation: 200 char max
- Field filtering: Hide IDs, timestamps, booleans
- URL detection: Convert to clickable links
- Icon inference: 📦 repo, 🔍 search, 📄 file, 👤 user

**Example:**
```json
{"items": [{
  "name": "react",
  "description": "A JavaScript library",
  "html_url": "https://github.com/facebook/react",
  "stargazers_count": 220000,
  "id": 12345,          // filtered
  "created_at": "...",  // filtered
  "private": false      // filtered
}]}
```

**Result:** Card with title "react", description, stars count, clickable link, 📦 icon.

**Benefits:**
- O(1) scaling: New tools work automatically
- Zero maintenance per tool
- Consistent visual language

### 6. Terminal UI (`src/ui/app.py`)

```python
class WisprActionsApp:
    async def on_mount()
        # Initialize MCP gateway
        # Connect servers
        # Initialize intent parser

    def action_hold_to_speak()
        # Start recording on V press

    async def process_audio()
        # 1. Transcribe (Whisper)
        # 2. Parse intent (GPT-4)
        # 3. Execute via MCP
        # 4. Bind data → UI
        # 5. Display result
```

**Features:**
- Real-time waveform during recording
- MCP server status badges
- Always show transcript (even on failure)
- Syntax highlighting for parsed commands

---

## Key Decisions

### Why MCP Gateway?

**Alternative:** Direct SDK integration (Slack API, Gmail API, etc.)

**Chosen:** MCP gateway with dynamic tool discovery

**Rationale:**
- Adding services = config change only (O(1))
- Leverage community MCP servers
- Zero maintenance (providers maintain servers)
- System grows more powerful as ecosystem grows

### Why Auto Data Binder?

**Alternative:** Custom UI bindings per tool

**Chosen:** Heuristic-based automatic mapping

**Rationale:**
- O(1) scaling: Works with any tool automatically
- Consistent UX across all tools
- Zero code per new tool

**Trade-off:** Generic vs optimized UIs. Generic is good enough for 80% of cases.

### Why GPT-4 Function Calling?

**Rationale:**
- No training data needed
- Handles ambiguity naturally
- Works with dynamic tool catalogs
- Same provider as Whisper (simpler)

**Trade-off:** Latency (~1-2s). Could use GPT-4o-mini for 3x speedup.

### Why Terminal UI?

**Rationale:**
- Focus on architecture, not frontend
- Faster development
- Backend-agnostic (same gateway works with any frontend)

---

## Scalability

### Adding a Service

**Traditional approach:**
```python
if service == "slack": slack_client.send(...)
elif service == "gmail": gmail_client.send(...)
# O(N) code changes
```

**With MCP:**
```json
{"name": "notion", "command": "npx", "args": [...]}
```
**O(1) config change, zero code.**

### Tool Routing

Current: 14 tools from 3 servers
Routing: O(1) dictionary lookup
GPT-4 limit: 100+ tools supported

---

## Performance

| Stage | Current | Optimized |
|-------|---------|-----------|
| Whisper API | ~2-3s | ~0.5s (local) |
| GPT-4 intent | ~1-2s | ~0.3s (4o-mini) |
| MCP execute | ~0.5s | ~0.5s |
| **Total** | **4-6s** | **1.3s** |

**Optimization path:**
1. Local Whisper (faster-whisper)
2. GPT-4o-mini
3. Intent caching
4. Tool filtering

---

## Summary

**Architecture prioritizes:**
1. **Scalability:** O(1) integration via MCP + auto data binder
2. **Intelligence:** GPT-4 function calling for natural language → actions
3. **Simplicity:** Single provider (OpenAI), minimal components
4. **Modularity:** Clean separation of concerns

Demonstrates modern AI tooling, protocol-based integrations, and practical system design.
