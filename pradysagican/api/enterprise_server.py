"""
PHASE 17: ENTERPRISE REST API
==============================
Production-grade FastAPI server with authentication, rate limiting, and observability.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import time
import uuid

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pradysagican.agents.gpt_bot_catalog import GPTBotCatalog, GPTBotDefinition
from pradysagican.evaluation.framework import EvaluationCase, EvaluationFramework, EvaluationResult
from pradysagican.observability.langfuse_adapter import LangfuseAdapter
from pradysagican.observability.persistent_store import PersistentObservabilityStore

logger = logging.getLogger(__name__)


class RequestStatus(str, Enum):
    """Status of a request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HealthStatus(str, Enum):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AgentRequest(BaseModel):
    """Request to process by agent."""
    query: str
    context: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    max_tokens: int = 4096


class AgentResponse(BaseModel):
    """Response from agent."""
    request_id: str
    status: RequestStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: float
    tokens_used: int


class HealthCheckResponse(BaseModel):
    """System health check response."""
    status: HealthStatus
    timestamp: str
    uptime_seconds: float
    requests_total: int
    requests_successful: int
    requests_failed: int
    error_rate: float
    avg_response_time_ms: float


class RuntimeStatusResponse(BaseModel):
    """Runtime and deployment readiness status."""

    status: str
    checks: Dict[str, bool]
    timestamp: str


class TraceEventResponse(BaseModel):
    """Trace event payload returned by trace endpoints."""

    request_id: str
    status: str
    latency_ms: float
    tokens_used: int
    timestamp: str


class EvaluationSummaryResponse(BaseModel):
    """Aggregated evaluation summary."""

    total_requests_evaluated: int
    pass_rate: float
    avg_quality_score: float
    avg_relevance_score: float
    avg_coherence_score: float
    avg_cost_usd: float
    timestamp: str


class GPTBotRouteRequest(BaseModel):
    """Request payload for GPT bot routing."""

    query: str
    preferred_bot: Optional[str] = None
    preferred_category: Optional[str] = None


class AuthenticationError(Exception):
    """Authentication failed."""
    pass


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

class APIKeyManager:
    """Manage API keys for authentication."""
    
    def __init__(self):
        self.valid_keys: Dict[str, Dict[str, Any]] = {}
        self.create_test_key()
    
    def create_test_key(self) -> str:
        """Create a test API key."""
        key = "test-key-" + str(uuid.uuid4())
        self.valid_keys[key] = {
            "name": "test_user",
            "created_at": datetime.now().isoformat(),
            "rate_limit": 100  # calls per minute
        }
        return key
    
    def validate_key(self, api_key: str) -> Dict[str, Any]:
        """Validate an API key."""
        if api_key not in self.valid_keys:
            raise AuthenticationError("Invalid API key")
        
        return self.valid_keys[api_key]


# ============================================================================
# REQUEST TRACKING & METRICS
# ============================================================================

class RequestTracker:
    """Track requests for metrics and monitoring."""
    
    def __init__(self):
        self.requests: List[Dict[str, Any]] = []
        self.start_time = time.time()
    
    def record_request(self, request_id: str, status: RequestStatus, 
                      processing_time_ms: float, tokens_used: int,
                      error: Optional[str] = None) -> None:
        """Record request metrics."""
        self.requests.append({
            "request_id": request_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time_ms,
            "tokens_used": tokens_used,
            "error": error
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        if not self.requests:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "error_rate": 0.0,
                "avg_response_time_ms": 0.0,
                "total_tokens_used": 0,
                "uptime_seconds": time.time() - self.start_time
            }
        
        total = len(self.requests)
        successful = sum(1 for r in self.requests if r["status"] == RequestStatus.COMPLETED)
        failed = sum(1 for r in self.requests if r["status"] == RequestStatus.FAILED)
        avg_time = sum(r["processing_time_ms"] for r in self.requests) / total
        total_tokens = sum(r["tokens_used"] for r in self.requests)
        
        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": failed,
            "error_rate": failed / total if total > 0 else 0.0,
            "avg_response_time_ms": avg_time,
            "total_tokens_used": total_tokens,
            "uptime_seconds": time.time() - self.start_time
        }


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimitTracker:
    """Track rate limits per API key."""
    
    def __init__(self):
        self.key_requests: Dict[str, List[float]] = {}
    
    def check_rate_limit(self, api_key: str, limit: int = 100, 
                        window_seconds: int = 60) -> bool:
        """Check if API key is within rate limit."""
        now = time.time()
        
        if api_key not in self.key_requests:
            self.key_requests[api_key] = []
        
        # Remove old requests outside window
        self.key_requests[api_key] = [
            ts for ts in self.key_requests[api_key]
            if now - ts < window_seconds
        ]
        
        # Check if at limit
        if len(self.key_requests[api_key]) >= limit:
            return False
        
        # Record this request
        self.key_requests[api_key].append(now)
        return True


