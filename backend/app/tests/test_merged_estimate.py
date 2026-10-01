"""套盒合并用纸：分盒落地、合计派生、快照不变、干算互证。

测试用临时 sqlite 库 + fastapi 打桩，纯标准库即可跑（无网环境也能验证）：
    python -m pytest app/tests -q
"""
import contextlib
import json
import os
import sys
import tempfile
import types

try:
    import pytest
except ImportError:
    pytest = types.ModuleType("pytest")

    @contextlib.contextmanager
    def _raises(exc, *a, **kw):
        class _EI:
            value = None
        ei = _EI()
        try:
            yield ei
        except exc as e:
            ei.value = e
        else:
            raise AssertionError(f"expected {exc}")
    pytest.raises = _raises
    sys.modules["pytest"] = pytest

# --- 无 fastapi 环境下的最小打桩（CI 有真包时不影响） ---
try:
    import fastapi  # noqa: F401
except ImportError:
    fastapi = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code=400, detail=""):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    fastapi.HTTPException = HTTPException
    sys.modules.setdefault("fastapi", fastapi)

    pydantic = types.ModuleType("pydantic")

    class BaseModel:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

        def model_dump(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    pydantic.BaseModel = BaseModel
    sys.modules.setdefault("pydantic", pydantic)

from fastapi import HTTPException  # noqa: E402

_tmp = tempfile.TemporaryDirectory()
os.environ["DATA_DIR"] = _tmp.name
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app import seed  # noqa: E402
from app.db import connect  # noqa: E402
from app.repositories import history  # noqa: E402
from app.services import estimate_service as svc  # noqa: E402

seed.init_db()


def _box_rows():
    c = connect()
    try:
        return {r["id"]: dict(r) for r in c.execute("SELECT * FROM boxes").fetchall()}
    finally:
        c.close()


def _update_box(bid, **fields):
    c = connect()
    try:
        sets = ",".join(f"{k}=?" for k in fields)
        c.execute(f"UPDATE boxes SET {sets} WHERE id=?", (*fields.values(), bid))
        c.commit()
    finally:
        c.close()


# 种子盒：1 书型盒 .30/.20/.15 clean；2 方形礼盒 .25/.25/.10 clean；3 dirty
CLEAN = [1, 2]
DIRTY = 3


def test_single_box_total_equals_solo_estimate():
    """只交一盒：合计必须等于该盒单独测算。"""
    solo = svc.run_single_estimate(1, None, "cross", False, "")
    merged = svc.run_estimate([1], None, "cross", False, "")
    assert merged["total_paper_m2"] == solo["paper_m2"]
    assert merged["total_box_surface_m2"] == solo["box_surface"]
    assert merged["boxes"][0]["paper_m2"] == solo["paper_m2"]


def test_detail_sum_equals_total_and_is_consistent():
    """口径自洽：分盒读数之和 == 合计字段（先分盒后派生）。"""
    r = svc.run_estimate(CLEAN, None, "cross", False, "")
    assert round(sum(b["paper_m2"] for b in r["boxes"]), 3) == r["total_paper_m2"]
    assert round(sum(b["box_surface"] for b in r["boxes"]), 3) == r["total_box_surface_m2"]
    assert [b["box_id"] for b in r["boxes"]] == CLEAN


def test_empty_list_rejected_without_row():
    before = history.count_runs()
    with pytest.raises(HTTPException) as ei:
        svc.run_estimate([], None, "cross", True, "")
    assert ei.value.status_code == 422
    assert history.count_runs() == before  # 不增行


def test_dirty_or_missing_box_fails_whole_order():
    before = history.count_runs()
    # 任一 dirty：整单失败
    with pytest.raises(HTTPException) as ei:
        svc.run_estimate([1, DIRTY], None, "cross", True, "")
    assert ei.value.status_code == 422
    # 任一不存在：整单失败
    with pytest.raises(HTTPException) as ei:
        svc.run_estimate([1, 999], None, "cross", True, "")
    assert ei.value.status_code == 404
    assert history.count_runs() == before  # 均不增行


def test_duplicate_ids_rejected():
    with pytest.raises(HTTPException):
        svc.run_estimate([1, 1], None, "cross", True, "")


def test_snapshot_frozen_after_box_dimensions_change():
    """写入后改盒长宽高：列表合计与详情分盒表仍等于写入快照，不按新尺寸重算。"""
    r = svc.run_estimate(CLEAN, None, "cross", True, "套盒单")
    rid = r["run_id"]
    snap_pairs = [(b["box_id"], b["paper_m2"], b["box_surface"],
                   dict(b["snapshot"])) for b in r["boxes"]]
    total_saved = r["total_paper_m2"]

    # 改其中一盒的长宽高
    orig = _box_rows()[1]
    try:
        _update_box(1, length=0.88, width=0.66, height=0.44)

        detail = history.get_run(rid)
        listed = next(x for x in history.list_runs() if x["id"] == rid)

        for src in (detail, listed):
            res = src["result"]
            assert res["total_paper_m2"] == total_saved
            # 列表/详情两路读数不打架
            assert src["total_paper_m2"] == res["total_paper_m2"]
            for (bid, pm, bs, snap), got in zip(snap_pairs, res["boxes"]):
                assert got["box_id"] == bid
                assert got["paper_m2"] == pm
                assert got["box_surface"] == bs
                assert got["snapshot"] == snap  # 仍是旧尺寸，而非 0.88/0.66/0.44
            assert round(sum(b["paper_m2"] for b in res["boxes"]), 3) == src["total_paper_m2"]
    finally:
        _update_box(1, length=orig["length"], width=orig["width"], height=orig["height"])


def test_dry_rerun_with_same_ids_matches_saved_snapshot():
    """算纸台用写入时同一组 id 再干算，须与回看互证。"""
    r = svc.run_estimate(CLEAN, None, "cross", True, "")
    rid = r["run_id"]
    dry = svc.estimate_boxes(CLEAN, None, "cross")  # 同一组 id 干算（基于当前尺寸）
    saved = history.get_run(rid)["result"]
    # 注意：本用例在快照用例还原尺寸后运行，当前尺寸==快照尺寸，故须完全一致
    assert dry["boxes"] == saved["boxes"]
    assert dry["total_paper_m2"] == saved["total_paper_m2"]
    assert dry["total_box_surface_m2"] == saved["total_box_surface_m2"]


def test_saved_box_ids_roundtrip():
    r = svc.run_estimate(CLEAN, None, "cross", True, "")
    row = history.get_run(r["run_id"])
    assert row["box_ids"] == CLEAN
    assert json.loads(json.dumps(row["result"]))["boxes"][0]["snapshot"]["length"] > 0

# --- 无 pytest 时直接运行：python3 app/tests/test_merged_estimate.py ---
if __name__ == "__main__":
    failures = 0
    g = dict(globals())
    for name, fn in list(g.items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(e).__name__}: {e}")
    print(f"\n{len([n for n in g if n.startswith('test_')]) - failures} passed, {failures} failed")
    sys.exit(1 if failures else 0)
