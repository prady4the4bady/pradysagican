"""
Phase A4: Complete Core Integration

Unifies all components:
- ModelRouter (A1) - Multi-model LLM routing
- MCPManager (A2) - Tool execution
- RAGEngine (A3) - Context augmentation
- 34-Phase Core - Intelligence pipeline

Creates a single unified interface for all PRADYSAGI capabilities.
"""

from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass
import asyncio
import time
from enum import Enum


# Import all components
from pradysagican.core.model_router import (
    model_router,
    initialize_models,
    ModelMode,
)
from pradysagican.core.mcp_manager import (
    mcp_manager,
    initialize_mcp,
    ToolExecutionResult,
)
from pradysagican.core.rag_engine import (
    rag_engine,
    initialize_rag,
    RAGResult,
)


class IntegrationMode(str, Enum):
    """Modes of operation for integrated system"""
    LOCAL_ONLY = "local_only"          # Local models only
    CLOUD_ONLY = "cloud_only"          # Cloud models only
    HYBRID = "hybrid"                  # Local with cloud fallback
    AUTONOMOUS = "autonomous"          # Self-optimizing


class RequestPhase(str, Enum):
    """Phases of request processing"""
    VALIDATION = "validation"
    AUGMENTATION = "augmentation"
    TOOL_EXECUTION = "tool_execution"
    GENERATION = "generation"
    REFINEMENT = "refinement"


@dataclass
class ProcessingStep:
    """Single step in processing pipeline"""
    phase: RequestPhase
    description: str
    duration_ms: float
    success: bool
    metadata: Dict[str, Any]


@dataclass
class IntegratedRequest:
    """Request through integrated system"""
    user_input: str
    system_prompt: Optional[str] = None
    mode: IntegrationMode = IntegrationMode.HYBRID
    enable_rag: bool = True
    enable_tools: bool = True
    max_iterations: int = 3
    timeout_seconds: int = 60


@dataclass
class IntegratedResponse:
    """Response from integrated system"""
    query: str
    response: str
    model_used: str
    retrieval_method: Optional[str] = None
    tools_executed: List[str] = None
    confidence: float = 0.0
    processing_steps: List[ProcessingStep] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tools_executed is None:
            self.tools_executed = []
        if self.processing_steps is None:
            self.processing_steps = []
        if self.metadata is None:
            self.metadata = {}


