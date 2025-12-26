# Architecture - Wispr Actions

## System Overview

Wispr Actions is a voice-controlled gateway that connects users to multiple productivity applications through natural language. The system uses the Model Context Protocol (MCP) as an abstraction layer, allowing a single intelligent gateway to work with any service that provides an MCP server.

## High-Level Data Flow

```
Voice Input (hold V key)
    ↓
[AudioCapture] → PyAudio streams mic input, calculates volume for waveform
    ↓
[Transcriber] → OpenAI Whisper API converts audio to text
    ↓
[IntentParser] → GPT-4 + MCP tool catalog → Structured function call
    ↓
[MCPGateway] → Routes to correct MCP server based on tool name
    ↓
[MCP Server] → Executes action (filesystem, GitHub, etc.)
    ↓
[WisprActionsApp] → Displays result in terminal UI
```

**Total latency: ~4-6 seconds**
- Whisper API: ~2-3s
- GPT-4 function calling: ~1-2s
- MCP execution: ~0.5-1s

---

## Component Architecture

### 1. Audio Capture Layer

**File:** [src/voice/capture.py](../src/voice/capture.py)

**Responsibility:** Capture audio from microphone and provide volume monitoring

**Implementation:**
```python
class AudioCapture:
    def start_recording(self):
        # Opens PyAudio stream in blocking mode
        # No callback threads - simpler integration with Textual

    def get_volume_level(self) -> int:
        # Reads one chunk, calculates RMS volume
        # Returns 0-100 for waveform visualization
        # Stores chunks for later transcription

    def get_audio_data(self) -> bytes:
        # Returns all buffered audio as raw bytes
        # Used after recording stops
```

