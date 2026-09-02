"""Searchable institutional knowledge: every change Kosma has ever reviewed,
what it predicted, and (once shipped) what actually happened. Answers "have
we seen this before" - deterministic substring search over real rows, not
embeddings, matching this product's "deterministic first" rule (see
docs/architecture.md). A real semantic search can replace the matching logic
later without changing this endpoint's shape."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.auth import require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.agent import Agent
from kosma_api.models.change_proposal import ChangeProposal
from kosma_api.models.impact_report import ImpactReport
from kosma_api.models.prediction_outcome import PredictionOutcome

router = APIRouter(
    prefix="/v1/behavioral-memory", tags=["behavioral-memory"], dependencies=[Depends(require_dashboard_session)]
)


def _worst_segment(report: ImpactReport | None) -> dict | None:
    if report is None or not report.segment_metrics:
        return None
    worst = min(report.segment_metrics, key=lambda s: s["success_delta"])
    return {"segment": worst["segment"], "success_delta": worst["success_delta"]}


def _outcome_summary(outcome: PredictionOutcome | None) -> dict | None:
    if outcome is None or not outcome.prediction_error:
        return None
    errors = list(outcome.prediction_error.values())
    return {
        "segments_confirmed": len(errors),
        "mean_absolute_error": round(sum(abs(e) for e in errors) / len(errors), 4),
    }


def _matches(query: str, proposal: ChangeProposal, agent_name: str | None, report: ImpactReport | None) -> bool:
    haystack = " ".join(
        filter(
            None,
            [
                proposal.description,
                agent_name,
                report.recommendation.value if report and hasattr(report.recommendation, "value") else None,
                *(s["segment"] for s in (report.segment_metrics if report else [])),
            ],
        )
    ).lower()
    return query.lower() in haystack


@router.get("")
def search_behavioral_memory(
    q: str | None = Query(default=None, description="Free-text search across description, agent, and segments"),
    db: Session = Depends(get_db),
) -> dict:
    proposals = list(db.scalars(select(ChangeProposal).order_by(ChangeProposal.created_at.desc())))
    agent_names = {a.id: a.name for a in db.scalars(select(Agent))}
    reports = {r.change_proposal_id: r for r in db.scalars(select(ImpactReport))}
    outcomes = {o.change_proposal_id: o for o in db.scalars(select(PredictionOutcome))}

    items = []
    for p in proposals:
        agent_name = agent_names.get(p.agent_id)
        report = reports.get(p.id)
        if q and not _matches(q, p, agent_name, report):
            continue
        items.append(
            {
                "id": str(p.id),
                "description": p.description,
                "agent_name": agent_name,
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                "created_at": p.created_at.isoformat(),
                "recommendation": (
                    report.recommendation.value if report and hasattr(report.recommendation, "value") else None
                ),
                "confidence": report.confidence if report else None,
                "worst_segment": _worst_segment(report),
                "outcome_summary": _outcome_summary(outcomes.get(p.id)),
            }
        )

    return {"query": q, "total": len(items), "items": items}
