import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from kosma_api.auth import require_dashboard_session
from kosma_api.change_engine.analysis import run_analysis
from kosma_api.db.session import get_db
from kosma_api.models.agent_config import AgentConfig
from kosma_api.models.change_proposal import ChangeProposal, ChangeProposalStatus
from kosma_api.models.impact_report import ImpactReport
from kosma_api.schemas.change_engine import (
    ChangeProposalIn,
    ChangeProposalListOut,
    ChangeProposalOut,
    ImpactReportOut,
)

router = APIRouter(
    prefix="/v1/change-proposals", tags=["change-engine"], dependencies=[Depends(require_dashboard_session)]
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ChangeProposalOut)
def create_change_proposal(body: ChangeProposalIn, db: Session = Depends(get_db)) -> ChangeProposal:
    baseline = db.get(AgentConfig, body.baseline_config_id)
    candidate = db.get(AgentConfig, body.candidate_config_id)
    if baseline is None or candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent_config")
    if baseline.agent_id != body.agent_id or candidate.agent_id != body.agent_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baseline_config_id and candidate_config_id must belong to agent_id",
        )

    proposal = ChangeProposal(
        project_id=baseline.agent.project_id,
        agent_id=body.agent_id,
        baseline_config_id=body.baseline_config_id,
        candidate_config_id=body.candidate_config_id,
        description=body.description,
        status=ChangeProposalStatus.draft,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("", response_model=ChangeProposalListOut)
def list_change_proposals(db: Session = Depends(get_db)) -> ChangeProposalListOut:
    total = db.scalar(select(func.count()).select_from(ChangeProposal)) or 0
    items = db.scalars(select(ChangeProposal).order_by(ChangeProposal.created_at.desc())).all()
    return ChangeProposalListOut(items=items, total=total)


@router.get("/{proposal_id}", response_model=ChangeProposalOut)
def get_change_proposal(proposal_id: uuid.UUID, db: Session = Depends(get_db)) -> ChangeProposal:
    proposal = db.get(ChangeProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change proposal not found")
    return proposal


@router.post("/{proposal_id}/analyze", response_model=ImpactReportOut)
def analyze_change_proposal(proposal_id: uuid.UUID, db: Session = Depends(get_db)) -> ImpactReport:
    proposal = db.get(ChangeProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change proposal not found")

    existing = db.scalar(select(ImpactReport).where(ImpactReport.change_proposal_id == proposal_id))
    if existing is not None:
        # Analysis is idempotent: re-POSTing an already-analyzed proposal returns
        # the existing report rather than re-running (and re-inserting replay
        # traces) a second time.
        return _load_with_evidence(db, existing.id)

    proposal.status = ChangeProposalStatus.analyzing
    db.commit()

    report = run_analysis(db, proposal)
    return _load_with_evidence(db, report.id)


@router.get("/{proposal_id}/impact-report", response_model=ImpactReportOut)
def get_impact_report(proposal_id: uuid.UUID, db: Session = Depends(get_db)) -> ImpactReport:
    report = db.scalar(select(ImpactReport).where(ImpactReport.change_proposal_id == proposal_id))
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not analyzed yet")
    return _load_with_evidence(db, report.id)


def _load_with_evidence(db: Session, report_id: uuid.UUID) -> ImpactReport:
    return db.scalar(
        select(ImpactReport).where(ImpactReport.id == report_id).options(selectinload(ImpactReport.evidence))
    )
