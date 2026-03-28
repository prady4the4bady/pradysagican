"""
PHASE 17: ENTERPRISE REST API - TESTS
Tests for production-grade REST API with authentication and rate limiting.
"""

import pytest
from fastapi.testclient import TestClient
from pradysagican.api.enterprise_server import (
    EnterpriseAPIServer,
    RequestStatus, APIKeyManager, RateLimitTracker
)


@pytest.fixture
def api_server():
    """Create an API server for testing."""
    return EnterpriseAPIServer(observability_db_path="data/observability_test.db")


@pytest.fixture
def client(api_server):
    """Create a test client."""
    return TestClient(api_server.get_app())


@pytest.fixture
def test_api_key(api_server):
    """Get a test API key."""
    return api_server.api_key_manager.create_test_key()


class TestAPIKeyManagement:
    """Test API key authentication."""
    
    def test_create_test_key(self):
        """Test creating a test key."""
        manager = APIKeyManager()
        key = manager.create_test_key()
        
        assert key is not None
        assert key.startswith("test-key-")
    
    def test_validate_valid_key(self):
        """Test validating a valid key."""
        manager = APIKeyManager()
        key = manager.create_test_key()
        
        info = manager.validate_key(key)
        assert info["name"] == "test_user"
    
    def test_validate_invalid_key(self):
        """Test validating an invalid key."""
        manager = APIKeyManager()
        
        with pytest.raises(Exception):
            manager.validate_key("invalid-key")


