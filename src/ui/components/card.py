"""
Card component
"""
from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING
from textual.widgets import Label
from textual.containers import Vertical
from rich.text import Text

if TYPE_CHECKING:
    from .keyvalue import KeyValueComponent
    from .link import LinkComponent


class CardComponent(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    component: str = "card"
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    metadata: Optional[List] = None
    link: Optional[object] = None


class CardWidget(Vertical):
    def __init__(self, card: CardComponent, **kwargs):
        super().__init__(**kwargs)
        self.card = card
        self.border_title = self._build_title()
        self.styles.border = ("solid", "blue")
        self.styles.padding = (1, 2)
        self.styles.margin = (0, 0, 1, 0)
        self.styles.height = "auto"
        self.styles.min_height = 3

    def _build_title(self) -> str:
        title = self.card.title

        if self.card.icon:
            title = f"{self.card.icon} {title}"

        return title

    def compose(self):
        from .keyvalue import KeyValueWidget, KeyValueComponent
        from .link import LinkWidget, LinkComponent

        if self.card.subtitle:
            yield Label(self.card.subtitle, classes="card-subtitle")

        if self.card.metadata:
            for kv in self.card.metadata:
                if isinstance(kv, KeyValueComponent):
                    yield KeyValueWidget(kv)
                else:
                    text = Text()
                    text.append(f"{kv.get('key', '')}: ", style="dim")
                    text.append(kv.get('value', ''), style="white")
                    yield Label(text)

        if self.card.link:
            if isinstance(self.card.link, LinkComponent):
                yield LinkWidget(self.card.link)
            else:
                text = Text()
                text.append("🔗 ", style="blue")
                text.append(self.card.link.get('text', ''), style="blue underline")
                text.append(f" ({self.card.link.get('url', '')})", style="dim")
                yield Label(text)
