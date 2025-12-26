"""
Brave Search data binding - maps search results to UI components.

Response Structure (each item in list):
{
    "title": str,           -> CardComponent.title
    "description": str,     -> CardComponent.subtitle (truncated to 150 chars)
    "url": str,             -> LinkComponent.url + extract domain for metadata
}

UI Mapping:
- ListComponent(items=[CardComponent, ...])
  - CardComponent:
    - title: result["title"]
    - subtitle: result["description"][:150]
    - icon: "🔍"
    - metadata: [KeyValueComponent(key="Source", value=domain)]
    - link: LinkComponent(text="Open", url=result["url"])
"""
import json
from typing import Any
from urllib.parse import urlparse
from ..components.banner import BannerComponent
from ..components.card import CardComponent
from ..components.list import ListComponent
from ..components.keyvalue import KeyValueComponent
from ..components.link import LinkComponent


def map_brave_search(data: Any) -> Any:
    """Map Brave Search results to UI components."""
    try:
        # Parse MCP result structure: list of TextContent objects
        # Each TextContent.text contains JSON for one result
        results = []
        if isinstance(data, list):
            for item in data:
                if hasattr(item, 'text'):
                    result = json.loads(item.text)
                    results.append(result)

        if not results:
            return BannerComponent(
                type="info",
                message="No search results found",
                icon="🔍"
            )

        # Map each result to a CardComponent
        cards = []
        for result in results[:5]:  # Show max 5 results
            # Extract fields from response
            title = result.get('title', 'No title')
            description = result.get('description', '')
            url = result.get('url', '')

            # Build metadata (domain from URL)
            metadata = []
            if url:
                try:
                    domain = urlparse(url).netloc
                    metadata.append(KeyValueComponent(key="Source", value=domain))
                except Exception:
                    pass

            # Build link
            link = LinkComponent(text="Open", url=url) if url else None

            # Create card with mapped fields
            card = CardComponent(
                title=title,
                subtitle=description[:150] if description else None,
                icon="🔍",
                metadata=metadata if metadata else None,
                link=link
            )
            cards.append(card)

        return ListComponent(items=cards)

    except Exception as e:
        return BannerComponent(
            type="error",
            message=f"Error mapping search results: {str(e)[:100]}",
            icon="⚠"
        )
