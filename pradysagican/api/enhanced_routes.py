"""
Phase B: Enhanced API Routes

Adds WebSocket streaming, RAG integration, and MCP tool execution
to the existing PRADYSAGI API server.

This module provides the missing REST/WebSocket endpoints for:
- Real-time chat with streaming
- RAG document management  
- MCP tool discovery and execution
- System configuration
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models for Phase A Integration
# ============================================================================

class ChatRequestV2(BaseModel):
    """Chat request with integration support"""
    message: str = Field(..., min_length=1, max_length=4096)
    system_prompt: Optional[str] = None
    enable_rag: bool = True
    enable_tools: bool = True


class ChatResponseV2(BaseModel):
    """Chat response with metadata"""
    query: str
    response: str
    model_used: str
    retrieval_method: Optional[str] = None
    tools_executed: List[str] = Field(default_factory=list)
    confidence: float = 0.85
    duration_ms: float
    timestamp: str


class RAGDocumentRequest(BaseModel):
    """Request to add RAG documents"""
    documents: List[Dict[str, str]]  # List of {content, source}


class MCPToolExecutionRequest(BaseModel):
    """Request to execute MCP tool"""
    tool_name: str
    params: Dict[str, Any]


class ToolInfo(BaseModel):
    """Information about an MCP tool"""
    name: str
    category: str
    description: str
    input_schema: Dict[str, Any]


# ============================================================================
# Factory Function to Add Routes to Existing App
# ============================================================================

def add_integration_routes(app: FastAPI, pradysagi_instance) -> None:
    """
    Add Phase A integration routes to existing FastAPI app
    
    Usage:
        app = FastAPI()
        # ... existing setup ...
        add_integration_routes(app, pradysagi)
    """
    
    # ────────────────────────────────────────────────────────────────────────
    # WebSocket Chat Streaming
    # ────────────────────────────────────────────────────────────────────────
    
    @app.websocket("/ws/v2/chat")
    async def websocket_chat_v2(websocket: WebSocket):
        """
        WebSocket endpoint for real-time streaming chat with integration
        
        Usage:
            ws://localhost:8000/ws/v2/chat
            
            Send: {"message": "What is AI?", "enable_rag": true}
            Receive: {"type": "chunk", "content": "text..."}
                     {"type": "complete", ...}
        """
        await websocket.accept()
        logger.info("📡 WebSocket connection established")
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                from pradysagican.core.integration import IntegratedRequest
                
                # Create request
                integrated_req = IntegratedRequest(
                    user_input=message_data.get("message", ""),
                    system_prompt=message_data.get("system_prompt"),
                    enable_rag=message_data.get("enable_rag", True),
                    enable_tools=message_data.get("enable_tools", False),
                )
                
                # Stream response
                chunk_count = 0
                try:
                    async for chunk in pradysagi_instance.stream(integrated_req):
                        chunk_count += 1
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk,
                            "chunk_id": chunk_count,
                            "timestamp": datetime.now().isoformat()
                        })
                        await asyncio.sleep(0.01)
                    
                    await websocket.send_json({
                        "type": "complete",
                        "total_chunks": chunk_count,
                        "timestamp": datetime.now().isoformat()
                    })
                
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        except Exception as e:
            logger.error(f"❌ WebSocket error: {str(e)}")
        
        finally:
            await websocket.close()
            logger.info("📡 WebSocket connection closed")
    
    
    # ────────────────────────────────────────────────────────────────────────
    # REST Chat Endpoint
    # ────────────────────────────────────────────────────────────────────────
    
    @app.post("/api/v2/chat", response_model=ChatResponseV2)
    async def rest_chat_v2(request: ChatRequestV2):
        """
        REST endpoint for chat with full integration
        
        Includes RAG augmentation and MCP tool execution
        """
        try:
            from pradysagican.core.integration import IntegratedRequest
            
            integrated_req = IntegratedRequest(
                user_input=request.message,
                system_prompt=request.system_prompt,
                enable_rag=request.enable_rag,
                enable_tools=request.enable_tools,
            )
            
            response = await pradysagi_instance.process(integrated_req)
            
            return ChatResponseV2(
                query=response.query,
                response=response.response,
                model_used=response.model_used,
                retrieval_method=response.retrieval_method,
                tools_executed=response.tools_executed,
                confidence=response.confidence,
                duration_ms=response.duration_ms,
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"❌ Chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    # ────────────────────────────────────────────────────────────────────────
    # RAG Management
    # ────────────────────────────────────────────────────────────────────────
    
    @app.post("/api/v2/rag/documents")
    async def add_rag_documents(request: RAGDocumentRequest):
        """Add documents to RAG system"""
        try:
            doc_tuples = [
                (doc["content"], doc["source"])
                for doc in request.documents
            ]
            
            doc_ids = await pradysagi_instance.add_context_documents(doc_tuples)
            
            return {
                "status": "added",
                "count": len(doc_ids),
                "doc_ids": doc_ids,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ RAG error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    @app.get("/api/v2/rag/stats")
    async def get_rag_stats():
        """Get RAG system statistics"""
        stats = pradysagi_instance.rag_engine.get_stats()
        return {
            "documents": stats["total_documents"],
            "retrieval_history": stats["retrieval_history_length"],
            "average_coverage": stats["average_coverage"],
            "timestamp": datetime.now().isoformat()
        }
    
    
    # ────────────────────────────────────────────────────────────────────────
    # MCP Tool Management
    # ────────────────────────────────────────────────────────────────────────
    
    @app.get("/api/v2/tools", response_model=Dict[str, List[ToolInfo]])
    async def list_tools_v2():
        """List all available MCP tools organized by backend"""
        tools_dict = await pradysagi_instance.mcp_manager.list_available_tools()
        
        result = {}
        for backend_name, tools in tools_dict.items():
            result[backend_name] = [
                ToolInfo(
                    name=tool.name,
                    category=tool.category.value,
                    description=tool.description,
                    input_schema=tool.input_schema
                )
                for tool in tools
            ]
        
        return result
    
    
    @app.post("/api/v2/tools/execute")
    async def execute_tool(request: MCPToolExecutionRequest):
        """Execute an MCP tool
        
        Example:
            POST /api/v2/tools/execute
            {
                "tool_name": "execute_shell",
                "params": {"command": "echo hello"}
            }
        """
        try:
            result = await pradysagi_instance.mcp_manager.execute_tool(
                request.tool_name,
                request.params
            )
            
            return {
                "tool": request.tool_name,
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Tool execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    # ────────────────────────────────────────────────────────────────────────
    # System Health & Stats
    # ────────────────────────────────────────────────────────────────────────
    
    @app.get("/api/v2/health")
    async def health_v2():
        """Check health of all integration components"""
        health = await pradysagi_instance.health_check()
        
        status = "healthy" if all(health.values()) else "degraded"
        
        return {
            "status": status,
            "components": health,
            "timestamp": datetime.now().isoformat()
        }
    
    
    @app.get("/api/v2/stats")
    async def stats_v2():
        """Get integration system statistics"""
        stats = pradysagi_instance.get_stats()
        
        return {
            "total_requests": stats["total_requests"],
            "rag_documents": stats["rag_documents"],
            "average_response_time_ms": stats["average_response_time_ms"],
            "tools_available": stats["tools_available"],
            "mode": stats["mode"],
            "timestamp": datetime.now().isoformat()
        }
    
    
    logger.info("✅ Integration routes added to API server")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Example of how to integrate with existing FastAPI app:
    
    from fastapi import FastAPI
    from pradysagican.api.enhanced_routes import add_integration_routes
    from pradysagican.core.integration import pradysagi, initialize_pradysagi
    
    app = FastAPI()
    
    @app.on_event("startup")
    async def startup():
        await initialize_pradysagi()
        add_integration_routes(app, pradysagi)
    
    # Run: uvicorn your_module:app --reload
    """
    pass
