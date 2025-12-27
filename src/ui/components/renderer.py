"""
Component renderer
"""
from typing import Any
from textual.widgets import Static
from .banner import BannerComponent, BannerWidget
from .card import CardComponent, CardWidget
from .list import ListComponent, ListWidget
from .keyvalue import KeyValueComponent, KeyValueWidget
from .link import LinkComponent, LinkWidget


def render_component(component: Any) -> Static:
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
    else:
        return Static(str(component))
