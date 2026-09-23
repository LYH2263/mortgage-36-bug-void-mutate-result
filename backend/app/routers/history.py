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
        run = s.get_run(run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        if run["status"] != "valid":
            raise HTTPException(409, "run already invalidated")
        updated = s.invalidate_run(run_id)
        if updated is None:  # 并发作废等兜底情形
            raise HTTPException(409, "run already invalidated")
        return updated
