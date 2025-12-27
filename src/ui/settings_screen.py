"""
Settings screen
"""
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Button, Label, Input
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from typing import Dict, List, Any, Callable
from ui.components.mcp_settings import MCPSettingsWidget


class SettingsScreen(Screen):
    BINDINGS = [
        Binding("escape", "cancel", "Back", show=True),
        Binding("b", "cancel", "Back", show=True),
    ]

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-container {
        width: 90;
        height: auto;
        border: solid $primary;
        padding: 1 2;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $primary;
    }

    #server-list {
        height: auto;
        overflow-y: auto;
        margin-bottom: 2;
    }

    .server-header {
        layout: horizontal;
        height: 3;
        border: solid $accent;
        margin: 1 0;
        padding: 0 1;
        background: $panel;
        align: left middle;
    }

    .server-name {
        width: 1fr;
        content-align: left middle;
    }

    .toggle-button {
        min-width: 8;
        margin: 0 1;
    }

    .auth-status {
        color: $text-muted;
        margin: 0 2;
    }

    .auth-status.authenticated {
        color: $success;
    }

    .credentials {
        padding-left: 2;
        padding-top: 0;
        padding-bottom: 0;
        margin-bottom: 1;
        border-left: solid $accent;
        height: auto;
    }

    .args-section {
        padding-left: 2;
        padding-top: 0;
        padding-bottom: 0;
        margin-bottom: 1;
        border-left: solid $accent;
        height: auto;
    }

    .credential-label {
        margin-top: 1;
        color: $text;
    }

    .credential-input {
        width: 100%;
        margin-bottom: 1;
    }

    .no-credentials {
        color: $text-muted;
        margin-left: 2;
        margin-bottom: 2;
    }

    .tools-header {
        margin-top: 1;
        margin-left: 2;
        color: $text;
        text-style: bold;
    }

    .tools-list {
        margin-left: 2;
        margin-bottom: 1;
        margin-right: 2;
        color: $text-muted;
        overflow: auto;
        height: auto;
    }

    .tools-list.enabled {
        color: $secondary;
    }

    .test-result {
        margin-left: 2;
        margin-bottom: 1;
    }

    .button-row {
        layout: horizontal;
        align: center middle;
        margin-top: 2;
        height: 3;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        server_configs: List[Dict[str, Any]],
        connected_servers: Dict[str, Any],
        on_save: Callable[[List[Dict[str, Any]]], None],
        mcp_gateway=None,
        original_configs: List[Dict[str, Any]] = None
    ):
        super().__init__()
        self.server_configs = server_configs
        self.original_configs = original_configs if original_configs else server_configs
        self.connected_servers = connected_servers
        self.on_save_callback = on_save
        self.mcp_gateway = mcp_gateway
        self.server_widgets: List[MCPSettingsWidget] = []
        self.test_results: Dict[str, str] = {}  # server_name -> test result message

        # Get tools cache from gateway
        self.tools_cache = mcp_gateway.tools_cache if mcp_gateway else {}

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        yield Header()

        with Container(id="settings-container"):
            yield Static("MCP Server Configuration", classes="title")

            with Vertical(id="server-list"):
                # Create a widget for each server
                for i, server_config in enumerate(self.server_configs):
                    server_name = server_config["name"]
                    is_connected = server_name in self.connected_servers

                    if is_connected:
                        status = "Connected"
                    elif server_config.get("enabled", True):
                        status = "Enabled (not connected)"
                    else:
                        status = "Disabled"

                    # Use original config for display (has templates) but pass expanded for runtime
                    original_config = self.original_configs[i] if i < len(self.original_configs) else server_config

                    # Get available tools for this server
                    available_tools = self.tools_cache.get(server_name, [])

                    widget = MCPSettingsWidget(server_config, status, original_config, available_tools)
                    self.server_widgets.append(widget)
                    yield widget

            with Horizontal(classes="button-row"):
                yield Button("Save & Exit", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            self.action_save()
        elif event.button.id == "cancel-button":
            self.action_cancel()
        elif event.button.id and event.button.id.startswith("toggle-"):
            # Extract server name from button ID (toggle-{server_name})
            server_name = event.button.id[7:]  # Remove "toggle-" prefix
            self.toggle_server(server_name, event.button)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in credential input - just blur/unfocus."""
        # When user presses Enter, stop editing (blur the input)
        # This stops the cursor from flickering but doesn't close settings
        event.input.blur()

    def action_save(self) -> None:
        """Save the configuration and quit the app."""
        # Collect updated configs from all widgets
        updated_configs = []
        for widget in self.server_widgets:
            updated_config = widget.get_updated_config()
            updated_configs.append(updated_config)

        # Call the save callback
        self.on_save_callback(updated_configs)

        # Show notification briefly
        self.app.notify("Settings saved! Exiting...", severity="information")

        # Quit the app so user can restart
        self.app.exit()

    def action_cancel(self) -> None:
        """Cancel and close settings without saving."""
        self.app.pop_screen()

    def toggle_server(self, server_name: str, button: Button) -> None:
        """Toggle server on/off. If turning ON and credentials needed, test connection first."""
        # Find the widget for this server
        widget = None
        for w in self.server_widgets:
            if w.server_config["name"] == server_name:
                widget = w
                break

        if not widget:
            return

        # Get current enabled state
        current_state = widget.server_config.get("enabled", True)

        if current_state:
            # Currently ON, turning OFF - simple toggle
            widget.server_config["enabled"] = False
            button.label = "OFF"
            button.variant = "default"

            # Update status
            try:
                status_label = widget.query_one(f"#status-{server_name}", Label)
                status_label.update("Disabled")
            except Exception:
                pass
        else:
            # Currently OFF, turning ON - test connection if credentials needed
            if widget.server_config.get("env", {}):
                # Has credentials - test connection first
                self.test_and_enable(server_name, button, widget)
            else:
                # No credentials needed - just enable
                widget.server_config["enabled"] = True
                button.label = "ON"
                button.variant = "success"

                # Update status
                try:
                    status_label = widget.query_one(f"#status-{server_name}", Label)
                    status_label.update("Enabled")
                except Exception:
                    pass

    def test_and_enable(self, server_name: str, button: Button, widget) -> None:
        """Test connection and enable only if successful."""
        # Get updated config from widget (with current input values)
        updated_config = widget.get_updated_config()
        updated_config["enabled"] = True  # Temporarily enable for testing

        # Show "Testing..." status
        self.app.notify(f"Testing connection to {updated_config.get('display_name', server_name)}...")

        # Run the test connection asynchronously
        self.run_worker(self._test_and_enable_async(server_name, updated_config, widget, button))

    async def _test_and_enable_async(self, server_name: str, server_config: Dict[str, Any], widget, button: Button) -> None:
        """Async worker to test connection and enable if successful."""
        if not self.mcp_gateway:
            self.app.notify("Failed: Gateway not available", severity="error")
            return

        try:
            # Attempt to connect to this server
            await self.mcp_gateway.connect_server(server_config)

            # Check if connection was successful
            if server_name in self.mcp_gateway.sessions:
                # Success! Enable the server
                widget.server_config["enabled"] = True
                button.label = "ON"
                button.variant = "success"

                tools_count = len(self.mcp_gateway.tools_cache.get(server_name, []))

                # Update auth status to show authenticated
                try:
                    auth_label = widget.query_one(f"#auth-{server_name}", Label)
                    auth_label.update("Authenticated ✓")
                    auth_label.add_class("authenticated")
                except Exception:
                    pass

                # Update available tools list
                widget.available_tools = self.mcp_gateway.tools_cache.get(server_name, [])
                widget.update_tools_display()

                self.app.notify(f"✓ Connected! ({tools_count} tools available)", severity="information")
            else:
                # Connection failed - keep it OFF
                widget.server_config["enabled"] = False
                button.label = "OFF"
                button.variant = "default"
                self.app.notify("Failed: Connection timed out", severity="error")

        except Exception as e:
            # Connection failed - keep it OFF
            widget.server_config["enabled"] = False
            button.label = "OFF"
            button.variant = "default"
            self.app.notify(f"Failed: {str(e)[:50]}", severity="error")

        # Refresh widget
        widget.refresh()

    def test_connection(self, server_name: str) -> None:
        """Test connection to a server with current credentials."""
        # Find the widget for this server
        widget = None
        for w in self.server_widgets:
            if w.server_config["name"] == server_name:
                widget = w
                break

        if not widget:
            return

        # Get updated config from widget
        updated_config = widget.get_updated_config()

        # Show "Testing..." status
        self.app.notify(f"Testing connection to {updated_config.get('display_name', server_name)}...")

        # Run the test connection asynchronously
        self.run_worker(self._test_connection_async(server_name, updated_config, widget))

    async def _test_connection_async(self, server_name: str, server_config: Dict[str, Any], widget) -> None:
        """Async worker to test MCP server connection."""
        if not self.mcp_gateway:
            widget.test_status = "✗ Gateway not available"
            widget.refresh()
            self.app.notify("MCP gateway not available", severity="error")
            return

        try:
            # Attempt to connect to this server
            await self.mcp_gateway.connect_server(server_config)

            # Check if connection was successful
            if server_name in self.mcp_gateway.sessions:
                tools_count = len(self.mcp_gateway.tools_cache.get(server_name, []))
                widget.test_status = f"✓ Connected! ({tools_count} tools available)"
                widget.connection_status = "Connected (test)"

                # Update the status label
                try:
                    status_label = widget.query_one(f"#status-{server_name}", Label)
                    status_label.update(f"Connected")
                except Exception:
                    pass

                self.app.notify(f"✓ Successfully connected to {server_config.get('display_name', server_name)}", severity="information")
            else:
                widget.test_status = "✗ Connection failed (timeout)"
                self.app.notify(f"✗ Connection to {server_config.get('display_name', server_name)} timed out", severity="error")

        except Exception as e:
            widget.test_status = f"✗ Error: {str(e)[:50]}"
            self.app.notify(f"✗ Connection failed: {str(e)}", severity="error")

        # Refresh widget to show test result
        widget.refresh()
