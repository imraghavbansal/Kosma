import os

import httpx

from kosma.exceptions import KosmaConfigError, KosmaIngestError

DEFAULT_BASE_URL = "http://localhost:8000"


class KosmaClient:
    """Thin HTTP client over the Kosma ingestion API. Most users won't touch this
    directly - use `trace`/`tracer` from `kosma`, which create one internally from
    KOSMA_API_KEY / KOSMA_API_URL."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 10.0):
        self.api_key = api_key or os.environ.get("KOSMA_API_KEY")
        if not self.api_key:
            raise KosmaConfigError(
                "No API key provided. Pass api_key=... or set the KOSMA_API_KEY environment variable."
            )
        self.base_url = (base_url or os.environ.get("KOSMA_API_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def submit_trace(self, payload: dict) -> dict:
        try:
            response = httpx.post(
                f"{self.base_url}/v1/traces",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise KosmaIngestError(f"Could not reach Kosma API at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
            raise KosmaIngestError(
                f"Kosma API rejected trace (HTTP {response.status_code}): {response.text}"
            )
        return response.json()
