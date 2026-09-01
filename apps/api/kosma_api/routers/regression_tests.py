import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kosma_api.auth import require_dashboard_session
from kosma_api.change_engine.regression_suite import generate_from_impact_report
from kosma_api.db.session import get_db
from kosma_api.models.change_proposal import ChangeProposal
from kosma_api.models.impact_report import ImpactReport
from kosma_api.models.regression_test import RegressionTest
from kosma_api.schemas.change_engine import RegressionTestListOut, RegressionTestOut

router = APIRouter(tags=["regression-tests"], dependencies=[Depends(require_dashboard_session)])


@router.post(
    "/v1/impact-reports/{impact_report_id}/regression-tests",
    status_code=status.HTTP_201_CREATED,
    response_model=RegressionTestListOut,
)
def create_regression_tests(impact_report_id: uuid.UUID, db: Session = Depends(get_db)) -> RegressionTestListOut:
    report = db.get(ImpactReport, impact_report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact report not found")
    proposal = db.get(ChangeProposal, report.change_proposal_id)

    existing = db.scalars(
        select(RegressionTest).where(RegressionTest.impact_report_id == impact_report_id)
    ).all()
    if existing:
        # Idempotent, same reasoning as /analyze - re-posting doesn't duplicate.
        return RegressionTestListOut(items=existing, total=len(existing))

    tests = generate_from_impact_report(db, impact_report_id=impact_report_id, project_id=proposal.project_id)
    return RegressionTestListOut(items=tests, total=len(tests))


@router.get("/v1/regression-tests", response_model=RegressionTestListOut)
def list_regression_tests(db: Session = Depends(get_db)) -> RegressionTestListOut:
    total = db.scalar(select(func.count()).select_from(RegressionTest)) or 0
    items = db.scalars(select(RegressionTest).order_by(RegressionTest.created_at.desc())).all()
    return RegressionTestListOut(items=items, total=total)


@router.get("/v1/regression-tests/{test_id}", response_model=RegressionTestOut)
def get_regression_test(test_id: uuid.UUID, db: Session = Depends(get_db)) -> RegressionTest:
    test = db.get(RegressionTest, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regression test not found")
    return test
