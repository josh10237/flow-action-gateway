"""
Main Textual application for Wispr Actions
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from rich.text import Text
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from voice.capture import AudioCapture
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False
    AudioCapture = None

try:
    from voice.transcription import Transcriber
    from gateway.intent_parser import IntentParser
    from gateway.mcp_gateway import MCPGateway
    from gateway.mcp_config import MCPConfig
except ImportError:
    Transcriber = None
    IntentParser = None
    MCPGateway = None
    MCPConfig = None

try:
    from ui.settings_screen import SettingsScreen
except ImportError:
    SettingsScreen = None


class MicrophoneDisplay(Static):
    """ASCII art microphone with voice waveform."""

    def __init__(self, audio_capture=None):
        super().__init__()
        self.is_recording = False
        self.audio_capture = audio_capture
        self.transcript = None  # Store transcript for display
        self.parsed_command = None  # Store parsed command for display
        self.execution_result = None  # Store MCP execution result
        self.mcp_servers = []  # List of MCP server configs
        self.connected_servers = set()  # Set of connected server names

    def set_mcp_status(self, servers_config, connected_sessions):
        """Update MCP server status."""
        self.mcp_servers = servers_config
        self.connected_servers = set(connected_sessions.keys())
        self.refresh()

    def show_result(self, transcript: str, parsed_command: dict = None, execution_result: dict = None):
        """Show transcription, parsed command, and execution result."""
        self.transcript = transcript
        self.parsed_command = parsed_command
        self.execution_result = execution_result
        self.refresh()

    def clear_result(self):
        """Clear the result display."""
        self.transcript = None
        self.parsed_command = None
        self.execution_result = None
        self.refresh()

    def render(self) -> Text:
        # Get volume level for waveform bars
        volume = 0
        if self.is_recording and self.audio_capture:
            volume = self.audio_capture.get_volume_level()

        # Build the microphone pill shape with waveform
        lines = []

        # Add MCP status badges at the top
        if self.mcp_servers:
            for server in self.mcp_servers:
                icon = server.get("icon", "•")
                display_name = server.get("display_name", server["name"])
                is_connected = server["name"] in self.connected_servers

                # Format: "📁 Files ✓" or "🐙 GitHub ✗"
                status_icon = "✓" if is_connected else "✗"
                mcp_line = f"             {icon} {display_name} {status_icon}"
                lines.append(mcp_line)

        lines.append("")

        if self.is_recording:
            # Generate waveform bars (10 bars, varying heights)
            num_bars = 10
            max_height = 8
            bars = []

            # Create bars based on volume with some variation
            import random
            base_height = int((volume / 100) * max_height)
            for i in range(num_bars):
                # Add variation to make it look more natural
                variation = random.randint(-1, 1)
                bar_height = max(1, min(max_height, base_height + variation))
                bars.append(bar_height)

            # Render waveform (top to bottom, line by line)
            for row in range(max_height, 0, -1):
                line = "                    "
                for bar_height in bars:
                    if bar_height >= row:
                        line += "█ "
                    else:
                        line += "  "
                lines.append(line)

        else:
            # Empty space when not recording
            for _ in range(8):
                lines.append("")

        # Microphone pill body
        lines.append("           ╭────────────────────────────╮")
        lines.append("          ╱                              ╲")
        lines.append("         │                                │")
        lines.append("         │                                │")
        lines.append("         │          ████████              │")
        lines.append("         │          ████████              │")
        lines.append("         │                                │")
        lines.append("         │                                │")
        lines.append("          ╲                              ╱")
        lines.append("           ╰────────────────────────────╯")
        lines.append("")
        lines.append("                    ││││")
        lines.append("                ════════════")
        lines.append("")
        lines.append("")

        if self.is_recording:
            lines.append("                 recording")
        else:
            lines.append("             hold v to record")

        # Convert to Text object for rich formatting
        text = Text("\n".join(lines))

        # Add transcript and result display below microphone
        if self.transcript:
            text.append("\n\n")
            text.append("╭────────────────────────────────────────────────────────────╮\n")
            text.append("│ ", style="dim")
            text.append(self.transcript, style="italic white")
            text.append("\n")

            # If we have a parsed command, show it
            if self.parsed_command:
                text.append("│\n")
                text.append("│ ")

                function_name = self.parsed_command["function"]
                arguments = self.parsed_command["arguments"]

                text.append(function_name, style="bold blue")

                for key, value in arguments.items():
                    text.append(" ")
                    text.append(key, style="red")
                    text.append(" ")

                    if isinstance(value, list):
                        formatted_value = ", ".join(str(v) for v in value)
                        text.append(f'"{formatted_value}"', style="white")
                    elif isinstance(value, str):
                        text.append(f'"{value}"', style="white")
                    else:
                        text.append(str(value), style="white")

                text.append("\n")

                # Show execution result if available
                if self.execution_result:
                    text.append("│\n")
                    if self.execution_result.get("success"):
                        text.append("│ ✓ ", style="green")
                        # Show the data/content from MCP
                        data = self.execution_result.get("data", "")
                        if isinstance(data, list):
                            # MCP returns content as a list of content blocks
                            for item in data[:3]:  # Show first 3 items
                                if hasattr(item, 'text'):
                                    text.append(str(item.text)[:100], style="white")  # Truncate long output
                                    text.append("...\n│   ", style="dim")
                                else:
                                    text.append(str(item)[:100], style="white")
                                    text.append("...\n│   ", style="dim")
                        else:
                            text.append(str(data)[:200], style="white")  # Show first 200 chars
                        text.append("\n")
                    else:
                        text.append("│ ✗ ", style="red")
                        text.append(self.execution_result.get("message", "Unknown error"), style="red")
                        text.append("\n")
            else:
                # No command parsed
                text.append("│ ", style="dim")
                text.append("(no command found)", style="dim yellow")
                text.append("\n")

            text.append("╰────────────────────────────────────────────────────────────╯")

        return text

    def start_recording(self):
        """Start the recording animation."""
        self.is_recording = True
        if self.audio_capture:
            self.audio_capture.start_recording()
        self.animate()

    def stop_recording(self):
        """Stop the recording animation."""
        self.is_recording = False
        if self.audio_capture:
            self.audio_capture.stop_recording()
        self.refresh()

    def animate(self):
        """Update microphone display based on mic input."""
        if self.is_recording:
            self.refresh()
            self.set_timer(0.05, self.animate)  # Update 20x per second


class WisprActionsApp(App):
    """Main application for Wispr Actions."""

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
        color: $text;
    }

    MicrophoneDisplay {
        width: 100%;
        height: 100%;
        content-align: center middle;
        text-align: center;
    }

    MicrophoneDisplay.recording {
        color: $success;
    }
    """

    BINDINGS = [
        Binding("v", "hold_to_speak", "Hold to Speak", show=True, key_display="V"),
        Binding("s", "settings", "Settings", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.title = "Wispr Actions"
        self.sub_title = ""
        self.v_key_held = False
        self.release_timer = None
        self.mcp_servers_config = []  # Store MCP server configs for display

        # Initialize audio capture if available
        self.audio_capture = None
        if MIC_AVAILABLE and AudioCapture:
            try:
                self.audio_capture = AudioCapture()
            except Exception:
                # Mic initialization failed - audio_capture stays None
                self.audio_capture = None

        # Initialize transcription and intent parsing
        self.transcriber = None
        self.intent_parser = None
        self.mcp_gateway = None

        if Transcriber and IntentParser and config.get("openai_api_key"):
            try:
                self.transcriber = Transcriber(config["openai_api_key"])
                # MCP gateway will be initialized async in on_mount
                # Intent parser will get tools after gateway connects
            except Exception:
                # API initialization failed
                pass

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield MicrophoneDisplay(audio_capture=self.audio_capture)
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize MCP gateway when app starts."""
        if MCPGateway and MCPConfig:
            try:
                # Initialize MCP gateway
                mcp_config = MCPConfig()
                self.mcp_servers_config = mcp_config.get_server_configs()
                self.mcp_gateway = MCPGateway(mcp_config)

                # Connect to all MCP servers
                await self.mcp_gateway.connect_all()

                # Initialize intent parser with tools from MCP servers
                tools = self.mcp_gateway.get_gpt4_tools()
                self.intent_parser = IntentParser(self.config["openai_api_key"], tools)

                # Update microphone display with MCP status
                mic = self.query_one(MicrophoneDisplay)
                mic.set_mcp_status(self.mcp_servers_config, self.mcp_gateway.sessions)

                self.notify(f"Connected to {len(self.mcp_gateway.sessions)} MCP servers")
            except Exception as e:
                self.notify(f"MCP initialization failed: {str(e)}")

    def action_hold_to_speak(self) -> None:
        """Start recording when V is pressed."""
        mic = self.query_one(MicrophoneDisplay)

        # Start recording if not already
        if not mic.is_recording:
            mic.add_class("recording")
            mic.start_recording()
            self.v_key_held = True

        # Reset release timer - user is still holding
        if self.release_timer:
            self.release_timer.stop()

        # Set a timer to detect release (if key isn't pressed again soon)
        self.release_timer = self.set_timer(0.2, self.check_release)

    def check_release(self) -> None:
        """Check if V key was released (timer expired without re-press)."""
        mic = self.query_one(MicrophoneDisplay)

        if mic.is_recording:
            # Key was released - stop recording
            mic.remove_class("recording")
            mic.stop_recording()
            self.v_key_held = False

            # Process the audio (non-blocking)
            self.run_worker(self.process_audio())

    async def on_unmount(self) -> None:
        """Clean up when app closes."""
        # Clean up audio resources directly
        if self.audio_capture:
            self.audio_capture.cleanup()

        # Close MCP gateway connections
        if self.mcp_gateway:
            await self.mcp_gateway.close_all()

    def action_settings(self) -> None:
        """Open settings screen."""
        if not SettingsScreen:
            self.notify("Settings screen not available")
            return

        # Create save callback
        def on_save(updated_servers):
            # Save to config file
            if self.mcp_gateway and self.mcp_gateway.mcp_config:
                self.mcp_gateway.mcp_config.save_config(updated_servers)

        # Get current connection status
        connected_servers = self.mcp_gateway.sessions if self.mcp_gateway else {}

        # Get original configs (with env templates intact)
        original_configs = self.mcp_gateway.mcp_config.get_original_server_configs() if self.mcp_gateway and self.mcp_gateway.mcp_config else self.mcp_servers_config

        # Define callback to refresh MCP status when returning from settings
        def on_settings_close():
            # Update microphone display with current MCP status
            mic = self.query_one(MicrophoneDisplay)
            mic.set_mcp_status(self.mcp_servers_config, self.mcp_gateway.sessions if self.mcp_gateway else {})

        # Push settings screen
        self.push_screen(
            SettingsScreen(
                self.mcp_servers_config,
                connected_servers,
                on_save,
                self.mcp_gateway,  # Pass gateway for test connections
                original_configs  # Pass original configs for display
            ),
            callback=lambda _: on_settings_close()
        )

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    async def process_audio(self) -> None:
        """Process recorded audio through Whisper + GPT-4."""
        if not self.audio_capture:
            self.notify("Audio capture not available")
            return

        if not self.transcriber or not self.intent_parser:
            self.notify("OpenAI API not configured")
            return

        transcript = None
        parsed = None
        result = None
        mic = self.query_one(MicrophoneDisplay)

        try:
            # Get the recorded audio data
            audio_data = self.audio_capture.get_audio_data()

            if not audio_data:
                self.notify("No audio recorded")
                return

            # Step 1: Transcribe with Whisper
            self.notify("Transcribing...")

            # Run blocking I/O in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                self.transcriber.transcribe,
                audio_data,
                16000  # Sample rate from AudioCapture
            )

            if not transcript:
                self.notify("No speech detected")
                # Show empty transcript so user knows it tried
                mic.show_result("(no speech detected)", None, None)
                return

            # Step 2: Parse intent with GPT-4
            self.notify("Understanding command...")
            parsed = await loop.run_in_executor(
                None,
                self.intent_parser.parse,
                transcript
            )

            # Step 3: Execute the command via MCP if we have one
            if parsed:
                # Execute the tool via MCP gateway
                if self.mcp_gateway:
                    self.notify("Executing...")
                    result = await self.mcp_gateway.execute_tool(
                        parsed["function"],
                        parsed["arguments"]
                    )

                    # Show execution result in notification
                    if result["success"]:
                        self.notify(f"✓ {result['message']}")
                    else:
                        self.notify(f"✗ {result['message']}")
                else:
                    self.notify("Command recognized (MCP not connected)")
            else:
                self.notify(f"No command found in: {transcript}")

        except Exception as e:
            self.notify(f"Error: {str(e)}")
        finally:
            # ALWAYS show the transcript, even if parsing/execution failed
            if transcript:
                mic.show_result(transcript, parsed, result)
