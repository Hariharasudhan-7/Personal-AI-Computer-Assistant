from collections.abc import Mapping
from typing import Any

from backend.automation.agents import CalendarAutomationAgent, DriveAutomationAgent, MailAutomationAgent
from backend.automation.n8n_client import N8NWebhookError

from ..contracts import ToolContext, ToolResult


class N8NTool:
    def __init__(self, name: str, description: str, agent: Any) -> None:
        self.name = name
        self.description = description
        self.agent = agent

    def run(
        self,
        query: str,
        context: ToolContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        try:
            result = self.agent.run(query)
        except N8NWebhookError as error:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                content="The automation workflow could not be completed.",
                error=str(error),
            )
        return ToolResult(
            tool_name=self.name,
            ok=result.success,
            content=result.message,
            structured_data=result.data,
            error=None if result.success else result.message,
        )


def build_n8n_tools(settings=None, client=None) -> list[N8NTool]:
    return [
        N8NTool("mail", "Send, read, or manage email through the mail workflow.", MailAutomationAgent(settings, client)),
        N8NTool("drive", "Find, create, or manage files through the drive workflow.", DriveAutomationAgent(settings, client)),
        N8NTool("calendar", "Create, inspect, or manage calendar events through the calendar workflow.", CalendarAutomationAgent(settings, client)),
    ]
