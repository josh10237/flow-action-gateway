"""
Automatic data binding - maps any JSON response to UI components.

Uses heuristics to infer optimal UI components based on data structure and field names.

Mapping Rules:
1. Array of objects → ListComponent of CardComponents
2. Single object with <5 fields → KeyValueComponent grid
3. Single object with ≥5 fields → CardComponent with metadata
4. Fields with "url", "link", "href" → LinkComponent
5. Numeric fields → formatted KeyValueComponent
6. String fields → text display (HTML stripped, max 200 chars)

Field Filtering (auto-hidden):
- Boolean fields (not useful for display)
- ID fields (id, *_id, node_id, etc.)
- Timestamp fields (*_at: created_at, updated_at, published_at, etc.)
- Technical metadata (sha, etag, gravatar_id)
"""
import json
import re
import html
from html.parser import HTMLParser
from typing import Any, Dict, List
from .components.banner import BannerComponent
from .components.card import CardComponent
from .components.list import ListComponent
from .components.keyvalue import KeyValueComponent
from .components.link import LinkComponent


class HTMLStripper(HTMLParser):
    """Strip HTML tags from text."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text)


def strip_html(text: str) -> str:
    """Remove HTML tags and entities from text and clean up whitespace."""
    if not isinstance(text, str):
        return str(text)

    # First, decode HTML entities (&#x27; → ')
    text = html.unescape(text)

    # Quick check: if no < or > chars, skip tag parsing
    if '<' not in text and '>' not in text:
        return text

    try:
        stripper = HTMLStripper()
        stripper.feed(text)
        cleaned = stripper.get_data()

        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    except:
        # If HTML parsing fails, just return original
        return text


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def should_skip_field(key: str, value: Any) -> bool:
    """Check if a field should be skipped from display."""
    key_lower = key.lower()

    # Skip boolean fields
    if isinstance(value, bool):
        return True

    # Skip ID fields
    if key_lower == 'id' or key_lower.endswith('_id'):
        return True

    # Skip timestamp fields (created_at, updated_at, published_at, etc.)
    if key_lower.endswith('_at'):
        return True

    # Skip other common metadata fields
    if key_lower in ['node_id', 'sha', 'etag', 'gravatar_id']:
        return True

    return False


def is_url_field(key: str, value: Any) -> bool:
    """Check if a field likely contains a URL."""
    if not isinstance(value, str):
        return False
    key_lower = key.lower()
    return (
        'url' in key_lower or
        'link' in key_lower or
        'href' in key_lower or
        value.startswith('http://') or
        value.startswith('https://')
    )


def format_field_name(key: str) -> str:
    """Format field name for display (snake_case → Title Case)."""
    # Replace underscores with spaces
    words = key.replace('_', ' ').split()
    # Capitalize each word
    return ' '.join(word.capitalize() for word in words)


def infer_icon(data: Dict) -> str:
    """Infer appropriate icon based on data fields."""
    keys = [k.lower() for k in data.keys()]

    # Check for common patterns
    if any(k in keys for k in ['repo', 'repository', 'github']):
        return "📦"
    elif any(k in keys for k in ['search', 'query', 'results']):
        return "🔍"
    elif any(k in keys for k in ['file', 'document', 'path']):
        return "📄"
    elif any(k in keys for k in ['user', 'author', 'owner']):
        return "👤"
    elif any(k in keys for k in ['error', 'exception']):
        return "⚠️"
    else:
        return "📋"


def object_to_card(obj: Dict, max_fields: int = 10) -> CardComponent:
    """
    Convert a single object to a CardComponent.

    Simple rules:
    - Title: First 'title' or 'name' field found
    - Icon: Based on content type
    - Links: Any URL field becomes clickable
    - KVs: Everything else (description, numbers, strings, etc.)
    """
    # Find title (priority: title > name > first string)
    title = None
    title_key = None
    for key in ['title', 'name', 'full_name', 'id']:
        if key in obj and obj[key]:
            title = str(obj[key])
            title_key = key
            break

    if not title:
        # Fallback: use first short string
        for key, value in obj.items():
            if isinstance(value, str) and 3 < len(value) < 100:
                title = value
                title_key = key
                break

    if not title:
        title = "Result"

    # Collect links and KVs from all other fields
    links = []
    kvs = []

    for key, value in obj.items():
        # Skip title field (already used)
        if key == title_key:
            continue

        # Skip None/null values
        if value is None or value == "":
            continue

        # Skip noisy fields (IDs, timestamps, booleans)
        if should_skip_field(key, value):
            continue

        # Check if it's a URL → make it clickable
        if is_url_field(key, value):
            link_text = "Open" if key.lower() == 'url' else format_field_name(key)
            links.append(LinkComponent(text=link_text, url=value))
            continue

        # Everything else → add as KV
        # Format value nicely
        if isinstance(value, dict):
            # Nested object - try to extract useful field
            if 'login' in value:
                value = value['login']
            elif 'name' in value:
                value = value['name']
            else:
                value = json.dumps(value, default=str)
        elif isinstance(value, list):
            value = f"[{len(value)} items]"
        elif isinstance(value, (int, float)):
            # Format numbers with commas
            if isinstance(value, int) and value >= 1000:
                value = f"{value:,}"
            else:
                value = str(value)
        else:
            value = str(value)

        # Strip HTML tags
        value = strip_html(value)

        # Truncate to max 200 chars
        value = truncate_text(value, max_length=200)

        kvs.append(KeyValueComponent(
            key=format_field_name(key),
            value=value
        ))

        # Limit total KVs
        if len(kvs) >= max_fields:
            break

    return CardComponent(
        title=title,
        subtitle=None,  # Keep it simple - put description in KVs
        icon=infer_icon(obj),
        metadata=kvs if kvs else None,
        link=links[0] if links else None  # Use first link as primary
    )


def object_to_keyvalue_grid(obj: Dict) -> List[KeyValueComponent]:
    """Convert a small object to a list of KeyValueComponents."""
    result = []
    for key, value in obj.items():
        # Skip None/null values
        if value is None or value == "":
            continue

        # Skip noisy fields (IDs, timestamps, booleans)
        if should_skip_field(key, value):
            continue

        # Format value
        if isinstance(value, dict):
            value = json.dumps(value, default=str)
        elif isinstance(value, list):
            value = f"[{len(value)} items]"
        elif isinstance(value, (int, float)):
            if value >= 1000:
                value = f"{value:,}"
            else:
                value = str(value)
        else:
            value = str(value)

        # Strip HTML and truncate
        value = strip_html(value)
        value = truncate_text(value, max_length=200)

        result.append(
            KeyValueComponent(
                key=format_field_name(key),
                value=value
            )
        )

    return result


def bind_data(data: Any) -> Any:
    """
    Automatically bind MCP response data to UI components.

    Args:
        data: Raw MCP response data (could be list, dict, string, etc.)

    Returns:
        Component tree for rendering
    """
    try:
        # Parse MCP result structure (usually list with text field)
        parsed_data = None

        if isinstance(data, list) and len(data) > 0:
            # Check if it's a list of MCP TextContent objects
            if hasattr(data[0], 'text'):
                # Parse each item's text as JSON
                parsed_items = []
                for item in data:
                    if hasattr(item, 'text'):
                        try:
                            parsed_items.append(json.loads(item.text))
                        except json.JSONDecodeError:
                            # Not JSON, use as string
                            parsed_items.append(item.text)

                # If we got multiple items, that's our list
                if len(parsed_items) > 1:
                    parsed_data = parsed_items
                # If only one item, unwrap it
                elif len(parsed_items) == 1:
                    parsed_data = parsed_items[0]
                else:
                    parsed_data = None
            else:
                # Not TextContent objects, use list as-is
                parsed_data = data
        else:
            parsed_data = data

        # Now map based on structure

        # Case 1: List of objects → ListComponent of CardComponents
        if isinstance(parsed_data, list) and len(parsed_data) > 0:
            # Check if it's a list of objects
            if isinstance(parsed_data[0], dict):
                cards = [object_to_card(obj) for obj in parsed_data[:20]]  # Max 20 items
                return ListComponent(items=cards)
            else:
                # List of primitives - show as banner
                preview = ', '.join(str(x)[:50] for x in parsed_data[:5])
                if len(parsed_data) > 5:
                    preview += f"... ({len(parsed_data)} total)"
                return BannerComponent(
                    type="info",
                    message=preview,
                    icon="📋"
                )

        # Case 2: Single object
        elif isinstance(parsed_data, dict):
            # Check if it has 'items' or 'results' array (common pattern)
            if 'items' in parsed_data and isinstance(parsed_data['items'], list):
                items = parsed_data['items']
                if len(items) > 0 and isinstance(items[0], dict):
                    cards = [object_to_card(obj) for obj in items[:20]]
                    return ListComponent(items=cards)

            if 'results' in parsed_data and isinstance(parsed_data['results'], list):
                items = parsed_data['results']
                if len(items) > 0 and isinstance(items[0], dict):
                    cards = [object_to_card(obj) for obj in items[:20]]
                    return ListComponent(items=cards)

            # Single object with few fields → KeyValue grid
            if len(parsed_data) < 5:
                keyvalues = object_to_keyvalue_grid(parsed_data)
                # Return first KeyValue as a simple display
                if len(keyvalues) == 1:
                    return BannerComponent(
                        type="success",
                        message=f"{keyvalues[0].key}: {keyvalues[0].value}",
                        icon="✓"
                    )
                else:
                    # Multiple key-values - show in card
                    return CardComponent(
                        title="Result",
                        subtitle=None,
                        icon="📋",
                        metadata=keyvalues
                    )

            # Single object with many fields → CardComponent
            else:
                return object_to_card(parsed_data)

        # Case 3: String
        elif isinstance(parsed_data, str):
            # Strip HTML and truncate
            cleaned = strip_html(parsed_data)
            cleaned = truncate_text(cleaned, max_length=200)
            return BannerComponent(
                type="info",
                message=cleaned,
                icon="📄"
            )

        # Case 4: Number, boolean, null
        else:
            return BannerComponent(
                type="info",
                message=str(parsed_data),
                icon="📋"
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return BannerComponent(
            type="error",
            message=f"Data binding error: {str(e)[:100]}",
            icon="⚠"
        )
