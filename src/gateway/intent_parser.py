"""
Intent parsing using GPT-4 function calling
"""
from openai import OpenAI
from typing import Dict, List, Any, Optional
import json


class IntentParser:
    """Parses natural language commands using GPT-4 function calling."""

    def __init__(self, api_key: str, tools: List[Dict[str, Any]] = None):
        self.client = OpenAI(api_key=api_key)
        self.tools = tools or []

    def parse(self, transcript: str) -> Optional[Dict[str, Any]]:
        if not transcript.strip():
            return None

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a voice command assistant. Parse the user's voice command into the appropriate function call.

The user's home directory is /Users/joshbenson

When the user mentions a file/folder without a full path, use /Users/joshbenson/ as the base.
When they mention common folders like Desktop, Documents, Downloads, assume they mean /Users/joshbenson/Desktop, etc.

Examples:
- "read test.txt" → read_text_file(path="/Users/joshbenson/test.txt")
- "list files on desktop" → list_directory(path="/Users/joshbenson/Desktop")
- "list files in downloads" → list_directory(path="/Users/joshbenson/Downloads")
- "search for pdf files" → search_files(path="/Users/joshbenson", pattern="**/*.pdf")

If the command doesn't match any available function, don't make a function call."""
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
