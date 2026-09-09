from collections.abc import Mapping
from typing import Any

from ..contracts import ToolContext, ToolResult


class FileAutomationTool:
    name = "file_automation"
    description = "Create, read, modify, search, organize, or manage local files and folders."

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    def run(
        self,
        query: str,
        context: ToolContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        try:
            result = self.agent.process_command(query)
        except Exception as error:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="File automation could not complete the request.",
                error=f"File automation failed: {error}",
            )
        tool_results = result.get("tool_results", [])
        failure = next((item.get("error") for item in tool_results if not item.get("ok") and item.get("error")), None)
        message = str(result.get("response", ""))
        if not message and failure:
            message = "File automation could not complete the request."
        return ToolResult(
            tool_name=self.name,
            ok=bool(result.get("ok", False)),
            content=message,
            structured_data={"tool_results": tool_results},
            error=failure,
        )
