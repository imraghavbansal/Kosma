from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from kosma_api.auth import require_project_api_key
from kosma_api.db.session import get_db
from kosma_api.embeddings import mock_embed
from kosma_api.models.project import Project
from kosma_api.models.retrieval_event import RetrievalEvent
from kosma_api.models.span import Span
from kosma_api.models.tool_call import ToolCall
from kosma_api.models.trace import Trace, TraceSource
from kosma_api.pricing import estimate_cost
from kosma_api.schemas.ingestion import TraceAcceptedOut, TraceIn

router = APIRouter(prefix="/v1", tags=["ingestion"])


@router.post("/traces", status_code=status.HTTP_202_ACCEPTED, response_model=TraceAcceptedOut)
def ingest_trace(
    body: TraceIn,
    project: Project = Depends(require_project_api_key),
    db: Session = Depends(get_db),
) -> TraceAcceptedOut:
    # trace_ref doubles as an idempotency key: the SDK generates it once per trace
    # and reuses it across retries (see kosma.client.KosmaClient). A client-side
    # timeout doesn't mean the original request failed server-side - the insert may
    # have already committed and only the response was lost - so a retry with a
    # trace_ref that already exists is treated as "already done", not an error.
    # This was found for real: concurrent seeding hit exactly this race and turned
    # a successful write into a 500 on the retry, before this check existed.
    existing = db.scalar(select(Trace).where(Trace.trace_ref == body.trace_ref))
    if existing is not None:
        return TraceAcceptedOut(trace_id=existing.id, status="queued")

    refs = [span.ref for span in body.spans]
    if len(refs) != len(set(refs)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Duplicate span refs")
    known_refs = set(refs)
    for span in body.spans:
        if span.parent_ref is not None and span.parent_ref not in known_refs:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"span '{span.ref}' has unknown parent_ref '{span.parent_ref}'",
            )

    total_tokens = body.input_tokens + body.output_tokens
    cost = estimate_cost(db, body.model_provider, body.model_name, body.input_tokens, body.output_tokens)

    trace = Trace(
        project_id=project.id,
        agent_id=body.agent_id,
        agent_config_id=body.agent_config_id,
        trace_ref=body.trace_ref,
        workflow_tag=body.workflow_tag,
        segment_tags=body.segment_tags,
        input_text=body.input_text,
        input_embedding=mock_embed(body.input_text),
        status=body.status,
        success=body.success,
        latency_ms=body.latency_ms,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        total_tokens=total_tokens,
        estimated_cost=cost,
        model_provider=body.model_provider,
        model_name=body.model_name,
        source=TraceSource.live,
    )
    db.add(trace)
    db.flush()  # assign trace.id without committing yet

    ref_to_span_id: dict[str, object] = {}
    # first pass: create spans in an order where parents are created before children
    # (spans is a flat list; parent_ref may reference an earlier or later entry, so
    # resolve in dependency order rather than assuming list order)
    remaining = list(body.spans)
    while remaining:
        progressed = False
        still_remaining = []
        for span_in in remaining:
            if span_in.parent_ref is not None and span_in.parent_ref not in ref_to_span_id:
                still_remaining.append(span_in)
                continue
            span = Span(
                trace_id=trace.id,
                parent_span_id=ref_to_span_id.get(span_in.parent_ref) if span_in.parent_ref else None,
                span_type=span_in.span_type,
                name=span_in.name,
                input=span_in.input,
                output=span_in.output,
                span_metadata=span_in.metadata,
                latency_ms=span_in.latency_ms,
                error=span_in.error,
            )
            db.add(span)
            db.flush()
            ref_to_span_id[span_in.ref] = span.id

            if span_in.tool_call is not None:
                db.add(
                    ToolCall(
                        span_id=span.id,
                        tool_name=span_in.tool_call.tool_name,
                        arguments=span_in.tool_call.arguments,
                        result=span_in.tool_call.result,
                        valid_arguments=span_in.tool_call.valid_arguments,
                        success=span_in.tool_call.success,
                    )
                )
            if span_in.retrieval_event is not None:
                db.add(
                    RetrievalEvent(
                        span_id=span.id,
                        query=span_in.retrieval_event.query,
                        documents=span_in.retrieval_event.documents,
                    )
                )
            progressed = True
        if not progressed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cyclic parent_ref chain in spans"
            )
        remaining = still_remaining

    try:
        db.commit()
    except IntegrityError:
        # Narrow race: two requests with the same trace_ref both passed the
        # existence check above before either committed. The check above handles
        # the actual failure mode we saw in practice (sequential client retries);
        # this is defense in depth for genuinely concurrent duplicates.
        db.rollback()
        existing = db.scalar(select(Trace).where(Trace.trace_ref == body.trace_ref))
        if existing is not None:
            return TraceAcceptedOut(trace_id=existing.id, status="queued")
        raise

    # Embedding + workflow/segment tagging (Phase 5) is not implemented yet - "queued"
    # accurately reflects that this trace is written but not yet enriched.
    return TraceAcceptedOut(trace_id=trace.id, status="queued")
