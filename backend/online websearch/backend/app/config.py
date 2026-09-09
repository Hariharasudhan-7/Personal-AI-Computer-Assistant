from functools import lru_cache
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = "Personal AI Computer Assistant"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    search_timeout_seconds: int = 15
    max_results: int = 5

    def __post_init__(self) -> None:
        if self.gemini_api_key is None:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            self.gemini_api_key = self.gemini_api_key.strip().strip('"').strip("'")
        if self.gemini_model == "gemini-3.6-flash":
            self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)
        if self.search_timeout_seconds == 15:
            self.search_timeout_seconds = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "15"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
