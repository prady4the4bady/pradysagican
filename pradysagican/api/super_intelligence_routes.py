"""
SUPER-INTELLIGENCE SYSTEM ROUTES
==================================
FastAPI endpoints for the complete super-intelligence system.
Integrates all advanced capabilities into REST + WebSocket interfaces.
"""

from fastapi import APIRouter, WebSocket, HTTPException
from typing import Dict, Any, List, Optional
import json
import logging

from .super_intelligence_hub import (
    SuperIntelligenceHub,
    SystemCapability,
    MultiModalIntegration,
    AdvancedRAGSystem,
    MultiAgentCoordinator,
    get_hub,
    initialize_super_intelligence
)
from .integrated_repositories import (
    INTEGRATIONS,
    get_integration,
    list_all_repositories
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/super-intelligence", tags=["super-intelligence"])


@router.post("/initialize")
async def initialize_system() -> Dict[str, Any]:
    """Initialize the super-intelligence system."""
    hub = await initialize_super_intelligence()
    summary = hub.get_capabilities_summary()
    return {
        "status": "initialized",
        "total_capabilities": summary["total_capabilities"],
        "capabilities": summary["capabilities"]
    }


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Get current system status."""
    hub = get_hub()
    summary = hub.get_capabilities_summary()
    return {
        "status": "operational",
        "capabilities_registered": summary["total_capabilities"],
        "modules_loaded": summary["total_modules"],
        "active_models": summary["active_models"],
        "execution_count": summary["execution_count"]
    }


@router.get("/capabilities")
async def list_capabilities() -> Dict[str, List[str]]:
    """List all available capabilities."""
    hub = get_hub()
    summary = hub.get_capabilities_summary()
    return {
        "capabilities": summary["capabilities"],
        "count": len(summary["capabilities"])
    }


@router.get("/repositories")
async def list_repositories() -> Dict[str, Any]:
    """List all integrated repositories."""
    repos = list_all_repositories()
    return {
        "total_repositories": len(repos),
        "repositories": [
            {
                "name": r.name,
                "category": r.category.value,
                "description": r.description,
                "features": r.key_features
            }
            for r in repos
        ]
    }


@router.post("/execute")
async def execute_capability(
    capability: str,
    params: Dict[str, Any],
    auto_fallback: bool = True
) -> Dict[str, Any]:
    """Execute a specific capability."""
    try:
        cap = SystemCapability(capability)
        hub = get_hub()
        result = await hub.execute_capability(cap, params, auto_fallback)
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Unknown capability: {capability}")
    except Exception as e:
        logger.error(f"Error executing capability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route-task")
async def intelligent_route(
    task_description: str,
    task_params: Dict[str, Any],
    budget_limit: Optional[float] = None
) -> Dict[str, Any]:
    """Intelligently route task to best capability."""
    hub = get_hub()
    result = await hub.intelligent_route(task_description, task_params, budget_limit)
    return result


# Multi-modal Integration Endpoints
@router.post("/multimodal/process")
async def process_multimodal(
    text: Optional[str] = None,
    image_path: Optional[str] = None,
    audio_path: Optional[str] = None
) -> Dict[str, Any]:
    """Process multimodal input (text + image + audio)."""
    hub = get_hub()
    multimodal = MultiModalIntegration(hub)
    result = await multimodal.process_multimodal(text, image_path, audio_path)
    return result


# Advanced RAG Endpoints
@router.post("/rag/retrieve")
async def retrieve_documents(
    query: str,
    top_k: int = 5,
    strategy: str = "hybrid"
) -> List[Dict[str, Any]]:
    """Retrieve documents using advanced RAG."""
    hub = get_hub()
    rag = AdvancedRAGSystem(hub)
    results = await rag.retrieve_context(query, top_k, strategy)
    return results


@router.post("/rag/add-documents")
async def add_documents_to_rag(
    collection_id: str,
    documents: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Add documents to RAG system."""
    hub = get_hub()
    rag = AdvancedRAGSystem(hub)
    return await rag._semantic_search  # Placeholder


# Multi-Agent Endpoints
@router.post("/agents/spawn")
async def spawn_agent(
    role: str,
    specialization: str
) -> Dict[str, Any]:
    """Spawn a new agent with specific role."""
    hub = get_hub()
    coordinator = MultiAgentCoordinator(hub)
    agent_id = await coordinator.spawn_agent(role, specialization)
    return {
        "agent_id": agent_id,
        "role": role,
        "specialization": specialization,
        "status": "active"
    }


@router.post("/agents/coordinate")
async def coordinate_agents(task: str) -> Dict[str, Any]:
    """Coordinate multiple agents for a complex task."""
    hub = get_hub()
    coordinator = MultiAgentCoordinator(hub)
    result = await coordinator.coordinate_agents(task)
    return result


# Full Agent Integrations Endpoints
@router.post("/agents/create-workflow")
async def create_agent_workflow(
    name: str,
    steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create a workflow for full agents."""
    full_agents = get_integration("full_agents")
    if not full_agents:
        raise HTTPException(status_code=500, detail="Full agents integration not available")
    
    workflow = await full_agents.create_workflow(name, steps)
    return workflow


# LLM Runner Endpoints
@router.post("/llm/pull-model")
async def pull_llm_model(
    model_name: str,
    runner: str = "ollama"
) -> Dict[str, Any]:
    """Pull a model for local inference."""
    llm_runners = get_integration("llm_runners")
    if not llm_runners:
        raise HTTPException(status_code=500, detail="LLM runners integration not available")
    
    model = await llm_runners.pull_model(model_name, runner)
    return model


@router.post("/llm/generate")
async def generate_with_llm(
    model_id: str,
    prompt: str,
    max_tokens: int = 2048
) -> Dict[str, Any]:
    """Generate text using a local model."""
    llm_runners = get_integration("llm_runners")
    if not llm_runners:
        raise HTTPException(status_code=500, detail="LLM runners integration not available")
    
    result = await llm_runners.generate(model_id, prompt, max_tokens)
    return result


# Voice/Audio Endpoints
@router.post("/audio/transcribe")
async def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """Transcribe audio file to text."""
    voice_audio = get_integration("voice_audio")
    if not voice_audio:
        raise HTTPException(status_code=500, detail="Voice/Audio integration not available")
    
    result = await voice_audio.transcribe_audio(audio_path, language)
    return result


@router.post("/audio/tts")
async def text_to_speech(
    text: str,
    voice: str = "default",
    speed: float = 1.0
) -> Dict[str, Any]:
    """Convert text to speech."""
    voice_audio = get_integration("voice_audio")
    if not voice_audio:
        raise HTTPException(status_code=500, detail="Voice/Audio integration not available")
    
    result = await voice_audio.text_to_speech(text, voice, speed)
    return result


# Web Research Endpoints
@router.post("/research/search")
async def web_search(
    query: str,
    include_raw_content: bool = False
) -> Dict[str, Any]:
    """Perform web research."""
    web_research = get_integration("web_research")
    if not web_research:
        raise HTTPException(status_code=500, detail="Web research integration not available")
    
    results = await web_research.search_web(query, include_raw_content)
    return results


# WebSocket for Real-time Streaming
@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time task streaming."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Route message based on type
            if message.get("type") == "capability_execution":
                hub = get_hub()
                try:
                    result = await hub.execute_capability(
                        SystemCapability(message["capability"]),
                        message.get("params", {})
                    )
                    await websocket.send_json({
                        "type": "result",
                        "success": True,
                        "data": result
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
            elif message.get("type") == "task_routing":
                hub = get_hub()
                result = await hub.intelligent_route(
                    message["task_description"],
                    message.get("params", {}),
                    message.get("budget_limit")
                )
                await websocket.send_json({
                    "type": "routing_result",
                    "data": result
                })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@router.get("/export-state")
async def export_system_state() -> Dict[str, Any]:
    """Export current system state."""
    hub = get_hub()
    
    # Export to temporary file
    export_path = "/tmp/pradysagi_state.json"
    await hub.export_system_state(export_path)
    
    return {
        "exported": True,
        "path": export_path,
        "summary": hub.get_capabilities_summary()
    }


# Integration info endpoints
@router.get("/integration/{integration_name}")
async def get_integration_info(integration_name: str) -> Dict[str, Any]:
    """Get information about a specific integration."""
    integration = get_integration(integration_name)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {
        "name": integration_name,
        "class": type(integration).__name__,
        "has_repositories": hasattr(integration, 'repositories'),
        "repository_count": len(getattr(integration, 'repositories', []))
    }


@router.get("/integrations/all")
async def list_all_integrations() -> Dict[str, Any]:
    """List all available integrations."""
    integrations_list = []
    for name, integration in INTEGRATIONS.items():
        integrations_list.append({
            "name": name,
            "class": type(integration).__name__,
            "has_repositories": hasattr(integration, 'repositories')
        })
    
    return {
        "total_integrations": len(integrations_list),
        "integrations": integrations_list
    }


def add_super_intelligence_routes(app) -> None:
    """Add all super-intelligence routes to FastAPI app."""
    app.include_router(router)
    logger.info("Super-intelligence routes registered")
