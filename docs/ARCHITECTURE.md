# Architecture - Wispr Actions

## System Overview

Wispr Actions is a voice-controlled gateway that connects users to multiple productivity applications through natural language. The system uses the Model Context Protocol (MCP) as an abstraction layer, allowing a single intelligent gateway to work with any service.

## High-Level Data Flow

```
Voice Input
    ↓
[Audio Capture (PyAudio)]
    ↓
[OpenAI Whisper API] → Text Transcript
    ↓
[GPT-4 + MCP Tool Catalog] → Intent + Structured Parameters
    ↓
[MCP Gateway] → Routes to correct server
    ↓
[MCP Server (Slack/Gmail/etc.)] → Executes action
    ↓
[Terminal UI] → Shows result to user
```

## Component Architecture

### 1. Terminal UI Layer (Textual)

**Responsibility:** User interaction and visual feedback

**Key Components:**
- `WaveformWidget` - Real-time audio level visualization
- `TranscriptWidget` - Shows speech-to-text output with syntax highlighting
- `PreviewWidget` - Command preview/confirmation before execution
- `StatusWidget` - Service connection status and recent history
- `SetupScreen` - First-time auth/configuration flow

**Technologies:** Textual (Python TUI framework), Rich (formatting)

---

### 2. Voice Processing Pipeline

**Responsibility:** Convert audio to text

**Flow:**
1. **Audio Capture** (`voice/capture.py`)
   - PyAudio for microphone access
   - Configurable device selection
   - Real-time buffer management
   - Audio level monitoring for visualization

2. **Transcription** (`voice/transcribe.py`)
   - OpenAI Whisper API integration
   - Audio format conversion (WAV/MP3)
   - Error handling and retry logic
   - Optional: Local whisper-cpp fallback

**Technologies:** PyAudio, OpenAI Whisper API

---

### 3. Intent Understanding (GPT-4 Integration)

**Responsibility:** Parse natural language into structured tool calls

**How it works:**
```python
# Simplified example
tools = mcp_gateway.get_all_tools()  # Get tool catalog from all MCP servers

response = openai.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{
        "role": "user",
        "content": "Send an email to josh@wispr.ai saying the demo is ready"
    }],
    tools=tools  # GPT-4 sees all available tools
)

# GPT-4 returns:
# {
#   "tool_calls": [{
#     "function": {
#       "name": "send_email",
#       "arguments": {
#         "to": "josh@wispr.ai",
#         "subject": "Demo Update",
#         "body": "The demo is ready"
#       }
#     }
#   }]
# }
```

**Key Features:**
- Native function calling (no regex/keyword matching)
- Handles ambiguity and natural language variations
- Multi-turn conversation support

**Technologies:** OpenAI SDK, GPT-4 Turbo

---

### 4. MCP Gateway Core

**Responsibility:** Manage connections to multiple MCP servers and route tool calls

#### 4.1 MCPServerManager (`gateway/server_manager.py`)

**Manages multiple MCP server connections:**

```python
class MCPServerManager:
    def __init__(self):
        self.servers = {}  # server_name → MCPClient
        self.tool_registry = {}  # tool_name → server_name

    async def connect_server(self, name: str, config: dict):
        """Connect to an MCP server and discover its tools"""
        client = MCPClient(config)
        await client.connect()
        tools = await client.list_tools()

        # Register tools in global catalog
        for tool in tools:
            self.tool_registry[tool.name] = name

        self.servers[name] = client

    def get_all_tools(self) -> list[dict]:
        """Return unified tool catalog for Claude"""
        all_tools = []
        for server in self.servers.values():
            all_tools.extend(server.tools)
        return all_tools

    async def execute_tool(self, tool_name: str, arguments: dict):
        """Route tool call to correct server"""
        server_name = self.tool_registry[tool_name]
        server = self.servers[server_name]
        return await server.call_tool(tool_name, arguments)
```

