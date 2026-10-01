"""regress: bug-nest-open-first-only —— 多盒套装回看不许截成首盒。

列表与详情都必须完整展开写入快照的分盒数组，合计保持写入时由分盒
求和派生的值，盒名串覆盖全部分盒；改盒尺寸后回读仍不跟现行尺寸回刷。

无 pytest/fastapi 环境也能跑：python3 app/tests/test_nest_open_regress.py
"""
import contextlib
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

_tmp = tempfile.TemporaryDirectory()
os.environ["DATA_DIR"] = _tmp.name
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app import seed  # noqa: E402
from app.db import connect  # noqa: E402
from app.repositories import history  # noqa: E402
from app.services import estimate_service as svc  # noqa: E402

seed.init_db()

CLEAN = [1, 2]


def _update_box(bid, **fields):
    c = connect()
    try:
        sets = ",".join(f"{k}=?" for k in fields)
        c.execute(f"UPDATE boxes SET {sets} WHERE id=?", (*fields.values(), bid))
        c.commit()
    finally:
        c.close()


def test_detail_keeps_all_boxes_and_written_total():
    """详情：分盒全量展开，合计等于写入值（=分盒求和），不截首盒、不按首盒重算。"""
    r = svc.run_estimate(CLEAN, None, "cross", True, "regress")
    d = history.get_run(r["run_id"])
    assert [b["box_id"] for b in d["boxes"]] == CLEAN
    assert [b["box_id"] for b in d["result"]["boxes"]] == CLEAN
    assert d["total_paper_m2"] == r["total_paper_m2"]
    assert d["result"]["total_paper_m2"] == r["total_paper_m2"]
    assert d["total_box_surface_m2"] == r["total_box_surface_m2"]
    assert round(sum(b["paper_m2"] for b in d["boxes"]), 3) == d["total_paper_m2"]
    # 盒名串覆盖全部分盒
    assert d["box_names"] == [b["name"] for b in r["boxes"]]


def test_list_and_detail_read_same_snapshot():
    """列表与详情同一条读数：合计、分盒、盒名串两路一致。"""
    r = svc.run_estimate(CLEAN, None, "cross", True, "")
    rid = r["run_id"]
    listed = next(x for x in history.list_runs() if x["id"] == rid)
    detail = history.get_run(rid)
    assert listed["total_paper_m2"] == detail["total_paper_m2"] == r["total_paper_m2"]
    assert [b["box_id"] for b in listed["boxes"]] == [b["box_id"] for b in detail["boxes"]] == CLEAN
    assert listed["box_names"] == detail["box_names"]


def test_reopen_after_dimension_change_not_refreshed():
    """改任一子盒边长后再开旧编号：分盒与合计不跟现行尺寸回刷。"""
    r = svc.run_estimate(CLEAN, None, "cross", True, "")
    rid = r["run_id"]
    saved_total = r["total_paper_m2"]
    saved_boxes = [dict(b, snapshot=dict(b["snapshot"])) for b in r["boxes"]]

    c = connect()
    try:
        orig = dict(c.execute("SELECT * FROM boxes WHERE id=1").fetchone())
    finally:
        c.close()
    try:
        _update_box(1, length=0.88, width=0.66, height=0.44)
        d = history.get_run(rid)
        assert d["total_paper_m2"] == saved_total
        for got, want in zip(d["boxes"], saved_boxes):
            assert got["paper_m2"] == want["paper_m2"]
            assert got["snapshot"] == want["snapshot"]
        # 单盒套装：合计必须等于该盒单测
        solo = svc.run_estimate([1], None, "cross", True, "")
        one = history.get_run(solo["run_id"])
        assert one["total_paper_m2"] == one["boxes"][0]["paper_m2"]
    finally:
        _update_box(1, length=orig["length"], width=orig["width"], height=orig["height"])


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
