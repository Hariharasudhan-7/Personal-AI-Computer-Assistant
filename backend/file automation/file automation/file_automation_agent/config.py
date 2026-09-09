import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def get_openrouter_settings() -> tuple[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your environment or .env file.")
    return api_key, model


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent
