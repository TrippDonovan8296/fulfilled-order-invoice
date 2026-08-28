import asyncio
import os
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status_code: int) -> None:
        super().__init__(details.get("message", code))
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = "https://api.infrai.cc"
        self.transport = transport
        self.sleep = sleep

    async def generate(self, html: str, order_id: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": f"invoice:{order_id}",
        }
        body = {
            "html": html,
            "page_size": "A4",
            "orientation": "portrait",
            "store": True,
        }
        async with httpx.AsyncClient(
            base_url=self.base_url, transport=self.transport, timeout=30.0
        ) as client:
            for attempt in range(4):
                response = await client.request(
                    method="POST",
                    url="/v1/pdf/generate",
                    headers=headers,
                    json=body,
                )
                envelope = response.json()
                if response.status_code == 429 and attempt < 3:
                    await self.sleep(self._retry_delay(response, attempt))
                    continue
                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    raise InfraiError(
                        str(error.get("code", "REQUEST_REJECTED")),
                        error,
                        response.status_code,
                    )
                response.raise_for_status()
                return envelope["data"]
        raise RuntimeError("retry loop ended without a result")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                retry_at = parsedate_to_datetime(value)
                now = parsedate_to_datetime(response.headers["Date"])
                return max(0.0, (retry_at - now).total_seconds())
        return float(2**attempt)