class TestRateLimiting:
    """Test rate limiting."""
    
    def test_within_rate_limit(self):
        """Test that requests within limit are allowed."""
        tracker = RateLimitTracker()
        key = "test_key"
        
        # Should allow up to 5 requests
        for _ in range(5):
            result = tracker.check_rate_limit(key, limit=5, window_seconds=60)
            assert result is True
    
    def test_exceeds_rate_limit(self):
        """Test that requests exceeding limit are rejected."""
        tracker = RateLimitTracker()
        key = "test_key"
        
        # Fill up the limit
        for _ in range(5):
            tracker.check_rate_limit(key, limit=5)
        
        # Next request should fail
        result = tracker.check_rate_limit(key, limit=5)
        assert result is False


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_healthy(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "uptime_seconds" in data
        assert "requests_total" in data
    
    def test_health_check_includes_metrics(self, client):
        """Test health check includes all metrics."""
        response = client.get("/health")
        data = response.json()
        
        assert "requests_total" in data
        assert "requests_successful" in data
        assert "requests_failed" in data
        assert "error_rate" in data
        assert "avg_response_time_ms" in data


class TestRuntimeEndpoints:
    """Test runtime liveness/readiness/version endpoints."""

    def test_live_endpoint(self, client):
        response = client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_ready_endpoint(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "checks" in data
        assert "api_key_manager_ready" in data["checks"]
        assert "timestamp" in data

    def test_version_endpoint(self, client):
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "pradysagican-enterprise-api"
        assert "version" in data


class TestProcessRequest:
    """Test request processing endpoint."""
    
    def test_process_without_api_key(self, client):
        """Test that request without API key is rejected."""
        response = client.post(
            "/process",
            json={"query": "test query"}
        )
        
        assert response.status_code == 401
    
    def test_process_with_invalid_api_key(self, client):
        """Test that request with invalid API key is rejected."""
        response = client.post(
            "/process",
            json={"query": "test query"},
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401
    
    def test_process_with_valid_api_key(self, client, test_api_key):
        """Test successful request processing."""
        response = client.post(
            "/process",
            json={"query": "What is AI?"},
            headers={"X-API-Key": test_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "request_id" in data
        assert data["status"] == "completed"
        assert "result" in data
        assert data["processing_time_ms"] > 0
        assert data["tokens_used"] > 0
    
    def test_process_with_tools(self, client, test_api_key):
        """Test request processing with tools."""
        response = client.post(
            "/process",
            json={
                "query": "Search for AI papers",
                "tools": ["search", "analysis"]
            },
            headers={"X-API-Key": test_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["result"]["tools_used"] == ["search", "analysis"]
    
    def test_process_with_context(self, client, test_api_key):
        """Test request processing with context."""
        response = client.post(
            "/process",
            json={
                "query": "Analyze this",
                "context": {
                    "user_id": "123",
                    "session": "abc"
                }
            },
            headers={"X-API-Key": test_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["result"]["context_keys"]) > 0
    
    def test_rate_limit_exceeded(self, client, api_server, test_api_key):
        """Test that rate limit is enforced."""
        # Set a very low rate limit for testing
        api_server.api_key_manager.valid_keys[test_api_key]["rate_limit"] = 1
        
        # First request should succeed
        response1 = client.post(
            "/process",
            json={"query": "test"},
            headers={"X-API-Key": test_api_key}
        )
        assert response1.status_code == 200
        
        # Second request should fail (rate limit)
        response2 = client.post(
            "/process",
            json={"query": "test"},
            headers={"X-API-Key": test_api_key}
        )
        assert response2.status_code == 429


class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    def test_metrics_without_api_key(self, client):
        """Test that metrics without API key is rejected."""
        response = client.get("/metrics")
        
        assert response.status_code == 401
    
    def test_metrics_with_valid_key(self, client, test_api_key):
        """Test getting metrics with valid key."""
        response = client.get(
            "/metrics",
            headers={"X-API-Key": test_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data
        assert "error_rate" in data
        assert "avg_response_time_ms" in data
        assert "total_tokens_used" in data
    
    def test_metrics_after_requests(self, client, test_api_key):
        """Test metrics update after requests."""
        # Make a request
        client.post(
            "/process",
            json={"query": "test"},
            headers={"X-API-Key": test_api_key}
        )
        
        # Get metrics
        response = client.get(
            "/metrics",
            headers={"X-API-Key": test_api_key}
        )
        
        data = response.json()
        assert data["total_requests"] >= 1


class TestTracingAndEvaluation:
    """Test tracing and online evaluation endpoints."""

    def test_traces_endpoint_requires_auth(self, client):
        response = client.get("/traces")
        assert response.status_code == 401

    def test_traces_endpoint_after_request(self, client, test_api_key):
        client.post(
            "/process",
            json={"query": "Explain retrieval context grounding"},
            headers={"X-API-Key": test_api_key},
        )
        response = client.get("/traces", headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert "request_id" in data["items"][-1]

    def test_evaluation_summary_requires_auth(self, client):
        response = client.get("/evaluation/summary")
        assert response.status_code == 401

    def test_evaluation_summary_after_request(self, client, test_api_key):
        client.post(
            "/process",
            json={"query": "How does latency impact API quality?"},
            headers={"X-API-Key": test_api_key},
        )
        response = client.get("/evaluation/summary", headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests_evaluated"] >= 1
        assert 0.0 <= data["pass_rate"] <= 1.0
        assert "avg_quality_score" in data
        assert "avg_cost_usd" in data


class TestGPTBotCatalogEndpoints:
    """Test integrated GPT bot catalog and routing endpoints."""

    def test_list_gpt_bots_requires_auth(self, client):
        response = client.get("/gpt-bots")
        assert response.status_code == 401

    def test_list_gpt_bots(self, client, test_api_key):
        response = client.get("/gpt-bots", headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 70
        assert len(data["items"]) >= 1
        assert "name" in data["items"][0]
        assert "category" in data["items"][0]

    def test_list_gpt_bot_categories(self, client, test_api_key):
        response = client.get("/gpt-bots/categories", headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 10
        assert "Marketing" in data["items"]

    def test_get_gpt_bot_by_id(self, client, test_api_key):
        response = client.get("/gpt-bots/1", headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["item"]["id"] == 1
        assert data["item"]["name"] == "Ava"

    def test_get_gpt_bot_not_found(self, client, test_api_key):
        response = client.get("/gpt-bots/9999", headers={"X-API-Key": test_api_key})
        assert response.status_code == 404

    def test_route_gpt_bot_semantic_match(self, client, test_api_key):
        response = client.post(
            "/gpt-bots/route",
            json={"query": "Need help with SEO keywords and ad copy conversion"},
            headers={"X-API-Key": test_api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["route_type"] in ("semantic_match", "category_default")
        assert "bot" in data
        assert "architecture" in data
        assert "pipeline" in data["architecture"]
        assert len(data["architecture"]["pipeline"]) >= 1

    def test_route_gpt_bot_with_category_filter(self, client, test_api_key):
        response = client.post(
            "/gpt-bots/route",
            json={"query": "Improve my store conversion rate", "preferred_category": "E-commerce"},
            headers={"X-API-Key": test_api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bot"]["category"] == "E-commerce"

    def test_route_gpt_bot_with_invalid_category(self, client, test_api_key):
        response = client.post(
            "/gpt-bots/route",
            json={"query": "anything", "preferred_category": "Unknown Category"},
            headers={"X-API-Key": test_api_key},
        )
        assert response.status_code == 400


class TestTestKeyEndpoint:
    """Test test key generation endpoint."""
    
    def test_get_test_key(self, client):
        """Test getting a test key."""
        response = client.get("/keys/test")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "api_key" in data
        assert data["api_key"].startswith("test-key-")


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_request_format(self, client, test_api_key):
        """Test that invalid request format is handled."""
        response = client.post(
            "/process",
            json={"invalid_field": "value"},  # Missing required 'query' field
            headers={"X-API-Key": test_api_key}
        )
        
        # Should return 422 (validation error)
        assert response.status_code == 422


class TestRequestTracker:
    """Test request tracking and metrics."""
    
    def test_record_successful_request(self, api_server):
        """Test recording successful request."""
        tracker = api_server.request_tracker
        
        tracker.record_request(
            request_id="req_001",
            status=RequestStatus.COMPLETED,
            processing_time_ms=100.0,
            tokens_used=50
        )
        
        assert len(tracker.requests) == 1
    
    def test_record_failed_request(self, api_server):
        """Test recording failed request."""
        tracker = api_server.request_tracker
        
        tracker.record_request(
            request_id="req_001",
            status=RequestStatus.FAILED,
            processing_time_ms=50.0,
            tokens_used=0,
            error="Test error"
        )
        
        assert len(tracker.requests) == 1
        assert tracker.requests[0]["error"] == "Test error"
    
    def test_get_metrics(self, api_server):
        """Test getting aggregated metrics."""
        tracker = api_server.request_tracker
        
        tracker.record_request("req_001", RequestStatus.COMPLETED, 100.0, 50)
        tracker.record_request("req_002", RequestStatus.COMPLETED, 150.0, 60)
        tracker.record_request("req_003", RequestStatus.FAILED, 50.0, 0)
        
        metrics = tracker.get_metrics()
        
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 1
        assert abs(metrics["error_rate"] - 1/3) < 0.01
