"""
MCP Configuration Loader
Loads MCP server connection details from config
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any


class MCPConfig:
    """Manages MCP server configuration."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to mcp_config.json in project root
            config_path = Path(__file__).parent.parent.parent / "mcp_config.json"

        self.config_path = Path(config_path)
        self.servers = []
        self.load_config()

    def load_config(self):
        """Load MCP configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"MCP config not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Load all servers (we'll filter enabled ones when connecting)
        self.servers = config.get("servers", [])

        # Expand environment variables in env config
        for server in self.servers:
            env = server.get("env", {})
            expanded_env = {}
            for key, value in env.items():
                # Expand ${VAR} syntax
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    expanded_env[key] = os.getenv(env_var, "")
                else:
                    expanded_env[key] = value
            server["env"] = expanded_env

    def get_server_configs(self) -> List[Dict[str, Any]]:
        """Get list of all server configurations."""
        return self.servers

    def get_enabled_server_configs(self) -> List[Dict[str, Any]]:
        """Get list of enabled server configurations only."""
        return [s for s in self.servers if s.get("enabled", True)]
