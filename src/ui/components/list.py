"""
List component - scrollable list of items (cards, banners, etc).

Schema fields:
- items (required): List of components
"""
from pydantic import BaseModel
from typing import List, Any
from textual.containers import VerticalScroll


class ListComponent(BaseModel):
    """List component schema."""
    class Config:
        arbitrary_types_allowed = True

    component: str = "list"
    items: List[Any]  # List of other components


class ListWidget(VerticalScroll):
    """Textual widget for rendering a scrollable list."""

    def __init__(self, list_component: ListComponent, **kwargs):
        super().__init__(**kwargs)
        self.list_component = list_component

    def compose(self):
        """Compose the list items."""
        from .renderer import render_component

        for item in self.list_component.items:
            # If item is already a widget, yield it directly
            # Otherwise, render it as a component
            if hasattr(item, 'render') or hasattr(item, 'compose'):
                yield item
            else:
                yield render_component(item)
