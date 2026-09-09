from types import SimpleNamespace
from unittest.mock import Mock

from backend.automation.config import AutomationSettings
from backend.main_ai.factory import build_main_ai
from backend.main_ai.llm import OpenRouterLLM


def test_openrouter_llm_normalizes_tool_calls():
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(
            content="",
            tool_calls=[SimpleNamespace(
                id="call-1",
                function=SimpleNamespace(name="calendar", arguments='{"query":"book a meeting"}'),
            )],
        ))]
    )
    llm = OpenRouterLLM(api_key="test-key", client=client)

    result = llm.complete([{"role": "user", "content": "book a meeting"}], tools=[])

    assert result == {
        "content": "",
        "tool_calls": [{
            "id": "call-1",
            "function": {"name": "calendar", "arguments": {"query": "book a meeting"}},
        }],
    }
    client.chat.completions.create.assert_called_once()


def test_build_main_ai_registers_n8n_tools_without_openrouter_call():
    main_ai = build_main_ai(
        llm_client=Mock(),
        database_path=":memory:",
        n8n_settings=AutomationSettings(
            mail_webhook_url="https://n8n.test/mail",
            drive_webhook_url="https://n8n.test/drive",
            calendar_webhook_url="https://n8n.test/calendar",
        ),
    )

    assert {tool["function"]["name"] for tool in main_ai.tool_registry.descriptions()} == {
        "mail",
        "drive",
        "calendar",
    }
