from typing import Any

from backend.main_ai.contracts import ToolContext, ToolResult
from backend.main_ai.persistence.database import create_database, initialize_database
from backend.main_ai.persistence.repository import ConversationRepository
from backend.main_ai.service import MainAI
from backend.main_ai.tools import FunctionTool, ToolRegistry


class FakeLLM:
    def __init__(self, tool_name: str | None):
        self.tool_name = tool_name
        self.calls: list[dict[str, Any]] = []

    def complete(self, messages, tools=None, **kwargs):
        self.calls.append({"messages": messages, "tools": tools})
        if self.tool_name is None:
            return {"content": "General answer", "tool_calls": []}
        return {
            "content": "",
            "tool_calls": [{
                "id": "call-1",
                "function": {"name": self.tool_name, "arguments": {"query": "ignored"}},
            }],
        }


def make_main_ai(tool_name: str | None = "mail"):
    database = create_database(":memory:")
    initialize_database(database)
    repository = ConversationRepository(database)
    calls = []

    def run(query: str, context: ToolContext, arguments: dict[str, Any]) -> ToolResult:
        calls.append((query, context, arguments))
        return ToolResult(tool_name="mail", ok=True, content="Mail completed", structured_data={"id": "1"})

    registry = ToolRegistry({
        "mail": FunctionTool("mail", "Send or manage email", run),
    })
    llm = FakeLLM(tool_name)
    return MainAI(llm, registry, repository), repository, llm, calls


def test_main_ai_selects_tool_and_persists_turn():
    main_ai, repository, llm, calls = make_main_ai()

    result = main_ai.handle_message(
        user_id="local-user",
        conversation_id="conversation-1",
        content="Send an email to Alex",
    )

    assert result.success is True
    assert result.tool_name == "mail"
    assert result.message == "Mail completed"
    assert calls[0][0] == "Send an email to Alex"
    assert repository.history("conversation-1") == [
        {"role": "user", "content": "Send an email to Alex"},
        {"role": "assistant", "content": "Mail completed"},
    ]
    assert llm.calls[0]["tools"][0]["function"]["name"] == "mail"


def test_main_ai_returns_direct_answer_without_tool():
    main_ai, repository, _, _ = make_main_ai(tool_name=None)

    result = main_ai.handle_message(
        user_id="local-user",
        conversation_id="conversation-2",
        content="Hello",
    )

    assert result.success is True
    assert result.tool_name is None
    assert result.message == "General answer"
    assert repository.history("conversation-2")[-1] == {"role": "assistant", "content": "General answer"}


def test_main_ai_rejects_unknown_tool_and_persists_failure():
    main_ai, repository, _, _ = make_main_ai(tool_name="unknown")

    result = main_ai.handle_message(
        user_id="local-user",
        conversation_id="conversation-3",
        content="Do something unsupported",
    )

    assert result.success is False
    assert result.error == "Unknown tool"
    assert repository.history("conversation-3")[-1]["content"] == "I do not have a tool for that request."
