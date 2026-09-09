from typing import Any

from openai import OpenAI


class OpenRouterLLM:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must be configured")
        self.model = model
        self.client = client or OpenAI(api_key=api_key, base_url=base_url)

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or [],
            tool_choice="auto",
            **kwargs,
        )
        message = response.choices[0].message
        tool_calls = []
        for call in getattr(message, "tool_calls", None) or []:
            arguments = call.function.arguments
            if isinstance(arguments, str):
                import json
                arguments = json.loads(arguments)
            tool_calls.append({
                "id": call.id,
                "function": {
                    "name": call.function.name,
                    "arguments": arguments,
                },
            })
        return {"content": message.content or "", "tool_calls": tool_calls}
