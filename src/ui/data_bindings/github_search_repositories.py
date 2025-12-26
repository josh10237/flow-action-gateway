"""
GitHub search_repositories data binding - maps repo search results to UI components.

Response Structure:
{
    "total_count": int,
    "incomplete_results": bool,
    "items": [
        {
            "name": str,                    -> CardComponent.title
            "full_name": str,               -> CardComponent.title (preferred)
            "description": str,             -> CardComponent.subtitle
            "html_url": str,                -> LinkComponent.url
            "stargazers_count": int,        -> KeyValueComponent (⭐ Stars)
            "language": str,                -> KeyValueComponent (💻 Language)
            "owner": {
                "login": str                -> KeyValueComponent (👤 Owner)
            }
        },
        ...
    ]
}

UI Mapping:
- ListComponent(items=[CardComponent, ...])
  - CardComponent (for each item in items):
    - title: item["full_name"] or item["name"]
    - subtitle: item["description"][:150]
    - icon: "📦"
    - metadata: [
        KeyValueComponent(key="⭐ Stars", value=str(stargazers_count)),
        KeyValueComponent(key="💻 Language", value=language),
        KeyValueComponent(key="👤 Owner", value=owner.login)
      ]
    - link: LinkComponent(text="View on GitHub", url=item["html_url"])
"""
import json
from typing import Any
from ..components.banner import BannerComponent
from ..components.card import CardComponent
from ..components.list import ListComponent
from ..components.keyvalue import KeyValueComponent
from ..components.link import LinkComponent


def map_github_search(data: Any) -> Any:
    """Map GitHub search_repositories results to UI components."""
    try:
        print(f"\n[DEBUG] ===== GITHUB SEARCH MAPPING =====")
        print(f"[DEBUG] Data type: {type(data)}")
        print(f"[DEBUG] Data is list: {isinstance(data, list)}")
        if isinstance(data, list) and len(data) > 0:
            print(f"[DEBUG] Data length: {len(data)}")
            print(f"[DEBUG] First item type: {type(data[0])}")
            print(f"[DEBUG] First item: {data[0]}")
            if hasattr(data[0], 'text'):
                print(f"[DEBUG] First item text (first 500 chars): {data[0].text[:500]}")

        # Parse MCP result structure
        # GitHub returns a single response with {total_count, incomplete_results, items: [...]}
        results = []
        if isinstance(data, list) and len(data) > 0:
            # Get the first item which should contain the response
            item = data[0]
            if hasattr(item, 'text'):
                try:
                    response = json.loads(item.text)
                    print(f"[DEBUG] Parsed response keys: {response.keys() if isinstance(response, dict) else 'not a dict'}")

                    # GitHub API returns {total_count, incomplete_results, items: [...]}
                    if isinstance(response, dict) and 'items' in response:
                        results = response['items']
                        print(f"[DEBUG] Found {len(results)} items in response")
                    else:
                        print(f"[DEBUG] Response doesn't have 'items' key")
                        print(f"[DEBUG] Response structure: {response}")
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON decode error: {e}")
                    print(f"[DEBUG] Raw text: {item.text[:500]}")

        if not results:
            return BannerComponent(
                type="info",
                message="No repositories found",
                icon="📦"
            )

        # Map each result to a CardComponent
        cards = []
        for result in results[:10]:  # Show max 10 results
            # Extract fields from response
            name = result.get('name', result.get('full_name', 'Unknown'))
            full_name = result.get('full_name', name)
            description = result.get('description', '')
            url = result.get('html_url', '')
            stars = result.get('stargazers_count', 0)
            language = result.get('language', 'Unknown')
            owner = result.get('owner', {})
            owner_login = owner.get('login', 'Unknown') if isinstance(owner, dict) else 'Unknown'

            # Build metadata
            metadata = []
            if stars is not None:
                metadata.append(KeyValueComponent(key="⭐ Stars", value=str(stars)))
            if language:
                metadata.append(KeyValueComponent(key="💻 Language", value=language))
            if owner_login:
                metadata.append(KeyValueComponent(key="👤 Owner", value=owner_login))

            # Build link
            link = LinkComponent(text="View on GitHub", url=url) if url else None

            # Create card with mapped fields
            card = CardComponent(
                title=full_name,
                subtitle=description[:150] if description else None,
                icon="📦",
                metadata=metadata if metadata else None,
                link=link
            )
            cards.append(card)

        return ListComponent(items=cards)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return BannerComponent(
            type="error",
            message=f"Error mapping GitHub results: {str(e)[:100]}",
            icon="⚠"
        )
