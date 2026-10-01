import json
from datetime import datetime, timezone
from app.db import connect

def insert_run(box_id, overlap, result, note="", box_ids=None):
    ids = box_ids if box_ids is not None else [box_id]
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(box_id,box_ids,overlap,result_json,note,created_at) VALUES (?,?,?,?,?,?)",
            (box_id, json.dumps(ids), overlap,
             json.dumps(result, ensure_ascii=False), note,
             datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()

def _present(row):
    """列表/详情共用同一读数：合计与分盒都直接取写入快照，绝不按现尺寸重算。"""
    d = dict(row)
    result = json.loads(d.pop("result_json"))
    ids = json.loads(d.pop("box_ids")) if d.get("box_ids") else ([d.get("box_id")] if d.get("box_id") is not None else [])
    d["box_ids"] = ids
    d["result"] = result
    # 分盒为事实源；合计字段随快照一同读出（写入时即由分盒派生）
    d["boxes"] = result.get("boxes", [])
    d["total_paper_m2"] = result.get("total_paper_m2")
    d["total_box_surface_m2"] = result.get("total_box_surface_m2")
    d["box_names"] = [b.get("name") for b in result.get("boxes", [])]
    return d

def list_runs(limit=50):
    c = connect()
    try:
        rows = c.execute(
            "SELECT * FROM calc_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        # 列表与详情同一展开：分盒全量 + 写入时派生的合计，不截首盒、不重算
        return [_present(r) for r in rows]
    finally:
        c.close()

def get_run(run_id):
    c = connect()
    try:
        row = c.execute("SELECT * FROM calc_runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        # 与列表同一份 _present 展开：boxes/total/box_names 全部来自写入快照
        return _present(row)
    finally:
        c.close()

def count_runs():
    c = connect()
    try:
        return c.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        c.close()
