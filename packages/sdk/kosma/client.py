import os
import time

import httpx

from kosma.exceptions import KosmaConfigError, KosmaIngestError

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class KosmaClient:
    """Thin HTTP client over the Kosma ingestion API. Most users won't touch this
    directly - use `trace`/`tracer` from `kosma`, which create one internally from
    KOSMA_API_KEY / KOSMA_API_URL.

    Retries on connection errors and timeouts (not on 4xx/5xx responses, which are
    real rejections, not transient failures) with exponential backoff. This matters
    in practice, not just in theory: a hosted Postgres instance under concurrent
    load can transiently drop a connection, and a trace shouldn't be lost to that."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key or os.environ.get("KOSMA_API_KEY")
        if not self.api_key:
            raise KosmaConfigError(
                "No API key provided. Pass api_key=... or set the KOSMA_API_KEY environment variable."
            )
        self.base_url = (base_url or os.environ.get("KOSMA_API_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def submit_trace(self, payload: dict) -> dict:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/v1/traces",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.5 * (2**attempt))
                    continue
                raise KosmaIngestError(
                    f"Could not reach Kosma API at {self.base_url} after "
                    f"{self.max_retries + 1} attempts: {exc}"
                ) from exc

            if response.status_code >= 500 and attempt < self.max_retries:
                last_error = KosmaIngestError(f"HTTP {response.status_code}: {response.text}")
                time.sleep(0.5 * (2**attempt))
                continue

            if response.status_code >= 400:
                raise KosmaIngestError(
                    f"Kosma API rejected trace (HTTP {response.status_code}): {response.text}"
                )
            return response.json()

        raise KosmaIngestError(f"Could not submit trace: {last_error}")
