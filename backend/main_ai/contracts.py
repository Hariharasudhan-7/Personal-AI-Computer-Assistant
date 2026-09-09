from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolContext:
    user_id: str
    conversation_id: str
    message_id: str
    attachment_ids: tuple[str, ...] = ()


@dataclass
class ToolResult:
    tool_name: str
    ok: bool
    content: str
    structured_data: Any = None
    citations: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None


@dataclass
class AssistantResponse:
    success: bool
    message: str
    tool_name: str | None = None
    data: Any = None
    citations: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None
