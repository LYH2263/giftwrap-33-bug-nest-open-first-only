from fastapi import HTTPException
from app.engines.wrap_math import paper_area, ribbon_estimate
from app.repositories import boxes, history, settings_repo


def _normalize_ids(ids) -> list[int]:
    if not ids:
        raise HTTPException(422, "box_ids 不能为空")
    ids = list(ids)
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "box_ids 含重复礼盒")
    return ids


def estimate_boxes(ids: list[int], overlap: float | None, wrap_style: str) -> dict:
    """干算：校验整组盒子并逐盒落地面积。不写库，落库与回看共用本结果。

    口径拍板：先逐盒算分盒（尺寸在此时快照），合计由分盒数组求和派生，
    分盒数组是唯一事实源，两路读数永不打架。
    """
    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()

    # 先把整组盒子全部取齐并校验，任一缺失/dirty 则整单失败（调用方不会写行）
    found = []
    for bid in ids:
        box = boxes.get_box(bid)
        if not box:
            raise HTTPException(404, f"box {bid} 不存在")
        if box.get("data_quality") == "dirty":
            raise HTTPException(422, f"box {bid} 为 dirty，整单拒收")
        found.append(box)

    details = []
    for box in found:
        calc = paper_area(box["length"], box["width"], box["height"], ov)
        ribbon = ribbon_estimate(box["length"], box["width"], box["height"], wrap_style)
        details.append({
            "box_id": box["id"],
            "name": box["name"],
            # 写入快照：此后盒子长宽高再改，本单读数不变
            "snapshot": {
                "length": box["length"], "width": box["width"], "height": box["height"],
                "data_quality": box.get("data_quality"),
            },
            "box_surface": calc["box_surface"],
            "paper_m2": calc["paper_m2"],
            "ribbon_m": ribbon["ribbon_m"],
        })

    # 合计 = 分盒读数求和后再按同一精度取舍（派生字段，不独立落值）
    return {
        "overlap": ov,
        "wrap_style": wrap_style,
        "boxes": details,
        "total_box_surface_m2": round(sum(d["box_surface"] for d in details), 3),
        "total_paper_m2": round(sum(d["paper_m2"] for d in details), 3),
    }


def run_estimate(ids: list[int], overlap: float | None, wrap_style: str, save: bool, note: str):
    ids = _normalize_ids(ids)
    result = estimate_boxes(ids, overlap, wrap_style)
    run_id = None
    if save:
        run_id = history.insert_run(ids[0], result["overlap"], result, note, box_ids=ids)
    return {"box_ids": ids, "run_id": run_id, **result}


def run_single_estimate(box_id: int, overlap: float | None, wrap_style: str, save: bool, note: str):
    """单盒入口：合计必须与该盒单独测算完全相等（保留旧响应字段）。"""
    result = estimate_boxes([box_id], overlap, wrap_style)
    d = result["boxes"][0]
    box = boxes.get_box(box_id)
    ribbon = ribbon_estimate(box["length"], box["width"], box["height"], wrap_style)
    run_id = None
    if save:
        run_id = history.insert_run(box_id, result["overlap"], result, note, box_ids=[box_id])
    return {
        "box": box, "run_id": run_id,
        "box_surface": d["box_surface"], "paper_m2": d["paper_m2"],
        "total_box_surface_m2": result["total_box_surface_m2"],
        "total_paper_m2": result["total_paper_m2"],
        "boxes": result["boxes"], "box_ids": [box_id],
        "ribbon": ribbon,
    }
