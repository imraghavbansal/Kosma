"""The dashboard home's real question: what needs attention right now. Not a
metrics wall - a triage view over the same ChangeProposal/ImpactReport/
PredictionOutcome tables everything else reads, just assembled around
"what should I look at" instead of "what happened.\""""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.auth import require_dashboard_session
from kosma_api.change_engine.scorecard import compute_calibration_summary
from kosma_api.db.session import get_db
from kosma_api.models.agent import Agent
from kosma_api.models.change_proposal import ChangeProposal, ChangeProposalStatus
from kosma_api.models.impact_report import ImpactReport, Recommendation
from kosma_api.models.prediction_outcome import PredictionOutcome

router = APIRouter(prefix="/v1/command-center", tags=["command-center"], dependencies=[Depends(require_dashboard_session)])


def _proposal_summary(proposal: ChangeProposal, report: ImpactReport | None, agent_name: str | None) -> dict:
    return {
        "id": str(proposal.id),
        "description": proposal.description,
        "status": proposal.status.value if hasattr(proposal.status, "value") else str(proposal.status),
        "agent_name": agent_name,
        "created_at": proposal.created_at.isoformat(),
        "recommendation": (
            report.recommendation.value if report and hasattr(report.recommendation, "value") else None
        ),
        "confidence": report.confidence if report else None,
    }


@router.get("")
def get_command_center(db: Session = Depends(get_db)) -> dict:
    proposals = list(db.scalars(select(ChangeProposal).order_by(ChangeProposal.created_at.desc())))
    agent_names = {a.id: a.name for a in db.scalars(select(Agent))}
    reports = {
        r.change_proposal_id: r
        for r in db.scalars(select(ImpactReport))
    }
    outcomes_by_proposal = {
        o.change_proposal_id: o for o in db.scalars(select(PredictionOutcome))
    }

    waiting_for_review = [
        _proposal_summary(p, reports.get(p.id), agent_names.get(p.agent_id))
        for p in proposals
        if p.status == ChangeProposalStatus.analyzed
    ]

    highest_risk = [
        s
        for s in waiting_for_review
        if s["recommendation"] in (Recommendation.BLOCK.value, Recommendation.MODIFY.value)
    ]

    recent_verdicts = [
        _proposal_summary(p, reports.get(p.id), agent_names.get(p.agent_id))
        for p in proposals
        if p.id in reports
    ][:8]

    awaiting_outcome_verification = []
    for p in proposals:
        if p.status != ChangeProposalStatus.shipped:
            continue
        outcome = outcomes_by_proposal.get(p.id)
        has_confirmed_segment = outcome is not None and any(
            a.get("status") != "insufficient_data" for a in outcome.actual_metrics.values()
        )
        if not has_confirmed_segment:
            awaiting_outcome_verification.append(
                _proposal_summary(p, reports.get(p.id), agent_names.get(p.agent_id))
            )

    calibration = compute_calibration_summary(db)

    return {
        "waiting_for_review": waiting_for_review,
        "highest_risk": highest_risk,
        "recent_verdicts": recent_verdicts,
        "awaiting_outcome_verification": awaiting_outcome_verification,
        "prediction_accuracy": {
            "calibration_rate": calibration["calibration_rate"],
            "segments_evaluated": calibration["segments_evaluated"],
        },
    }
