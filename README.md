# Wispr Actions

Voice-controlled gateway for productivity apps using the Model Context Protocol (MCP).

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   python main.py
   ```

3. **First time setup:**
   - You'll be prompted for your OpenAI API key
   - Optionally connect services (Gmail, etc.)
   - Configuration is saved to `.env`

## Controls

- **Space** - Start/stop voice recording
- **S** - Settings
- **Q** - Quit

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed technical architecture.

## Project Structure

```
wispr-actions/
├── main.py              # Entry point with onboarding
├── src/
│   ├── ui/              # Textual UI components
│   ├── voice/           # Audio capture & Whisper
│   ├── gateway/         # MCP gateway core
│   ├── integrations/    # MCP servers (Gmail, iMessage, etc.)
│   └── utils/           # Config, helpers
├── tests/
├── docs/
└── requirements.txt
```

## Development

Built for the Wispr full-stack engineering challenge. Demonstrates:
- Scalable MCP gateway pattern (O(1) integration effort)
- GPT-4 function calling for intent understanding
- Rich terminal UI with Textual
- Voice-to-action pipeline (Whisper → GPT-4 → MCP → Action)
