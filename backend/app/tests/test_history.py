import json

import pytest

from app.db import connect
from app.seed import init_db
from app.services.mortgage_service import MortgageService


@pytest.fixture()
def svc():
    init_db()
    c = connect()
    c.execute("DELETE FROM calc_runs")
    c.commit()
    c.close()
    with MortgageService() as s:
        yield s


def _persist(svc, supersedes_id=None, loan_id=1):
    return svc.schedule(1_000_000, 3.5, 360, loan_id, True, 12, supersedes_id)["run_id"]


def _raw(rid):
    c = connect()
    row = c.execute("SELECT * FROM calc_runs WHERE id=?", (rid,)).fetchone()
    c.close()
    return dict(row)


def test_invalidate_marks_invalid_and_keeps_figures(svc):
    rid = _persist(svc)
    before = _raw(rid)
    run = svc.invalidate_run(rid)
    assert run["status"] == "invalid"
    assert run["invalidated_at"]
    after = _raw(rid)
    # 作废禁止改动结果：result_json 原文不变，月供与利息合计保持原值
    assert after["result_json"] == before["result_json"]
    # 作废同样禁止改动输入快照
    assert after["input_json"] == before["input_json"]
    # 钉选的 method 设置不受作废影响
    from app.db import connect as _connect
    c = _connect()
    methods = c.execute("SELECT value FROM settings WHERE key='method'").fetchall()
    c.close()
    assert [r["value"] for r in methods] == ["equal_payment"]
    result = json.loads(after["result_json"])
    assert result["monthly_payment"] == 4490.45
    assert result["total_interest"] == json.loads(before["result_json"])["total_interest"]


def test_double_invalidate_fails(svc):
    rid = _persist(svc)
    assert svc.invalidate_run(rid) is not None
    assert svc.invalidate_run(rid) is None


def test_default_history_hides_invalid(svc):
    a = _persist(svc)
    b = _persist(svc)
    svc.invalidate_run(a)
    assert [r["id"] for r in svc.history()] == [b]
    assert [r["id"] for r in svc.history(only_valid=False)] == [b, a]


def test_invalid_run_still_readable_by_id(svc):
    rid = _persist(svc)
    svc.invalidate_run(rid)
    run = svc.get_run(rid)
    assert run["status"] == "invalid"
    assert run["result"]["monthly_payment"] == 4490.45
    assert run["result"]["total_interest"] > 0


def test_persist_again_writes_new_row_with_supersedes(svc):
    a = _persist(svc)
    b = _persist(svc, supersedes_id=a)
    assert b != a
    assert svc.get_run(b)["supersedes_id"] == a
    # persist 只写新记录，不改动旧记录状态
    assert svc.get_run(a)["status"] == "valid"


def test_supersedes_must_exist(svc):
    with pytest.raises(LookupError):
        svc.schedule(100, 3.5, 12, None, True, 12, 999999)


def test_retest_flow_default_list_only_gains_new_valid_row(svc):
    a = _persist(svc)
    svc.invalidate_run(a)
    b = _persist(svc, supersedes_id=a)
    items = svc.history()
    assert [r["id"] for r in items] == [b]
    assert items[0]["supersedes_id"] == a
