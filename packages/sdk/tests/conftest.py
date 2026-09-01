import pytest

from kosma.client import KosmaClient


class FakeClient(KosmaClient):
    """Captures submitted payloads instead of making a real HTTP call, so SDK
    unit tests exercise the real trace/span logic without needing a live API."""

    def __init__(self):
        self.submitted: list[dict] = []
        self.api_key = "fake-key"
        self.base_url = "http://fake"
        self.timeout = 1.0

    def submit_trace(self, payload: dict) -> dict:
        self.submitted.append(payload)
        return {"trace_id": f"fake-trace-{len(self.submitted)}", "status": "queued"}


@pytest.fixture()
def fake_client() -> FakeClient:
    return FakeClient()
