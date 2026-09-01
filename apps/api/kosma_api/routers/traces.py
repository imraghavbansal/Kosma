import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from kosma_api.auth import require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.retrieval_event import RetrievalEvent
from kosma_api.models.span import Span
from kosma_api.models.tool_call import ToolCall
from kosma_api.models.trace import Trace
from kosma_api.schemas.ingestion import SpanOut, TraceListOut, TraceOut

router = APIRouter(prefix="/v1/traces", tags=["traces"], dependencies=[Depends(require_dashboard_session)])


@router.get("", response_model=TraceListOut)
def list_traces(
    workflow_tag: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
) -> TraceListOut:
    stmt = select(Trace).order_by(Trace.created_at.desc())
    count_stmt = select(func.count()).select_from(Trace)
    if workflow_tag is not None:
        stmt = stmt.where(Trace.workflow_tag == workflow_tag)
        count_stmt = count_stmt.where(Trace.workflow_tag == workflow_tag)

    total = db.scalar(count_stmt) or 0
    traces = db.scalars(stmt.limit(limit).offset(offset)).all()
    return TraceListOut(items=traces, total=total)


@router.get("/{trace_id}", response_model=TraceOut)
def get_trace(trace_id: uuid.UUID, db: Session = Depends(get_db)) -> TraceOut:
    trace = db.scalar(
        select(Trace)
        .where(Trace.id == trace_id)
        .options(
            selectinload(Trace.spans).selectinload(Span.tool_calls),
            selectinload(Trace.spans).selectinload(Span.retrieval_events),
        )
    )
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")

    spans_out = [
        SpanOut(
            id=span.id,
            parent_span_id=span.parent_span_id,
            span_type=span.span_type,
            name=span.name,
            input=span.input,
            output=span.output,
            span_metadata=span.span_metadata,
            latency_ms=span.latency_ms,
            error=span.error,
            created_at=span.created_at,
            tool_calls=[_tool_call_to_dict(tc) for tc in span.tool_calls],
            retrieval_events=[_retrieval_event_to_dict(re) for re in span.retrieval_events],
        )
        for span in trace.spans
    ]

    return TraceOut(
        id=trace.id,
        trace_ref=trace.trace_ref,
        agent_id=trace.agent_id,
        agent_config_id=trace.agent_config_id,
        workflow_tag=trace.workflow_tag,
        segment_tags=trace.segment_tags,
        input_text=trace.input_text,
        status=trace.status,
        success=trace.success,
        latency_ms=trace.latency_ms,
        input_tokens=trace.input_tokens,
        output_tokens=trace.output_tokens,
        total_tokens=trace.total_tokens,
        estimated_cost=float(trace.estimated_cost),
        model_provider=trace.model_provider,
        model_name=trace.model_name,
        source=trace.source,
        created_at=trace.created_at,
        spans=spans_out,
    )


def _tool_call_to_dict(tc: ToolCall) -> dict:
    return {
        "id": str(tc.id),
        "tool_name": tc.tool_name,
        "arguments": tc.arguments,
        "result": tc.result,
        "valid_arguments": tc.valid_arguments,
        "success": tc.success,
    }


def _retrieval_event_to_dict(re: RetrievalEvent) -> dict:
    return {"id": str(re.id), "query": re.query, "documents": re.documents}
