import json, sqlite3
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).isoformat()

def insert(conn, kind, payload, result, loan_id=None, supersedes_id=None):
    cur = conn.execute(
        "INSERT INTO calc_runs(kind,loan_id,input_json,result_json,created_at,status,supersedes_id) VALUES (?,?,?,?,?,'valid',?)",
        (kind, loan_id, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), _now(), supersedes_id))
    conn.commit(); return int(cur.lastrowid)

def list_recent(conn, limit=50, only_valid=True):
    sql = "SELECT * FROM calc_runs"
    if only_valid:
        sql += " WHERE status='valid'"
    sql += " ORDER BY id DESC LIMIT ?"
    return [dict(r) for r in conn.execute(sql, (limit,)).fetchall()]

def get(conn, run_id):
    row = conn.execute("SELECT * FROM calc_runs WHERE id=?", (run_id,)).fetchone()
    return dict(row) if row else None

def invalidate(conn, run_id):
    row = get(conn, run_id)
    if not row:
        return False
    blank = {"monthly_payment": 0.0, "total_interest": 0.0, "total_payment": 0.0, "preview": [], "row_count": 0}
    conn.execute(
        "UPDATE calc_runs SET status='invalid', invalidated_at=?, result_json=? WHERE id=?",
        (_now(), json.dumps(blank, ensure_ascii=False), run_id),
    )
    conn.commit()
    return True
