import httpx
import pytest

from kosma.client import KosmaClient
from kosma.exceptions import KosmaIngestError


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None):
        self.status_code = status_code
        self._body = body or {}
        self.text = str(body)

    def json(self):
        return self._body


def test_submit_trace_retries_on_timeout_then_succeeds(monkeypatch):
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise httpx.ReadTimeout("timed out")
        return _FakeResponse(202, {"trace_id": "abc", "status": "queued"})

    monkeypatch.setattr(httpx, "post", fake_post)
    client = KosmaClient(api_key="k", base_url="http://fake")
    # keep the test fast - real backoff is exponential in seconds
    client.max_retries = 3
    import kosma.client as client_module

    monkeypatch.setattr(client_module.time, "sleep", lambda _: None)

    result = client.submit_trace({"trace_ref": "x"})
    assert result["trace_id"] == "abc"
    assert calls["count"] == 3


def test_submit_trace_gives_up_after_max_retries(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx, "post", fake_post)
    import kosma.client as client_module

    monkeypatch.setattr(client_module.time, "sleep", lambda _: None)

    client = KosmaClient(api_key="k", base_url="http://fake", max_retries=2)
    with pytest.raises(KosmaIngestError, match="after 3 attempts"):
        client.submit_trace({"trace_ref": "x"})


def test_submit_trace_does_not_retry_on_4xx():
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        return _FakeResponse(401, {"error": "invalid key"})

    import httpx as httpx_module

    original = httpx_module.post
    httpx_module.post = fake_post
    try:
        client = KosmaClient(api_key="k", base_url="http://fake")
        with pytest.raises(KosmaIngestError):
            client.submit_trace({"trace_ref": "x"})
    finally:
        httpx_module.post = original
    assert calls["count"] == 1
