from collections.abc import Mapping
from typing import Any

from ..contracts import ToolContext, ToolResult


class WebSearchTool:
    name = "web_search"
    description = "Find and explain current or recently changed information from the live web."

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    def run(
        self,
        query: str,
        context: ToolContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        try:
            result = self.agent.run(query)
        except Exception:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="The web search could not be completed.",
                error="Web search workflow failed",
            )

        citations = [
            {
                "title": item.title,
                "url": item.url,
                "snippet": item.snippet,
            }
            for item in result.results
        ]
        return ToolResult(
            tool_name=self.name,
            ok=True,
            content=result.answer,
            structured_data={
                "query": result.query,
                "search_query": result.search_query,
                "results": citations,
            },
            citations=citations,
        )
