"""
MCP Configuration Loader
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import copy


class MCPConfig:
    """Manages MCP server configuration."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "mcp_config.json"

        self.config_path = Path(config_path)
        self.servers = []
        self.original_servers = []
        self.load_config()

    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"MCP config not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        self.original_servers = copy.deepcopy(config.get("servers", []))
        self.servers = config.get("servers", [])

        for server in self.servers:
            enabled = server.get("enabled", True)
            if isinstance(enabled, str) and enabled.startswith("${") and enabled.endswith("}"):
                env_var = enabled[2:-1]
                env_value = os.getenv(env_var, "true").lower()
                server["enabled"] = env_value in ("true", "1", "yes")

            args = server.get("args", [])
            expanded_args = []
            for arg in args:
                if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                    env_var = arg[2:-1]
                    expanded_args.append(os.getenv(env_var, ""))
                else:
                    expanded_args.append(arg)
            server["args"] = expanded_args

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
        return self.servers

    def get_enabled_server_configs(self) -> List[Dict[str, Any]]:
        return [s for s in self.servers if s.get("enabled", True)]

    def get_original_server_configs(self) -> List[Dict[str, Any]]:
        return self.original_servers

    def save_user_config(self, updated_servers: List[Dict[str, Any]]):
        env_path = self.config_path.parent / ".env"

        existing_env = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key.strip()] = value.strip()

        for server in updated_servers:
            server_name = server["name"].upper().replace("-", "_")
            enabled = server.get("enabled", True)
            existing_env[f"MCP_{server_name}_ENABLED"] = "true" if enabled else "false"

            for i, arg in enumerate(server.get("args", [])):
                if isinstance(arg, str):
                    existing_env[f"MCP_{server_name}_ARG_{i}"] = arg

            env_vars = server.get("env", {})
            for key, value in env_vars.items():
                if value:
                    existing_env[key] = value

        temp_path = env_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            f.write("OPENAI_API_KEY=" + existing_env.get("OPENAI_API_KEY", "") + "\n")
            f.write("\n# MCP Server Configuration\n")

            for server in updated_servers:
                server_name = server["name"].upper().replace("-", "_")
                display_name = server.get("display_name", server["name"])

                f.write(f"\n# {display_name}\n")
                f.write(f"MCP_{server_name}_ENABLED={existing_env.get(f'MCP_{server_name}_ENABLED', 'true')}\n")

                for i, arg in enumerate(server.get("args", [])):
                    arg_key = f"MCP_{server_name}_ARG_{i}"
                    if arg_key in existing_env:
                        f.write(f"{arg_key}={existing_env[arg_key]}\n")

                for key in server.get("env", {}).keys():
                    if key in existing_env:
                        f.write(f"{key}={existing_env[key]}\n")

        temp_path.replace(env_path)
        self.load_config()

    def save_config(self, new_servers: List[Dict[str, Any]]):
        self.save_user_config(new_servers)
