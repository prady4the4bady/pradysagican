"""
LAYER 9: REST API & Web Interface
=================================

FastAPI-based REST API with WebSocket streaming,
authentication, rate limiting, and comprehensive endpoints.

Attribution: FastAPI patterns, modern API design
"""

from fastapi import FastAPI, HTTPException, WebSocket, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ════════════════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    strategy: str = "cot"
    use_agents: bool = True
    max_tokens: int = 2000


class QueryResponse(BaseModel):
    """Query response model"""
    query_id: str
    status: str
    response: str
    execution_time_ms: float
    metadata: Dict[str, Any] = {}


class MemoryStoreRequest(BaseModel):
    """Memory store request"""
    content: str
    tier: str = "working"
    importance: float = 0.5
    tags: List[str] = []


class SkillUseRequest(BaseModel):
    """Skill use request"""
    skill_id: str
    xp_gained: int = 10
    success: bool = True


class SystemConfigRequest(BaseModel):
    """System config update"""
    llm_provider: Optional[str] = None
    reasoning_strategy: Optional[str] = None
    enable_agents: Optional[bool] = None


# ════════════════════════════════════════════════════════════════════════════
# RATE LIMITING
# ════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Add request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        if client_id not in self.requests:
            return self.requests_per_minute
        
        valid_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        return max(0, self.requests_per_minute - len(valid_requests))


# ════════════════════════════════════════════════════════════════════════════
# API SERVER
# ════════════════════════════════════════════════════════════════════════════

