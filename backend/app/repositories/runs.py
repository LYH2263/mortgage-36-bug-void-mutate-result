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
    """作废仅翻转可见性状态：不改动 result_json/input_json。

    返回 dict（首次作废成功）、None（记录不存在）、False（已是失效态，拒绝重复作废）。
    """
    row = get(conn, run_id)
    if not row:
        return None
    if row["status"] != "valid":
        return False
    cur = conn.execute(
        "UPDATE calc_runs SET status='invalid', invalidated_at=? WHERE id=? AND status='valid'",
        (_now(), run_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        return False
    return get(conn, run_id)
