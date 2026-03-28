"""
PHASE 17: ENTERPRISE REST API
==============================
Production-grade FastAPI server with authentication, rate limiting, and observability.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import time
import uuid

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

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
                 version: str = "1.0.0"):
        self.app = FastAPI(
            title=title,
            version=version,
            description="Enterprise AI Agent API with authentication, rate limiting, and observability"
        )
        
        self.api_key_manager = APIKeyManager()
        self.request_tracker = RequestTracker()
        self.rate_limiter = RateLimitTracker()
        self.processor = RequestProcessor()
        
        self._setup_middleware()
        self._setup_routes()
    
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
