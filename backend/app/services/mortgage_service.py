import json
from app.db import connect
from app.engines.amortization import equal_payment_schedule
from app.repositories import loans, runs, settings

class MortgageService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_loans(self): return loans.list_all(self._c)
    def loan(self, lid): return loans.get(self._c, lid)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50, only_valid=True):
        return [self._decode(r) for r in runs.list_recent(self._c, limit, only_valid)]
    def get_run(self, run_id):
        """按编号查看，失效记录同样可读（只读）。"""
        row = runs.get(self._c, run_id)
        return self._decode(row) if row else None
    def invalidate_run(self, run_id):
        """作废仅影响列表可见性：结果与输入快照原样保留；记录缺失或已作废时返回 None。"""
        if not runs.invalidate(self._c, run_id):
            return None
        return self.get_run(run_id)
    def schedule(self, principal, annual_rate, months, loan_id, persist, preview_rows=12, supersedes_id=None):
        if supersedes_id is not None and runs.get(self._c, supersedes_id) is None:
            raise LookupError(f"run {supersedes_id} not found")
        full = equal_payment_schedule(principal, annual_rate, months)
        out = {k: full[k] for k in ("monthly_payment", "total_interest", "total_payment")}
        out["preview"] = full["rows"][:preview_rows]
        out["row_count"] = len(full["rows"])
        rid = None
        if persist:
            rid = runs.insert(self._c, "schedule", {"principal": principal, "annual_rate": annual_rate, "months": months}, out, loan_id, supersedes_id)
        return {"run_id": rid, **out}
    def dashboard(self):
        items = loans.list_all(self._c)
        return {"loan_count": len(items), "clean": len([x for x in items if "种子" not in x["name"]]), "dirty": len([x for x in items if "种子" in x["name"]])}
    @staticmethod
    def _decode(row):
        row = dict(row)
        row["input"] = json.loads(row.pop("input_json") or "{}")
        row["result"] = json.loads(row.pop("result_json") or "{}")
        return row
