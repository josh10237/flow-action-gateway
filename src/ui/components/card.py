"""
Card component - displays title, subtitle, metadata, and optional link.

Schema fields:
- title (required): Main heading
- subtitle (optional): Secondary text
- icon (optional): Emoji icon
- metadata (optional): List of KeyValueComponent
- link (optional): LinkComponent
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
    """Card component schema."""
    class Config:
        arbitrary_types_allowed = True

    component: str = "card"
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    metadata: Optional[List] = None  # List[KeyValueComponent]
    link: Optional[object] = None  # LinkComponent


class CardWidget(Vertical):
    """Textual widget for rendering a card."""

    def __init__(self, card: CardComponent, **kwargs):
        super().__init__(**kwargs)
        self.card = card
        self.border_title = self._build_title()
        self.styles.border = ("solid", "blue")
        self.styles.padding = (1, 2)
        self.styles.margin = (0, 0, 1, 0)
        self.styles.height = "auto"  # Allow card to expand to fit content
        self.styles.min_height = 3  # Ensure cards are never collapsed

    def _build_title(self) -> str:
        """Build the border title with optional icon."""
        title = self.card.title

        # Add icon
        if self.card.icon:
            title = f"{self.card.icon} {title}"

        return title

    def compose(self):
        """Compose the card contents."""
        from .keyvalue import KeyValueWidget, KeyValueComponent
        from .link import LinkWidget, LinkComponent

        # Subtitle
        if self.card.subtitle:
            yield Label(self.card.subtitle, classes="card-subtitle")

        # Metadata key-value pairs
        if self.card.metadata:
            for kv in self.card.metadata:
                if isinstance(kv, KeyValueComponent):
                    yield KeyValueWidget(kv)
                else:
                    # Fallback for dict format
                    text = Text()
                    text.append(f"{kv.get('key', '')}: ", style="dim")
                    text.append(kv.get('value', ''), style="white")
                    yield Label(text)

        # Link
        if self.card.link:
            if isinstance(self.card.link, LinkComponent):
                yield LinkWidget(self.card.link)
            else:
                # Fallback for dict format
                text = Text()
                text.append("🔗 ", style="blue")
                text.append(self.card.link.get('text', ''), style="blue underline")
                text.append(f" ({self.card.link.get('url', '')})", style="dim")
                yield Label(text)
