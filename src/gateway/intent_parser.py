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

        # Debug: Print available tools
        print(f"\n=== Intent Parser initialized with {len(self.tools)} tools ===", file=__import__('sys').stderr)
        for tool in self.tools:
            print(f"  - {tool['function']['name']}: {tool['function']['description'][:80]}...", file=__import__('sys').stderr)

    def parse(self, transcript: str) -> Optional[Dict[str, Any]]:
        """
        Parse a voice transcript into a structured command.

        Args:
            transcript: Text from Whisper

        Returns:
            Dict with 'function', 'arguments', and 'original_text'
            None if no command was recognized
        """
        if not transcript.strip():
            return None

        try:
            # Call GPT-4 with function calling
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

            # Check if GPT-4 made a function call
            if not message.tool_calls:
                print(f"\n=== No tool call for: '{transcript}' ===", file=__import__('sys').stderr)
                print(f"GPT-4 response: {message.content}", file=__import__('sys').stderr)
                return None

            # Extract the function call
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            return {
                "function": function_name,
                "arguments": arguments,
                "original_text": transcript
            }

        except Exception as e:
            # Log error but don't crash
            print(f"Error parsing intent: {e}", file=__import__('sys').stderr)
            return None
