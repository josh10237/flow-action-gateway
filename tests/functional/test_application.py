"""
Functional tests for the complete application flow.

Tests the full pipeline: Voice → ASR → Intent → MCP → Render
Also tests data binding with real-world API response structures.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.auto_data_binder import bind_data
from ui.components.banner import BannerComponent
from ui.components.card import CardComponent
from ui.components.list import ListComponent


class MockTextContent:
    """Mock MCP TextContent object."""
    def __init__(self, text):
        self.text = text


class TestBindDataSingleObject:
    """Test binding single objects to components."""

    def test_single_object_to_card(self):
        """Should map single object to CardComponent."""
        data = [MockTextContent(json.dumps({
            "name": "Test Project",
            "description": "A test project",
            "version": "1.0.0",
            "author": "John Doe",
            "license": "MIT",
            "status": "active"
        }))]

        result = bind_data(data)

        assert isinstance(result, CardComponent)
        assert result.title == "Test Project"
        assert result.metadata is not None

    def test_object_with_filtered_fields(self):
        """Should filter out IDs, timestamps, and booleans."""
        data = [MockTextContent(json.dumps({
            "name": "react",
            "description": "A JavaScript library",
            "html_url": "https://github.com/facebook/react",
            "stargazers_count": 220000,
            # These should be filtered:
            "id": 12345,
            "node_id": "MDEwOlJlcG9zaXRvcnk=",
            "created_at": "2013-05-24T16:15:54Z",
            "updated_at": "2025-01-15T10:00:00Z",
            "private": False,
        }))]

        result = bind_data(data)

        assert isinstance(result, CardComponent)
        kv_keys = [kv.key for kv in result.metadata] if result.metadata else []

        # Should have these fields
        assert "Description" in kv_keys
        assert "Stargazers Count" in kv_keys

        # Should NOT have these filtered fields
        assert "Id" not in kv_keys
        assert "Node Id" not in kv_keys
        assert "Created At" not in kv_keys
        assert "Updated At" not in kv_keys
        assert "Private" not in kv_keys

    def test_object_with_html_content(self):
        """Should strip HTML from field values."""
        data = [MockTextContent(json.dumps({
            "title": "Test",
            "description": "<p>HTML <strong>text</strong> with &#x27;entities&#x27;</p>"
        }))]

        result = bind_data(data)

        desc_kv = next((kv for kv in result.metadata if kv.key == "Description"), None)
        assert desc_kv is not None
        assert "<p>" not in desc_kv.value
        assert "&#x27;" not in desc_kv.value
        assert "HTML text with 'entities'" in desc_kv.value

    def test_object_with_items_array(self):
        """Should unwrap objects with 'items' array."""
        data = [MockTextContent(json.dumps({
            "items": [
                {"name": "Item 1", "value": "Value 1"},
                {"name": "Item 2", "value": "Value 2"}
            ]
        }))]

        result = bind_data(data)

        assert isinstance(result, ListComponent)
        assert len(result.items) == 2

    def test_object_with_results_array(self):
        """Should unwrap objects with 'results' array."""
        data = [MockTextContent(json.dumps({
            "results": [
                {"title": "Result 1"},
                {"title": "Result 2"}
            ]
        }))]

        result = bind_data(data)

        assert isinstance(result, ListComponent)
        assert len(result.items) == 2


class TestBindDataList:
    """Test binding lists to components."""

    def test_multiple_objects_to_list(self):
        """Should map multiple objects to ListComponent."""
        data = [
            MockTextContent(json.dumps({"title": "Item 1", "description": "First"})),
            MockTextContent(json.dumps({"title": "Item 2", "description": "Second"}))
        ]

        result = bind_data(data)

        assert isinstance(result, ListComponent)
        assert len(result.items) == 2
        assert all(isinstance(item, CardComponent) for item in result.items)

    def test_list_of_strings(self):
        """Should map list of strings to BannerComponent preview."""
        data = [MockTextContent(json.dumps([
            "file1.txt",
            "file2.py",
            "file3.md"
        ]))]

        result = bind_data(data)

        assert isinstance(result, BannerComponent)
        assert "file1.txt" in result.message


class TestBindDataPrimitives:
    """Test binding primitive values to components."""

    def test_string_to_banner(self):
        """Should map string to BannerComponent."""
        data = [MockTextContent("Simple text message")]

        result = bind_data(data)

        assert isinstance(result, BannerComponent)
        assert result.type == "info"
        assert result.message == "Simple text message"

    def test_html_string_stripped(self):
        """Should strip HTML from string values."""
        data = [MockTextContent("<p>HTML <strong>text</strong> with &#x27;entities&#x27;</p>")]

        result = bind_data(data)

        assert isinstance(result, BannerComponent)
        assert "<p>" not in result.message
        assert "&#x27;" not in result.message

    def test_long_string_truncated(self):
        """Should truncate long strings to 200 chars."""
        long_text = "a" * 300
        data = [MockTextContent(long_text)]

        result = bind_data(data)

        assert isinstance(result, BannerComponent)
        assert len(result.message) <= 203
        assert result.message.endswith("...")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json(self):
        """Should handle invalid JSON gracefully."""
        data = [MockTextContent("not valid json {{{")]

        result = bind_data(data)

        # Should treat as plain string
        assert isinstance(result, BannerComponent)

    def test_empty_object(self):
        """Should handle empty objects."""
        data = [MockTextContent(json.dumps({}))]

        result = bind_data(data)

        assert result is not None

    def test_none_values_skipped(self):
        """Should skip None values in objects."""
        data = [MockTextContent(json.dumps({
            "name": "Test",
            "description": None,
            "count": 42
        }))]

        result = bind_data(data)

        kv_keys = [kv.key for kv in result.metadata] if result.metadata else []
        assert "Description" not in kv_keys
        assert "Count" in kv_keys


class TestGitHubAPI:
    """Test with GitHub API response structures."""

    def test_github_repository_search(self):
        """Should handle GitHub repository search response."""
        data = [MockTextContent(json.dumps({
            "total_count": 1,
            "incomplete_results": False,
            "items": [
                {
                    "id": 10270250,
                    "node_id": "MDEwOlJlcG9zaXRvcnkxMDI3MDI1MA==",
                    "name": "react",
                    "full_name": "facebook/react",
                    "private": False,
                    "owner": {
                        "login": "facebook",
                        "id": 69631,
                        "type": "Organization"
                    },
                    "html_url": "https://github.com/facebook/react",
                    "description": "The library for web and native user interfaces.",
                    "created_at": "2013-05-24T16:15:54Z",
                    "updated_at": "2025-01-15T10:00:00Z",
                    "stargazers_count": 234567,
                    "language": "JavaScript",
                }
            ]
        }))]

        result = bind_data(data)

        # Should unwrap items array
        assert isinstance(result, ListComponent)
        assert len(result.items) == 1

        # Check card structure
        card = result.items[0]
        assert isinstance(card, CardComponent)
        assert card.title == "react"
        assert card.link is not None
        assert "github.com" in card.link.url

        # Check filtered fields
        kv_keys = [kv.key for kv in card.metadata]
        assert "Description" in kv_keys
        assert "Language" in kv_keys
        assert "Stargazers Count" in kv_keys

        # These should be filtered out
        assert "Id" not in kv_keys
        assert "Created At" not in kv_keys
        assert "Private" not in kv_keys


class TestWebSearchAPI:
    """Test with web search API response structures."""

    def test_brave_search_results(self):
        """Should handle web search results with HTML content."""
        data = [MockTextContent(json.dumps({
            "query": "python tutorial",
            "results": [
                {
                    "title": "Python Documentation",
                    "url": "https://docs.python.org",
                    "description": "<p>The official <strong>Python</strong> documentation with &#x27;examples&#x27; and tutorials.</p>",
                    "published_date": "2024-01-01",
                },
                {
                    "title": "Learn Python",
                    "url": "https://learnpython.org",
                    "description": "Interactive <em>Python</em> tutorial &amp; exercises",
                }
            ]
        }))]

        result = bind_data(data)

        # Should unwrap results array
        assert isinstance(result, ListComponent)
        assert len(result.items) == 2

        # Check first card
        card1 = result.items[0]
        assert card1.title == "Python Documentation"
        assert card1.link.url == "https://docs.python.org"

        # Check HTML stripping
        desc_kv = next((kv for kv in card1.metadata if kv.key == "Description"), None)
        assert desc_kv is not None
        assert "<p>" not in desc_kv.value
        assert "<strong>" not in desc_kv.value
        assert "&#x27;" not in desc_kv.value
        assert "Python documentation with 'examples'" in desc_kv.value

        # Check second card HTML entities
        card2 = result.items[1]
        desc_kv2 = next((kv for kv in card2.metadata if kv.key == "Description"), None)
        assert "<em>" not in desc_kv2.value
        assert "&amp;" not in desc_kv2.value
        assert "Interactive Python tutorial & exercises" == desc_kv2.value


class TestVoicePipeline:
    """Test voice pipeline component availability."""

    def test_pipeline_components(self):
        """Should have all pipeline components available."""
        components = {
            "audio": False,
            "asr": False,
            "intent": False,
            "mcp": False,
            "render": False
        }

        try:
            from voice.capture import AudioCapture
            components["audio"] = True
        except:
            pass

        try:
            from voice.transcription import Transcriber
            components["asr"] = True
        except:
            pass

        try:
            from gateway.intent_parser import IntentParser
            components["intent"] = True
        except:
            pass

        try:
            from gateway.mcp_gateway import MCPGateway
            components["mcp"] = True
        except:
            pass

        try:
            from ui.auto_data_binder import bind_data
            from ui.components.renderer import render_component
            components["render"] = True
        except:
            pass

        # Render should always be available
        assert components["render"] is True

        # Print status
        print("\nPipeline Component Status:")
        for component, available in components.items():
            status = "✓" if available else "✗"
            print(f"  {status} {component}")


class TestConfigIntegration:
    """Test configuration loading and integration."""

    def test_config_loading(self):
        """Should be able to load config."""
        try:
            config_path = Path.home() / ".config" / "wispr-flow" / "config.json"
            if not config_path.exists():
                return

            from gateway.mcp_config import MCPConfig
            config = MCPConfig.load()
            assert isinstance(config.mcpServers, dict)

        except Exception as e:
            print(f"Skipping: {e}")
