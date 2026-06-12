import json
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from models.schemas import ResearchReport, ResearchTask, Source
from agents.task_decomposer import TaskDecomposer
from tools.web_search import SearchTool
from tools.content_fetcher import _is_private_or_local_host
from tools.report_generator import generate_markdown, _parse_markdown_sections, _slugify, markdown_to_pdf
from config import is_configured_value


class TestDecomposer:
    """Task decomposition parsing tests; no API key required for parsing."""

    @pytest.fixture
    def decomposer(self):
        return TaskDecomposer(api_key="sk-test", model="test-model")

    def test_parse_json_array(self, decomposer):
        output = '["Subtopic A", "Subtopic B", "Subtopic C"]'
        result = decomposer._parse_subtopics(output)
        assert result == ["Subtopic A", "Subtopic B", "Subtopic C"]

    def test_parse_json_object_with_subtopics_key(self, decomposer):
        output = '{"subtopics": ["Angle 1", "Angle 2", "Angle 3"]}'
        result = decomposer._parse_subtopics(output)
        assert result == ["Angle 1", "Angle 2", "Angle 3"]

    def test_parse_markdown_code_fenced_json(self, decomposer):
        output = '```json\n["Topic X", "Topic Y"]\n```'
        result = decomposer._parse_subtopics(output)
        assert result == ["Topic X", "Topic Y"]

    def test_parse_fallback_numbered_list(self, decomposer):
        output = "1. First topic\n2. Second topic\n3. Third topic"
        result = decomposer._parse_subtopics(output)
        assert len(result) == 3
        assert "First topic" in result
        assert "Second topic" in result

    def test_fallback_decompose(self, decomposer):
        result = decomposer._fallback_decompose("AI Safety", 3)
        assert len(result) == 3
        assert all("AI Safety" in r for r in result)

    def test_build_prompt_keeps_json_example_literal(self, decomposer):
        prompt = decomposer._build_prompt("AI Safety", 3, 4, "quick")
        assert '{"subtopics": [' in prompt


class TestConfig:
    def test_placeholder_values_are_not_configured(self):
        assert not is_configured_value("")
        assert not is_configured_value("your_deepseek_api_key")
        assert not is_configured_value("your_tavily_api_key")
        assert not is_configured_value("provider-your-key")
        assert not is_configured_value("https://your-project.supabase.co")

    def test_realistic_values_are_configured(self):
        assert is_configured_value("deepseek_live_value_123")
        assert is_configured_value("tavily_live_value_123")
        assert is_configured_value("https://abc123.supabase.co")


class TestSearchTool:
    class FakeDDGS:
        def text(self, query, max_results=5):
            return [
                {
                    "href": f"https://example.com/{i}",
                    "title": f"Result {i}",
                    "body": f"Snippet {i} for {query}",
                }
                for i in range(max_results)
            ]

    @pytest.fixture
    def search(self):
        return SearchTool(api_key="", ddgs_client=TestSearchTool.FakeDDGS())

    def test_search_empty_query(self, search):
        assert search.search("") == []
        assert search.search("   ") == []

    def test_search_returns_mocked_results(self, search):
        results = search.search("Python programming", max_results=3)
        assert isinstance(results, list)
        assert len(results) == 3
        for r in results:
            assert "url" in r
            assert "title" in r
            assert "content" in r

    def test_search_clamps_result_count(self, search):
        results = search.search("Python programming", max_results=50)
        assert len(results) == 10


class TestContentFetcherSafety:
    def test_rejects_private_and_local_hosts(self):
        assert _is_private_or_local_host("localhost")
        assert _is_private_or_local_host("127.0.0.1")
        assert _is_private_or_local_host("10.0.0.8")
        assert _is_private_or_local_host("192.168.1.10")
        assert not _is_private_or_local_host("example.com")


class TestReportGenerator:
    def test_generate_markdown_basic(self):
        report = ResearchReport(
            id="r1",
            topic="Test Topic",
            subtopics=["Overview", "Details"],
            depth="standard",
            tasks=[
                ResearchTask(
                    id="t1",
                    subtopic="Overview",
                    summary="This is a test summary for Overview.",
                    sources=[Source(url="https://example.com", title="Test Source", snippet="A test snippet.")],
                    status="complete",
                ),
                ResearchTask(
                    id="t2",
                    subtopic="Details",
                    summary="Detailed findings here.",
                    sources=[],
                    status="complete",
                ),
            ],
            status="complete",
        )
        md = generate_markdown(report)
        assert "# Research Report: Test Topic" in md
        assert "## Overview" in md
        assert "## Details" in md
        assert "## Table of Contents" in md
        assert "## Key Takeaways" in md
        assert "## References" in md
        assert "standard" in md.lower()

    def test_generate_markdown_empty(self):
        report = ResearchReport(id="r2", topic="", subtopics=[], tasks=[])
        md = generate_markdown(report)
        assert "No topic provided" in md

    def test_slugify(self):
        assert _slugify("Hello World") == "hello-world"
        assert _slugify("AI & ML: Future Trends") == "ai-ml-future-trends"

    def test_parse_markdown_sections(self):
        md = "# Main Title\n\n## Section A\n\n- bullet 1\n- bullet 2\n\n## Section B\n\nSome text here."
        sections = _parse_markdown_sections(md)
        assert len(sections) >= 2


class TestLLMClient:
    def test_deepseek_client_initialization(self):
        from llm.client import LLMClient
        client = LLMClient(provider="deepseek", api_key="sk-test", model="deepseek-chat")
        assert client.provider == "deepseek"
        assert client.model == "deepseek-chat"
