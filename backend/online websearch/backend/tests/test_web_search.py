from unittest.mock import Mock

import pytest

from app.config import Settings
from app.models.schemas import SearchResult
from app.services.duckduckgo_service import DuckDuckGoService
from app.services.gemini_service import GeminiService
from app.services.web_search_agent import WebSearchAgent, WebSearchAgentError


class FakeGemini:
    def __init__(self):
        self.calls = []

    def generate_search_query(self, query):
        self.calls.append(("query", query))
        return "latest ai developments"

    def generate_final_answer(self, query, search_query, results):
        self.calls.append(("answer", query, search_query, results))
        return "Gemini answer"


def make_agent():
    gemini = FakeGemini()
    search = Mock()
    search.search.return_value = [
        SearchResult(title=f"Result {index}", url=f"https://example.com/{index}", snippet="Useful")
        for index in range(5)
    ]
    return WebSearchAgent(Settings(), gemini, search), gemini, search


@pytest.fixture(autouse=True)
def configure_settings(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")


def test_complete_web_search_workflow():
    agent, _, _ = make_agent()
    response = agent.run("latest AI developments")
    assert response.search_required is True
    assert len(response.results) == 5
    assert response.answer == "Gemini answer"


def test_search_query_generation_and_search():
    agent, gemini, search = make_agent()
    result = agent.run("What happened in AI today?")
    assert result.search_required is True
    assert result.search_query == "latest ai developments"
    assert [call[0] for call in gemini.calls] == ["query", "answer"]
    search.search.assert_called_once_with("latest ai developments")


def test_duckduckgo_result_cleaning_and_top_five():
    client = Mock(return_value=[
        {"title": f"Title {index}", "href": f"https://example.com/{index}", "body": "Snippet"}
        for index in range(8)
    ])
    results = DuckDuckGoService(Settings(), search_client=client).search("query")
    assert len(results) == 5
    assert results[0].title == "Title 0"
    assert results[-1].url == "https://example.com/4"


def test_gemini_query_and_final_response():
    client = Mock()
    client.models.generate_content.side_effect = [
        Mock(text="current AI news"),
        Mock(text="AI answer with sources"),
    ]
    service = GeminiService(Settings(gemini_api_key="test-key"), client=client)
    assert service.generate_search_query("latest AI") == "current AI news"
    assert service.generate_final_answer("latest AI", "current AI news", []) == "AI answer with sources"


def test_search_error_is_handled():
    agent, _, search = make_agent()
    search.search.side_effect = RuntimeError("network unavailable")
    with pytest.raises(WebSearchAgentError, match="Web-search request could not be completed"):
        agent.run("latest AI")
