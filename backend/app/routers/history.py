from fastapi import APIRouter, HTTPException
from app.services.mortgage_service import MortgageService
router = APIRouter()

@router.get("/history")
def history(limit: int = 50, only_valid: bool = True):
    with MortgageService() as s: return {"items": s.history(limit, only_valid)}

@router.get("/history/{run_id}")
def history_detail(run_id: int):
    with MortgageService() as s:
        run = s.get_run(run_id)
        if run is None: raise HTTPException(404, "run not found")
        return run

@router.post("/history/{run_id}/invalidate")
def invalidate(run_id: int):
    with MortgageService() as s:
        if s.get_run(run_id) is None: raise HTTPException(404, "run not found")
        run = s.invalidate_run(run_id)
        if run is None: raise HTTPException(404, "run not found")
        return run
