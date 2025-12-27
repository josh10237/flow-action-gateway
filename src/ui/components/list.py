"""
List component
"""
from pydantic import BaseModel
from typing import List, Any
from textual.containers import Vertical


class ListComponent(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    component: str = "list"
    items: List[Any]


class ListWidget(Vertical):
    def __init__(self, list_component: ListComponent, **kwargs):
        super().__init__(**kwargs)
        self.list_component = list_component

    def compose(self):
        from .renderer import render_component

        for item in self.list_component.items:
            if hasattr(item, 'render') or hasattr(item, 'compose'):
                yield item
            else:
                yield render_component(item)
