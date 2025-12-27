"""
Link component
"""
from pydantic import BaseModel
from textual.widgets import Button
import webbrowser


class LinkComponent(BaseModel):
    component: str = "link"
    text: str
    url: str


class LinkWidget(Button):
    def __init__(self, link: LinkComponent, **kwargs):
        label = f"🔗 {link.text}"
        super().__init__(label, **kwargs)
        self.link = link
        self.styles.margin = (0, 0, 1, 0)

    def on_button_pressed(self) -> None:
        try:
            webbrowser.open(self.link.url)
        except Exception:
            pass
