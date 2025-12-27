"""
Unit tests for HTML processing utilities.

Tests strip_html and truncate_text functions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.auto_data_binder import strip_html, truncate_text


class TestHTMLStripping:
    """Test HTML tag and entity removal."""

    def test_strip_basic_tags(self):
        """Should remove basic HTML tags."""
        html = "<p>Hello <strong>world</strong></p>"
        assert strip_html(html) == "Hello world"

    def test_strip_html_entities(self):
        """Should decode HTML entities like &#x27; to '."""
        html = "Claude&#x27;s API"
        assert strip_html(html) == "Claude's API"

    def test_strip_common_entities(self):
        """Should decode common HTML entities like &amp; and &quot;."""
        html = "Test &amp; &quot;quoted&quot; text"
        assert strip_html(html) == "Test & \"quoted\" text"

    def test_strip_complex_html(self):
        """Should handle complex HTML with nested tags and entities."""
        html = "<div>Test &amp; <strong>bold</strong> &#x27;text&#x27;</div>"
        assert strip_html(html) == "Test & bold 'text'"

    def test_strip_no_html(self):
        """Should return unchanged text without HTML."""
        text = "Plain text with no tags"
        assert strip_html(text) == text

    def test_strip_whitespace_cleanup(self):
        """Should clean up excessive whitespace from HTML."""
        html = "<p>Multiple    spaces\n\n\nand newlines</p>"
        result = strip_html(html)
        assert "    " not in result
        assert "\n\n\n" not in result
        assert "Multiple spaces and newlines" == result

    def test_strip_empty_tags(self):
        """Should remove empty HTML tags."""
        html = "<p></p><div>Content</div><p></p>"
        assert strip_html(html) == "Content"


class TestTextTruncation:
    """Test text truncation logic."""

    def test_truncate_long_text(self):
        """Should truncate text longer than max length."""
        text = "a" * 300
        result = truncate_text(text, max_length=200)
        assert len(result) == 203  # 200 chars + "..."
        assert result.endswith("...")

    def test_no_truncate_short_text(self):
        """Should not truncate text shorter than max length."""
        text = "Short text"
        result = truncate_text(text, max_length=200)
        assert result == text
        assert not result.endswith("...")

    def test_truncate_exact_length(self):
        """Should not truncate text exactly at max length."""
        text = "a" * 200
        result = truncate_text(text, max_length=200)
        assert result == text

    def test_truncate_custom_length(self):
        """Should respect custom max_length parameter."""
        text = "a" * 150
        result = truncate_text(text, max_length=50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_truncate_non_string(self):
        """Should convert non-strings to strings before truncating."""
        result = truncate_text(12345, max_length=3)
        assert result == "123..."
