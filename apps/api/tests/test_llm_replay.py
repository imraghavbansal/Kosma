"""Real counterfactual replay's HTTP layer - mocked here (no real API calls,
no real cost, no network in tests), but exercising the actual request/parse
logic that talks to OpenAI/Anthropic in production."""

import httpx
import pytest

from kosma_api.change_engine import llm_replay


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict, text: str = ""):
        self.status_code = status_code
        self._json = json_body
        self.text = text or str(json_body)

    def json(self):
        return self._json


def test_generate_candidate_output_openai(monkeypatch):
    def fake_post(url, headers, json, timeout):
        assert url == llm_replay.OPENAI_CHAT_URL
        assert headers["Authorization"] == "Bearer sk-test"
        assert json["model"] == "gpt-4o-mini"
        return _FakeResponse(
            200,
            {
                "choices": [{"message": {"content": "Here is your refund."}}],
                "usage": {"prompt_tokens": 42, "completion_tokens": 8},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    text, in_tok, out_tok = llm_replay.generate_candidate_output(
        provider="openai",
        api_key="sk-test",
        model="gpt-4o-mini",
        prompt_text="You are a support agent.",
        input_text="I want a refund",
    )
    assert text == "Here is your refund."
    assert in_tok == 42
    assert out_tok == 8


def test_generate_candidate_output_anthropic(monkeypatch):
    def fake_post(url, headers, json, timeout):
        assert url == llm_replay.ANTHROPIC_MESSAGES_URL
        assert headers["x-api-key"] == "anthropic-test"
        return _FakeResponse(
            200,
            {
                "content": [{"type": "text", "text": "Refund approved."}],
                "usage": {"input_tokens": 20, "output_tokens": 5},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    text, in_tok, out_tok = llm_replay.generate_candidate_output(
        provider="anthropic",
        api_key="anthropic-test",
        model="claude-3-5-haiku-20241022",
        prompt_text="You are a support agent.",
        input_text="I want a refund",
    )
    assert text == "Refund approved."
    assert in_tok == 20
    assert out_tok == 5


def test_generate_candidate_output_raises_on_http_error(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return _FakeResponse(401, {"error": "invalid api key"})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(llm_replay.LLMReplayError):
        llm_replay.generate_candidate_output(
            provider="openai", api_key="bad-key", model="gpt-4o-mini", prompt_text="x", input_text="y"
        )


def test_judge_success_parses_json_response(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return _FakeResponse(
            200,
            {
                "choices": [{"message": {"content": '{"success": true, "reason": "resolved the request"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    result = llm_replay.judge_success(
        provider="openai", api_key="sk-test", input_text="refund please", output_text="refund issued"
    )
    assert result is True


def test_judge_success_handles_prose_wrapped_json(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return _FakeResponse(
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": 'Sure, here is my judgment: {"success": false, "reason": "did not help"} Hope that helps!'
                        }
                    }
                ],
                "usage": {},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    result = llm_replay.judge_success(
        provider="openai", api_key="sk-test", input_text="refund please", output_text="no can do"
    )
    assert result is False


def test_judge_success_raises_on_unparseable_response(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return _FakeResponse(200, {"choices": [{"message": {"content": "not json at all"}}], "usage": {}})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(llm_replay.LLMReplayError):
        llm_replay.judge_success(provider="openai", api_key="sk-test", input_text="x", output_text="y")


def test_unsupported_provider_raises():
    with pytest.raises(llm_replay.LLMReplayError):
        llm_replay.generate_candidate_output(
            provider="cohere", api_key="k", model="m", prompt_text="p", input_text="i"
        )
