"""
PHASE 12: AGENT FRAMEWORK TIER 1 — TEST SUITE
Test SuperIntelligenceAgent orchestrator with all frontier capabilities
"""

import pytest
from datetime import datetime

from pradysagican.agents.super_intelligence_agent import (
    AgentRole,
    TaskType,
    Task,
    ExecutionResult,
    AgentCapability,
    SuperIntelligenceAgent,
    initialize_super_intelligence_agent,
    demonstrate_super_intelligence
)


class TestAgentCapability:
    """Test agent capability definitions."""
    
    def test_create_capability(self):
        """Test creating a capability."""
        cap = AgentCapability(
            name="Test Capability",
            task_types=[TaskType.REASONING],
            phase_dependency=9
        )
        assert cap.name == "Test Capability"
        assert cap.enabled is True


class TestTask:
    """Test task definitions."""
    
    def test_create_task(self):
        """Test creating a task."""
        task = Task(
            task_id="task_001",
            task_type=TaskType.REASONING,
            description="Test reasoning",
            input_data={"test": True}
        )
        assert task.task_id == "task_001"
        assert task.status == "pending"
        assert task.priority == 5


class TestExecutionResult:
    """Test execution results."""
    
    def test_create_result(self):
        """Test creating an execution result."""
        result = ExecutionResult(
            task_id="task_001",
            success=True,
            output_data={"result": "success"},
            execution_time_ms=100.0
        )
        assert result.task_id == "task_001"
        assert result.success is True


class TestSuperIntelligenceAgent:
    """Test SuperIntelligenceAgent orchestrator."""
    
    def test_agent_creation(self):
        """Test creating SuperIntelligenceAgent."""
        agent = SuperIntelligenceAgent("TestAgent")
        assert agent.name == "TestAgent"
        assert agent.role == AgentRole.COORDINATOR
        assert len(agent.capabilities) > 0
    
    def test_capabilities_registered(self):
        """Test that all capabilities are registered."""
        agent = SuperIntelligenceAgent()
        
        # Should have 12 capabilities (3 from each phase 9-11, 4 each)
        assert len(agent.capabilities) == 12
        
        # Check Phase 9 capabilities
        phase_9_caps = [c for c in agent.capabilities if c.phase_dependency == 9]
        assert len(phase_9_caps) == 4
        
        # Check Phase 10 capabilities
        phase_10_caps = [c for c in agent.capabilities if c.phase_dependency == 10]
        assert len(phase_10_caps) == 4
        
        # Check Phase 11 capabilities
        phase_11_caps = [c for c in agent.capabilities if c.phase_dependency == 11]
        assert len(phase_11_caps) == 4
    
    @pytest.mark.asyncio
    async def test_handle_reasoning_task(self):
        """Test handling reasoning task."""
        agent = SuperIntelligenceAgent()
        
        task = Task(
            task_id="reasoning_001",
            task_type=TaskType.REASONING,
            description="Test reasoning",
            input_data={"problem": "test problem"}
        )
        
        result = await agent.handle_task(task)
        
        assert result.task_id == "reasoning_001"
        assert result.success is True
        assert "conscious_state" in result.output_data
    
    @pytest.mark.asyncio
    async def test_handle_analysis_task(self):
        """Test handling analysis task."""
        agent = SuperIntelligenceAgent()
        
        task = Task(
            task_id="analysis_001",
            task_type=TaskType.ANALYSIS,
            description="Test analysis",
            input_data={"trace_ids": []}
        )
        
        result = await agent.handle_task(task)
        
        assert result.task_id == "analysis_001"
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_handle_prediction_task(self):
        """Test handling prediction task."""
        agent = SuperIntelligenceAgent()
        
        task = Task(
            task_id="prediction_001",
            task_type=TaskType.PREDICTION,
            description="Test prediction",
            input_data={"actions": []}
        )
        
        result = await agent.handle_task(task)
        
        assert result.task_id == "prediction_001"
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_handle_creative_task(self):
        """Test handling creative task."""
        agent = SuperIntelligenceAgent()
        
        task = Task(
            task_id="creative_001",
            task_type=TaskType.CREATIVE,
            description="Test creativity",
            input_data={"goal": {}, "num_branches": 3}
        )
        
        result = await agent.handle_task(task)
        
        assert result.task_id == "creative_001"
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test executing multiple tasks."""
        agent = SuperIntelligenceAgent()
        
        tasks = [
            Task("task_1", TaskType.REASONING, "Test 1", {}, priority=5),
            Task("task_2", TaskType.ANALYSIS, "Test 2", {"trace_ids": []}, priority=8),
            Task("task_3", TaskType.PREDICTION, "Test 3", {"actions": []}, priority=3),
        ]
        
        results = await agent.execute_workflow(tasks)
        
        assert len(results) == 3
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_get_system_status(self):
        """Test getting system status."""
        agent = SuperIntelligenceAgent()
        
        # Execute a task first
        task = Task("status_test", TaskType.REASONING, "Test", {})
        await agent.handle_task(task)
        
        status = await agent.get_system_status()
        
        assert status["agent_name"] == agent.name
        assert status["role"] == "coordinator"
        assert status["capabilities"] == 12
        assert status["tasks_completed"] == 1
        assert status["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_think(self):
        """Test the main thinking loop."""
        agent = SuperIntelligenceAgent()
        
        thought = await agent.think("What is consciousness?")
        
        assert thought["problem"] == "What is consciousness?"
        assert thought["conscious"] is True
        assert thought["ready_to_act"] is True
        assert "principles_learned" in thought
    
    @pytest.mark.asyncio
    async def test_task_routing(self):
        """Test task routing to different handlers."""
        agent = SuperIntelligenceAgent()
        
        # Test that different task types are routed correctly
        task_types = [
            (TaskType.REASONING, "problem"),
            (TaskType.RESEARCH, "trace"),
            (TaskType.ANALYSIS, "trace_ids"),
            (TaskType.ENGINEERING, "component"),
            (TaskType.CREATIVE, "goal"),
            (TaskType.PREDICTION, "actions"),
        ]
        
        for task_type, field_name in task_types:
            task = Task(
                task_id=f"route_test_{task_type}",
                task_type=task_type,
                description=f"Test {task_type}",
                input_data={field_name: None} if field_name else {}
            )
            result = await agent.handle_task(task)
            assert result.success is True, f"Failed routing {task_type}"


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test initializing SuperIntelligenceAgent."""
        agent = await initialize_super_intelligence_agent("TestBot")
        
        assert agent is not None
        assert agent.name == "TestBot"
        assert len(agent.capabilities) == 12
    
    @pytest.mark.asyncio
    async def test_demonstrate_super_intelligence(self):
        """Test full demonstration."""
        result = await demonstrate_super_intelligence()
        
        assert "tasks_executed" in result
        assert "success_count" in result
        assert "agent_status" in result
        assert "thought_result" in result
        assert result["tasks_executed"] == 3
        assert result["success_count"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
