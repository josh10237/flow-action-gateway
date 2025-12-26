"""
Data binding router - routes tool results to appropriate mappers.

Naming convention: MCPNAME_FUNCTIONNAME.py
Example: brave_search_brave_web_search.py, github_search_repositories.py
"""
from typing import Any
from ..components.banner import BannerComponent
from .brave_search_brave_web_search import map_brave_search
from .github_search_repositories import map_github_search


def route_to_components(data: Any, tool_name: str = None) -> Any:
    """
    Route MCP tool result to appropriate data binding.

    Args:
        data: The data from MCP tool execution
        tool_name: The tool that was executed (e.g., "brave_web_search")

    Returns:
        Component tree for rendering
    """
    try:
        # Route to specific binding if available
        if tool_name == "brave_web_search":
            return map_brave_search(data)
        elif tool_name == "search_repositories":
            return map_github_search(data)

        # Fallback for unknown tools: raw JSON display
        import json
        if isinstance(data, list) and len(data) > 0:
            content = data[0]
            if hasattr(content, 'text'):
                text = content.text
            else:
                text = str(content)
        else:
            text = json.dumps(data, indent=2, default=str)

        # Truncate if too long
        if len(text) > 500:
            text = text[:500] + "..."

        return BannerComponent(
            type="info",
            message=text,
            icon="📄"
        )

    except Exception as e:
        return BannerComponent(
            type="error",
            message=f"Error routing result: {str(e)[:100]}",
            icon="⚠"
        )
