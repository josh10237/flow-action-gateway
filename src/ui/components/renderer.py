"""
Component renderer - converts component schemas to Textual widgets.
"""
from typing import Any
from textual.widgets import Static
from .banner import BannerComponent, BannerWidget
from .card import CardComponent, CardWidget
from .list import ListComponent, ListWidget
from .keyvalue import KeyValueComponent, KeyValueWidget
from .link import LinkComponent, LinkWidget
from .file import FileComponent, FileWidget


def render_component(component: Any) -> Static:
    """
    Render a component to a Textual widget.

    Args:
        component: Component schema instance

    Returns:
        Textual widget
    """
    if isinstance(component, BannerComponent):
        return BannerWidget(component)
    elif isinstance(component, CardComponent):
        return CardWidget(component)
    elif isinstance(component, ListComponent):
        return ListWidget(component)
    elif isinstance(component, KeyValueComponent):
        return KeyValueWidget(component)
    elif isinstance(component, LinkComponent):
        return LinkWidget(component)
    elif isinstance(component, FileComponent):
        return FileWidget(component)
    else:
        # Fallback: display as string
        return Static(str(component))
