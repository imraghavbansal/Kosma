import functools
import time
import uuid
from collections.abc import Callable

from kosma.client import KosmaClient
from kosma.span import Span, new_span_ref


class TraceContext:
    """One end-to-end execution of an agent. Created via `tracer.start_trace(...)`
    (see the module-level `tracer` below) or implicitly by the `@trace` decorator.
    Use as a context manager; spans are created with `trace.span(...)` inside it."""

    def __init__(
        self,
        name: str,
        *,
        agent_id: str,
        agent_config_id: str,
        workflow_tag: str | None = None,
        segment_tags: dict | None = None,
        input_text: str = "",
        client: KosmaClient | None = None,
    ):
        self.name = name
        self.trace_ref = str(uuid.uuid4())
        self.agent_id = agent_id
        self.agent_config_id = agent_config_id
        self.workflow_tag = workflow_tag
        self.segment_tags = segment_tags or {}
        self.input_text = input_text
        self.model_provider: str | None = None
        self.model_name: str | None = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.success: bool | None = None
        self.trace_id: str | None = None  # populated after submission

        self._client = client or KosmaClient()
        self._spans: list[Span] = []
        self._parent_stack: list[str] = []
        self._start: float | None = None
        self.latency_ms = 0
        self.status = "completed"

    def set_input_text(self, text: str) -> "TraceContext":
        self.input_text = text
        return self

    def set_model(self, provider: str, model_name: str) -> "TraceContext":
        self.model_provider = provider
        self.model_name = model_name
        return self

    def set_usage(self, input_tokens: int, output_tokens: int) -> "TraceContext":
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        return self

    def set_workflow(self, workflow_tag: str, **segment_tags) -> "TraceContext":
        self.workflow_tag = workflow_tag
        self.segment_tags.update(segment_tags)
        return self

    def set_success(self, success: bool) -> "TraceContext":
        self.success = success
        return self

    def span(self, name: str, span_type: str = "custom") -> Span:
        ref = new_span_ref()
        parent_ref = self._parent_stack[-1] if self._parent_stack else None
        return Span(self, ref, parent_ref, span_type, name)

    def _push_parent(self, ref: str) -> None:
        self._parent_stack.append(ref)

    def _pop_parent(self) -> None:
        self._parent_stack.pop()

    def _record_span(self, span: Span) -> None:
        self._spans.append(span)

    def __enter__(self) -> "TraceContext":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        assert self._start is not None
        self.latency_ms = int((time.perf_counter() - self._start) * 1000)
        if exc is not None:
            self.status = "error"
            if self.success is None:
                self.success = False
        self._submit()
        return False  # never suppress the caller's exception

    def _submit(self) -> dict:
        payload = {
            "trace_ref": self.trace_ref,
            "agent_id": self.agent_id,
            "agent_config_id": self.agent_config_id,
            "workflow_tag": self.workflow_tag,
            "segment_tags": self.segment_tags,
            "input_text": self.input_text,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "status": self.status,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "spans": [s.to_payload() for s in self._spans],
        }
        result = self._client.submit_trace(payload)
        self.trace_id = result.get("trace_id")
        return result


class Tracer:
    """Module-level entry point: `from kosma import tracer`."""

    def start_trace(
        self,
        name: str,
        *,
        agent_id: str,
        agent_config_id: str,
        workflow_tag: str | None = None,
        segment_tags: dict | None = None,
        input_text: str = "",
        client: KosmaClient | None = None,
    ) -> TraceContext:
        return TraceContext(
            name,
            agent_id=agent_id,
            agent_config_id=agent_config_id,
            workflow_tag=workflow_tag,
            segment_tags=segment_tags,
            input_text=input_text,
            client=client,
        )


tracer = Tracer()


def trace(
    name: str,
    *,
    agent_id: str,
    agent_config_id: str,
    workflow_tag: str | None = None,
    segment_tags: dict | None = None,
    client: KosmaClient | None = None,
) -> Callable:
    """Decorator form: wraps a whole function call as one trace.

        @trace(name="research-agent", agent_id=..., agent_config_id=...)
        def run_agent(query: str) -> str:
            ...

    The wrapped function's first positional argument (if any) is used as the
    trace's input_text. For finer control over spans, tool calls, or retrieval
    events inside the function, use `tracer.start_trace(...)` directly instead.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            input_text = str(args[0]) if args else kwargs.get("input_text", "")
            with tracer.start_trace(
                name,
                agent_id=agent_id,
                agent_config_id=agent_config_id,
                workflow_tag=workflow_tag,
                segment_tags=segment_tags,
                input_text=input_text,
                client=client,
            ) as t:
                try:
                    result = func(*args, **kwargs)
                    t.set_success(True)
                    return result
                except Exception:
                    t.set_success(False)
                    raise

        return wrapper

    return decorator
