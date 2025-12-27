"""
Functional test for the demo workflow.

Tests the complete conversation flow with context using REAL MCP servers.
Just injects transcripts and validates actual intent parsing + execution.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gateway.intent_parser import IntentParser
from gateway.mcp_gateway import MCPGateway
from gateway.mcp_config import MCPConfig
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()


class TestDemoWorkflow:
    """Test the full demo workflow with real MCP servers."""

    async def setup(self):
        """Set up test fixtures with real MCP connection."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Connect to real MCP servers
        self.mcp_config = MCPConfig()
        self.gateway = MCPGateway(self.mcp_config)
        await self.gateway.connect_all()

        # Get real tools from MCP servers
        tools = self.gateway.get_gpt4_tools()

        # Get filesystem root
        filesystem_root = None
        server_configs = self.mcp_config.get_server_configs()
        filesystem_server = next((s for s in server_configs if s["name"] == "filesystem"), None)
        if filesystem_server and filesystem_server.get("args"):
            filesystem_root = filesystem_server["args"][-1]

        self.parser = IntentParser(api_key, tools, filesystem_root)

        print(f"Connected to {len(self.gateway.sessions)} MCP servers")
        print(f"Available tools: {len(tools)}")
        print(f"Filesystem root: {filesystem_root}\n")

    async def cleanup(self):
        """Clean up MCP connections."""
        if self.gateway:
            await self.gateway.close_all()

    async def test_step1_create_directory(self):
        """Step 1: Create a directory on desktop."""
        transcript = "can u create a new directory on desktop called graphql-project"

        result = self.parser.parse(transcript)

        assert result is not None, "Parser should return a result"
        assert result["function"] == "create_directory", f"Expected create_directory, got {result.get('function', 'NO FUNCTION')}"
        assert "path" in result["arguments"], "Should have path argument"

        # Execute the command
        exec_result = await self.gateway.execute_tool(result["function"], result["arguments"])

        print(f"✓ Step 1: {result['function']}({result['arguments']})")
        print(f"  Result: {exec_result.get('success', False)}\n")

        return result

    async def test_step2_create_file_with_context(self):
        """Step 2: Create a file in that same directory (with context from step 1)."""
        # First command
        step1_result = await self.test_step1_create_directory()

        context = {
            "previous_request": "can u create a new directory on desktop called graphql-project",
            "previous_function": step1_result["function"],
            "previous_arguments": step1_result["arguments"]
        }

        transcript = "in that same directory can u create a readme.md that says this is the new graphql project and then add some version number aswell"

        result = self.parser.parse(transcript, context)

        assert result is not None, "Parser should return a result"
        assert result["function"] == "write_file", f"Step 2 FAILED: Expected write_file, got {result.get('function', 'NO FUNCTION')}"
        assert "path" in result["arguments"], "Should have path argument"
        assert "readme" in result["arguments"]["path"].lower(), f"Path should contain readme, got {result['arguments']['path']}"
        assert "content" in result["arguments"], "Should have content argument"

        # Execute the command
        exec_result = await self.gateway.execute_tool(result["function"], result["arguments"])

        print(f"✓ Step 2: {result['function']}({result['arguments']})")
        print(f"  Result: {exec_result.get('success', False)}\n")

        return result

    async def test_step3_search_github(self):
        """Step 3: Search GitHub for graphql dataloader repos."""
        transcript = "can you look up a graphql data loader repo I can use here"

        result = self.parser.parse(transcript)

        assert result is not None, "Parser should return a result"
        assert result["function"] == "search_repositories", f"Expected search_repositories, got {result.get('function', 'NO FUNCTION')}"
        assert "query" in result["arguments"], "Should have query argument"

        # Execute the command
        exec_result = await self.gateway.execute_tool(result["function"], result["arguments"])

        print(f"✓ Step 3: {result['function']}({result['arguments']})")
        print(f"  Result: {exec_result.get('success', False)}\n")

        return result

    async def test_step4_get_readme_with_context(self):
        """Step 4: Get README for specific repo (with context from step 3)."""
        # First search for repos
        step3_result = await self.test_step3_search_github()

        # Execute to get actual results
        exec_result3 = await self.gateway.execute_tool(step3_result["function"], step3_result["arguments"])

        context = {
            "previous_request": "can you look up a graphql data loader repo I can use here",
            "previous_function": step3_result["function"],
            "previous_arguments": step3_result["arguments"],
            "previous_result": exec_result3.get("data") if exec_result3 else None
        }

        transcript = "hey can you actually just pull up the readme for that sheerun dataloader one"

        result = self.parser.parse(transcript, context)

        assert result is not None, "Parser should return a result"
        assert result["function"] == "get_file_contents", f"Expected get_file_contents, got {result.get('function', 'NO FUNCTION')}"
        assert "owner" in result["arguments"], "Should have owner argument"
        assert "repo" in result["arguments"], "Should have repo argument"
        assert "path" in result["arguments"], "Should have path argument"

        # Execute the command
        exec_result = await self.gateway.execute_tool(result["function"], result["arguments"])

        print(f"✓ Step 4: {result['function']}({result['arguments']})")
        print(f"  Result: {exec_result.get('success', False)}\n")

        return result

    async def test_full_workflow(self):
        """Run the complete demo workflow end-to-end."""
        print("\n=== Running Full Demo Workflow ===\n")

        # Step 1
        step1 = await self.test_step1_create_directory()

        # Step 2 with context (no result needed for directory creation)
        context1 = {
            "previous_request": "can u create a new directory on desktop called graphql-project",
            "previous_function": step1["function"],
            "previous_arguments": step1["arguments"],
            "previous_result": None
        }

        transcript2 = "in that same directory can u create a readme.md that says this is the new graphql project and then add some version number aswell"
        step2 = self.parser.parse(transcript2, context1)
        assert step2 is not None, "Step 2 should not fail"
        assert step2["function"] == "write_file", f"Step 2 FAILED: Expected write_file, got {step2.get('function', 'NO FUNCTION')}"
        assert "content" in step2["arguments"], f"Step 2 FAILED: Missing content argument"

        exec_result2 = await self.gateway.execute_tool(step2["function"], step2["arguments"])
        print(f"✓ Step 2: {step2['function']}({step2['arguments']})")
        print(f"  Result: {exec_result2.get('success', False)}\n")

        # Step 3
        transcript3 = "can you look up a graphql data loader repo I can use here"
        step3 = self.parser.parse(transcript3)
        assert step3 is not None, "Step 3 should not fail"

        exec_result3 = await self.gateway.execute_tool(step3["function"], step3["arguments"])
        print(f"✓ Step 3: {step3['function']}({step3['arguments']})")
        print(f"  Result: {exec_result3.get('success', False)}\n")

        # Step 4 with context including results
        context3 = {
            "previous_request": transcript3,
            "previous_function": step3["function"],
            "previous_arguments": step3["arguments"],
            "previous_result": exec_result3.get("data") if exec_result3 else None
        }

        transcript4 = "hey can you actually just pull up the readme for that sheerun dataloader one"
        step4 = self.parser.parse(transcript4, context3)
        assert step4 is not None, "Step 4 should not fail"

        exec_result4 = await self.gateway.execute_tool(step4["function"], step4["arguments"])
        print(f"✓ Step 4: {step4['function']}({step4['arguments']})")
        print(f"  Result: {exec_result4.get('success', False)}\n")

        print("=== All Steps Passed! ===\n")


async def main():
    test = TestDemoWorkflow()

    try:
        await test.setup()
        await test.test_full_workflow()
        print("\n✅ ALL TESTS PASSED!")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
