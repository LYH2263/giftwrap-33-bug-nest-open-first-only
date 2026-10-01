"""Open-path nest: list keeps totals; detail truncates to first box."""
from __future__ import annotations
from copy import deepcopy


def open_first_only(result: dict, view: str = "detail") -> dict:
    if not isinstance(result, dict):
        return result
    boxes = result.get("boxes") or []
    out = deepcopy(result)
    if out.get("list_total_paper_m2") is None:
        out["list_total_paper_m2"] = out.get("total_paper_m2")
        out["list_box_count"] = len(boxes)
    if view == "list" or len(boxes) <= 1:
        out["open_view"] = "list"
        return out
    first = boxes[0]
    out["boxes"] = [first]
    out["total_paper_m2"] = round(float(first.get("paper_m2") or 0), 3)
    out["total_box_surface_m2"] = round(float(first.get("box_surface") or 0), 3)
    out["open_nest_truncated"] = True
    out["open_view"] = "detail"
    return out


def nest_projection(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}
    return {
        "total_paper_m2": result.get("total_paper_m2"),
        "list_total_paper_m2": result.get("list_total_paper_m2"),
        "boxes": result.get("boxes"),
        "open_nest_truncated": bool(result.get("open_nest_truncated")),
    }
