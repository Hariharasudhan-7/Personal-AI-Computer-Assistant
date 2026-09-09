from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class OpenRouterClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.base_url = base_url
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY must be configured in the environment. Add it to your .env file.")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or [],
            tool_choice="auto",
            **kwargs,
        )

        message = response.choices[0].message
        result: dict[str, Any] = {"content": message.content or "", "tool_calls": []}
        if getattr(message, "tool_calls", None):
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": args,
                    },
                })
        return result
