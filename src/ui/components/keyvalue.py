"""
Key-Value component - displays a key-value pair.

Schema fields:
- key (required): Label text
- value (required): Value text
"""
from pydantic import BaseModel
from textual.widgets import Static
from rich.text import Text


class KeyValueComponent(BaseModel):
    """Key-Value component schema."""
    component: str = "keyvalue"
    key: str
    value: str


class KeyValueWidget(Static):
    """Textual widget for rendering a key-value pair."""

    def __init__(self, kv: KeyValueComponent, **kwargs):
        super().__init__(**kwargs)
        self.kv = kv

    def render(self) -> Text:
        """Render the key-value pair."""
        text = Text()
        text.append(f"{self.kv.key}: ", style="dim cyan")
        text.append(self.kv.value, style="white")
        return text
