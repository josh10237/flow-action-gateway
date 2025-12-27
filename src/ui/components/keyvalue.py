"""
Key-Value component
"""
from pydantic import BaseModel
from textual.widgets import Static
from rich.text import Text


class KeyValueComponent(BaseModel):
    component: str = "keyvalue"
    key: str
    value: str


class KeyValueWidget(Static):
    def __init__(self, kv: KeyValueComponent, **kwargs):
        super().__init__(**kwargs)
        self.kv = kv

    def render(self) -> Text:
        text = Text()
        text.append(f"{self.kv.key}: ", style="dim cyan")
        text.append(self.kv.value, style="white")
        return text
