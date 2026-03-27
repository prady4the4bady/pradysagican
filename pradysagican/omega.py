"""
PRADYSAGICAN v2.0 - MASTER ORCHESTRATOR
Integrates all 5 phases: Config → LLM → Reasoning → Memory → Safety → Advanced
Single unified system that leverages all capabilities
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import asyncio
import uuid

from .config import PradysagiConfig, get_config
from .llm_router import UniversalLLMRouter
from .dispatcher import PradysagiDispatcher, RequestSource
from .tool_registry import ToolRegistry
from .reasoning import ReasoningEngine, TaskClassifier
from .memory import MemoryManager
from .safety import SafeExecutionContext, SecurityLevel
from .advanced import AdvancedFeaturesManager

logger = logging.getLogger(__name__)


class PradysagiOmega:
    """Master orchestrator - the complete v2.0 system"""
    
    def __init__(self, config: Optional[PradysagiConfig] = None):
        """Initialize complete system"""
        self.config = config or get_config()
        
        logger.info("🚀 Initializing PRADYSAGICAN OMEGA v2.0")
        
        # Phase 1: Core infrastructure
        logger.info("  ├─ Initializing config system...")
        self.config_manager = self.config
        
        logger.info("  ├─ Initializing LLM router...")
        self.llm_router = UniversalLLMRouter(self.config)
        
        logger.info("  ├─ Initializing tool registry...")
        self.tool_registry = ToolRegistry()
        
        logger.info("  ├─ Initializing dispatcher...")
        self.dispatcher = PradysagiDispatcher(self.config)
        
        # Phase 2: Reasoning engine
        logger.info("  ├─ Initializing reasoning engine...")
        self.reasoning_engine = ReasoningEngine(
            self.llm_router,
            self.tool_registry,
            self.config
        )
        
        # Phase 3: Memory system
        logger.info("  ├─ Initializing memory system...")
        self.memory_manager = MemoryManager()
        
        # Phase 4: Safety framework
        logger.info("  ├─ Initializing safety framework...")
        self.safety_context = SafeExecutionContext(
            security_level=SecurityLevel[self.config.safety_level.upper()]
        )
        
        # Phase 5: Advanced features
        logger.info("  ├─ Initializing advanced features...")
        self.advanced_features = AdvancedFeaturesManager(self.llm_router)
        
        logger.info("  └─ ✅ PRADYSAGICAN OMEGA v2.0 Ready!\n")
        
        # Session tracking
        self.session_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.interaction_count = 0
        self.total_tokens_used = 0
    
    async def process_query(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Process query through complete system"""
        
        self.interaction_count += 1
        trace_id = str(uuid.uuid4())[:8]
        
        try:
            # Step 1: Safety validation
            logger.debug(f"[{trace_id}] Step 1: Validating input...")
            valid, error = await self.safety_context.validate_input(query, user_id)
            
            if not valid:
                return {
                    'success': False,
                    'error': error,
                    'trace_id': trace_id,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Step 2: Task analysis
            logger.debug(f"[{trace_id}] Step 2: Analyzing task...")
            analysis = await self.reasoning_engine.classifier.analyze(query)
            
            # Step 3: Recall relevant memories
            logger.debug(f"[{trace_id}] Step 3: Recalling memories...")
            relevant_memories = await self.memory_manager.recall_relevant(query)
            context = "\n".join(relevant_memories) if relevant_memories else ""
            
            # Step 4: Reasoning
            logger.debug(f"[{trace_id}] Step 4: Reasoning...")
            reasoning_trace = await self.reasoning_engine.reason(query, trace_id)
            
            # Step 5: Safety filtering
            logger.debug(f"[{trace_id}] Step 5: Filtering output...")
            filtered_answer = self.safety_context.filter_output(reasoning_trace.final_answer or "", user_id)
            
            # Step 6: Memory recording
            logger.debug(f"[{trace_id}] Step 6: Recording to memory...")
            await self.memory_manager.record_interaction(query, filtered_answer)
            
            # Step 7: Package response
            response = {
                'success': True,
                'query': query,
                'answer': filtered_answer,
                'task_complexity': analysis.complexity.value,
                'strategy': analysis.recommended_strategy.value,
                'reasoning_steps': len(reasoning_trace.reasoning_chain),
                'confidence': reasoning_trace.confidence,
                'execution_time_seconds': reasoning_trace.duration_seconds,
                'trace_id': trace_id,
                'timestamp': datetime.now().isoformat()
            }
            
            return response
        
        except Exception as e:
            logger.error(f"[{trace_id}] Error processing query: {e}")
            self.safety_context.log_error(user_id, e)
            
            return {
                'success': False,
                'error': str(e),
                'trace_id': trace_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        
        health = await self.dispatcher.health_check()
        memory_context = self.memory_manager.get_working_context()
        advanced_status = await self.advanced_features.get_system_status()
        audit_summary = self.safety_context.audit_trail.get_events(limit=20)
        
        return {
            'system': 'PRADYSAGICAN OMEGA v2.0',
            'session_id': self.session_id,
            'uptime_seconds': (datetime.now() - self.created_at).total_seconds(),
            'interactions': self.interaction_count,
            'deployment': {
                'status': health['status'],
                'available_providers': health['available_providers'],
                'provider_status': health['provider_status']
            },
            'memory': {
                'working_context_size': len(memory_context),
                'total_memories': sum(
                    len(self.memory_manager.episodic.store.memories.values())
                    for _ in [1]  # dummy loop
                ),
            },
            'advanced_features': advanced_status,
            'recent_audit_events': audit_summary,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_improvement_cycle(self):
        """Run autonomous self-improvement"""
        logger.info("Starting autonomous improvement cycle...")
        
        # Collect recent performance data
        recent_events = self.safety_context.audit_trail.events[-50:]
        recent_tasks = [
            {
                'event': e.event_type,
                'success': not e.blocked,
                'confidence': 0.8 if not e.blocked else 0.2
            }
            for e in recent_events
        ]
        
        # Run improvement
        result = await self.advanced_features.run_improvement_cycle(recent_tasks)
        
        logger.info(f"Improvement cycle complete: {result}")
        return result
    
    async def consolidate_memories(self):
        """Run nightly memory consolidation"""
        logger.info("Starting memory consolidation...")
        await self.memory_manager.run_consolidation()
        logger.info("Memory consolidation complete")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'primary_provider': self.config.primary_provider.value,
            'primary_model': self.config.primary_model,
            'fallback_providers': [p.value for p in self.config.fallback_providers],
            'safety_level': self.config.safety_level,
            'prefer_local': self.config.prefer_local,
            'test_mode': self.config.test_mode
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'total_interactions': self.interaction_count,
            'session_duration_seconds': (datetime.now() - self.created_at).total_seconds(),
            'cost_tracking': self.llm_router.cost_tracker.get_summary(),
            'tools_available': len(self.tool_registry.registry),
            'memories_stored': len(self.memory_manager.store.memories),
            'audit_events': len(self.safety_context.audit_trail.events)
        }


# Global singleton instance
_omega_instance: Optional[PradysagiOmega] = None


async def get_omega(config: Optional[PradysagiConfig] = None) -> PradysagiOmega:
    """Get or create global OMEGA instance"""
    global _omega_instance
    
    if _omega_instance is None:
        _omega_instance = PradysagiOmega(config or get_config())
    
    return _omega_instance


async def process_query(query: str, user_id: str = "default") -> Dict[str, Any]:
    """Convenience function to process query via global OMEGA"""
    omega = await get_omega()
    return await omega.process_query(query, user_id)


# Export main class and functions
__all__ = [
    'PradysagiOmega',
    'get_omega',
    'process_query',
]
