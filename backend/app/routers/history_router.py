from fastapi import APIRouter, HTTPException
from app.repositories import history as repo
from app.services.nest_open_view import nest_projection

router = APIRouter()

@router.get("/runs")
def runs(limit: int = 50):
    return {"items": repo.list_runs(limit)}

@router.get("/runs/{run_id}")
def run_detail(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404)
    r["open_projection"] = nest_projection(r.get("result") or {})
    return r
