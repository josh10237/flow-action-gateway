"""
MCP server configuration widget
"""
from textual.widgets import Static, Input, Label, Button
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from typing import Dict, Any


class MCPSettingsWidget(Static):
    def __init__(self, server_config: Dict[str, Any], connection_status: str = "Unknown", original_config: Dict[str, Any] = None, available_tools: list = None):
        super().__init__()
        self.server_config = server_config
        self.connection_status = connection_status
        self._original_config = original_config if original_config else server_config.copy()
        self.test_status = ""
        self.available_tools = available_tools or []

    def compose(self) -> ComposeResult:
        """Compose the server configuration widget."""
        icon = self.server_config.get("icon", "•")
        display_name = self.server_config.get("display_name", self.server_config["name"])
        enabled = self.server_config.get("enabled", True)

        # Server header with icon, name, authenticated status, and ON/OFF button
        with Container(classes="server-header"):
            yield Label(f"{icon} {display_name}", classes="server-name")

            # Show authenticated status for servers with credentials
            if self.server_config.get("env", {}):
                # Check if we have actual credentials (not empty)
                has_creds = any(v for v in self.server_config.get("env", {}).values())
                if has_creds and self.connection_status == "Connected":
                    yield Label("Authenticated ✓", classes="auth-status authenticated", id=f"auth-{self.server_config['name']}")
                else:
                    yield Label("Not authenticated", classes="auth-status", id=f"auth-{self.server_config['name']}")

            # ON/OFF button (combines toggle and test)
            toggle_variant = "success" if enabled else "default"
            toggle_text = "ON" if enabled else "OFF"
            yield Button(toggle_text, variant=toggle_variant, id=f"toggle-{self.server_config['name']}", classes="toggle-button")

        # Test result (if available)
        if self.test_status:
            yield Label(self.test_status, classes="test-result", id=f"test-result-{self.server_config['name']}")

        # Credentials section (if env vars exist)
        env_vars = self.server_config.get("env", {})
        original_env = self._original_config.get("env", {})

        if env_vars:
            with Vertical(classes="credentials"):
                for key, value in env_vars.items():
                    # Use original template as placeholder if it's a template
                    original_value = original_env.get(key, "")

                    # If original is a template like ${VAR}, show it as placeholder
                    # Otherwise show the actual value (or expanded value from env)
                    if original_value.startswith("${") and original_value.endswith("}"):
                        # Template - show as placeholder, value should be actual env var value or empty
                        import os
                        env_var_name = original_value[2:-1]
                        actual_value = os.getenv(env_var_name, "")
                        placeholder = f"{key} (e.g., {original_value})"
                    else:
                        # Literal value - show it
                        actual_value = value
                        placeholder = key

                    yield Label(f"{key}:", classes="credential-label")
                    yield Input(
                        value=actual_value,
                        placeholder=placeholder,
                        password=True,  # Hide credential values
                        id=f"env-{self.server_config['name']}-{key}",
                        classes="credential-input"
                    )
        else:
            yield Label("No credentials required", classes="no-credentials")

        # Args section (for filesystem server directory path)
        args = self.server_config.get("args", [])
        if self.server_config["name"] == "filesystem" and len(args) > 0:
            # Last arg is the directory path for filesystem server
            directory_path = args[-1]

            with Vertical(classes="args-section"):
                yield Label("Directory Access:", classes="credential-label")
                yield Input(
                    value=directory_path,
                    placeholder="/path/to/directory",
                    id=f"args-{self.server_config['name']}-directory",
                    classes="credential-input"
                )

        # Available tools section (always show, even if empty)
        yield Label("Available tools:", classes="tools-header")

        if self.available_tools:
            # Extract tool names from the tool list (tools are Pydantic objects)
            tool_names = [getattr(tool, "name", "unknown") for tool in self.available_tools]
            tools_text = ", ".join(tool_names)
        else:
            tools_text = "None (not connected)"

        # Add "enabled" class if server is enabled to make tools purple
        tools_classes = "tools-list"
        if enabled and self.available_tools:
            tools_classes += " enabled"

        yield Label(tools_text, classes=tools_classes, id=f"tools-{self.server_config['name']}")

    def update_tools_display(self):
        """Update the tools list display after connecting."""
        if not self.available_tools:
            return

        # Try to find and update the existing tools label
        try:
            tools_label = self.query_one(f"#tools-{self.server_config['name']}", Label)
            tool_names = [getattr(tool, "name", "unknown") for tool in self.available_tools]
            tools_text = ", ".join(tool_names)
            tools_label.update(tools_text)

            # Add enabled class if server is enabled
            if self.server_config.get("enabled", True):
                tools_label.add_class("enabled")
        except Exception:
            # If label doesn't exist, we need to remount the widget
            # This happens when connecting for the first time
            pass

    def get_updated_config(self) -> Dict[str, Any]:
        """Get the updated server configuration from widget state."""
        config = self.server_config.copy()

        # Get enabled state from button
        try:
            toggle_button = self.query_one(f"#toggle-{self.server_config['name']}", Button)
            config["enabled"] = (toggle_button.label == "ON")
        except Exception:
            pass  # Keep original if widget not found

        # Get env var values
        env_vars = self.server_config.get("env", {})
        if env_vars:
            updated_env = {}
            for key in env_vars.keys():
                try:
                    input_widget = self.query_one(f"#env-{self.server_config['name']}-{key}", Input)
                    value = input_widget.value.strip()
                    updated_env[key] = value
                except Exception:
                    updated_env[key] = env_vars[key]  # Keep original if widget not found

            config["env"] = updated_env

        # Get args (directory path for filesystem server)
        if self.server_config["name"] == "filesystem":
            try:
                dir_input = self.query_one(f"#args-{self.server_config['name']}-directory", Input)
                directory_path = dir_input.value.strip()
                if directory_path:
                    # Update the last arg with the new directory path
                    args = config.get("args", []).copy()
                    if len(args) > 0:
                        args[-1] = directory_path
                        config["args"] = args
            except Exception:
                pass  # Keep original if widget not found

        return config
