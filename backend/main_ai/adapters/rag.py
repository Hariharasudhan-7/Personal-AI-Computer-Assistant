from collections.abc import Callable, Mapping
from typing import Any

from ..contracts import ToolContext, ToolResult


class RAGTool:
    name = "rag"
    description = "Answer questions using only the contents of the user's uploaded documents."

    def __init__(
        self,
        retriever_for_attachment: Callable[[str], Any | None],
        answer_question: Callable[..., tuple[str, list[Any]]],
        chat_history_for_context: Callable[[ToolContext], list[dict[str, str]]] | None = None,
    ) -> None:
        self.retriever_for_attachment = retriever_for_attachment
        self.answer_question = answer_question
        self.chat_history_for_context = chat_history_for_context or (lambda context: [])

    def run(
        self,
        query: str,
        context: ToolContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        attachment_ids = tuple(context.attachment_ids)
        if not attachment_ids:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="Please upload a document before asking a document-specific question.",
                error="RAG requires an attachment",
            )
        if len(attachment_ids) > 1:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="Please select one document for a document-specific question.",
                error="RAG requires exactly one attachment",
            )

        retriever = self.retriever_for_attachment(attachment_ids[0])
        if retriever is None:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="That document is not ready for questions yet.",
                error="Document retriever is unavailable",
            )

        try:
            answer, documents = self.answer_question(
                query=query,
                retriever=retriever,
                chat_history=self.chat_history_for_context(context),
            )
        except Exception:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="I could not answer that question from the uploaded document.",
                error="RAG workflow failed",
            )

        citations = []
        for document in documents:
            metadata = getattr(document, "metadata", {}) or {}
            citation = {"source": str(metadata.get("source", "Unknown document"))}
            if metadata.get("page") is not None:
                citation["page"] = str(metadata["page"])
            citations.append(citation)

        return ToolResult(
            tool_name=self.name,
            ok=True,
            content=str(answer),
            structured_data={"attachment_id": attachment_ids[0]},
            citations=citations,
        )
