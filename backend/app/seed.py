from app.db import connect
import json

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS boxes(id INTEGER PRIMARY KEY,name TEXT,length REAL,width REAL,height REAL,data_quality TEXT,note TEXT);
    CREATE TABLE IF NOT EXISTS papers(id INTEGER PRIMARY KEY,name TEXT,roll_width REAL,data_quality TEXT,note TEXT);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,box_id INT,box_ids TEXT,overlap REAL,result_json TEXT,note TEXT,created_at TEXT);
    """)
    # 迁移：旧库补 box_ids 列（套盒合并算纸的同组 id）
    cols = {r["name"] for r in c.execute("PRAGMA table_info(calc_runs)").fetchall()}
    if "box_ids" not in cols:
        c.execute("ALTER TABLE calc_runs ADD COLUMN box_ids TEXT")
        # 旧行的同组 id 即其单盒 id，便于回看与干算互证
        c.execute("UPDATE calc_runs SET box_ids='['||box_id||']' WHERE box_id IS NOT NULL AND box_ids IS NULL")
        # 旧结果 JSON 升级为「分盒+派生合计」结构（旧行无尺寸快照，snapshot 置空）
        for row in c.execute("SELECT id,box_id,result_json FROM calc_runs").fetchall():
            try:
                old = json.loads(row["result_json"])
            except (TypeError, ValueError):
                continue
            if isinstance(old, dict) and "boxes" not in old and "paper_m2" in old:
                bname = c.execute("SELECT name FROM boxes WHERE id=?",
                                  (row["box_id"],)).fetchone()
                detail = {
                    "box_id": old.get("box_id"),
                    "name": bname["name"] if bname else None,
                    "box_surface": old.get("box_surface"),
                    "paper_m2": old.get("paper_m2"),
                    "snapshot": None,
                }
                new = {
                    "overlap": old.get("overlap"),
                    "boxes": [detail],
                    "total_box_surface_m2": old.get("box_surface"),
                    "total_paper_m2": old.get("paper_m2"),
                }
                c.execute("UPDATE calc_runs SET result_json=? WHERE id=?",
                          (json.dumps(new, ensure_ascii=False), row["id"]))
        c.commit()
    if c.execute("SELECT COUNT(*) c FROM boxes").fetchone()["c"] == 0:
        c.executemany("INSERT INTO boxes(name,length,width,height,data_quality,note) VALUES (?,?,?,?,?,?)",[
            ("书型盒",0.30,0.20,0.15,"clean",""),
            ("方形礼盒",0.25,0.25,0.10,"clean",""),
            ("脏数据-负高",0.2,0.2,-0.1,"dirty","高度负"),
        ])
        c.executemany("INSERT INTO papers(name,roll_width,data_quality,note) VALUES (?,?,?,?)",[
            ("哑光纸1.0m",1.0,"clean",""),
            ("牛皮纸0.7m",0.7,"clean",""),
        ])
        c.execute("INSERT INTO settings(key,value) VALUES ('overlap','1.15')")
        c.commit()
    c.close()
