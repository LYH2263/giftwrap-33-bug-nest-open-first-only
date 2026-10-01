from app.db import connect

def list_papers():
    c = connect()
    try:
        return [dict(r) for r in c.execute("SELECT * FROM papers ORDER BY id").fetchall()]
    finally:
        c.close()
