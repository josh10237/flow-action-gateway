"""
Link component - displays a clickable link.

Schema fields:
- text (required): Link text to display
- url (required): URL to link to
"""
from pydantic import BaseModel
from textual.widgets import Button
import webbrowser


class LinkComponent(BaseModel):
    """Link component schema."""
    component: str = "link"
    text: str
    url: str


class LinkWidget(Button):
    """Textual widget for rendering a clickable link."""

    def __init__(self, link: LinkComponent, **kwargs):
        # Set button label with icon and URL
        label = f"🔗 {link.text}"
        super().__init__(label, **kwargs)
        self.link = link
        self.styles.margin = (0, 0, 1, 0)

    def on_button_pressed(self) -> None:
        """Open URL in browser when clicked."""
        try:
            webbrowser.open(self.link.url)
        except Exception as e:
            # If browser open fails, just log it
            print(f"[ERROR] Failed to open URL: {e}")
