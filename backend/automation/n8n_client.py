from typing import Any

import httpx

from .schemas import AutomationRequest, AutomationResult


class N8NWebhookError(RuntimeError):
    """Raised when an N8N webhook cannot produce a valid result."""


class N8NWebhookClient:
    def __init__(
        self,
        timeout_seconds: float = 30.0,
        http_client: Any | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def invoke(self, webhook_url: str | None, query: str) -> AutomationResult:
        if not webhook_url:
            raise N8NWebhookError("N8N webhook is not configured")

        request = AutomationRequest(query=query)
        try:
            response = self.http_client.post(webhook_url, params={"query": request.query})
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response is not None else "unknown"
            detail = error.response.text[:300] if error.response is not None else ""
            raise N8NWebhookError(
                f"N8N webhook request failed with HTTP {status_code}: {detail}"
            ) from error
        except httpx.HTTPError as error:
            raise N8NWebhookError("N8N webhook request failed") from error

        payload = self._parse_response(response)

        if isinstance(payload, str):
            return AutomationResult(success=True, message=payload)

        if isinstance(payload, list):
            if not all(isinstance(item, dict) for item in payload):
                raise N8NWebhookError("N8N webhook returned an invalid response")
            return AutomationResult(
                success=True,
                message="Workflow completed successfully.",
                data=payload,
            )

        if not isinstance(payload, dict):
            raise N8NWebhookError("N8N webhook returned an invalid response")

        if "success" not in payload:
            text = payload.get("text") or payload.get("response") or payload.get("output")
            if isinstance(text, str) and text.strip():
                return AutomationResult(success=True, message=text.strip(), data=payload)
            if payload.get("error") or payload.get("status") in {"error", "failed", "failure"}:
                return AutomationResult(
                    success=False,
                    message=str(payload.get("error") or payload.get("status")),
                    data=payload,
                )
            return AutomationResult(
                success=True,
                message=str(payload.get("status") or "Workflow completed successfully."),
                data=payload,
            )

        try:
            result = AutomationResult.model_validate(payload)
        except ValueError as error:
            raise N8NWebhookError("N8N webhook response has an invalid shape") from error

        if not result.message:
            result.message = str(payload.get("status") or "Workflow completed successfully.")
        if result.data is None and "output" in payload:
            result.data = payload["output"]

        return result

    @staticmethod
    def _parse_response(response: Any) -> Any:
        try:
            return response.json()
        except ValueError:
            text = getattr(response, "text", "")
            if isinstance(text, str) and text.strip():
                return text.strip()
            raise N8NWebhookError("N8N webhook returned invalid JSON") from None

    def close(self) -> None:
        close = getattr(self.http_client, "close", None)
        if close:
            close()
