"""
Main Textual application for Wispr Actions
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from textual.binding import Binding
from textual.reactive import reactive
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

try:
    from ui.data_bindings import route_to_components
    from ui.components.renderer import render_component
except ImportError:
    route_to_components = None
    render_component = None


class MicrophoneDisplay(Static):
    """ASCII art microphone with voice waveform."""

    # Use reactive variables to force re-rendering when they change
    update_counter = reactive(0)

    def __init__(self, audio_capture=None):
        super().__init__()
        self.is_recording = False
        self.audio_capture = audio_capture
        self.transcript = None  # Store transcript for display
        self.parsed_command = None  # Store parsed command for display
        self.execution_result = None  # Store MCP execution result
        self.timings = {}  # Store timing information
        self.mcp_servers = []  # List of MCP server configs
        self.connected_servers = set()  # Set of connected server names

    def set_mcp_status(self, servers_config, connected_sessions):
        """Update MCP server status."""
        self.mcp_servers = servers_config
        self.connected_servers = set(connected_sessions.keys())
        self.refresh()

    def show_result(self, transcript: str, parsed_command: dict = None, execution_result: dict = None, timings: dict = None):
        """Show transcription, parsed command, execution result, and timings."""
        print(f"[DEBUG] show_result called: transcript={bool(transcript)}, parsed={bool(parsed_command)}, result={bool(execution_result)}, timings={timings}")
        self.transcript = transcript
        self.parsed_command = parsed_command
        self.execution_result = execution_result
        self.timings = timings or {}

        # Force re-render by updating reactive variable
        self.update_counter += 1
        print(f"[DEBUG] update_counter incremented to {self.update_counter}")

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

            # ASR line with timing
            text.append("│ ")
            if 'asr' in self.timings:
                asr_ms = int(self.timings['asr'] * 1000)
                text.append(f"ASR {asr_ms}ms: ", style="dim cyan")
            text.append(self.transcript, style="italic white")
            text.append("\n")

            # Intent line with timing
            if self.parsed_command:
                text.append("│\n│ ")

                if 'intent' in self.timings:
                    intent_ms = int(self.timings['intent'] * 1000)
                    text.append(f"Intent {intent_ms}ms: ", style="dim cyan")

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

                # Execution line with timing and response
                if self.execution_result:
                    try:
                        text.append("│\n│ ")

                        if 'execution' in self.timings:
                            exec_ms = int(self.timings['execution'] * 1000)
                            text.append(f"Execution {exec_ms}ms: ", style="dim cyan")

                        if self.execution_result.get("success"):
                            text.append("✓ Success - ", style="green")

                            # Show truncated JSON preview
                            data = self.execution_result.get("data", "")
                            import json
                            try:
                                # Truncate data first to avoid huge serialization
                                if isinstance(data, list):
                                    if len(data) > 1:
                                        data_preview = data[:1]  # Just first item
                                    else:
                                        data_preview = data
                                else:
                                    data_preview = data

                                data_json = json.dumps(data_preview, indent=0, default=str)
                                # Show first 150 chars, remove newlines for inline display
                                preview = data_json[:150].replace('\n', ' ').replace('  ', ' ')
                                text.append(preview, style="dim white")
                                if len(data_json) > 150:
                                    text.append("...", style="dim")
                            except Exception:
                                text.append("(data)", style="dim")

                            text.append("\n")
                        else:
                            text.append("✗ ", style="red")
                            text.append(self.execution_result.get("message", "Unknown error"), style="red")
                            text.append("\n")
                    except Exception as e:
                        text.append("│\n│ ", style="dim")
                        text.append(f"(Display Error: {str(e)[:100]})\n", style="red")
                        import traceback
                        traceback.print_exc()
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

    #result-container {
        width: 100%;
        height: auto;
        padding: 1 2;
    }

    .card {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        background: $panel;
    }

    .card-subtitle {
        color: $text-muted;
        padding: 0 0 1 0;
    }

    .tools-list.enabled {
        color: $accent;
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
        self.current_processing_task = None  # Track current audio processing task

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

        # Check if rendering is available
        self.rendering_available = route_to_components is not None and render_component is not None

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
        # Container for rich result display (mounted dynamically)
        yield Container(id="result-container")
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

            # Cancel any previous processing task
            if self.current_processing_task and not self.current_processing_task.is_finished:
                self.current_processing_task.cancel()
                print("[DEBUG] Cancelled previous processing task")

            # Process the audio (non-blocking)
            self.current_processing_task = self.run_worker(self.process_audio(), exclusive=True)

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

        # Timing tracking
        import time
        timings = {}

        try:
            # Get the recorded audio data
            audio_data = self.audio_capture.get_audio_data()

            if not audio_data:
                self.notify("No audio recorded")
                return

            # Step 1: Transcribe with Whisper
            self.notify("Transcribing...")
            start_time = time.time()

            # Run blocking I/O in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                self.transcriber.transcribe,
                audio_data,
                16000  # Sample rate from AudioCapture
            )

            timings['asr'] = time.time() - start_time

            if not transcript:
                self.notify("No speech detected")
                # Show empty transcript so user knows it tried
                mic.show_result("(no speech detected)", None, None, timings)
                return

            # Show ASR result immediately
            mic.show_result(transcript, None, None, timings)

            # Step 2: Parse intent with GPT-4
            self.notify("Understanding command...")
            start_time = time.time()

            parsed = await loop.run_in_executor(
                None,
                self.intent_parser.parse,
                transcript
            )

            timings['intent'] = time.time() - start_time

            # Show ASR + Intent immediately
            mic.show_result(transcript, parsed, None, timings)

            # Step 3: Execute the command via MCP if we have one
            if parsed:
                # Execute the tool via MCP gateway
                if self.mcp_gateway:
                    self.notify("Executing...")
                    start_time = time.time()

                    result = await self.mcp_gateway.execute_tool(
                        parsed["function"],
                        parsed["arguments"]
                    )

                    timings['execution'] = time.time() - start_time

                    # Show execution result in notification
                    if result["success"]:
                        self.notify(f"✓ {result['message']}")
                    else:
                        self.notify(f"✗ {result['message']}")

                    # Show ALL results immediately after execution
                    mic.show_result(transcript, parsed, result, timings)

                    # Render rich results if available
                    if result.get("success") and self.rendering_available:
                        try:
                            start_time = time.time()
                            await self.render_rich_results(result, parsed)
                            timings['render'] = time.time() - start_time
                            # Update display with render timing
                            mic.show_result(transcript, parsed, result, timings)
                        except Exception as e:
                            # If render fails, just log it and continue
                            print(f"[ERROR] Rich render failed: {str(e)}")
                            import traceback
                            traceback.print_exc()
                else:
                    self.notify("Command recognized (MCP not connected)")
            else:
                self.notify(f"No command found in: {transcript}")

        except Exception as e:
            self.notify(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            # Show error state if we have a transcript
            if transcript:
                mic.show_result(transcript, parsed, None, timings)

    async def render_rich_results(self, result: dict, parsed: dict) -> None:
        """
        Render execution results using the display mapper.

        Args:
            result: MCP execution result
            parsed: Parsed command (for tool name)
        """
        try:
            # Get the result container
            container = self.query_one("#result-container", Container)

            # Clear previous results
            await container.remove_children()

            # Extract data from result
            data = result.get("data", "")
            tool_name = parsed.get("function") if parsed else None

            # Map data to components (instant, no LLM needed)
            component = route_to_components(data, tool_name)

            # Render component to widget
            widget = render_component(component)

            # Mount widget in container
            await container.mount(widget)

        except Exception as e:
            # Fallback to simple error display
            self.notify(f"Error rendering results: {str(e)}")
            import traceback
            traceback.print_exc()
