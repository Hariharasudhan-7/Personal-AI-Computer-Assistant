import os
from collections.abc import Iterable
from typing import Any

from backend.automation.config import AutomationSettings
from backend.automation.n8n_client import N8NWebhookClient

from .adapters.file_automation import FileAutomationTool
from .adapters.n8n import N8NTool, build_n8n_tools
from .adapters.rag import RAGTool
from .adapters.web_search import WebSearchTool
from .llm import OpenRouterLLM
from .persistence.database import create_database, initialize_database
from .persistence.repository import ConversationRepository
from .service import MainAI
from .tools import MainAITool, ToolRegistry


def build_tool_registry(
    *,
    n8n_settings: AutomationSettings | None = None,
    n8n_client: N8NWebhookClient | None = None,
    file_automation_agent: Any | None = None,
    rag_tool: RAGTool | None = None,
    web_search_agent: Any | None = None,
    extra_tools: Iterable[MainAITool] = (),
) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in build_n8n_tools(settings=n8n_settings, client=n8n_client):
        registry.register(tool)
    if file_automation_agent is not None:
        registry.register(FileAutomationTool(file_automation_agent))
    if rag_tool is not None:
        registry.register(rag_tool)
    if web_search_agent is not None:
        registry.register(WebSearchTool(web_search_agent))
    for tool in extra_tools:
        registry.register(tool)
    return registry


def build_main_ai(
    *,
    llm_client: Any | None = None,
    tool_registry: ToolRegistry | None = None,
    database_path: str | None = None,
    initialize_schema: bool = True,
    **tool_kwargs: Any,
) -> MainAI:
    database = create_database(database_path)
    if initialize_schema:
        initialize_database(database)
    repository = ConversationRepository(database)
    llm = llm_client or OpenRouterLLM(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    )
    registry = tool_registry or build_tool_registry(**tool_kwargs)
    return MainAI(llm_client=llm, tool_registry=registry, repository=repository)
