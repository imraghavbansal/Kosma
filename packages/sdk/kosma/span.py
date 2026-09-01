import time
import uuid


class Span:
    """A single unit of work inside a trace (retrieval, an LLM call, a tool call,
    ...). Created via `trace.span(...)` - see trace.py. Not meant to be
    instantiated directly."""

    def __init__(self, owner: "TraceContext", ref: str, parent_ref: str | None, span_type: str, name: str):
        self.owner = owner
        self.ref = ref
        self.parent_ref = parent_ref
        self.span_type = span_type
        self.name = name
        self.input: dict = {}
        self.output: dict = {}
        self.metadata: dict = {}
        self.error: str | None = None
        self.latency_ms = 0
        self.tool_call: dict | None = None
        self.retrieval_event: dict | None = None
        self._start: float | None = None

    def set_input(self, **kwargs) -> "Span":
        self.input.update(kwargs)
        return self

    def set_output(self, **kwargs) -> "Span":
        self.output.update(kwargs)
        return self

    def set_metadata(self, **kwargs) -> "Span":
        self.metadata.update(kwargs)
        return self

    def set_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        result: dict,
        *,
        valid_arguments: bool = True,
        success: bool = True,
    ) -> "Span":
        self.tool_call = {
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "valid_arguments": valid_arguments,
            "success": success,
        }
        return self

    def set_retrieval(self, query: str, documents: list[dict]) -> "Span":
        self.retrieval_event = {"query": query, "documents": documents}
        return self

    def set_error(self, message: str) -> "Span":
        self.error = message
        return self

    def __enter__(self) -> "Span":
        self._start = time.perf_counter()
        self.owner._push_parent(self.ref)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        assert self._start is not None
        self.latency_ms = int((time.perf_counter() - self._start) * 1000)
        if exc is not None:
            self.error = f"{exc_type.__name__}: {exc}"
        self.owner._pop_parent()
        self.owner._record_span(self)
        return False  # never suppress the caller's exception

    def to_payload(self) -> dict:
        return {
            "ref": self.ref,
            "parent_ref": self.parent_ref,
            "span_type": self.span_type,
            "name": self.name,
            "input": self.input,
            "output": self.output,
            "metadata": self.metadata,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "tool_call": self.tool_call,
            "retrieval_event": self.retrieval_event,
        }


def new_span_ref() -> str:
    return f"span-{uuid.uuid4().hex[:12]}"
