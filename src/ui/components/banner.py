"""
Banner component
"""
from pydantic import BaseModel
from typing import Optional, Literal
from textual.widgets import Static
from rich.text import Text


class BannerComponent(BaseModel):
    component: str = "banner"
    type: Literal["success", "error", "info"]
    message: str
    icon: Optional[str] = None


class BannerWidget(Static):
    def __init__(self, banner: BannerComponent, **kwargs):
        super().__init__(**kwargs)
        self.banner = banner

    def render(self) -> Text:
        text = Text()

        if self.banner.type == "success":
            style = "green"
            default_icon = "✓"
        elif self.banner.type == "error":
            style = "red"
            default_icon = "✗"
        else:
            style = "blue"
            default_icon = "ℹ"

        icon = self.banner.icon or default_icon
        text.append(f"{icon} ", style=style)
        text.append(self.banner.message, style=style)

        return text
