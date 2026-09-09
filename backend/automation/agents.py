from .config import AutomationSettings, get_automation_settings
from .n8n_client import N8NWebhookClient
from .schemas import AutomationResult


class _AutomationAgent:
    webhook_setting: str

    def __init__(
        self,
        settings: AutomationSettings | None = None,
        client: N8NWebhookClient | None = None,
    ) -> None:
        self.settings = settings or get_automation_settings()
        self.client = client or N8NWebhookClient(self.settings.timeout_seconds)

    def run(self, query: str) -> AutomationResult:
        return self.client.invoke(getattr(self.settings, self.webhook_setting), query)


class MailAutomationAgent(_AutomationAgent):
    webhook_setting = "mail_webhook_url"


class DriveAutomationAgent(_AutomationAgent):
    webhook_setting = "drive_webhook_url"


class CalendarAutomationAgent(_AutomationAgent):
    webhook_setting = "calendar_webhook_url"