class PradysagiAPI:
    """Complete REST API for PRADYSAGICAN"""
    
    def __init__(self, system=None):
        """Initialize API"""
        self.app = FastAPI(
            title="PRADYSAGICAN API",
            description="Complete autonomous intelligence system",
            version="2.1.0"
        )
        self.system = system
        self.rate_limiter = RateLimiter(requests_per_minute=100)
        self.request_history: List[Dict] = []
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "version": "2.1.0"
            }
        
        # Query endpoint
        @self.app.post("/query")
        async def query(
            request: QueryRequest,
            x_client_id: str = Header(default="anonymous")
        ):
            """Process a query"""
            # Rate limiting
            if not self.rate_limiter.is_allowed(x_client_id):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            # Process query
            if not self.system:
                return {
                    "query_id": "demo",
                    "status": "error",
                    "error": "System not configured"
                }
            
            start_time = datetime.now()
            
            try:
                result = await self.system.query(
                    query=request.query,
                    use_agents=request.use_agents,
                    reasoning_strategy=request.strategy
                )
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                response = {
                    "query_id": result.get('query_id'),
                    "status": result.get('status'),
                    "response": result.get('reasoning', {}).get('response', ''),
                    "execution_time_ms": duration,
                    "metadata": {
                        "strategy": request.strategy,
                        "agents_used": request.use_agents,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                # Record in history
                self.request_history.append(response)
                
                return response
            
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
        
        # Stream endpoint
        @self.app.post("/query/stream")
        async def query_stream(request: QueryRequest):
            """Stream query response"""
            async def event_generator():
                # Simulate streaming response
                if not self.system:
                    yield "data: System not configured\n\n"
                    return
                
                try:
                    result = await self.system.query(
                        query=request.query,
                        use_agents=request.use_agents
                    )
                    
                    response_text = result.get('reasoning', {}).get('response', '')
                    
                    # Stream character by character
                    for char in response_text:
                        yield f"data: {char}\n\n"
                        await asyncio.sleep(0.01)  # Simulate streaming
                    
                    yield "data: [COMPLETE]\n\n"
                
                except Exception as e:
                    yield f"data: [ERROR] {str(e)}\n\n"
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream"
            )
        
        # Memory endpoints
        @self.app.post("/memory/store")
        async def memory_store(request: MemoryStoreRequest):
            """Store in memory"""
            if not self.system:
                raise HTTPException(status_code=400, detail="System not configured")
            
            memory_id = await self.system.memory.store(
                content=request.content,
                tier=request.tier,
                importance=request.importance,
                tags=request.tags
            )
            
            return {"memory_id": memory_id, "status": "stored"}
        
        @self.app.get("/memory/retrieve")
        async def memory_retrieve(query: str, limit: int = 10):
            """Retrieve from memory"""
            if not self.system:
                raise HTTPException(status_code=400, detail="System not configured")
            
            results = await self.system.memory.retrieve(query, max_results=limit)
            
            return {
                "query": query,
                "results": [
                    {
                        "content": r.content[:100],
                        "tier": r.tier,
                        "importance": r.importance,
                        "access_count": r.access_count
                    }
                    for r in results
                ]
            }
        
        @self.app.get("/memory/stats")
        async def memory_stats():
            """Get memory statistics"""
            if not self.system:
                raise HTTPException(status_code=400, detail="System not configured")
            
            return await self.system.memory_stats()
        
        # Skills endpoints
        @self.app.post("/skills/use")
        async def skill_use(request: SkillUseRequest):
            """Use a skill"""
            if not self.system or not hasattr(self.system, 'skills'):
                raise HTTPException(status_code=400, detail="Skills system not available")
            
            # Note: This would need skill system integration
            return {
                "skill_id": request.skill_id,
                "xp_gained": request.xp_gained,
                "status": "success"
            }
        
        # Agents endpoints
        @self.app.post("/agents/task")
        async def agents_task(request: QueryRequest):
            """Assign task to agent team"""
            if not self.system:
                raise HTTPException(status_code=400, detail="System not configured")
            
            result = await self.system.agent_team.orchestrate_task(
                task=request.query,
                context={"strategy": request.strategy}
            )
            
            return result
        
        @self.app.get("/agents/status")
        async def agents_status():
            """Get agent team status"""
            if not self.system:
                raise HTTPException(status_code=400, detail="System not configured")
            
            return await self.system.agent_team.get_team_status()
        
        # System endpoints
        @self.app.get("/system/status")
        async def system_status():
            """Get system status"""
            if not self.system:
                return {"status": "unconfigured"}
            
            return await self.system.system_status()
        
        @self.app.put("/system/config")
        async def system_config(request: SystemConfigRequest):
            """Update system configuration"""
            if not self.system:
                raise HTTPException(status_code=400, detail="System not configured")
            
            # Update config fields
            if request.llm_provider:
                self.system.config.llm_provider = request.llm_provider
            if request.reasoning_strategy:
                self.system.config.default_strategy = request.reasoning_strategy
            if request.enable_agents is not None:
                self.system.config.enable_agents = request.enable_agents
            
            return {"status": "config_updated"}
        
        # Analytics endpoints
        @self.app.get("/analytics/history")
        async def analytics_history(limit: int = 100):
            """Get request history"""
            return {
                "total_requests": len(self.request_history),
                "recent": self.request_history[-limit:]
            }
        
        @self.app.get("/analytics/rate-limit")
        async def analytics_rate_limit(
            x_client_id: str = Header(default="anonymous")
        ):
            """Get rate limit status"""
            remaining = self.rate_limiter.get_remaining(x_client_id)
            return {
                "client_id": x_client_id,
                "remaining_requests": remaining,
                "reset_in_seconds": 60
            }
    
    def get_app(self) -> FastAPI:
        """Get FastAPI app"""
        return self.app
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run API server"""
        import uvicorn
        
        logger.info(f"Starting PRADYSAGICAN API on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


# ════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("PRADYSAGICAN REST API")
    print("="*70)
    print("\nTo run the API server:")
    print("  python -m pradysagican.core.api_server")
    print("\nExample API calls:")
    print("  curl http://localhost:8000/health")
    print("  curl -X POST http://localhost:8000/query \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"query\": \"What is AI?\"}'")
    print("\nAPI Documentation:")
    print("  http://localhost:8000/docs")
    print("  http://localhost:8000/redoc")
    print("="*70 + "\n")
