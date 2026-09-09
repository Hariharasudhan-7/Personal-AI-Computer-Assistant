from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AutomationSettings:
    mail_webhook_url: str | None = None
    drive_webhook_url: str | None = None
    calendar_webhook_url: str | None = None
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        values = {
            "mail_webhook_url": (self.mail_webhook_url, "MAIL_N8N_WEBHOOK_URL"),
            "drive_webhook_url": (self.drive_webhook_url, "DRIVE_N8N_WEBHOOK_URL"),
            "calendar_webhook_url": (self.calendar_webhook_url, "CALENDAR_N8N_WEBHOOK_URL"),
        }
        for field_name, (value, env_name) in values.items():
            if value is None:
                value = os.getenv(env_name)
            if value:
                value = value.strip().strip('"').strip("'")
            object.__setattr__(self, field_name, value or None)

        if self.timeout_seconds == 30.0:
            object.__setattr__(
                self,
                "timeout_seconds",
                float(os.getenv("N8N_TIMEOUT_SECONDS", "30")),
            )
        if self.timeout_seconds <= 0:
            raise ValueError("N8N_TIMEOUT_SECONDS must be greater than zero")


@lru_cache
def get_automation_settings() -> AutomationSettings:
    return AutomationSettings()
