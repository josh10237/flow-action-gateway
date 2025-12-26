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
        self.original_servers = []  # Keep original templates for UI
        self.load_config()

    def load_config(self):
        """Load MCP configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"MCP config not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Keep original config with templates intact
        import copy
        self.original_servers = copy.deepcopy(config.get("servers", []))

        # Load all servers (we'll filter enabled ones when connecting)
        self.servers = config.get("servers", [])

        # Expand environment variables in all config fields
        for server in self.servers:
            # Expand ${VAR} in enabled field
            enabled = server.get("enabled", True)
            if isinstance(enabled, str) and enabled.startswith("${") and enabled.endswith("}"):
                env_var = enabled[2:-1]
                # Convert to boolean
                env_value = os.getenv(env_var, "true").lower()
                server["enabled"] = env_value in ("true", "1", "yes")

            # Expand ${VAR} in args array
            args = server.get("args", [])
            expanded_args = []
            for arg in args:
                if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                    env_var = arg[2:-1]
                    expanded_args.append(os.getenv(env_var, ""))
                else:
                    expanded_args.append(arg)
            server["args"] = expanded_args

            # Expand ${VAR} in env config
            env = server.get("env", {})
            expanded_env = {}
            for key, value in env.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
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

    def get_original_server_configs(self) -> List[Dict[str, Any]]:
        """Get list of original server configurations (with env templates intact)."""
        return self.original_servers

    def save_user_config(self, updated_servers: List[Dict[str, Any]]):
        """
        Save user-specific configuration to .env file.

        This updates credentials, enabled state, and paths while leaving
        mcp_config.json untouched (it stays version controlled).

        Args:
            updated_servers: List of server configuration dictionaries from UI
        """
        # Path to .env file
        env_path = self.config_path.parent / ".env"

        # Read existing .env to preserve other variables
        existing_env = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key.strip()] = value.strip()

        # Update with new server configs
        for server in updated_servers:
            server_name = server["name"].upper()

            # Save enabled state
            enabled = server.get("enabled", True)
            existing_env[f"MCP_{server_name}_ENABLED"] = "true" if enabled else "false"

            # Save args (directory path for filesystem)
            if server_name == "FILESYSTEM":
                args = server.get("args", [])
                if len(args) > 0:
                    # Last arg is the directory path
                    existing_env["MCP_FILESYSTEM_PATH"] = args[-1]

            # Save credentials (env vars)
            env_vars = server.get("env", {})
            for key, value in env_vars.items():
                if value:  # Only save non-empty values
                    existing_env[key] = value

        # Write back to .env atomically
        temp_path = env_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            # Group by server
            f.write("OPENAI_API_KEY=" + existing_env.get("OPENAI_API_KEY", "") + "\n")
            f.write("\n# MCP Server Configuration\n\n")

            # Filesystem
            f.write("# Filesystem MCP\n")
            f.write(f"MCP_FILESYSTEM_ENABLED={existing_env.get('MCP_FILESYSTEM_ENABLED', 'true')}\n")
            f.write(f"MCP_FILESYSTEM_PATH={existing_env.get('MCP_FILESYSTEM_PATH', os.path.expanduser('~'))}\n\n")

            # GitHub
            f.write("# GitHub MCP\n")
            f.write(f"MCP_GITHUB_ENABLED={existing_env.get('MCP_GITHUB_ENABLED', 'true')}\n")
            f.write(f"GITHUB_PERSONAL_ACCESS_TOKEN={existing_env.get('GITHUB_PERSONAL_ACCESS_TOKEN', '')}\n")

        # Atomic rename
        temp_path.replace(env_path)

        # Reload config to pick up new values
        self.load_config()

    def save_config(self, new_servers: List[Dict[str, Any]]):
        """
        DEPRECATED: Use save_user_config() instead.

        This method now delegates to save_user_config() to write to .env
        instead of mcp_config.json (which should stay version controlled).
        """
        self.save_user_config(new_servers)
