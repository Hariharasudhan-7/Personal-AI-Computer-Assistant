from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

from dotenv import load_dotenv

from .factory import build_main_ai
from .llm import OpenRouterLLM
from .adapters.rag import RAGTool
from .rag_runtime import AttachmentRAG


def _add_service_path(relative_path: Path) -> None:
    service_path = Path(__file__).resolve().parents[2] / relative_path
    if str(service_path) not in sys.path:
        sys.path.insert(0, str(service_path))


def _build_file_agent(llm_client: Any) -> Any:
    _add_service_path(Path("backend") / "file automation" / "file automation")
    from file_automation_agent.ai.agent import FileAutomationAgent  # pyright: ignore[reportMissingImports]

    base_dir = os.getenv("FILE_AUTOMATION_BASE_DIR", "automation_workspace")
    return FileAutomationAgent(base_dir=base_dir, llm_client=llm_client)


def _build_web_search_agent() -> Any:
    _add_service_path(Path("backend") / "online websearch" / "backend")
    from app.config import Settings  # pyright: ignore[reportMissingImports]
    from app.services.web_search_agent import WebSearchAgent  # pyright: ignore[reportMissingImports]

    return WebSearchAgent(Settings())


def build_runtime_main_ai():
    workspace_root = Path(__file__).resolve().parents[2]
    load_dotenv(workspace_root / ".env")
    shared_llm = OpenRouterLLM(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    )
    attachment_rag = AttachmentRAG()
    main_ai = build_main_ai(
        llm_client=shared_llm,
        file_automation_agent=_build_file_agent(shared_llm),
        rag_tool=RAGTool(
            retriever_for_attachment=attachment_rag.retriever_for_attachment,
            answer_question=attachment_rag.answer_question,
        ),
        web_search_agent=_build_web_search_agent(),
    )
    main_ai.attachment_rag = attachment_rag
    return main_ai
