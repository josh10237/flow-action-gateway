"""
Automatic data binding - maps JSON responses to UI components
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
    if not isinstance(text, str):
        return str(text)

    text = html.unescape(text)

    if '<' not in text and '>' not in text:
        return text

    try:
        stripper = HTMLStripper()
        stripper.feed(text)
        cleaned = stripper.get_data()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    except:
        return text


def truncate_text(text: str, max_length: int = 200) -> str:
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def should_skip_field(key: str, value: Any) -> bool:
    key_lower = key.lower()

    if isinstance(value, bool):
        return True

    if key_lower == 'id' or key_lower.endswith('_id'):
        return True

    if key_lower.endswith('_at'):
        return True

    if key_lower in ['node_id', 'sha', 'etag', 'gravatar_id']:
        return True

    return False


def is_url_field(key: str, value: Any) -> bool:
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
    words = key.replace('_', ' ').split()
    return ' '.join(word.capitalize() for word in words)


def infer_icon(data: Dict) -> str:
    keys = [k.lower() for k in data.keys()]

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
    title = None
    title_key = None
    for key in ['title', 'name', 'full_name', 'id']:
        if key in obj and obj[key]:
            title = str(obj[key])
            title_key = key
            break

    if not title:
        for key, value in obj.items():
            if isinstance(value, str) and 3 < len(value) < 100:
                title = value
                title_key = key
                break

    if not title:
        title = "Result"

    links = []
    kvs = []

    for key, value in obj.items():
        if key == title_key:
            continue

        if value is None or value == "":
            continue

        if should_skip_field(key, value):
            continue

        if is_url_field(key, value):
            link_text = "Open" if key.lower() == 'url' else format_field_name(key)
            links.append(LinkComponent(text=link_text, url=value))
            continue

        if isinstance(value, dict):
            if 'login' in value:
                value = value['login']
            elif 'name' in value:
                value = value['name']
            else:
                value = json.dumps(value, default=str)
        elif isinstance(value, list):
            value = f"[{len(value)} items]"
        elif isinstance(value, (int, float)):
            if isinstance(value, int) and value >= 1000:
                value = f"{value:,}"
            else:
                value = str(value)
        else:
            value = str(value)

        value = strip_html(value)
        value = truncate_text(value, max_length=200)

        kvs.append(KeyValueComponent(
            key=format_field_name(key),
            value=value
        ))

        if len(kvs) >= max_fields:
            break

    return CardComponent(
        title=title,
        subtitle=None,
        icon=infer_icon(obj),
        metadata=kvs if kvs else None,
        link=links[0] if links else None
    )


def object_to_keyvalue_grid(obj: Dict) -> List[KeyValueComponent]:
    result = []
    for key, value in obj.items():
        if value is None or value == "":
            continue

        if should_skip_field(key, value):
            continue

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
    try:
        parsed_data = None

        if isinstance(data, list) and len(data) > 0:
            if hasattr(data[0], 'text'):
                parsed_items = []
                for item in data:
                    if hasattr(item, 'text'):
                        try:
                            parsed_items.append(json.loads(item.text))
                        except json.JSONDecodeError:
                            parsed_items.append(item.text)

                if len(parsed_items) > 1:
                    parsed_data = parsed_items
                elif len(parsed_items) == 1:
                    parsed_data = parsed_items[0]
                else:
                    parsed_data = None
            else:
                parsed_data = data
        else:
            parsed_data = data

        if isinstance(parsed_data, list) and len(parsed_data) > 0:
            if isinstance(parsed_data[0], dict):
                cards = [object_to_card(obj) for obj in parsed_data[:20]]
                return ListComponent(items=cards)
            else:
                preview = ', '.join(str(x)[:50] for x in parsed_data[:5])
                if len(parsed_data) > 5:
                    preview += f"... ({len(parsed_data)} total)"
                return BannerComponent(
                    type="info",
                    message=preview,
                    icon="📋"
                )

        elif isinstance(parsed_data, dict):
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

            if len(parsed_data) < 5:
                keyvalues = object_to_keyvalue_grid(parsed_data)
                if len(keyvalues) == 1:
                    return BannerComponent(
                        type="success",
                        message=f"{keyvalues[0].key}: {keyvalues[0].value}",
                        icon="✓"
                    )
                else:
                    return CardComponent(
                        title="Result",
                        subtitle=None,
                        icon="📋",
                        metadata=keyvalues
                    )

            else:
                return object_to_card(parsed_data)

        elif isinstance(parsed_data, str):
            cleaned = strip_html(parsed_data)
            cleaned = truncate_text(cleaned, max_length=200)
            return BannerComponent(
                type="info",
                message=cleaned,
                icon="📄"
            )

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
