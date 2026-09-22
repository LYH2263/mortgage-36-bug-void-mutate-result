import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from app.db import connect
from app.main import app
from app.seed import init_db


@pytest.fixture()
def client():
    init_db()
    c = connect()
    c.execute("DELETE FROM calc_runs")
    c.commit()
    c.close()
    with TestClient(app) as tc:
        yield tc


def _persist(client, **kw):
    body = {"principal": 1_000_000, "annual_rate": 3.5, "months": 360, "persist": True}
    body.update(kw)
    r = client.post("/api/schedule", json=body)
    assert r.status_code == 200
    return r.json()


def test_invalidate_returns_200_and_keeps_figures(client):
    out = _persist(client)
    rid = out["run_id"]
    r = client.post(f"/api/history/{rid}/invalidate")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "invalid"
    assert body["result"]["monthly_payment"] == out["monthly_payment"]
    assert body["result"]["total_interest"] == out["total_interest"]


def test_double_invalidate_returns_409(client):
    rid = _persist(client)["run_id"]
    assert client.post(f"/api/history/{rid}/invalidate").status_code == 200
    assert client.post(f"/api/history/{rid}/invalidate").status_code == 409


def test_invalidate_missing_run_returns_404(client):
    assert client.post("/api/history/999999/invalidate").status_code == 404


def test_default_list_hides_invalid_but_detail_readable(client):
    a = _persist(client)["run_id"]
    b = _persist(client)["run_id"]
    client.post(f"/api/history/{a}/invalidate")
    ids = [x["id"] for x in client.get("/api/history").json()["items"]]
    assert ids == [b]
    ids_all = [x["id"] for x in client.get("/api/history", params={"only_valid": "false"}).json()["items"]]
    assert ids_all == [b, a]
    d = client.get(f"/api/history/{a}")
    assert d.status_code == 200
    assert d.json()["status"] == "invalid"
    assert client.get("/api/history/999999").status_code == 404


def test_retest_flow_default_list_only_gains_new_valid_row(client):
    a = _persist(client)["run_id"]
    client.post(f"/api/history/{a}/invalidate")
    r = client.post("/api/schedule", json={
        "principal": 1_000_000, "annual_rate": 3.5, "months": 360,
        "persist": True, "supersedes_id": a,
    })
    assert r.status_code == 200
    b = r.json()["run_id"]
    items = client.get("/api/history").json()["items"]
    assert [x["id"] for x in items] == [b]
    assert items[0]["supersedes_id"] == a


def test_supersedes_missing_run_returns_404(client):
    r = client.post("/api/schedule", json={
        "principal": 1_000_000, "annual_rate": 3.5, "months": 360,
        "persist": True, "supersedes_id": 999999,
    })
    assert r.status_code == 404
