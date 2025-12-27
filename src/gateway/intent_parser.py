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

    def parse(self, transcript: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
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

            # Build context reminder if we have previous context
            context_reminder = ""
            if context and context.get("previous_request") and context.get("previous_function"):
                prev_args = context.get('previous_arguments', {})

                # Extract path arguments
                path_args = {}
                for key, value in prev_args.items():
                    if 'path' in key.lower() or 'directory' in key.lower() or 'file' in key.lower():
                        path_args[key] = value

                if path_args:
                    prev_path = list(path_args.values())[0]
                    context_reminder = f"\n\nCONTEXT: The user just ran '{context['previous_function']}' on path '{prev_path}'. "
                    context_reminder += f"If they refer to 'that directory', 'that folder', 'there', 'the same directory', etc., they mean '{prev_path}'."

            messages = [
                {
                    "role": "system",
                    "content": system_content + context_reminder
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ]

            # Debug: print context being sent (only if context exists)
            if context and context.get("previous_request"):
                import os
                if os.getenv("DEBUG_INTENT_PARSER"):
                    print("\n=== Intent Parser Messages ===")
                    for msg in messages:
                        print(f"{msg['role'].upper()}: {msg['content'][:200]}")
                    print("==============================\n")

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if not message.tool_calls:
                import os
                if os.getenv("DEBUG_INTENT_PARSER"):
                    print(f"\n=== No Tool Call Returned ===")
                    print(f"Transcript: {transcript}")
                    print(f"GPT-4 Response: {message.content}")
                    print(f"Has context: {context is not None}")
                    print("============================\n")

                # Return the debug info so the UI can show it
                return {
                    "function": None,
                    "arguments": {},
                    "original_text": transcript,
                    "error": f"GPT-4 didn't recognize a command. It said: {message.content or '(no explanation)'}"
                }

            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            return {
                "function": function_name,
                "arguments": arguments,
                "original_text": transcript
            }

        except Exception as e:
            import os
            if os.getenv("DEBUG_INTENT_PARSER"):
                import traceback
                print(f"\n=== Intent Parser Error ===")
                print(f"Error: {e}")
                traceback.print_exc()
                print("===========================\n")
            return None
