from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from kosma_api.auth import require_dashboard_session
from kosma_api.change_engine.scorecard import compute_calibration_summary
from kosma_api.db.session import get_db

router = APIRouter(prefix="/v1/scorecard", tags=["scorecard"], dependencies=[Depends(require_dashboard_session)])


@router.get("/calibration")
def get_calibration(db: Session = Depends(get_db)) -> dict:
    return compute_calibration_summary(db)