**Key Features:**
- Concurrent server connections
- Health checking and reconnection
- Graceful degradation (one failure doesn't break others)
- Tool catalog caching
- Intelligent routing based on tool name

#### 4.2 MCPClient (`gateway/mcp_client.py`)

**Per-server MCP protocol implementation:**

```python
class MCPClient:
    def __init__(self, config: dict):
        self.server_process = None
        self.read_stream = None
        self.write_stream = None
        self.tools = []

    async def connect(self):
        """Start MCP server subprocess and establish stdio connection"""
        self.server_process = await self._start_server()
        self.read_stream, self.write_stream = get_stdio_streams(self.server_process)
        await self._initialize_connection()
        self.tools = await self.list_tools()

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool on this MCP server"""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        })
        return response
```

**Technologies:** MCP SDK, asyncio

---

### 5. Integration Layer

**Responsibility:** MCP server implementations for each service

Each integration is a separate MCP server that can run as a subprocess:

**Example: Slack MCP Server** (`integrations/slack/mcp_server.py`)
```python
from mcp import McpServer

slack_server = McpServer("slack")

@slack_server.tool("send_message")
def send_message(channel: str, text: str) -> dict:
    """Send a message to a Slack channel"""
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    result = client.chat_postMessage(channel=channel, text=text)
    return {"success": True, "ts": result["ts"]}

@slack_server.tool("list_channels")
def list_channels() -> list[dict]:
    """List all Slack channels"""
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    result = client.conversations_list()
    return result["channels"]
```

**Benefits:**
- Each service is isolated
- Can be developed/tested independently
- Easy to add new services (just config, no gateway changes)
- Community can contribute servers

---

## Key Architectural Decisions

### Why MCP?

**Alternative:** Direct SDK integration for each service
**Chosen:** MCP gateway pattern

**Rationale:**
- **Scalability:** Adding new services requires only configuration
- **Ecosystem leverage:** Benefit from community-built MCP servers
- **Separation of concerns:** Gateway logic separate from service-specific code
- **Future-proof:** As MCP ecosystem grows, system gets more powerful

### Why GPT-4?

**Alternative:** Claude, local models, custom NLU
**Chosen:** GPT-4 Turbo with function calling

**Rationale:**
- **Single provider:** Same provider as Whisper (one API key, simpler billing)
- **Function calling:** Excellent structured output via native tool use
- **Proven reliability:** Mature function calling implementation
- **Simplicity:** Reduces integration complexity for demo

### Why Terminal UI?

**Alternative:** Web app, native app, browser extension
**Chosen:** Rich terminal UI (Textual)

**Rationale:**
- **Focus:** Demonstrates architecture, not React skills
- **Speed:** Faster to build than GUI
- **Sufficiency:** Same backend can power any frontend later

### Why Whisper API?

**Alternative:** Local Whisper, other STT services
**Chosen:** OpenAI Whisper API

**Rationale:**
- **Quality:** State-of-the-art accuracy
- **Speed:** Faster than local inference
- **Simplicity:** No model management
- **Cost:** Acceptable for demo ($0.006/min)

---

## Scalability Considerations

### Adding a New Service

**Current approach (without MCP):**
```python
# Need to modify gateway code for each service
if intent.service == "slack":
    slack_client.send(...)
elif intent.service == "gmail":
    gmail_client.send(...)
elif intent.service == "calendar":
    calendar_client.send(...)
# O(N) code changes
```

**With MCP:**
```yaml
# Just add to config.yaml
servers:
  - name: notion
    command: python
    args: [integrations/notion/mcp_server.py]
    env:
      NOTION_API_KEY: ${NOTION_API_KEY}
```

**Result:** O(1) integration effort

### Tool Catalog Size

With 10 services × 5 tools each = 50 tools in catalog. GPT-4 Turbo supports 100+ tools reliably; tool descriptions guide selection.

---

## Performance Targets

| Component | Target | Estimated |
|-----------|--------|-----------|
| Voice → Text | < 3s | ~2s |
| Text → Intent | < 2s | ~1s |
| Intent → Action | < 1s | ~500ms |
| **Total** | **< 6s** | **~3.5s** |

Acceptable for non-real-time actions (emails, messages, etc.).

---

## Summary

The architecture prioritizes **scalability** (MCP gateway pattern), **intelligence** (GPT-4 function calling), **simplicity** (single provider), and **modularity** (isolated MCP servers). This demonstrates understanding of modern AI tooling while staying focused on practical implementation.
