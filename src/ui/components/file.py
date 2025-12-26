"""
File component - displays file information.

Schema fields:
- name (required): File name
- path (optional): File path
- size (optional): File size
- modified (optional): Last modified date
"""
from pydantic import BaseModel
from typing import Optional
from textual.widgets import Static
from rich.text import Text


class FileComponent(BaseModel):
    """File component schema."""
    component: str = "file"
    name: str
    path: Optional[str] = None
    size: Optional[str] = None
    modified: Optional[str] = None


class FileWidget(Static):
    """Textual widget for rendering a file."""

    def __init__(self, file: FileComponent, **kwargs):
        super().__init__(**kwargs)
        self.file = file

    def render(self) -> Text:
        """Render the file info."""
        text = Text()
        text.append("📄 ", style="yellow")
        text.append(self.file.name, style="white bold")

        if self.file.path:
            text.append(f"\n   Path: {self.file.path}", style="dim white")
        if self.file.size:
            text.append(f"\n   Size: {self.file.size}", style="dim cyan")
        if self.file.modified:
            text.append(f"\n   Modified: {self.file.modified}", style="dim cyan")

        return text
