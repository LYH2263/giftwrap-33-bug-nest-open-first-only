from fastapi import APIRouter, Query
from app.schemas.estimate import EstimateRequest
from app.services import estimate_service
router = APIRouter()

@router.get("/estimate")
def get_est(box_id: int | None = None,
            box_ids: str | None = Query(None, description="逗号分隔的多个礼盒 id"),
            overlap: float | None = None, wrap_style: str = "cross", save: bool = False):
    if box_ids is not None:
        ids = [int(x) for x in box_ids.split(",") if x != ""]
        # 多盒干算（GET 不落库）
        return estimate_service.run_estimate(ids, overlap, wrap_style, False, "")
    if box_id is None:
        # 未给任何盒子：交 service 统一拒（422）
        return estimate_service.run_estimate(None, overlap, wrap_style, False, "")
    return estimate_service.run_single_estimate(box_id, overlap, wrap_style, save, "")

@router.post("/estimate")
def post_est(body: EstimateRequest):
    if body.box_ids is not None:
        return estimate_service.run_estimate(
            body.box_ids, body.overlap, body.wrap_style, body.save, body.note)
    if body.box_id is None:
        return estimate_service.run_estimate(
            None, body.overlap, body.wrap_style, body.save, body.note)
    return estimate_service.run_single_estimate(
        body.box_id, body.overlap, body.wrap_style, body.save, body.note)
