"""
Intent parsing using GPT-4 function calling
"""
from openai import OpenAI
from typing import Dict, List, Any, Optional
import json


class IntentParser:
    """Parses natural language commands using GPT-4 function calling."""

    def __init__(self, api_key: str, tools: List[Dict[str, Any]] = None, filesystem_root: str = None):
        self.client = OpenAI(api_key=api_key)
        self.tools = tools or []
        self.filesystem_root = filesystem_root

    def parse(self, transcript: str) -> Optional[Dict[str, Any]]:
        if not transcript.strip():
            return None

        try:
            system_content = """You are a voice command assistant. Parse the user's voice command into the appropriate function call.

Examples:
- "list files on desktop" → list_directory(path="Desktop")
- "search github for react repos" → search_repositories(query="react")
- "search for python tutorials" → brave_web_search(query="python tutorials")

If the command doesn't match any available function, don't make a function call."""

            if self.filesystem_root:
                system_content += f"\n\nFor file operations, all paths are relative to the root directory: {self.filesystem_root}"

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": transcript
                    }
                ],
                tools=self.tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if not message.tool_calls:
                return None

            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            return {
                "function": function_name,
                "arguments": arguments,
                "original_text": transcript
            }

        except Exception:
            return None
