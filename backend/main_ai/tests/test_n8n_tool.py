from unittest.mock import Mock

from backend.automation.config import AutomationSettings
from backend.automation.n8n_client import N8NWebhookClient
from backend.automation.schemas import AutomationResult
from backend.main_ai.contracts import ToolContext
from backend.main_ai.adapters.n8n import build_n8n_tools


def test_n8n_tools_normalize_workflow_results():
    settings = AutomationSettings(
        mail_webhook_url="https://n8n.test/mail",
        drive_webhook_url="https://n8n.test/drive",
        calendar_webhook_url="https://n8n.test/calendar",
    )
    client = Mock(spec=N8NWebhookClient)
    client.invoke.return_value = AutomationResult(success=True, message="Done", data={"id": "1"})
    tools = build_n8n_tools(settings=settings, client=client)
    context = ToolContext("user", "conversation", "message")

    result = tools[0].run("send an email", context)

    assert result.tool_name == "mail"
    assert result.ok is True
    assert result.content == "Done"
    assert result.structured_data == {"id": "1"}
    client.invoke.assert_called_once_with("https://n8n.test/mail", "send an email")
