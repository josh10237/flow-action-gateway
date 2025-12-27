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
    from ui.auto_data_binder import bind_data
    from ui.components.renderer import render_component
except ImportError:
    bind_data = None
    render_component = None


class MicrophoneDisplay(Static):
    """ASCII art microphone with voice waveform."""

    update_counter = reactive(0)

    def __init__(self, audio_capture=None):
        super().__init__()
        self.is_recording = False
        self.audio_capture = audio_capture
        self.transcript = None
        self.parsed_command = None
        self.execution_result = None
        self.timings = {}
        self.mcp_servers = []
        self.connected_servers = set()

    def set_mcp_status(self, servers_config, connected_sessions):
        self.mcp_servers = servers_config
        self.connected_servers = set(connected_sessions.keys())
        self.refresh()

    def show_result(self, transcript: str, parsed_command: dict = None, execution_result: dict = None, timings: dict = None):
        self.transcript = transcript
        self.parsed_command = parsed_command
        self.execution_result = execution_result
        self.timings = timings or {}
        self.update_counter += 1

    def clear_result(self):
        self.transcript = None
        self.parsed_command = None
        self.execution_result = None
        self.refresh()

    def render(self) -> Text:
        volume = 0
        if self.is_recording and self.audio_capture:
            volume = self.audio_capture.get_volume_level()

        lines = []

        if self.mcp_servers:
            for server in self.mcp_servers:
                icon = server.get("icon", "•")
                display_name = server.get("display_name", server["name"])
                is_connected = server["name"] in self.connected_servers
                status_icon = "✓" if is_connected else "✗"
                mcp_line = f"             {icon} {display_name} {status_icon}"
                lines.append(mcp_line)

        lines.append("")

        if self.is_recording:
            num_bars = 10
            max_height = 8
            bars = []

            import random
            base_height = int((volume / 100) * max_height)
            for _ in range(num_bars):
                variation = random.randint(-1, 1)
                bar_height = max(1, min(max_height, base_height + variation))
                bars.append(bar_height)

            for row in range(max_height, 0, -1):
                line = "                    "
                for bar_height in bars:
                    if bar_height >= row:
                        line += "█ "
                    else:
                        line += "  "
                lines.append(line)

        else:
            for _ in range(8):
                lines.append("")

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

        text = Text("\n".join(lines))

        if self.transcript:
            text.append("\n\n")
            text.append("╭────────────────────────────────────────────────────────────╮\n")

            text.append("│ ")
            if 'asr' in self.timings:
                asr_ms = int(self.timings['asr'] * 1000)
                text.append(f"ASR {asr_ms}ms: ", style="dim cyan")
            text.append(self.transcript, style="italic white")
            text.append("\n")

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

                if self.execution_result:
                    try:
                        text.append("│\n│ ")

                        if 'execution' in self.timings:
                            exec_ms = int(self.timings['execution'] * 1000)
                            text.append(f"Execution {exec_ms}ms: ", style="dim cyan")

                        if self.execution_result.get("success"):
                            text.append("✓ Success - ", style="green")

                            data = self.execution_result.get("data", "")
                            import json
                            try:
                                if isinstance(data, list):
                                    if len(data) > 1:
                                        data_preview = data[:1]
                                    else:
                                        data_preview = data
                                else:
                                    data_preview = data

                                data_json = json.dumps(data_preview, indent=0, default=str)
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
                text.append("│ ", style="dim")
                text.append("(no command found)", style="dim yellow")
                text.append("\n")

            text.append("╰────────────────────────────────────────────────────────────╯")

        return text

    def start_recording(self):
        self.is_recording = True
        if self.audio_capture:
            self.audio_capture.start_recording()
        self.animate()

    def stop_recording(self):
        self.is_recording = False
        if self.audio_capture:
            self.audio_capture.stop_recording()
        self.refresh()

    def animate(self):
        if self.is_recording:
            self.refresh()
            self.set_timer(0.05, self.animate)


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
        self.mcp_servers_config = []
        self.current_processing_task = None

        self.audio_capture = None
        if MIC_AVAILABLE and AudioCapture:
            try:
                self.audio_capture = AudioCapture()
            except Exception:
                self.audio_capture = None

        self.transcriber = None
        self.intent_parser = None
        self.mcp_gateway = None
        self.rendering_available = bind_data is not None and render_component is not None

        if Transcriber and IntentParser and config.get("openai_api_key"):
            try:
                self.transcriber = Transcriber(config["openai_api_key"])
            except Exception:
                pass

    def compose(self) -> ComposeResult:
        yield Header()
        yield MicrophoneDisplay(audio_capture=self.audio_capture)
        yield Container(id="result-container")
        yield Footer()

    async def on_mount(self) -> None:
        if MCPGateway and MCPConfig:
            try:
                mcp_config = MCPConfig()
                self.mcp_servers_config = mcp_config.get_server_configs()
                self.mcp_gateway = MCPGateway(mcp_config)

                await self.mcp_gateway.connect_all()

                tools = self.mcp_gateway.get_gpt4_tools()

                # Get filesystem root for intent parsing context
                filesystem_root = None
                filesystem_server = next((s for s in self.mcp_servers_config if s["name"] == "filesystem"), None)
                if filesystem_server and filesystem_server.get("args"):
                    filesystem_root = filesystem_server["args"][-1]

                self.intent_parser = IntentParser(self.config["openai_api_key"], tools, filesystem_root)

                mic = self.query_one(MicrophoneDisplay)
                mic.set_mcp_status(self.mcp_servers_config, self.mcp_gateway.sessions)

                self.notify(f"Connected to {len(self.mcp_gateway.sessions)} MCP servers")
            except Exception as e:
                self.notify(f"MCP initialization failed: {str(e)}")

    def action_hold_to_speak(self) -> None:
        mic = self.query_one(MicrophoneDisplay)

        if not mic.is_recording:
            mic.add_class("recording")
            mic.start_recording()
            self.v_key_held = True

        if self.release_timer:
            self.release_timer.stop()

        self.release_timer = self.set_timer(0.2, self.check_release)

    def check_release(self) -> None:
        mic = self.query_one(MicrophoneDisplay)

        if mic.is_recording:
            mic.remove_class("recording")
            mic.stop_recording()
            self.v_key_held = False

            if self.current_processing_task and not self.current_processing_task.is_finished:
                self.current_processing_task.cancel()

            self.current_processing_task = self.run_worker(self.process_audio(), exclusive=True)

    async def on_unmount(self) -> None:
        if self.audio_capture:
            self.audio_capture.cleanup()

        if self.mcp_gateway:
            await self.mcp_gateway.close_all()

    def action_settings(self) -> None:
        if not SettingsScreen:
            self.notify("Settings screen not available")
            return

        # Reload config from disk to get fresh values
        if self.mcp_gateway and self.mcp_gateway.mcp_config:
            self.mcp_gateway.mcp_config.load_config()
            self.mcp_servers_config = self.mcp_gateway.mcp_config.get_server_configs()

        async def on_save(updated_servers):
            if self.mcp_gateway and self.mcp_gateway.mcp_config:
                self.mcp_gateway.mcp_config.save_config(updated_servers)

                try:
                    await self.mcp_gateway.close_all()
                    await self.mcp_gateway.connect_all()

                    # Reload config after reconnecting
                    self.mcp_gateway.mcp_config.load_config()
                    self.mcp_servers_config = self.mcp_gateway.mcp_config.get_server_configs()

                    # Update intent parser with new tools and filesystem root
                    if self.intent_parser:
                        self.intent_parser.tools = self.mcp_gateway.get_gpt4_tools()

                        # Update filesystem root if it changed
                        filesystem_server = next((s for s in self.mcp_servers_config if s["name"] == "filesystem"), None)
                        if filesystem_server and filesystem_server.get("args"):
                            self.intent_parser.filesystem_root = filesystem_server["args"][-1]
                        else:
                            self.intent_parser.filesystem_root = None

                    mic = self.query_one(MicrophoneDisplay)
                    mic.set_mcp_status(self.mcp_servers_config, self.mcp_gateway.sessions)

                    self.notify(f"Reconnected: {len(self.mcp_gateway.sessions)} servers active")
                except Exception as e:
                    self.notify(f"Reconnection failed: {str(e)}")

        connected_servers = self.mcp_gateway.sessions if self.mcp_gateway else {}
        original_configs = self.mcp_gateway.mcp_config.get_original_server_configs() if self.mcp_gateway and self.mcp_gateway.mcp_config else self.mcp_servers_config

        def on_settings_close():
            # Reload config to refresh UI
            if self.mcp_gateway and self.mcp_gateway.mcp_config:
                self.mcp_gateway.mcp_config.load_config()
                self.mcp_servers_config = self.mcp_gateway.mcp_config.get_server_configs()

            mic = self.query_one(MicrophoneDisplay)
            mic.set_mcp_status(self.mcp_servers_config, self.mcp_gateway.sessions if self.mcp_gateway else {})

        self.push_screen(
            SettingsScreen(
                self.mcp_servers_config,
                connected_servers,
                on_save,
                self.mcp_gateway,
                original_configs
            ),
            callback=lambda _: on_settings_close()
        )

    def action_quit(self) -> None:
        self.exit()

    async def process_audio(self) -> None:
        if not self.audio_capture:
            self.notify("Audio capture not available")
            return

        if not self.transcriber or not self.intent_parser:
            self.notify("OpenAI API not configured")
            return

        transcript = None
        parsed = None
        mic = self.query_one(MicrophoneDisplay)

        import time
        import asyncio
        timings = {}

        try:
            audio_data = self.audio_capture.get_audio_data()

            if not audio_data:
                self.notify("No audio recorded")
                return

            self.notify("Transcribing...")
            start_time = time.time()

            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                self.transcriber.transcribe,
                audio_data,
                16000
            )

            timings['asr'] = time.time() - start_time

            if not transcript:
                self.notify("No speech detected")
                mic.show_result("(no speech detected)", None, None, timings)
                return

            mic.show_result(transcript, None, None, timings)

            self.notify("Understanding command...")
            start_time = time.time()

            parsed = await loop.run_in_executor(
                None,
                self.intent_parser.parse,
                transcript
            )

            timings['intent'] = time.time() - start_time
            mic.show_result(transcript, parsed, None, timings)

            if parsed:
                if self.mcp_gateway:
                    self.notify("Executing...")
                    start_time = time.time()

                    result = await self.mcp_gateway.execute_tool(
                        parsed["function"],
                        parsed["arguments"]
                    )

                    timings['execution'] = time.time() - start_time

                    if result["success"]:
                        self.notify(f"✓ {result['message']}")
                    else:
                        self.notify(f"✗ {result['message']}")

                    mic.show_result(transcript, parsed, result, timings)

                    if result.get("success") and self.rendering_available:
                        try:
                            start_time = time.time()
                            await self.render_rich_results(result)
                            timings['render'] = time.time() - start_time
                            mic.show_result(transcript, parsed, result, timings)
                        except Exception:
                            pass
                else:
                    self.notify("Command recognized (MCP not connected)")
            else:
                self.notify(f"No command found in: {transcript}")

        except Exception as e:
            self.notify(f"Error: {str(e)}")
            if transcript:
                mic.show_result(transcript, parsed, None, timings)

    async def render_rich_results(self, result: dict) -> None:
        try:
            container = self.query_one("#result-container", Container)
            await container.remove_children()

            data = result.get("data", "")
            component = bind_data(data)
            widget = render_component(component)

            await container.mount(widget)

        except Exception as e:
            self.notify(f"Error rendering results: {str(e)}")
