from fastapi import APIRouter, HTTPException
from app.schemas.schedule import ScheduleRequest
from app.services.mortgage_service import MortgageService
router = APIRouter()
@router.post("/schedule")
def post_schedule(body: ScheduleRequest):
    with MortgageService() as s:
        try:
            return s.schedule(body.principal, body.annual_rate, body.months, body.loan_id, body.persist, body.preview_rows, body.supersedes_id)
        except LookupError as e:
            raise HTTPException(404, str(e))