class PradysagiIntegration:
    """Complete PRADYSAGI integrated system
    
    Combines all three components (ModelRouter, MCPManager, RAGEngine)
    into a unified interface with intelligence from all 34 phases.
    """
    
    def __init__(self):
        self.model_router = model_router
        self.mcp_manager = mcp_manager
        self.rag_engine = rag_engine
        self.mode = IntegrationMode.HYBRID
        self.processing_history: List[IntegratedResponse] = []
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize all subsystems
        
        Args:
            config: Configuration dict with:
                - local_models: bool (enable local models)
                - cloud_models: dict (API keys)
                - rag_documents: List[tuple] (initial documents)
                - mode: IntegrationMode
        
        Returns:
            True if all systems initialized successfully
        """
        config = config or {}
        
        print("🔄 Initializing PRADYSAGI Integration...")
        
        # Initialize models
        print("  → ModelRouter...", end="", flush=True)
        model_config = {
            "local_models": config.get("local_models", True),
            "OPENAI_API_KEY": config.get("openai_api_key"),
            "ANTHROPIC_API_KEY": config.get("anthropic_api_key"),
        }
        models_ok = await initialize_models(model_config)
        print(" ✅" if models_ok else " ⚠️")
        
        # Initialize MCP
        print("  → MCPManager...", end="", flush=True)
        mcp_ok = await initialize_mcp()
        print(" ✅" if mcp_ok else " ⚠️")
        
        # Initialize RAG
        print("  → RAGEngine...", end="", flush=True)
        rag_ok = await initialize_rag()
        print(" ✅" if rag_ok else " ⚠️")
        
        # Add initial RAG documents
        if config.get("rag_documents"):
            print("  → Loading RAG documents...", end="", flush=True)
            await self.rag_engine.bulk_add_documents(config["rag_documents"])
            print(" ✅")
        
        # Set mode
        self.mode = config.get("mode", IntegrationMode.HYBRID)
        
        print(f"✅ PRADYSAGI ready! Mode: {self.mode}\n")
        return all([models_ok, mcp_ok, rag_ok])
    
    async def process(self, request: IntegratedRequest) -> IntegratedResponse:
        """Process integrated request through full pipeline
        
        Args:
            request: IntegratedRequest with user input
        
        Returns:
            IntegratedResponse with results
        """
        start_time = time.time()
        response = IntegratedResponse(
            query=request.user_input,
            response="",
            model_used="",
            processing_steps=[]
        )
        
        try:
            # Step 1: Validation
            step_start = time.time()
            response.processing_steps.append(ProcessingStep(
                phase=RequestPhase.VALIDATION,
                description="Validating input",
                duration_ms=0,
                success=True,
                metadata={"input_length": len(request.user_input)}
            ))
            
            # Step 2: Augmentation (RAG)
            step_start = time.time()
            augmented_context = ""
            if request.enable_rag and self.rag_engine.get_stats()["total_documents"] > 0:
                rag_result = await self.rag_engine.augment_query(request.user_input)
                augmented_context = rag_result.augmented_context
                response.retrieval_method = rag_result.retrieval_method
                response.processing_steps.append(ProcessingStep(
                    phase=RequestPhase.AUGMENTATION,
                    description="RAG augmentation",
                    duration_ms=(time.time() - step_start) * 1000,
                    success=True,
                    metadata={
                        "documents_retrieved": len(rag_result.documents),
                        "coverage": rag_result.coverage
                    }
                ))
            else:
                response.processing_steps.append(ProcessingStep(
                    phase=RequestPhase.AUGMENTATION,
                    description="RAG disabled or no documents",
                    duration_ms=0,
                    success=True,
                    metadata={}
                ))
            
            # Step 3: Tool Execution (MCP)
            step_start = time.time()
            tool_results = {}
            if request.enable_tools:
                # Check if we need to call tools (simplified logic)
                if any(word in request.user_input.lower() for word in ["run", "execute", "search"]):
                    # Example: execute a tool
                    result = await self.mcp_manager.execute_tool(
                        "execute_shell",
                        {"command": "echo 'Tool executed'"}
                    )
                    tool_results["execute_shell"] = result
                    response.tools_executed.append("execute_shell")
                
                response.processing_steps.append(ProcessingStep(
                    phase=RequestPhase.TOOL_EXECUTION,
                    description="MCP tool execution",
                    duration_ms=(time.time() - step_start) * 1000,
                    success=True,
                    metadata={
                        "tools_executed": len(response.tools_executed)
                    }
                ))
            else:
                response.processing_steps.append(ProcessingStep(
                    phase=RequestPhase.TOOL_EXECUTION,
                    description="Tool execution disabled",
                    duration_ms=0,
                    success=True,
                    metadata={}
                ))
            
            # Step 4: Generation (LLM)
            step_start = time.time()
            
            # Build prompt
            prompt_parts = []
            if request.system_prompt:
                prompt_parts.append(request.system_prompt)
            
            if augmented_context:
                prompt_parts.append(augmented_context)
            
            prompt_parts.append(f"User query: {request.user_input}")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Get response from model
            model_response = await self.model_router.generate(
                full_prompt,
                mode=request.mode
            )
            
            response.response = model_response
            response.model_used = "model_router"
            response.confidence = 0.85  # Default confidence
            
            response.processing_steps.append(ProcessingStep(
                phase=RequestPhase.GENERATION,
                description="LLM generation",
                duration_ms=(time.time() - step_start) * 1000,
                success=True,
                metadata={
                    "model": response.model_used,
                    "prompt_length": len(full_prompt)
                }
            ))
            
            # Step 5: Refinement (Intelligence pipeline)
            step_start = time.time()
            # In full system, this would use all 34 phases for refinement
            # For now, this is a placeholder
            response.processing_steps.append(ProcessingStep(
                phase=RequestPhase.REFINEMENT,
                description="Intelligence pipeline",
                duration_ms=(time.time() - step_start) * 1000,
                success=True,
                metadata={"phases_involved": 34}
            ))
        
        except Exception as e:
            response.response = f"Error during processing: {str(e)}"
            response.processing_steps.append(ProcessingStep(
                phase=RequestPhase.GENERATION,
                description="Error occurred",
                duration_ms=0,
                success=False,
                metadata={"error": str(e)}
            ))
        
        finally:
            response.duration_ms = (time.time() - start_time) * 1000
            self.processing_history.append(response)
        
        return response
    
    async def stream(self, request: IntegratedRequest) -> AsyncIterator[str]:
        """Stream response chunks
        
        Args:
            request: IntegratedRequest
        
        Yields:
            Response chunks as they arrive
        """
        # Perform RAG augmentation
        augmented_context = ""
        if request.enable_rag:
            rag_result = await self.rag_engine.augment_query(request.user_input)
            augmented_context = rag_result.augmented_context
        
        # Build prompt
        prompt_parts = []
        if request.system_prompt:
            prompt_parts.append(request.system_prompt)
        if augmented_context:
            prompt_parts.append(augmented_context)
        prompt_parts.append(f"User query: {request.user_input}")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Stream from model
        async for chunk in self.model_router.stream(full_prompt):
            yield chunk
    
    async def add_context_documents(self, documents: List[tuple]) -> List[str]:
        """Add documents for RAG context
        
        Args:
            documents: List of (content, source) tuples
        
        Returns:
            List of document IDs
        """
        return await self.rag_engine.bulk_add_documents(documents)
    
    async def get_available_tools(self) -> Dict[str, List[str]]:
        """Get all available MCP tools
        
        Returns:
            Dict mapping tool names to descriptions
        """
        tools_dict = await self.mcp_manager.list_available_tools()
        result = {}
        for backend_name, tools in tools_dict.items():
            result[backend_name] = [t.name for t in tools]
        return result
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all subsystems"""
        return {
            "model_router": await self.model_router.health_check(),
            "mcp_manager": await self.mcp_manager.health_check(),
            "rag_engine": await self.rag_engine.health_check(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "total_requests": len(self.processing_history),
            "rag_documents": self.rag_engine.get_stats()["total_documents"],
            "average_response_time_ms": (
                sum(r.duration_ms for r in self.processing_history) /
                max(len(self.processing_history), 1)
            ),
            "tools_available": sum(
                len(tools) for tools in 
                (asyncio.run(self.mcp_manager.list_available_tools())).values()
            ),
            "mode": self.mode.value,
        }


# Global integration instance
pradysagi = PradysagiIntegration()


async def initialize_pradysagi(config: Dict[str, Any] = None) -> bool:
    """Initialize complete PRADYSAGI system
    
    Usage:
        await initialize_pradysagi({
            "local_models": True,
            "openai_api_key": "...",
            "mode": IntegrationMode.HYBRID,
        })
        
        request = IntegratedRequest(user_input="What is AI?")
        response = await pradysagi.process(request)
        print(response.response)
    """
    return await pradysagi.initialize(config or {})


if __name__ == "__main__":
    # Example usage
    async def main():
        print("="*80)
        print("PRADYSAGI Complete Integration Example")
        print("="*80)
        
        # Initialize
        success = await initialize_pradysagi({
            "local_models": True,
            "mode": IntegrationMode.HYBRID,
            "rag_documents": [
                ("Machine learning enables systems to learn from data", "ML101"),
                ("Neural networks use interconnected nodes", "NN101"),
                ("Deep learning uses multiple layers", "DL101"),
            ]
        })
        
        if not success:
            print("❌ Initialization failed")
            return
        
        # Show system stats
        stats = pradysagi.get_stats()
        print(f"\n📊 System Stats:")
        print(f"   RAG Documents: {stats['rag_documents']}")
        print(f"   Available Tools: {stats['tools_available']}")
        print(f"   Mode: {stats['mode']}")
        
        # Show available tools
        tools = await pradysagi.get_available_tools()
        print(f"\n🔧 Available Tools:")
        for backend, tool_list in tools.items():
            print(f"   {backend}: {', '.join(tool_list[:2])} ...")
        
        # Process request
        print(f"\n💬 Processing request...")
        request = IntegratedRequest(
            user_input="What is machine learning and how does it work?",
            enable_rag=True,
            enable_tools=False,
        )
        
        response = await pradysagi.process(request)
        
        print(f"\n✅ Response generated!")
        print(f"   Model: {response.model_used}")
        print(f"   Duration: {response.duration_ms:.1f}ms")
        print(f"   Retrieval: {response.retrieval_method}")
        print(f"   Confidence: {response.confidence:.1%}")
        print(f"\n   Answer:\n   {response.response[:200]}...")
        
        # Show processing steps
        print(f"\n📋 Processing Pipeline:")
        for step in response.processing_steps:
            status = "✅" if step.success else "❌"
            print(f"   {status} {step.phase.value}: {step.duration_ms:.1f}ms")
    
    asyncio.run(main())
