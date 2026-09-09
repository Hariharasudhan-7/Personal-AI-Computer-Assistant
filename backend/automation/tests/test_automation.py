from unittest.mock import Mock

import httpx
import pytest

from backend.automation.agents import CalendarAutomationAgent, DriveAutomationAgent, MailAutomationAgent
from backend.automation.config import AutomationSettings
from backend.automation.n8n_client import N8NWebhookClient, N8NWebhookError
from backend.automation.registry import build_agent_registry


class FakeResponse:
    def __init__(self, payload, status_code=200, text=None):
        self.payload = payload
        self.status_code = status_code
        self.text = text if text is not None else ""

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://n8n.test/webhook")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


@pytest.fixture
def settings():
    return AutomationSettings(
        mail_webhook_url="https://n8n.test/mail",
        drive_webhook_url="https://n8n.test/drive",
        calendar_webhook_url="https://n8n.test/calendar",
    )


def test_each_agent_posts_query_and_returns_result(settings):
    http_client = Mock()
    http_client.post.return_value = FakeResponse(
        {"success": True, "message": "Completed", "data": {"id": "123"}}
    )
    client = N8NWebhookClient(http_client=http_client)

    agents = [
        (MailAutomationAgent, "https://n8n.test/mail"),
        (DriveAutomationAgent, "https://n8n.test/drive"),
        (CalendarAutomationAgent, "https://n8n.test/calendar"),
    ]
    for agent_class, webhook_url in agents:
        result = agent_class(settings=settings, client=client).run("do the task")
        assert result.success is True
        assert result.data == {"id": "123"}
        http_client.post.assert_called_with(webhook_url, params={"query": "do the task"})


def test_blank_query_is_rejected(settings):
    client = N8NWebhookClient(http_client=Mock())
    with pytest.raises(ValueError, match="Query must not be empty"):
        MailAutomationAgent(settings=settings, client=client).run("   ")


def test_missing_webhook_is_rejected():
    settings = AutomationSettings()
    with pytest.raises(N8NWebhookError, match="not configured"):
        MailAutomationAgent(settings=settings, client=N8NWebhookClient(http_client=Mock())).run("send mail")


def test_http_failure_is_normalized(settings):
    http_client = Mock()
    http_client.post.return_value = FakeResponse({"error": "failed"}, status_code=500)
    with pytest.raises(N8NWebhookError, match="request failed"):
        MailAutomationAgent(
            settings=settings,
            client=N8NWebhookClient(http_client=http_client),
        ).run("send mail")


def test_invalid_json_is_rejected(settings):
    http_client = Mock()
    response = FakeResponse({})
    response.json = Mock(side_effect=ValueError("invalid json"))
    http_client.post.return_value = response
    with pytest.raises(N8NWebhookError, match="invalid JSON"):
        MailAutomationAgent(
            settings=settings,
            client=N8NWebhookClient(http_client=http_client),
        ).run("send mail")


def test_plain_text_response_is_returned_as_success(settings):
    http_client = Mock()
    http_client.post.return_value = FakeResponse(
        ValueError("not json"),
        text="The email was sent successfully.",
    )

    result = MailAutomationAgent(
        settings=settings,
        client=N8NWebhookClient(http_client=http_client),
    ).run("send mail")

    assert result.success is True
    assert result.message == "The email was sent successfully."


def test_text_field_response_is_returned_as_success(settings):
    http_client = Mock()
    http_client.post.return_value = FakeResponse({"text": "Workflow finished."})

    result = MailAutomationAgent(
        settings=settings,
        client=N8NWebhookClient(http_client=http_client),
    ).run("send mail")

    assert result.success is True
    assert result.message == "Workflow finished."


def test_n8n_success_response_without_success_field_is_accepted(settings):
    http_client = Mock()
    http_client.post.return_value = FakeResponse({"status": "completed", "result": "Email sent"})

    result = MailAutomationAgent(
        settings=settings,
        client=N8NWebhookClient(http_client=http_client),
    ).run("send mail")

    assert result.success is True
    assert result.message == "completed"
    assert result.data == {"status": "completed", "result": "Email sent"}


def test_business_failure_is_returned(settings):
    http_client = Mock()
    http_client.post.return_value = FakeResponse(
        {"success": False, "message": "Permission denied", "data": None}
    )
    result = MailAutomationAgent(
        settings=settings,
        client=N8NWebhookClient(http_client=http_client),
    ).run("send mail")
    assert result.success is False
    assert result.message == "Permission denied"


def test_registry_exposes_all_agents(settings):
    registry = build_agent_registry(settings=settings, client=N8NWebhookClient(http_client=Mock()))
    assert set(registry) == {"mail", "drive", "calendar"}
