"""Unauthenticated, safe aggregate stats - no trace content, no secrets, just
counts. Exists so the login page can show real numbers instead of a
decorative illustration (see apps/web/src/components/login-visual.tsx)."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kosma_api.db.session import get_db
from kosma_api.models.change_proposal import ChangeProposal, ChangeProposalStatus
from kosma_api.models.impact_report import ImpactReport
from kosma_api.models.trace import Trace

router = APIRouter(prefix="/v1/public", tags=["public"])


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)) -> dict:
    total_traces = db.scalar(select(func.count()).select_from(Trace)) or 0
    total_analyzed = db.scalar(
        select(func.count())
        .select_from(ChangeProposal)
        .where(ChangeProposal.status.in_([ChangeProposalStatus.analyzed, ChangeProposalStatus.shipped]))
    ) or 0

    latest_report = db.scalar(select(ImpactReport).order_by(ImpactReport.created_at.desc()).limit(1))
    latest = None
    if latest_report is not None:
        latest = {
            "recommendation": latest_report.recommendation.value
            if hasattr(latest_report.recommendation, "value")
            else str(latest_report.recommendation),
            "confidence": latest_report.confidence,
            # Segment success deltas only - no trace content, no input text, no
            # evidence trace IDs. Safe to show unauthenticated: it's what the
            # login page's Blast Radius Diff visual renders as real (not
            # illustrative) data.
            "segment_metrics": [
                {
                    "segment": s["segment"],
                    "workflow": s["workflow"],
                    "region": s["region"],
                    "success_delta": s["success_delta"],
                    "baseline_success_rate": s["baseline_success_rate"],
                    "candidate_success_rate": s["candidate_success_rate"],
                    "sample_size": s["sample_size"],
                }
                for s in latest_report.segment_metrics
            ],
        }

    return {
        "total_traces": total_traces,
        "total_analyzed_changes": total_analyzed,
        "latest_impact_report": latest,
    }
