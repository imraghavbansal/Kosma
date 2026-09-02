"""Real counterfactual replay: calls an actual LLM to generate the candidate
config's real output for a real historical input, then a second real LLM
call judges whether that output looks successful. Used instead of
mock_behavior.simulate() whenever a project has configured its own
llm_provider/llm_api_key (see routers/projects.py) - this is the difference
between "a demo of the mechanism" and an actual answer to "what would this
change really do."

Evidence tier: the generation call is REPLAYED (a real model actually ran).
The success judgment is PREDICTED - an LLM's own assessment, not ground
truth - and is always labeled that way, never asserted as fact (see
PRODUCT-SPEC.md's evidence hierarchy)."""

import json

import httpx

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT = 30.0

# Small, cheap models for the judge call - judging doesn't need the same
# model (or size) as the config being tested, and keeping it fixed keeps
# judging cost predictable regardless of what the candidate config uses.
JUDGE_MODEL_BY_PROVIDER = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
}


class LLMReplayError(Exception):
    """A real call to the configured provider failed - never silently
    swallowed into a fabricated result."""


def _call_openai(api_key: str, model: str, system_prompt: str, user_message: str) -> tuple[str, int, int]:
    resp = httpx.post(
        OPENAI_CHAT_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
        },
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise LLMReplayError(f"OpenAI request failed ({resp.status_code}): {resp.text[:300]}")
    data = resp.json()
    text = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _call_anthropic(api_key: str, model: str, system_prompt: str, user_message: str) -> tuple[str, int, int]:
    resp = httpx.post(
        ANTHROPIC_MESSAGES_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": 1024,
        },
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise LLMReplayError(f"Anthropic request failed ({resp.status_code}): {resp.text[:300]}")
    data = resp.json()
    text = "".join(block.get("text", "") for block in data.get("content", []))
    usage = data.get("usage", {})
    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def _call_provider(provider: str, api_key: str, model: str, system_prompt: str, user_message: str) -> tuple[str, int, int]:
    if provider == "openai":
        return _call_openai(api_key, model, system_prompt, user_message)
    if provider == "anthropic":
        return _call_anthropic(api_key, model, system_prompt, user_message)
    raise LLMReplayError(f"Unsupported llm_provider '{provider}' - only 'openai' and 'anthropic' are wired up")


def generate_candidate_output(
    *, provider: str, api_key: str, model: str, prompt_text: str, input_text: str
) -> tuple[str, int, int]:
    """Runs the candidate config's real prompt against a real historical
    input, via a real model call. Returns (output_text, input_tokens,
    output_tokens)."""
    system_prompt = prompt_text or "You are a helpful assistant."
    return _call_provider(provider, api_key, model, system_prompt, input_text)


_JUDGE_SYSTEM_PROMPT = (
    "You judge whether an AI agent's response successfully resolved the user's "
    "request. Respond with strict JSON only: {\"success\": true or false, "
    "\"reason\": \"one short sentence\"}. No other text."
)


def judge_success(*, provider: str, api_key: str, input_text: str, output_text: str) -> bool:
    """A second real LLM call scoring the generated output. This is a
    PREDICTED judgment, not ground truth - callers must label it as such."""
    judge_model = JUDGE_MODEL_BY_PROVIDER.get(provider)
    if judge_model is None:
        raise LLMReplayError(f"No judge model configured for provider '{provider}'")
    user_message = f"User request:\n{input_text}\n\nAgent response:\n{output_text}"
    raw, _, _ = _call_provider(provider, api_key, judge_model, _JUDGE_SYSTEM_PROMPT, user_message)
    try:
        # Judge models sometimes wrap JSON in prose despite instructions -
        # take the first {...} block rather than failing outright.
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])
        return bool(parsed["success"])
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise LLMReplayError(f"Judge model returned unparseable output: {raw[:200]}") from exc
