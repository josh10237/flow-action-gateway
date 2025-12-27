"""
Unit tests for field filtering logic.

Tests should_skip_field, is_url_field, format_field_name, and infer_icon.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.auto_data_binder import should_skip_field, is_url_field, format_field_name, infer_icon


class TestFieldSkipping:
    """Test field filtering logic."""

    def test_skip_boolean_fields(self):
        """Should skip boolean values."""
        assert should_skip_field("private", True) is True
        assert should_skip_field("is_active", False) is True
        assert should_skip_field("enabled", True) is True

    def test_skip_id_field(self):
        """Should skip 'id' field."""
        assert should_skip_field("id", 12345) is True
        assert should_skip_field("ID", "abc123") is True

    def test_skip_underscore_id_fields(self):
        """Should skip fields ending in _id."""
        assert should_skip_field("user_id", 67890) is True
        assert should_skip_field("repo_id", "abc123") is True
        assert should_skip_field("parent_id", 999) is True

    def test_skip_special_id_fields(self):
        """Should skip special ID fields like node_id, gravatar_id."""
        assert should_skip_field("node_id", "MDQ6VXNlcjE=") is True
        assert should_skip_field("gravatar_id", "abc123") is True

    def test_skip_timestamp_fields(self):
        """Should skip fields ending in _at (timestamps)."""
        assert should_skip_field("created_at", "2025-01-01T00:00:00Z") is True
        assert should_skip_field("updated_at", "2025-01-01T00:00:00Z") is True
        assert should_skip_field("published_at", "2025-01-01T00:00:00Z") is True
        assert should_skip_field("pushed_at", "2025-01-01T00:00:00Z") is True
        assert should_skip_field("deleted_at", "2025-01-01T00:00:00Z") is True

    def test_skip_technical_metadata(self):
        """Should skip technical metadata fields."""
        assert should_skip_field("sha", "abc123def456") is True
        assert should_skip_field("etag", 'W/"abc123"') is True

    def test_keep_normal_fields(self):
        """Should not skip normal fields."""
        assert should_skip_field("name", "John") is False
        assert should_skip_field("description", "A great project") is False
        assert should_skip_field("count", 42) is False
        assert should_skip_field("status", "active") is False
        assert should_skip_field("title", "My Project") is False

    def test_keep_fields_with_at_not_at_end(self):
        """Should not skip fields that contain 'at' but don't end with _at."""
        assert should_skip_field("category", "software") is False
        assert should_skip_field("location", "Seattle") is False


class TestURLDetection:
    """Test URL field detection."""

    def test_detect_url_by_field_name_url(self):
        """Should detect fields named 'url'."""
        assert is_url_field("url", "https://example.com") is True
        assert is_url_field("URL", "https://example.com") is True

    def test_detect_url_by_field_name_containing_url(self):
        """Should detect fields containing 'url' in name."""
        assert is_url_field("html_url", "https://example.com") is True
        assert is_url_field("avatar_url", "https://example.com") is True
        assert is_url_field("api_url", "https://example.com") is True

    def test_detect_url_by_field_name_link(self):
        """Should detect fields named 'link' or containing 'link'."""
        assert is_url_field("link", "https://example.com") is True
        assert is_url_field("permalink", "https://example.com") is True

    def test_detect_url_by_field_name_href(self):
        """Should detect fields named 'href'."""
        assert is_url_field("href", "https://example.com") is True

    def test_detect_url_by_https_prefix(self):
        """Should detect URLs by https:// prefix."""
        assert is_url_field("website", "https://example.com") is True
        assert is_url_field("homepage", "https://example.com") is True

    def test_detect_url_by_http_prefix(self):
        """Should detect URLs by http:// prefix."""
        assert is_url_field("website", "http://example.com") is True

    def test_not_detect_non_url_string(self):
        """Should not detect non-URL strings."""
        assert is_url_field("name", "example") is False
        assert is_url_field("description", "Not a URL") is False

    def test_not_detect_non_string(self):
        """Should not detect non-string values as URLs."""
        assert is_url_field("count", 42) is False
        assert is_url_field("enabled", True) is False
        assert is_url_field("data", {"key": "value"}) is False


class TestFieldNameFormatting:
    """Test field name formatting."""

    def test_format_snake_case_two_words(self):
        """Should convert snake_case to Title Case."""
        assert format_field_name("full_name") == "Full Name"
        assert format_field_name("first_name") == "First Name"

    def test_format_snake_case_multiple_words(self):
        """Should convert multi-word snake_case."""
        assert format_field_name("stargazers_count") == "Stargazers Count"
        assert format_field_name("html_url") == "Html Url"
        assert format_field_name("api_base_url") == "Api Base Url"

    def test_format_single_word(self):
        """Should capitalize single words."""
        assert format_field_name("name") == "Name"
        assert format_field_name("description") == "Description"
        assert format_field_name("status") == "Status"

    def test_format_already_capitalized(self):
        """Should handle already capitalized words."""
        assert format_field_name("Name") == "Name"
        assert format_field_name("DESCRIPTION") == "Description"


class TestIconInference:
    """Test icon selection based on data fields."""

    def test_infer_repo_icon_repository(self):
        """Should infer repo icon for 'repository' field."""
        assert infer_icon({"repository": "test"}) == "📦"

    def test_infer_repo_icon_repo(self):
        """Should infer repo icon for 'repo' field."""
        assert infer_icon({"repo": "test"}) == "📦"

    def test_infer_repo_icon_github(self):
        """Should infer repo icon for 'github' field."""
        assert infer_icon({"github": "test"}) == "📦"

    def test_infer_search_icon_search(self):
        """Should infer search icon for 'search' field."""
        assert infer_icon({"search": "test"}) == "🔍"

    def test_infer_search_icon_query(self):
        """Should infer search icon for 'query' field."""
        assert infer_icon({"query": "test"}) == "🔍"

    def test_infer_search_icon_results(self):
        """Should infer search icon for 'results' field."""
        assert infer_icon({"results": ["item1", "item2"]}) == "🔍"

    def test_infer_file_icon_file(self):
        """Should infer file icon for 'file' field."""
        assert infer_icon({"file": "test.txt"}) == "📄"

    def test_infer_file_icon_document(self):
        """Should infer file icon for 'document' field."""
        assert infer_icon({"document": "test.pdf"}) == "📄"

    def test_infer_file_icon_path(self):
        """Should infer file icon for 'path' field."""
        assert infer_icon({"path": "/home/user/file.txt"}) == "📄"

    def test_infer_user_icon_user(self):
        """Should infer user icon for 'user' field."""
        assert infer_icon({"user": "john"}) == "👤"

    def test_infer_user_icon_author(self):
        """Should infer user icon for 'author' field."""
        assert infer_icon({"author": "jane"}) == "👤"

    def test_infer_user_icon_owner(self):
        """Should infer user icon for 'owner' field."""
        assert infer_icon({"owner": "acme"}) == "👤"

    def test_infer_error_icon_error(self):
        """Should infer error icon for 'error' field."""
        assert infer_icon({"error": "Something went wrong"}) == "⚠️"

    def test_infer_error_icon_exception(self):
        """Should infer error icon for 'exception' field."""
        assert infer_icon({"exception": "ValueError"}) == "⚠️"

    def test_infer_default_icon(self):
        """Should use default icon for unknown types."""
        assert infer_icon({"unknown": "data"}) == "📋"
        assert infer_icon({"custom_field": "value"}) == "📋"
        assert infer_icon({}) == "📋"
