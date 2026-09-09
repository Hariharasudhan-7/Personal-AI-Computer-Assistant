from collections.abc import Mapping

from .agents import CalendarAutomationAgent, DriveAutomationAgent, MailAutomationAgent
from .config import AutomationSettings
from .n8n_client import N8NWebhookClient


def build_agent_registry(
    settings: AutomationSettings | None = None,
    client: N8NWebhookClient | None = None,
) -> Mapping[str, object]:
    return {
        "mail": MailAutomationAgent(settings=settings, client=client),
        "drive": DriveAutomationAgent(settings=settings, client=client),
        "calendar": CalendarAutomationAgent(settings=settings, client=client),
    }
