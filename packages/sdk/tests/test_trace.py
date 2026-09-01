from kosma.trace import tracer


def test_trace_with_no_spans_submits_expected_payload(fake_client):
    with tracer.start_trace(
        "test-agent",
        agent_id="agent-1",
        agent_config_id="config-1",
        input_text="hello",
        client=fake_client,
    ) as t:
        t.set_model("mock", "mock-v1")
        t.set_usage(10, 5)

    assert len(fake_client.submitted) == 1
    payload = fake_client.submitted[0]
    assert payload["agent_id"] == "agent-1"
    assert payload["agent_config_id"] == "config-1"
    assert payload["input_text"] == "hello"
    assert payload["model_provider"] == "mock"
    assert payload["model_name"] == "mock-v1"
    assert payload["input_tokens"] == 10
    assert payload["output_tokens"] == 5
    assert payload["status"] == "completed"
    assert payload["spans"] == []
    assert t.trace_id == "fake-trace-1"


def test_flat_sibling_spans_have_no_parent(fake_client):
    with tracer.start_trace(
        "test-agent", agent_id="a", agent_config_id="c", input_text="q", client=fake_client
    ) as t:
        with t.span("retrieval", span_type="retrieval"):
            pass
        with t.span("generation", span_type="llm"):
            pass

    spans = fake_client.submitted[0]["spans"]
    assert len(spans) == 2
    assert all(s["parent_ref"] is None for s in spans)
    assert [s["name"] for s in spans] == ["retrieval", "generation"]


def test_nested_spans_record_correct_parent_ref(fake_client):
    with tracer.start_trace(
        "test-agent", agent_id="a", agent_config_id="c", input_text="q", client=fake_client
    ) as t:
        with t.span("retrieval", span_type="retrieval") as outer:
            with t.span("vector_search", span_type="vector_search") as inner:
                inner.set_output(hits=3)
            outer.set_output(documents=["doc-1"])

    spans = {s["name"]: s for s in fake_client.submitted[0]["spans"]}
    assert spans["retrieval"]["parent_ref"] is None
    assert spans["vector_search"]["parent_ref"] == spans["retrieval"]["ref"]
    assert spans["vector_search"]["output"] == {"hits": 3}
    assert spans["retrieval"]["output"] == {"documents": ["doc-1"]}


def test_span_records_tool_call_and_retrieval_event(fake_client):
    with tracer.start_trace(
        "test-agent", agent_id="a", agent_config_id="c", input_text="q", client=fake_client
    ) as t:
        with t.span("lookup", span_type="tool_call") as s:
            s.set_tool_call("check_order", {"order_id": "1"}, {"status": "ok"})
        with t.span("search", span_type="retrieval") as s:
            s.set_retrieval("refund policy", [{"doc_id": "d1", "score": 0.9}])

    spans = {s["name"]: s for s in fake_client.submitted[0]["spans"]}
    assert spans["lookup"]["tool_call"]["tool_name"] == "check_order"
    assert spans["lookup"]["tool_call"]["success"] is True
    assert spans["search"]["retrieval_event"]["query"] == "refund policy"
    assert spans["search"]["retrieval_event"]["documents"][0]["doc_id"] == "d1"


def test_exception_inside_trace_marks_failure_but_still_submits_and_reraises(fake_client):
    class Boom(Exception):
        pass

    try:
        with tracer.start_trace(
            "test-agent", agent_id="a", agent_config_id="c", input_text="q", client=fake_client
        ) as t:
            raise Boom("kaboom")
    except Boom:
        pass
    else:
        raise AssertionError("expected Boom to propagate out of the trace context manager")

    payload = fake_client.submitted[0]
    assert payload["status"] == "error"
    assert payload["success"] is False


def test_exception_inside_span_records_error_but_reraises(fake_client):
    class Boom(Exception):
        pass

    try:
        with tracer.start_trace(
            "test-agent", agent_id="a", agent_config_id="c", input_text="q", client=fake_client
        ) as t:
            with t.span("risky"):
                raise Boom("nope")
    except Boom:
        pass
    else:
        raise AssertionError("expected Boom to propagate out of the span context manager")

    span = fake_client.submitted[0]["spans"][0]
    assert "Boom" in span["error"]


def test_trace_decorator_uses_first_arg_as_input_text_and_sets_success(fake_client):
    from kosma.trace import trace

    @trace("decorated-agent", agent_id="a", agent_config_id="c", client=fake_client)
    def run(query: str) -> str:
        return f"answer to {query}"

    result = run("what is the refund policy?")

    assert result == "answer to what is the refund policy?"
    payload = fake_client.submitted[0]
    assert payload["input_text"] == "what is the refund policy?"
    assert payload["success"] is True


def test_trace_decorator_marks_failure_and_reraises_on_exception(fake_client):
    from kosma.trace import trace

    @trace("decorated-agent", agent_id="a", agent_config_id="c", client=fake_client)
    def run(query: str) -> str:
        raise ValueError("bad input")

    try:
        run("bad query")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError to propagate")

    payload = fake_client.submitted[0]
    assert payload["success"] is False
