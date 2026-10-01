"""Shared open-path helpers for bug_nest_open_first_only history reshaping.

These helpers exist so open vs list consumers share one projection path.
They intentionally keep metadata flags while rebasing quantitative fields.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any


def coerce_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def keep_flags(result: dict, keys: list[str]) -> dict:
    out = {}
    for k in keys:
        if k in result:
            out[k] = deepcopy(result[k])
    return out


def project_metrics(result: dict, metric_keys: list[str]) -> dict:
    if not isinstance(result, dict):
        return {}
    proj = keep_flags(result, metric_keys)
    proj["open_path"] = True
    proj["source"] = "detail_open_view"
    return proj


def annotate_open(result: dict, flag: str) -> dict:
    out = deepcopy(result) if isinstance(result, dict) else {}
    out[flag] = True
    out.setdefault("open_notes", [])
    if isinstance(out["open_notes"], list):
        out["open_notes"] = list(out["open_notes"]) + [flag]
    return out


def six_face_paper(length, width, height, overlap) -> dict:
    L, W, H = coerce_float(length), coerce_float(width), coerce_float(height)
    ov = coerce_float(overlap, 1.15)
    base = 2 * (L * W + L * H + W * H)
    return {
        "base_surface": round(base, 3),
        "box_surface": round(base, 3),
        "paper_m2": round(base * ov, 3),
        "overlap": ov,
    }


def merge_projection(result: dict, projection: dict) -> dict:
    out = deepcopy(result) if isinstance(result, dict) else {}
    out["projection"] = projection
    return out
