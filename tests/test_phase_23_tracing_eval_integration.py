"""PHASE 23 tests: tracing + evaluation pipeline integration."""

from fastapi.testclient import TestClient

from pradysagican.api.enterprise_server import EnterpriseAPIServer


def test_trace_and_evaluation_state_growth() -> None:
    server = EnterpriseAPIServer()
    client = TestClient(server.get_app())
    api_key = server.api_key_manager.create_test_key()

    before_traces = len(server.trace_events)
    before_evals = len(server.evaluation_results)

    response = client.post(
        "/process",
        json={"query": "Design a resilient multi-agent orchestration strategy"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200

    assert len(server.trace_events) == before_traces + 1
    assert len(server.evaluation_results) == before_evals + 1


def test_trace_payload_shape() -> None:
    server = EnterpriseAPIServer()
    client = TestClient(server.get_app())
    api_key = server.api_key_manager.create_test_key()

    client.post(
        "/process",
        json={"query": "Summarize evaluation metrics for production APIs"},
        headers={"X-API-Key": api_key},
    )

    trace = server.trace_events[-1]
    assert "request_id" in trace
    assert "status" in trace
    assert "latency_ms" in trace
    assert "tokens_used" in trace
    assert "timestamp" in trace
