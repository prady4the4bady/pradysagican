"""
PRADYSAGICAN v2.0 - Multi-Entry Point Dispatcher
Routes requests from CLI, API, MCP, and Daemon to unified core engine
"""

import uuid
import time
import logging
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .config import PradysagiConfig, get_config
from .llm_router import UniversalLLMRouter

logger = logging.getLogger(__name__)


class RequestSource(str, Enum):
    """Where the request originated"""
    CLI = "cli"
    API = "api"
    MCP = "mcp"
    DAEMON = "daemon"
    TEST = "test"


@dataclass
class RequestContext:
    """Metadata about a request"""
    source: RequestSource
    user_id: Optional[str] = None
    session_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def elapsed_seconds(self) -> float:
        """Time since request started"""
        return time.time() - self.start_time


@dataclass
class Task:
    """Represents a user task/query"""
    query: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: Optional[RequestContext] = None
    requested_tools: list = field(default_factory=list)
    priority: str = field(default="normal")  # low, normal, high, urgent
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    """Result of task execution"""
    answer: str
    task_id: str
    strategy: str  # How it was solved (direct, chain_of_thought, tree_search, etc)
    intermediate_steps: list = field(default_factory=list)
    tool_calls: list = field(default_factory=list)
    reasoning_trace: list = field(default_factory=list)
    confidence: float = 0.5
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PradysagiDispatcher:
    """
    Central dispatcher for PRADYSAGICAN v2.0
    Routes requests to appropriate interface and manages core execution
    """
    
    def __init__(self, config: Optional[PradysagiConfig] = None):
        self.config = config or get_config()
        self.llm_router = UniversalLLMRouter(self.config)
        self.session_counter = 0
        
        logger.info(
            f"Initialized PRADYSAGICAN v2.0 Dispatcher "
            f"(primary: {self.config.primary_provider.value}, "
            f"fallbacks: {[p.value for p in self.config.fallback_providers]})"
        )
    
    async def process(
        self,
        query: str,
        source: RequestSource,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Result:
        """
        Process a user query through PRADYSAGICAN
        
        Args:
            query: User query or command
            source: Where query came from
            user_id: Optional user identifier
            metadata: Additional context
        
        Returns:
            Result object with answer and metadata
        """
        
        # Create request context
        context = RequestContext(
            source=source,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Create task
        task = Task(
            query=query,
            context=context,
        )
        
        logger.info(f"[{context.trace_id}] Processing: {query[:100]}... (source: {source.value})")
        
        try:
            # Route to appropriate handler
            if source == RequestSource.CLI:
                result = await self._process_cli(task, context)
            elif source == RequestSource.API:
                result = await self._process_api(task, context)
            elif source == RequestSource.MCP:
                result = await self._process_mcp(task, context)
            elif source == RequestSource.DAEMON:
                result = await self._process_daemon(task, context)
            else:
                result = await self._process_direct(task, context)
            
            logger.info(
                f"[{context.trace_id}] Completed in {context.elapsed_seconds:.2f}s "
                f"(strategy: {result.strategy})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[{context.trace_id}] Error processing query: {e}", exc_info=True)
            return Result(
                answer=f"Error processing query: {str(e)}",
                task_id=task.task_id,
                strategy="error",
                duration_seconds=context.elapsed_seconds,
                confidence=0.0,
            )
    
    async def _process_cli(self, task: Task, context: RequestContext) -> Result:
        """Process CLI request"""
        # For CLI: prefer fast response, use lower complexity reasoning
        return await self._execute_task(task, context)
    
    async def _process_api(self, task: Task, context: RequestContext) -> Result:
        """Process API request"""
        # For API: balance speed and quality
        return await self._execute_task(task, context)
    
    async def _process_mcp(self, task: Task, context: RequestContext) -> Result:
        """Process MCP request"""
        # For MCP: can use more advanced reasoning
        return await self._execute_task(task, context)
    
    async def _process_daemon(self, task: Task, context: RequestContext) -> Result:
        """Process autonomous daemon request"""
        # For daemon: use full reasoning capabilities
        return await self._execute_task(task, context)
    
    async def _process_direct(self, task: Task, context: RequestContext) -> Result:
        """Direct processing"""
        return await self._execute_task(task, context)
    
    async def _execute_task(self, task: Task, context: RequestContext) -> Result:
        """
        Main task execution pipeline
        
        This is where the real work happens:
        1. Parse query
        2. Classify complexity
        3. Select strategy
        4. Execute with tools
        5. Return result
        """
        
        start_time = time.time()
        
        try:
            # Step 1: Classify task complexity (will implement later)
            complexity = self._classify_task(task.query)
            logger.debug(f"Task complexity: {complexity}")
            
            # Step 2: Get LLM response based on task
            llm_response = await self.llm_router.complete(
                prompt=task.query,
                model=self.config.primary_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            # Step 3: Create result
            result = Result(
                answer=llm_response,
                task_id=task.task_id,
                strategy="direct",  # Will be more complex later
                duration_seconds=time.time() - start_time,
                confidence=0.8,  # Will be calculated properly later
                metadata={
                    'source': context.source.value,
                    'complexity': complexity,
                    'provider': self.config.primary_provider.value,
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing task: {e}", exc_info=True)
            raise
    
    def _classify_task(self, query: str) -> str:
        """
        Classify task complexity
        (Placeholder - will implement proper classification later)
        """
        query_lower = query.lower()
        
        # Simple heuristics for now
        if len(query) < 20 and query.count(' ') < 3:
            return "simple"
        elif any(kw in query_lower for kw in ['research', 'analyze', 'investigate', 'write', 'create']):
            return "complex"
        else:
            return "moderate"
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check system health and provider availability
        """
        available_providers = []
        provider_status = {}
        
        # Try each provider in fallback chain
        for provider in self.llm_router.fallback_chain:
            try:
                # Quick test call
                response = await self.llm_router.complete(
                    prompt="Say 'ok'",
                    model="llama2" if provider.value == "ollama" else self.config.primary_model,
                )
                
                if response:
                    available_providers.append(provider.value)
                    provider_status[provider.value] = "✓ OK"
                else:
                    provider_status[provider.value] = "✗ No response"
                    
            except Exception as e:
                provider_status[provider.value] = f"✗ {type(e).__name__}"
        
        cost_summary = self.llm_router.cost_tracker.get_summary()
        
        return {
            'status': 'healthy' if available_providers else 'degraded',
            'available_providers': available_providers,
            'provider_status': provider_status,
            'costs': cost_summary,
            'timestamp': datetime.now().isoformat(),
        }


# Global dispatcher instance
_dispatcher_instance: Optional[PradysagiDispatcher] = None


def get_dispatcher(config: Optional[PradysagiConfig] = None) -> PradysagiDispatcher:
    """Get or create global dispatcher instance"""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = PradysagiDispatcher(config)
    return _dispatcher_instance


async def dispatch(
    query: str,
    source: RequestSource,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Result:
    """
    Process a query through PRADYSAGICAN
    Convenience function using global dispatcher
    """
    dispatcher = get_dispatcher()
    return await dispatcher.process(query, source, user_id, metadata)
