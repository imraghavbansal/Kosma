"""Lightweight real analytics computed on demand from existing trace data.
Not the full embedding-based failure clustering PRODUCT-SPEC.md describes as
a future direction - this groups failed traces by workflow+segment, which is
a real, honest, deterministic aggregation over actual data rather than a
placeholder or fabricated numbers."""

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.auth import require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.trace import Trace

router = APIRouter(prefix="/v1/analytics", tags=["analytics"], dependencies=[Depends(require_dashboard_session)])


@router.get("/failure-clusters")
def failure_clusters(db: Session = Depends(get_db)) -> dict:
    failed = db.scalars(select(Trace).where(Trace.success.is_(False))).all()

    groups: dict[str, list[Trace]] = defaultdict(list)
    for trace in failed:
        region = trace.segment_tags.get("region", "unknown")
        key = f"{trace.workflow_tag}:{region}"
        groups[key].append(trace)

    clusters = [
        {
            "label": key,
            "workflow": key.split(":")[0],
            "region": key.split(":")[1],
            "count": len(traces),
            "sample_trace_ids": [str(t.id) for t in traces[:5]],
        }
        for key, traces in groups.items()
    ]
    clusters.sort(key=lambda c: c["count"], reverse=True)

    return {"clusters": clusters, "total_failures": len(failed)}
