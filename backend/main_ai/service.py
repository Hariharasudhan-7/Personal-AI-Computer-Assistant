from collections.abc import Mapping
import json
from typing import Any, Protocol
from uuid import uuid4

from .contracts import AssistantResponse, ToolContext, ToolResult
from .persistence.repository import ConversationRepository
from .tools import ToolRegistry


class MainAILLM(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> dict[str, Any]:
        ...


class MainAI:
    def __init__(
        self,
        llm_client: MainAILLM,
        tool_registry: ToolRegistry,
        repository: ConversationRepository,
        max_tool_calls: int = 1,
    ) -> None:
        if max_tool_calls < 1:
            raise ValueError("max_tool_calls must be at least one")
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.repository = repository
        self.max_tool_calls = max_tool_calls

    def handle_message(
        self,
        *,
        user_id: str,
        conversation_id: str,
        content: str,
        attachment_ids: list[str] | None = None,
    ) -> AssistantResponse:
        query = content.strip()
        if not query:
            raise ValueError("Message content must not be empty")

        message_id = str(uuid4())
        context = ToolContext(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            attachment_ids=tuple(attachment_ids or []),
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Main AI router. Select exactly one specialist tool when the user asks "
                    "for an action or factual lookup. Always select exactly one tool for actionable requests. "
                    "Use file_automation for creating, reading, writing, editing, opening, moving, deleting, "
                    "or searching local files and folders. Use the RAG tool for uploaded-file questions, "
                    "the web-search tool for current information, and never claim an action succeeded "
                    "without the tool result. Do not select multiple tools for one request."
                ),
            },
            *self.repository.history(conversation_id),
            {"role": "user", "content": query},
        ]

        tool_name: str | None = None
        tool_arguments: dict[str, Any] = {}
        tool_result = ToolResult(tool_name="main_ai", ok=True, content="")
        assistant_message = ""
        response = self.llm_client.complete(messages, tools=self.tool_registry.descriptions())
        tool_calls = response.get("tool_calls", [])

        if tool_calls:
            if len(tool_calls) > self.max_tool_calls:
                assistant_message = "I could not safely choose a single task to perform."
                tool_result = ToolResult(tool_name="main_ai", ok=False, content=assistant_message, error="Multiple tools requested")
            else:
                call = tool_calls[0]
                function = call.get("function", {})
                tool_name = function.get("name")
                tool_arguments = function.get("arguments") or {}
                if not isinstance(tool_arguments, dict):
                    tool_arguments = {}
                tool = self.tool_registry.get(tool_name or "")
                if tool is None:
                    assistant_message = "I do not have a tool for that request."
                    tool_result = ToolResult(tool_name=tool_name or "unknown", ok=False, content=assistant_message, error="Unknown tool")
                else:
                    try:
                        tool_result = tool.run(query, context, tool_arguments)
                        assistant_message = tool_result.content
                    except Exception:
                        assistant_message = "The requested task could not be completed."
                        tool_result = ToolResult(
                            tool_name=tool.name,
                            ok=False,
                            content=assistant_message,
                            error="Specialist tool failed",
                        )
                    if assistant_message and tool_result.ok:
                        analysis_messages = [
                            {
                                "role": "system",
                                "content": (
                                    "You are the Main AI final responder. Explain the specialist workflow result "
                                    "to the user clearly and concisely. Do not claim anything beyond the result. "
                                    "Return only the final user-facing response and do not call tools."
                                ),
                            },
                            {"role": "user", "content": query},
                            {
                                "role": "tool",
                                "name": tool_name or "specialist",
                                "content": json.dumps(
                                    {
                                        "success": tool_result.ok,
                                        "message": tool_result.content,
                                        "data": tool_result.structured_data,
                                    },
                                    default=str,
                                ),
                            },
                        ]
                        try:
                            analysis = self.llm_client.complete(analysis_messages, tools=[])
                            analyzed_message = str(analysis.get("content") or "").strip()
                            if analyzed_message:
                                assistant_message = analyzed_message
                        except Exception:
                            pass
        else:
            assistant_message = str(response.get("content") or "I could not determine how to help with that request.")

        self.repository.save_turn(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            query=query,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tool_result={
                "ok": tool_result.ok,
                "content": tool_result.content,
                "data": tool_result.structured_data,
                "citations": tool_result.citations,
                "error": tool_result.error,
            },
            assistant_message_id=str(uuid4()),
            assistant_content=assistant_message,
        )
        return AssistantResponse(
            success=tool_result.ok,
            message=assistant_message,
            tool_name=tool_name or None,
            data=tool_result.structured_data,
            citations=tool_result.citations,
            error=tool_result.error,
        )
