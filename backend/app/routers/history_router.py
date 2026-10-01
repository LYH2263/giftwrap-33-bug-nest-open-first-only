from fastapi import APIRouter, HTTPException
from app.repositories import history as repo

router = APIRouter()

@router.get("/runs")
def runs(limit: int = 50):
    return {"items": repo.list_runs(limit)}

@router.get("/runs/{run_id}")
def run_detail(run_id: int):
    # 详情与列表同源：直接回读写入快照（分盒全量 + 派生合计），无第二套投影
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404)
    return r
