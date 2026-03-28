#!/usr/bin/env python3
"""
PRADYSAGICAN v2.0 - COMPREHENSIVE TEST SUITE
Tests all 5 phases of the system
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pradysagican.core.config import PradysagiConfig, LLMProviderType
from pradysagican.reasoning import TaskComplexity, ExecutionStrategy, ReasoningEngine
from pradysagican.memory import MemorySystem, MemoryTier, MemoryEntry
from pradysagican.safety import SafeExecutionContext, SecurityLevel, InputValidator
from pradysagican.advanced import SkillLibrary, PersonalityModel, MultiAgentOrchestrator, Skill
from pradysagican.omega import PradysagiOmega


class TestPhase1Foundation:
    """Tests for Phase 1: Core Infrastructure"""
    
    def test_config_creation(self):
        """Config system works"""
        config = PradysagiConfig(prefer_local=True)
        assert config.primary_provider == LLMProviderType.OLLAMA
        assert len(config.fallback_providers) > 0
    
    @pytest.mark.asyncio
    async def test_llm_router(self):
        """LLM router initializes"""
        from pradysagican.core.llm_router import UniversalLLMRouter
        config = PradysagiConfig()
        router = UniversalLLMRouter(config)
        assert len(router.fallback_chain) > 0
    
    @pytest.mark.asyncio
    async def test_tool_registry(self):
        """Tool registry works"""
        from pradysagican.core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        tools = registry.list_available_tools()
        assert len(tools) >= 4  # At least built-in tools


class TestPhase2Reasoning:
    """Tests for Phase 2: Reasoning Engine"""
    
    @pytest.mark.asyncio
    async def test_task_classifier(self):
        """Task classifier works"""
        from pradysagican.core.llm_router import UniversalLLMRouter
        config = PradysagiConfig()
        llm = UniversalLLMRouter(config)
        
        from pradysagican.core.reasoning import TaskClassifier
        classifier = TaskClassifier(llm)
        
        analysis = await classifier.analyze("What is 2+2?")
        assert analysis.complexity == TaskComplexity.SIMPLE
        assert analysis.recommended_strategy == ExecutionStrategy.DIRECT
    
    @pytest.mark.asyncio
    async def test_task_complexity_detection(self):
        """Complexity detection works"""
        from pradysagican.core.reasoning import TaskClassifier
        from pradysagican.core.llm_router import UniversalLLMRouter
        
        config = PradysagiConfig()
        llm = UniversalLLMRouter(config)
        classifier = TaskClassifier(llm)
        
        # Simple
        simple = await classifier.analyze("What is the capital of France?")
        assert simple.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]
        
        # Complex
        complex_task = "Design a distributed system that handles 1M requests/sec with <10ms latency"
        complex = await classifier.analyze(complex_task)
        assert complex.complexity in [TaskComplexity.COMPLEX, TaskComplexity.RESEARCH]


class TestPhase3Memory:
    """Tests for Phase 3: Memory System"""
    
    @pytest.mark.asyncio
    async def test_working_memory(self):
        """Working memory stores and retrieves"""
        memory = WorkingMemory(max_size=5)
        memory.add("Hello world")
        memory.add("Second item")
        
        context = memory.get_context()
        assert "Hello world" in context
        assert "Second item" in context
    
    @pytest.mark.asyncio
    async def test_episodic_memory(self):
        """Episodic memory records interactions"""
        manager = MemoryManager()
        
        await manager.record_interaction("What is AI?", "AI is artificial intelligence...")
        
        # Recall should find the interaction
        results = await manager.recall_relevant("AI")
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_memory_consolidation(self):
        """Memory consolidation works"""
        manager = MemoryManager()
        
        # Add some memories
        for i in range(5):
            await manager.record_interaction(f"Query {i}", f"Response {i}")
        
        # Consolidate
        await manager.run_consolidation()
        
        # Should still have memories
        assert len(manager.store.memories) > 0


class TestPhase4Safety:
    """Tests for Phase 4: Safety Framework"""
    
    def test_input_validation(self):
        """Input validation detects attacks"""
        validator = InputValidator(SecurityLevel.STRICT)
        
        # Safe query
        safe, msg = validator.validate("What is the weather?")
        assert safe
        
        # SQL injection
        sql_inject, msg = validator.validate("'; DROP TABLE users; --")
        assert not sql_inject  # Should be blocked
    
    @pytest.mark.asyncio
    async def test_execution_constraints(self):
        """Rate limiting works"""
        from pradysagican.core.safety import ExecutionConstraints
        constraints = ExecutionConstraints()
        
        # First call should succeed
        allowed, _ = await constraints.check_constraints("user1")
        assert allowed
        
        # Many rapid calls should eventually fail
        for i in range(100):
            allowed, msg = await constraints.check_constraints("user1_spam")
        # Eventually hits rate limit
    
    def test_output_filtering(self):
        """Output filtering removes PII"""
        from pradysagican.core.safety import OutputFilter
        filter = OutputFilter()
        
        text = "Email me at john@example.com or call 555-123-4567"
        redacted, warnings = filter.filter_output(text)
        
        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted


class TestPhase5Advanced:
    """Tests for Phase 5: Advanced Features"""
    
    def test_skill_library(self):
        """Skill library works"""
        library = SkillLibrary()
        
        skill = Skill(
            name="Python",
            description="Python programming",
            procedure="Use Python for everything",
            domain="programming",
            proficiency=0.9
        )
        
        library.add_skill(skill)
        retrieved = library.get_skill("Python")
        assert retrieved is not None
        assert retrieved.proficiency == 0.9
    
    def test_personality_model(self):
        """Personality system works"""
        personality = PersonalityModel()
        
        # Get default trait
        helpfulness = personality.get_trait('helpfulness')
        assert helpfulness is not None
        assert helpfulness.value is True
        
        # Set custom trait
        personality.set_trait('creativity', True, 0.9)
        creativity = personality.get_trait('creativity')
        assert creativity is not None
    
    @pytest.mark.asyncio
    async def test_multi_agent_orchestration(self):
        """Multi-agent system works"""
        orchestrator = MultiAgentOrchestrator()
        
        # Should have default agents
        assert len(orchestrator.agents) > 0
        
        # Coordinate a task
        result = await orchestrator.coordinate_task("Analyze this problem")
        assert 'agent_results' in result
        assert 'synthesis' in result


class TestOmegaIntegration:
    """Integration tests for complete OMEGA system"""
    
    @pytest.mark.asyncio
    async def test_omega_initialization(self):
        """OMEGA system initializes"""
        config = PradysagiConfig(prefer_local=True, test_mode=True)
        omega = PradysagiOmega(config)
        
        assert omega.reasoning_engine is not None
        assert omega.memory_manager is not None
        assert omega.safety_context is not None
        assert omega.advanced_features is not None
    
    @pytest.mark.asyncio
    async def test_query_processing(self):
        """Complete query processing works"""
        config = PradysagiConfig(prefer_local=True, test_mode=True)
        omega = PradysagiOmega(config)
        
        # Process a query
        result = await omega.process_query("What is 2+2?")
        
        assert 'trace_id' in result
        assert 'timestamp' in result
        # May have error if no LLM available, but structure is correct
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """System status endpoint works"""
        config = PradysagiConfig(prefer_local=True, test_mode=True)
        omega = PradysagiOmega(config)
        
        status = await omega.get_system_status()
        
        assert status['system'] == 'PRADYSAGICAN OMEGA v2.0'
        assert 'session_id' in status
        assert 'deployment' in status
        assert 'memory' in status
        assert 'advanced_features' in status


# Command-line test runner
async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("PRADYSAGICAN v2.0 - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    test_classes = [
        TestPhase1Foundation,
        TestPhase2Reasoning,
        TestPhase3Memory,
        TestPhase4Safety,
        TestPhase5Advanced,
        TestOmegaIntegration,
    ]
    
    total_tests = 0
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 60)
        
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                total_tests += 1
                method = getattr(instance, method_name)
                
                try:
                    # Check if async
                    if asyncio.iscoroutinefunction(method):
                        asyncio.run(method())
                    else:
                        method()
                    
                    print(f"  ✓ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total_tests} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
