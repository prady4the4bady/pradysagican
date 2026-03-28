"""PHASE 24 tests: persistence + dashboard/report export."""

from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from pradysagican.api.enterprise_server import EnterpriseAPIServer


def _setup_server_with_temp_db(db_path: str) -> tuple[EnterpriseAPIServer, TestClient, str]:
    server = EnterpriseAPIServer(observability_db_path=db_path)
    client = TestClient(server.get_app())
    key = server.api_key_manager.create_test_key()
    return server, client, key


def test_dashboard_and_export_after_requests() -> None:
    db_file = Path("data") / f"observability_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.db"
    _, client, key = _setup_server_with_temp_db(str(db_file))

    # Generate at least one trace + eval
    response = client.post(
        "/process",
        json={"query": "Create a deployable architecture summary"},
        headers={"X-API-Key": key},
    )
    assert response.status_code == 200

    dashboard = client.get("/dashboard", headers={"X-API-Key": key})
    assert dashboard.status_code == 200
    d = dashboard.json()
    assert "runtime_checks" in d
    assert "metrics" in d
    assert "evaluation" in d
    assert "recent_traces" in d
    assert len(d["recent_traces"]) >= 1

    report = client.get("/reports/export?limit=20", headers={"X-API-Key": key})
    assert report.status_code == 200
    r = report.json()
    assert r["trace_count"] >= 1
    assert r["evaluation_count"] >= 1
    assert len(r["traces"]) >= 1
    assert len(r["evaluations"]) >= 1

