"""
MCP Gateway - Connects to and manages MCP servers
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, List, Any
from gateway.mcp_config import MCPConfig


class MCPGateway:
    """Gateway that connects to multiple MCP servers and aggregates their tools."""

    def __init__(self, mcp_config: MCPConfig = None):
        self.mcp_config = mcp_config or MCPConfig()
        self.sessions: Dict[str, ClientSession] = {}
        self.stdio_tasks: Dict[str, asyncio.Task] = {}
        self.connection_ready: Dict[str, asyncio.Event] = {}
        self.tools_cache: Dict[str, List[Dict]] = {}
        self.tool_to_server: Dict[str, str] = {}

    async def connect_all(self):
        for server_config in self.mcp_config.get_enabled_server_configs():
            try:
                await self.connect_server(server_config)
            except Exception as e:
                print(f"Failed to connect to {server_config['name']}: {e}")

    async def connect_server(self, server_config: Dict[str, Any]):
        name = server_config["name"]

        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env")
        )

        self.connection_ready[name] = asyncio.Event()
        task = asyncio.create_task(self._maintain_connection(name, server_params))
        self.stdio_tasks[name] = task

        try:
            await asyncio.wait_for(self.connection_ready[name].wait(), timeout=5.0)
            print(f"Connected to {name}: {len(self.tools_cache.get(name, []))} tools available")
        except asyncio.TimeoutError:
            print(f"Timeout connecting to {name}")

    async def _maintain_connection(self, name: str, server_params: StdioServerParameters):
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    tools_result = await session.list_tools()
                    tools = tools_result.tools if hasattr(tools_result, 'tools') else []

                    self.sessions[name] = session
                    self.tools_cache[name] = tools

                    for tool in tools:
                        self.tool_to_server[tool.name] = name

                    self.connection_ready[name].set()

                    while True:
                        await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Connection to {name} failed: {e}")
            if name in self.connection_ready:
                self.connection_ready[name].set()

    def get_gpt4_tools(self) -> List[Dict[str, Any]]:
        gpt4_tools = []

        for server_name, tools in self.tools_cache.items():
            for tool in tools:
                gpt4_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Tool from {server_name}",
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                gpt4_tools.append(gpt4_tool)

        return gpt4_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        server_name = self.tool_to_server.get(tool_name)

        if not server_name:
            return {
                "success": False,
                "message": f"Unknown tool: {tool_name}"
            }

        session = self.sessions.get(server_name)
        if not session:
            return {
                "success": False,
                "message": f"Server not connected: {server_name}"
            }

        try:
            result = await session.call_tool(tool_name, arguments)

            return {
                "success": True,
                "message": f"Executed {tool_name}",
                "data": result.content if hasattr(result, 'content') else result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing {tool_name}: {str(e)}"
            }

    async def close_all(self):
        for task in self.stdio_tasks.values():
            task.cancel()

        if self.stdio_tasks:
            await asyncio.gather(*self.stdio_tasks.values(), return_exceptions=True)

        self.sessions.clear()
        self.stdio_tasks.clear()
        self.tools_cache.clear()
        self.tool_to_server.clear()
