from collections.abc import Callable, Mapping
from typing import Any, Protocol

from .contracts import ToolContext, ToolResult


class MainAITool(Protocol):
    name: str
    description: str

    def run(self, query: str, context: ToolContext, arguments: Mapping[str, Any] | None = None) -> ToolResult:
        ...


class FunctionTool:
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable[[str, ToolContext, Mapping[str, Any]], ToolResult],
    ) -> None:
        self.name = name
        self.description = description
        self._function = function

    def run(
        self,
        query: str,
        context: ToolContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        return self._function(query, context, arguments or {})


class ToolRegistry:
    def __init__(self, tools: Mapping[str, MainAITool] | None = None) -> None:
        self._tools = dict(tools or {})

    def register(self, tool: MainAITool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> MainAITool | None:
        return self._tools.get(name)

    def descriptions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                },
            }
            for tool in self._tools.values()
        ]
