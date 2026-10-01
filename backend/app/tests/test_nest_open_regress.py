"""回看开放路径回归：详情不得截首盒、不得按首盒重算合计。

历史 bug（nest_open_first_only）：列表合计等于写入，详情却把 boxes 截成
首项、total 重算成只含首盒，盒名串残缺。修复后列表/详情共用同一展开，
都直接回读写入快照。本文件用临时 sqlite 库 + 标准库打桩，无网可跑：
    python -m pytest app/tests -q   或   python3 app/tests/test_nest_open_regress.py
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

_tmp = tempfile.TemporaryDirectory()
os.environ["DATA_DIR"] = _tmp.name
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app import seed  # noqa: E402
from app.db import connect  # noqa: E402
from app.repositories import history  # noqa: E402
from app.services import estimate_service as svc  # noqa: E402

seed.init_db()

# 种子盒：1 书型盒 .30/.20/.15 clean；2 方形礼盒 .25/.25/.10 clean；3 dirty
CLEAN = [1, 2]


def _update_box(bid, **fields):
    c = connect()
    try:
        sets = ",".join(f"{k}=?" for k in fields)
        c.execute(f"UPDATE boxes SET {sets} WHERE id=?", (*fields.values(), bid))
        c.commit()
    finally:
        c.close()


def _box_row(bid):
    c = connect()
    try:
        return dict(c.execute("SELECT * FROM boxes WHERE id=?", (bid,)).fetchone())
    finally:
        c.close()


def test_detail_keeps_all_boxes_and_written_total():
    """多盒套装详情：分盒全量展开，合计==写入值==分盒求和，盒名串完整。"""
    written = svc.run_estimate(CLEAN, None, "cross", True, "套盒单")
    rid = written["run_id"]

    detail = history.get_run(rid)
    res = detail["result"]
    # 分盒不截首项：全量、保持写入顺序
    assert [b["box_id"] for b in res["boxes"]] == CLEAN
    assert [b["box_id"] for b in detail["boxes"]] == CLEAN
    # 合计不重算成只含首盒：== 写入值 == 分盒求和
    assert res["total_paper_m2"] == written["total_paper_m2"]
    assert detail["total_paper_m2"] == written["total_paper_m2"]
    assert round(sum(b["paper_m2"] for b in res["boxes"]), 3) == res["total_paper_m2"]
    assert res["total_box_surface_m2"] == written["total_box_surface_m2"]
    # 盒名串完整（不再只剩首盒）
    assert detail["box_names"] == [b["name"] for b in written["boxes"]]
    assert detail["box_ids"] == CLEAN


def test_list_and_detail_are_the_same_reading():
    """列表与详情两路读数不打架：同一条编号处处相等。"""
    written = svc.run_estimate(CLEAN, None, "cross", True, "")
    rid = written["run_id"]

    detail = history.get_run(rid)
    listed = next(x for x in history.list_runs() if x["id"] == rid)
    for key in ("total_paper_m2", "total_box_surface_m2", "box_names", "box_ids"):
        assert listed[key] == detail[key]
    assert listed["result"] == detail["result"]


def test_reopen_after_dimension_change_does_not_refresh():
    """改任一子盒边长后再开旧编号：分盒与合计不跟现行尺寸回刷。"""
    written = svc.run_estimate(CLEAN, None, "cross", True, "")
    rid = written["run_id"]
    snap = [(b["box_id"], b["paper_m2"], dict(b["snapshot"])) for b in written["boxes"]]

    orig = _box_row(1)
    try:
        _update_box(1, length=0.88, width=0.66, height=0.44)
        detail = history.get_run(rid)
        assert detail["total_paper_m2"] == written["total_paper_m2"]
        for (bid, pm, old_snap), got in zip(snap, detail["result"]["boxes"]):
            assert got["box_id"] == bid
            assert got["paper_m2"] == pm
            assert got["snapshot"] == old_snap  # 仍是旧尺寸，而非 0.88/0.66/0.44
    finally:
        _update_box(1, length=orig["length"], width=orig["width"], height=orig["height"])


def test_single_box_set_total_equals_solo():
    """单盒套装：回看合计须等于该盒单测。"""
    solo = svc.run_single_estimate(1, None, "cross", False, "")
    written = svc.run_estimate([1], None, "cross", True, "")
    detail = history.get_run(written["run_id"])
    assert detail["total_paper_m2"] == solo["paper_m2"]
    assert len(detail["result"]["boxes"]) == 1
    assert detail["result"]["boxes"][0]["paper_m2"] == solo["paper_m2"]


def test_dry_rerun_cross_checks_saved_run():
    """算纸台用写入同组再干算：与旧编号合计互证（尺寸未改时完全一致）。"""
    written = svc.run_estimate(CLEAN, None, "cross", True, "")
    dry = svc.estimate_boxes(CLEAN, None, "cross")
    saved = history.get_run(written["run_id"])["result"]
    assert dry["boxes"] == saved["boxes"]
    assert dry["total_paper_m2"] == saved["total_paper_m2"]


# --- 无 pytest 时直接运行：python3 app/tests/test_nest_open_regress.py ---
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
