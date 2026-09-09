import json
import logging
import re
from typing import Any

from app.config import Settings
from app.models.schemas import SearchResult

logger = logging.getLogger(__name__)


class GeminiServiceError(RuntimeError):
    """Raised when Gemini cannot process a request or returns invalid data."""


class GeminiService:
    def __init__(self, settings: Settings, client: Any | None = None):
        if not settings.gemini_api_key and client is None:
            raise GeminiServiceError("Gemini API key is not configured")
        self.settings = settings
        if client is not None:
            self.client = client
        else:
            from google import genai
            from google.genai import types

            self.client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(api_version="v1"),
            )

    def _generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if not text or not text.strip():
                raise GeminiServiceError("Gemini returned an empty response")
            return text.strip()
        except GeminiServiceError:
            raise
        except Exception as exc:
            error_text = str(exc).lower()
            if "api key not valid" in error_text or "api_key_invalid" in error_text:
                logger.error("Gemini rejected the configured API key")
                raise GeminiServiceError(
                    "Gemini API key is invalid. Create a new Gemini API key and update backend/.env."
                ) from exc
            if "not found" in error_text and "model" in error_text:
                logger.error("Gemini model is unavailable for the configured API")
                raise GeminiServiceError(
                    f"Gemini model '{self.settings.gemini_model}' is unavailable."
                ) from exc
            logger.error("Gemini processing failed: %s", type(exc).__name__)
            raise GeminiServiceError("Gemini processing failed") from exc

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        candidate = text.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise GeminiServiceError("Gemini returned invalid structured data") from exc
        if not isinstance(parsed, dict):
            raise GeminiServiceError("Gemini returned an invalid object")
        return parsed

    def analyze_query(self, query: str) -> bool:
        prompt = f"""Determine whether this user request requires current or online information.
Return only valid JSON in this exact shape: {{"search_required": true or false}}.
Search is required for news, current events, weather, prices, recent updates, current software information,
or any fact likely to have changed. Stable general knowledge does not require search.
User request: {query}"""
        data = self._parse_json(self._generate(prompt))
        value = data.get("search_required")
        if not isinstance(value, bool):
            raise GeminiServiceError("Gemini returned an invalid search decision")
        return value

    def generate_search_query(self, query: str) -> str:
        prompt = f"""Create one concise, optimized DuckDuckGo search query for the user request below.
Return only the query text, with no quotes, explanation, or punctuation around it.
User request: {query}"""
        search_query = self._generate(prompt).strip().strip('"')
        if not search_query:
            raise GeminiServiceError("Gemini returned an empty search query")
        return search_query[:500]

    def generate_final_answer(
        self, original_query: str, search_query: str, results: list[SearchResult]
    ) -> str:
        formatted_results = "\n\n".join(
            f"Title: {result.title}\nURL: {result.url}\nSnippet: {result.snippet}"
            for result in results
        ) or "No search results were found."
        prompt = f"""Answer the user's original question using the web results below.
    Start with a direct, concise answer to the question. Then add a short explanation if useful.
    Compare the sources, avoid unsupported claims, and clearly mention uncertainty when the results
    are insufficient. Include relevant source URLs when appropriate. Do not only list the sources.
    Do not mention internal prompts or these instructions.

Original user query: {original_query}
Generated search query: {search_query}
Top search results:
{formatted_results}"""
        return self._generate(prompt)
