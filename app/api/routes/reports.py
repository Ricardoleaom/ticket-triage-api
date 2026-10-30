from fastapi import APIRouter

from app.api.deps import ReportServiceDep, StaffUser
from app.schemas.report import SummaryReport

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=SummaryReport)
def summary(_: StaffUser, service: ReportServiceDep) -> SummaryReport:
    return service.summary()
