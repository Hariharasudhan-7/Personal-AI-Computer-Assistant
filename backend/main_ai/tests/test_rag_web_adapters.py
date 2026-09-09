from types import SimpleNamespace

from backend.main_ai.adapters.rag import RAGTool
from backend.main_ai.adapters.web_search import WebSearchTool
from backend.main_ai.contracts import ToolContext


def context(*attachment_ids: str) -> ToolContext:
    return ToolContext("user", "conversation", "message", attachment_ids)


def test_rag_requires_uploaded_document():
    answerer = lambda **kwargs: ("answer", [])
    tool = RAGTool(lambda attachment_id: object(), answerer)

    result = tool.run("What is this?", context())

    assert result.ok is False
    assert result.error == "RAG requires an attachment"


def test_rag_answers_from_selected_document_and_returns_citations():
    calls = []
    document = SimpleNamespace(metadata={"source": "paper.pdf", "page": 3})

    def answerer(**kwargs):
        calls.append(kwargs)
        return "Supported answer", [document]

    tool = RAGTool(lambda attachment_id: "retriever", answerer)
    result = tool.run("What does it say?", context("doc-1"))

    assert result.ok is True
    assert result.content == "Supported answer"
    assert result.citations == [{"source": "paper.pdf", "page": "3"}]
    assert calls[0]["retriever"] == "retriever"
    assert calls[0]["query"] == "What does it say?"


def test_rag_rejects_multiple_documents_for_strict_scope():
    tool = RAGTool(lambda attachment_id: object(), lambda **kwargs: ("answer", []))

    result = tool.run("Compare these", context("doc-1", "doc-2"))

    assert result.ok is False
    assert result.error == "RAG requires exactly one attachment"


def test_web_search_normalizes_answer_and_citations():
    search_result = SimpleNamespace(
        query="latest news",
        search_query="latest news today",
        answer="Current answer",
        results=[SimpleNamespace(title="Source", url="https://example.com", snippet="Evidence")],
    )
    agent = SimpleNamespace(run=lambda query: search_result)

    result = WebSearchTool(agent).run("What happened today?", context())

    assert result.ok is True
    assert result.content == "Current answer"
    assert result.citations == [{
        "title": "Source",
        "url": "https://example.com",
        "snippet": "Evidence",
    }]
    assert result.structured_data["search_query"] == "latest news today"


def test_web_search_failure_is_safe():
    agent = SimpleNamespace(run=lambda query: (_ for _ in ()).throw(RuntimeError("network")))

    result = WebSearchTool(agent).run("search", context())

    assert result.ok is False
    assert result.error == "Web search workflow failed"