**Key decisions:**
- Blocking mode instead of callback threads (simpler with Textual's async model)
- 16kHz sample rate (optimal for Whisper)
- Volume calculation happens during recording (for live waveform)
- Audio buffered in queue for later retrieval

---

### 2. Transcription Layer

**File:** [src/voice/transcription.py](../src/voice/transcription.py)

**Responsibility:** Convert audio bytes to text using OpenAI Whisper

**Implementation:**
```python
class Transcriber:
    def transcribe(self, audio_data: bytes, sample_rate: int) -> str:
        # Convert raw PCM to WAV format
        # Call Whisper API with prompt hint
        # Filter hallucinations ("you", "thank you", etc.)
        # Return cleaned text or empty string
```

**Key features:**
- WAV format conversion (Whisper API requirement)
- Prompt hint: "File system commands, write file, read file, create directory"
- Hallucination filtering: Removes common false positives from silence
- Empty transcript handling: Returns "" if too short or noise

**Why Whisper API vs local:**
- API is faster than CPU inference
- No model management
- Good enough latency for demo
- Could switch to faster-whisper for production

---

### 3. Intent Understanding Layer

**File:** [src/gateway/intent_parser.py](../src/gateway/intent_parser.py)

**Responsibility:** Parse natural language into structured MCP tool calls

**How it works:**
```python
class IntentParser:
    def __init__(self, api_key: str, tools: List[Dict]):
        # tools = MCP tool catalog from all connected servers

    def parse(self, transcript: str) -> Optional[Dict]:
        # Call GPT-4 with function calling
        # System prompt includes:
        #   - User's working directory (/Users/joshbenson)
        #   - Path resolution examples
        #   - Common folder shortcuts
        # Returns: {"function": "tool_name", "arguments": {...}}
```

**Example flow:**
```
User says: "list files on desktop"
    ↓
GPT-4 receives:
  - Transcript: "list files on desktop"
  - Tools: [list_directory, read_text_file, write_file, ...]
  - System prompt: "When user says 'desktop', use /Users/joshbenson/Desktop"
    ↓
GPT-4 returns:
  {
    "function": "list_directory",
    "arguments": {"path": "/Users/joshbenson/Desktop"}
  }
```

**System prompt engineering:**
- Explicit working directory context
- Examples of path resolution
- "Be flexible with phrasing" to reduce false negatives
- "If unsure, pick closest match" to prefer action over silence

**Why GPT-4-turbo:**
- Same provider as Whisper (single API key)
- Excellent function calling reliability
- Handles ambiguity well
- Could switch to GPT-4o-mini for 3x speed boost

---

### 4. MCP Gateway Core

**File:** [src/gateway/mcp_gateway.py](../src/gateway/mcp_gateway.py)

**Responsibility:** Connect to multiple MCP servers, aggregate tools, route execution

#### Connection Management

**Pattern: Background tasks with async context managers**

```python
class MCPGateway:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.stdio_tasks: Dict[str, asyncio.Task] = {}  # Keep connections alive
        self.tools_cache: Dict[str, List] = {}
        self.tool_to_server: Dict[str, str] = {}  # Routing table

    async def connect_server(self, server_config: Dict):
        # Create stdio server parameters
        # Start background task to maintain connection
        # Wait for connection ready signal (with timeout)

    async def _maintain_connection(self, name: str, params):
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                # List tools from this server
                # Cache tools and build routing table
                # Signal connection ready
                # Keep alive indefinitely (while True: await sleep(1))
```

**Why this pattern:**
- MCP servers are stdio subprocesses - need to stay alive
- Async context managers ensure proper cleanup
- Background tasks don't block main UI thread
- Event-based synchronization for startup

#### Tool Catalog Aggregation

```python
def get_gpt4_tools(self) -> List[Dict]:
    """Build unified tool catalog for GPT-4 function calling"""
    gpt4_tools = []
    for server_name, tools in self.tools_cache.items():
        for tool in tools:
            gpt4_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
    return gpt4_tools
```

**Key insight:** GPT-4 sees all tools from all servers as a single catalog. Gateway handles routing transparently.

#### Tool Execution Routing

```python
async def execute_tool(self, tool_name: str, arguments: Dict):
    # Look up which server owns this tool
    server_name = self.tool_to_server[tool_name]

    # Get the session for that server
    session = self.sessions[server_name]

    # Execute via MCP protocol
    result = await session.call_tool(tool_name, arguments)

    return {
        "success": True,
        "message": f"Executed {tool_name}",
        "data": result.content
    }
```

**Routing is O(1) dictionary lookup** - doesn't matter how many servers we have.

---

### 5. Configuration Layer

**File:** [src/gateway/mcp_config.py](../src/gateway/mcp_config.py)

**Responsibility:** Load MCP server configurations and expand environment variables

**Implementation:**
```python
class MCPConfig:
    def load_config(self):
        # Read mcp_config.json
        # Expand ${ENV_VAR} syntax in env fields
        # Store all servers (both enabled and disabled)

    def get_enabled_server_configs(self) -> List[Dict]:
        # Filter servers where enabled=true
        # Used for connections

    def get_server_configs(self) -> List[Dict]:
        # Return all servers
        # Used for UI display (show disabled servers with ✗)
```

**Config format:**
```json
{
  "servers": [
    {
      "name": "filesystem",
      "display_name": "Files",
      "icon": "📁",
      "enabled": true,
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/joshbenson"],
      "env": {}
    }
  ]
}
```

**Adding a new service = editing this JSON only.** No code changes needed.

---

### 6. Terminal UI Layer

**File:** [src/ui/app.py](../src/ui/app.py)

**Responsibility:** Orchestrate voice → action pipeline and provide visual feedback

#### Main Application

```python
class WisprActionsApp(App):
    async def on_mount(self):
        # Initialize MCP gateway
        # Connect to all enabled servers
        # Initialize intent parser with tool catalog
        # Update UI with MCP status

    def action_hold_to_speak(self):
        # Triggered when V key pressed
        # Start recording
        # Set timer to detect release (0.2s debounce)

    def check_release(self):
        # Called when timer expires (key released)
        # Stop recording
        # Launch background worker to process audio

    async def process_audio(self):
        # Step 1: Transcribe (Whisper API)
        # Step 2: Parse intent (GPT-4)
        # Step 3: Execute via MCP
        # Step 4: Update display (always show transcript)
```

#### Microphone Display Widget

```python
class MicrophoneDisplay(Static):
    def render(self) -> Text:
        # Show MCP status badges at top
        #   "📁 Files ✓"  if connected
        #   "🐙 GitHub ✗" if disabled

        # Show waveform bars if recording
        #   Uses volume levels from AudioCapture

        # Show microphone ASCII art

        # Show "hold v to record" or "recording"

        # Show transcript with parsed command:
        #   Transcript text (italic)
        #   function_name (bold blue) arg1 "value" arg2 "value"
        #   Execution result (✓ success / ✗ error)
```

**Key features:**
- Real-time waveform visualization during recording
- MCP server status display (connected/disconnected)
- Always show transcript (even on failure)
- Syntax highlighting for parsed commands
- Execution result feedback

---

## Key Architectural Decisions

### 1. Why MCP Gateway Pattern?

**Alternative:** Direct SDK integration (SlackAPI, Gmail API, etc.)

**Chosen:** MCP gateway with dynamic tool discovery

**Rationale:**
- **Scalability:** Adding services is O(1) config, not O(N) code
- **Ecosystem leverage:** Benefit from community MCP servers
- **Separation of concerns:** Service logic separate from gateway
- **Future-proof:** System gets more powerful as MCP ecosystem grows
- **Zero maintenance:** Service providers maintain their own servers

**Trade-off:** Requires MCP servers to exist. Currently limited ecosystem, but growing fast.

### 2. Why GPT-4 Function Calling?

**Alternative:** Rule-based NLU, local models, regex matching

**Chosen:** GPT-4-turbo with native function calling

**Rationale:**
- **No training data needed:** Works out of the box with tool descriptions
- **Handles ambiguity:** "list files" vs "show files" vs "what's in the folder"
- **Single provider:** Same as Whisper (one API key, simpler billing)
- **Proven reliability:** Mature function calling implementation
- **Dynamic tool catalog:** Works with any number of tools

**Trade-off:** Latency (~1-2s) and cost ($0.01/request). Could use GPT-4o-mini for 3x faster + cheaper.

### 3. Why Terminal UI?

**Alternative:** Web app (React), native app (Electron/Swift), browser extension

**Chosen:** Textual (Python TUI framework)

**Rationale:**
- **Focus on architecture:** Demonstrates MCP gateway, not React skills
- **Faster development:** No frontend build process
- **Backend-agnostic:** Same gateway can power any frontend later
- **Sufficient for demo:** Shows all functionality clearly

**Trade-off:** Not production-ready UX. Fine for interview demo.

### 4. Why Whisper API?

**Alternative:** Local Whisper (faster-whisper), Soniox streaming, DeepGram

**Chosen:** OpenAI Whisper API (for now)

**Rationale:**
- **Quality:** State-of-the-art accuracy
- **Simplicity:** No model management, works immediately
- **Single provider:** Same as GPT-4
- **Good enough:** ~2s latency acceptable for demo

**Trade-off:** Latency and cost. Should switch to faster-whisper (local) for production.

---

## Scalability Analysis

### Adding a New Service

**Without MCP (traditional approach):**
```python
# Need to modify gateway code
if service == "slack":
    slack_client.send_message(...)
elif service == "gmail":
    gmail_client.send_email(...)
elif service == "notion":
    notion_client.create_page(...)
# O(N) code changes, O(N) maintenance
```

**With MCP (this implementation):**
```json
// Just edit mcp_config.json
{
  "name": "notion",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-notion"],
  "env": {"NOTION_API_KEY": "${NOTION_API_KEY}"}
}
```

**Result:** O(1) integration effort, zero code changes.

### Tool Catalog Size

Current: 14 filesystem tools from 1 server
Projected: 10 servers × 5 tools = 50 tools
GPT-4 limit: 100+ tools reliably supported

**Routing complexity:** O(1) dictionary lookup regardless of server count

---

## Performance Profile

| Stage | Current | Optimized |
|-------|---------|-----------|
| Audio capture | Instant | Instant |
| Whisper API | ~2-3s | ~0.5s (local) |
| GPT-4 intent | ~1-2s | ~0.3s (4o-mini) |
| MCP execute | ~0.5s | ~0.5s |
| **Total** | **4-6s** | **1.3s** |

**Optimization path:**
1. Switch to faster-whisper (local inference)
2. Switch to GPT-4o-mini (3x faster, 10x cheaper)
3. Parallel execution where possible

---

## Code Statistics

**Total lines of Python:** ~1,086 lines
**Core gateway logic:** 172 lines (mcp_gateway.py)
**UI orchestration:** 448 lines (app.py)
**Voice processing:** 160 lines (capture.py + transcription.py)
**Intent parsing:** 120 lines (intent_parser.py)

**Every line serves a purpose.** No dead code after cleanup.

---

## Summary

The architecture prioritizes:
1. **Scalability** via MCP gateway pattern (O(1) integration)
2. **Intelligence** via GPT-4 function calling (natural language → structured actions)
3. **Simplicity** via single provider (OpenAI for both Whisper + GPT-4)
4. **Modularity** via clean separation of concerns

This demonstrates understanding of modern AI tooling, protocol-based integrations, and practical system design for an interview context.