# ============================================================================
# REQUEST PROCESSING
# ============================================================================

class RequestProcessor:
    """Process incoming requests."""
    
    async def process(self, request: AgentRequest, request_id: str) -> Dict[str, Any]:
        """Process a request."""
        start_time = time.time()
        
        try:
            # Simulate processing
            await asyncio.sleep(0.1)
            
            # Estimate tokens
            tokens_used = len(request.query.split()) * 1.3
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "request_id": request_id,
                "status": RequestStatus.COMPLETED,
                "result": {
                    "response": f"Processed: {request.query[:50]}...",
                    "tools_used": request.tools or [],
                    "context_keys": list(request.context.keys()) if request.context else []
                },
                "error": None,
                "processing_time_ms": processing_time,
                "tokens_used": int(tokens_used)
            }
        
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "request_id": request_id,
                "status": RequestStatus.FAILED,
                "result": None,
                "error": str(e),
                "processing_time_ms": processing_time,
                "tokens_used": 0
            }


# ============================================================================
# ENTERPRISE API SERVER
# ============================================================================

class EnterpriseAPIServer:
    """Enterprise-grade REST API server."""
    
    def __init__(self, title: str = "PRADYSAGICAN Agent API", 
                 version: str = "1.0.0", observability_db_path: str = "data/observability.db"):
        self.version = version
        self.app = FastAPI(
            title=title,
            version=version,
            description="Enterprise AI Agent API with authentication, rate limiting, and observability"
        )
        
        self.api_key_manager = APIKeyManager()
        self.request_tracker = RequestTracker()
        self.rate_limiter = RateLimitTracker()
        self.processor = RequestProcessor()
        self.tracer = LangfuseAdapter()
        self.evaluator = EvaluationFramework()
        self.persistence = PersistentObservabilityStore(observability_db_path)
        self.bot_catalog = GPTBotCatalog()
        self.trace_events: List[Dict[str, Any]] = []
        self.evaluation_results: List[EvaluationResult] = []

        self._setup_middleware()
        self._setup_routes()

    def _runtime_checks(self) -> Dict[str, bool]:
        """Readiness checks that do not depend on external services."""
        metrics = self.request_tracker.get_metrics()
        checks = {
            "api_key_manager_ready": self.api_key_manager is not None,
            "rate_limiter_ready": self.rate_limiter is not None,
            "request_tracker_ready": self.request_tracker is not None,
            "processor_ready": self.processor is not None,
            "bot_catalog_ready": self.bot_catalog is not None,
            "error_rate_within_slo": metrics["error_rate"] <= 0.10,
        }
        return checks

    def _extract_expected_keywords(self, query: str, limit: int = 4) -> List[str]:
        tokens = [
            t.strip(".,!?;:()[]{}\"'").lower()
            for t in query.split()
            if len(t.strip(".,!?;:()[]{}\"'")) >= 4
        ]
        seen: List[str] = []
        for t in tokens:
            if t not in seen:
                seen.append(t)
            if len(seen) >= limit:
                break
        return seen

    def _record_trace(self, request_id: str, status: RequestStatus, latency_ms: float, tokens_used: int) -> None:
        event = {
            "request_id": request_id,
            "status": status.value,
            "latency_ms": round(latency_ms, 3),
            "tokens_used": int(tokens_used),
            "timestamp": datetime.now().isoformat(),
        }
        self.trace_events.append(event)
        self.persistence.insert_trace_event(event)
        self.tracer.trace(
            name="enterprise_api.process",
            input_data={"request_id": request_id},
            output_data=event,
            metadata={"component": "enterprise_server"},
        )
    
    def _setup_middleware(self) -> None:
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        @self.app.get("/health")
        async def health_check() -> HealthCheckResponse:
            """Health check endpoint."""
            metrics = self.request_tracker.get_metrics()
            
            # Determine status
            if metrics["error_rate"] > 0.1:
                status = HealthStatus.UNHEALTHY
            elif metrics["error_rate"] > 0.05:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthCheckResponse(
                status=status,
                timestamp=datetime.now().isoformat(),
                uptime_seconds=metrics["uptime_seconds"],
                requests_total=metrics["total_requests"],
                requests_successful=metrics["successful_requests"],
                requests_failed=metrics["failed_requests"],
                error_rate=metrics["error_rate"],
                avg_response_time_ms=metrics["avg_response_time_ms"]
            )

        @self.app.get("/live")
        async def live_check() -> Dict[str, Any]:
            """Liveness probe for container orchestration."""
            return {"status": "alive", "timestamp": datetime.now().isoformat()}

        @self.app.get("/ready")
        async def ready_check() -> RuntimeStatusResponse:
            """Readiness probe with internal component checks."""
            checks = self._runtime_checks()
            ready = all(checks.values())
            return RuntimeStatusResponse(
                status="ready" if ready else "not_ready",
                checks=checks,
                timestamp=datetime.now().isoformat(),
            )

        @self.app.get("/version")
        async def version_info() -> Dict[str, str]:
            """Runtime version metadata."""
            return {"name": "pradysagican-enterprise-api", "version": self.version}
        
        @self.app.post("/process")
        async def process_request(
            request: AgentRequest,
            x_api_key: str = Header(None)
        ) -> AgentResponse:
            """Process a request with authentication and rate limiting."""
            
            # Authentication
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            
            try:
                key_info = self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Rate limiting
            if not self.rate_limiter.check_rate_limit(x_api_key, 
                                                      key_info.get("rate_limit", 100)):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Process request
            request_id = str(uuid.uuid4())
            result = await self.processor.process(request, request_id)
            
            # Track metrics
            self.request_tracker.record_request(
                request_id=request_id,
                status=result["status"],
                processing_time_ms=result["processing_time_ms"],
                tokens_used=result["tokens_used"],
                error=result["error"]
            )

            self._record_trace(
                request_id=request_id,
                status=result["status"],
                latency_ms=result["processing_time_ms"],
                tokens_used=result["tokens_used"],
            )

            evaluation_case = EvaluationCase(
                case_id=request_id,
                prompt=request.query,
                expected_keywords=self._extract_expected_keywords(request.query),
                max_latency_ms=2000.0,
                max_cost_usd=0.02,
            )
            evaluation_result = self.evaluator.evaluate_case(
                model_name="enterprise_api_default",
                case=evaluation_case,
                output=result["result"]["response"] if result.get("result") else "",
                latency_ms=float(result["processing_time_ms"]),
                token_input=max(1, len(request.query.split())),
                token_output=max(1, int(result["tokens_used"])),
            )
            self.evaluation_results.append(evaluation_result)
            self.persistence.insert_evaluation_result(evaluation_result.__dict__)

            return AgentResponse(**result)
        
        @self.app.get("/metrics")
        async def get_metrics(x_api_key: str = Header(None)) -> Dict[str, Any]:
            """Get system metrics."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            return self.request_tracker.get_metrics()
        
        @self.app.get("/keys/test")
        async def get_test_key() -> Dict[str, str]:
            """Get a test API key (dev only)."""
            key = self.api_key_manager.create_test_key()
            return {"api_key": key}

        @self.app.get("/traces")
        async def get_traces(
            x_api_key: str = Header(None),
            limit: int = 20,
        ) -> Dict[str, Any]:
            """Get recent trace events."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            sliced = self.trace_events[-max(1, min(limit, 200)) :]
            return {
                "total": len(self.trace_events),
                "items": [TraceEventResponse(**e).model_dump() for e in sliced],
            }

        @self.app.get("/evaluation/summary")
        async def evaluation_summary(x_api_key: str = Header(None)) -> EvaluationSummaryResponse:
            """Get aggregated online evaluation summary."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            if not self.evaluation_results:
                return EvaluationSummaryResponse(
                    total_requests_evaluated=0,
                    pass_rate=0.0,
                    avg_quality_score=0.0,
                    avg_relevance_score=0.0,
                    avg_coherence_score=0.0,
                    avg_cost_usd=0.0,
                    timestamp=datetime.now().isoformat(),
                )

            report = self.evaluator.build_report(
                model_name="enterprise_api_default",
                results=self.evaluation_results,
            )
            return EvaluationSummaryResponse(
                total_requests_evaluated=report.total_cases,
                pass_rate=report.pass_rate,
                avg_quality_score=report.avg_quality_score,
                avg_relevance_score=report.avg_relevance_score,
                avg_coherence_score=report.avg_coherence_score,
                avg_cost_usd=report.avg_cost_usd,
                timestamp=datetime.now().isoformat(),
            )

        @self.app.get("/dashboard")
        async def dashboard(x_api_key: str = Header(None)) -> Dict[str, Any]:
            """Unified runtime dashboard payload for frontend/system integration."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            metrics = self.request_tracker.get_metrics()
            checks = self._runtime_checks()
            eval_summary = await evaluation_summary(x_api_key=x_api_key)
            return {
                "status": "ready" if all(checks.values()) else "degraded",
                "runtime_checks": checks,
                "metrics": metrics,
                "evaluation": eval_summary.model_dump(),
                "recent_traces": self.persistence.list_traces(limit=10),
                "timestamp": datetime.now().isoformat(),
            }

        @self.app.get("/reports/export")
        async def export_reports(
            x_api_key: str = Header(None),
            limit: int = 100,
        ) -> Dict[str, Any]:
            """Export persisted traces + evaluations for offline analysis."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            traces = self.persistence.list_traces(limit=limit)
            evaluations = self.persistence.list_evaluations(limit=limit)
            return {
                "exported_at": datetime.now().isoformat(),
                "trace_count": len(traces),
                "evaluation_count": len(evaluations),
                "traces": traces,
                "evaluations": evaluations,
            }

        @self.app.get("/gpt-bots")
        async def list_gpt_bots(
            x_api_key: str = Header(None),
            category: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """List integrated GPT helper bots from the imported catalog."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            bots = self.bot_catalog.list_bots(category=category, limit=limit)
            return {
                "total": len(bots),
                "category_filter": category,
                "items": [b.to_dict() for b in bots],
            }

        @self.app.get("/gpt-bots/categories")
        async def list_gpt_bot_categories(x_api_key: str = Header(None)) -> Dict[str, Any]:
            """List available bot categories and basic architecture blueprints."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            categories = self.bot_catalog.list_categories()
            return {"total": len(categories), "items": categories}

        @self.app.get("/gpt-bots/{bot_identifier}")
        async def get_gpt_bot(
            bot_identifier: str,
            x_api_key: str = Header(None),
        ) -> Dict[str, Any]:
            """Get one bot by numeric ID or case-insensitive name."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            bot: Optional[GPTBotDefinition] = self.bot_catalog.get_bot(bot_identifier)
            if not bot:
                raise HTTPException(status_code=404, detail="GPT bot not found")
            return {"item": bot.to_dict()}

        @self.app.post("/gpt-bots/route")
        async def route_gpt_bot(
            payload: GPTBotRouteRequest,
            x_api_key: str = Header(None),
        ) -> Dict[str, Any]:
            """Route an incoming task to the best-fit helper bot architecture."""
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing API key")
            try:
                self.api_key_manager.validate_key(x_api_key)
            except AuthenticationError:
                raise HTTPException(status_code=401, detail="Invalid API key")

            try:
                route = self.bot_catalog.route(
                    query=payload.query,
                    preferred_bot=payload.preferred_bot,
                    preferred_category=payload.preferred_category,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

            return route
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application."""
        return self.app
    
    async def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Run the server."""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# ============================================================================
# MAIN
# ============================================================================

def create_api_server() -> FastAPI:
    """Factory function to create the API server."""
    server = EnterpriseAPIServer()
    return server.get_app()


if __name__ == "__main__":
    # For direct execution
    app = create_api_server()
    uvicorn.run(app, host="0.0.0.0", port=8000)
