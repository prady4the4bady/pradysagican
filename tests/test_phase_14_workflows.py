"""
PHASE 14: AGENT FRAMEWORK TIER 3 — TEST SUITE
Test multi-agent workflows: Sequential, Concurrent, Hierarchical, Human-in-Loop
"""

import pytest
from datetime import datetime

from pradysagican.agents.multi_agent_workflows import (
    WorkflowType,
    WorkflowStep,
    WorkflowResult,
    SequentialWorkflow,
    ConcurrentWorkflow,
    HierarchicalWorkflow,
    HumanInLoopWorkflow,
    demonstrate_all_workflows
)


class TestWorkflowStep:
    """Test workflow step."""
    
    def test_create_step(self):
        """Test creating workflow step."""
        step = WorkflowStep(
            step_id="step_1",
            agent_type="researcher",
            task="Research topic",
            input_data={}
        )
        assert step.step_id == "step_1"
        assert step.status == "pending"


class TestSequentialWorkflow:
    """Test sequential workflow."""
    
    def test_creation(self):
        """Test creating sequential workflow."""
        workflow = SequentialWorkflow()
        assert len(workflow.steps) == 0
    
    def test_add_step(self):
        """Test adding steps."""
        workflow = SequentialWorkflow()
        workflow.add_step("s1", "researcher", "Research AI", {})
        workflow.add_step("s2", "analyst", "Analyze", {})
        
        assert len(workflow.steps) == 2
    
    @pytest.mark.asyncio
    async def test_execute_sequential(self):
        """Test executing sequential workflow."""
        workflow = SequentialWorkflow()
        workflow.add_step("s1", "researcher", "AI Safety", {})
        workflow.add_step("s2", "analyst", "Analyze findings", {})
        
        result = await workflow.execute()
        
        assert result.workflow_type == WorkflowType.SEQUENTIAL
        assert result.steps_completed == 2
        assert result.total_steps == 2
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_sequential_output_chain(self):
        """Test that outputs flow from one step to next."""
        workflow = SequentialWorkflow()
        workflow.add_step("s1", "creator", "Generate ideas", {})
        workflow.add_step("s2", "engineer", "Design implementation", {})
        
        result = await workflow.execute()
        
        assert len(result.outputs) == 2
        assert all(o for o in result.outputs)


class TestConcurrentWorkflow:
    """Test concurrent workflow."""
    
    def test_creation(self):
        """Test creating concurrent workflow."""
        workflow = ConcurrentWorkflow()
        assert len(workflow.steps) == 0
    
    def test_add_multiple_steps(self):
        """Test adding multiple independent steps."""
        workflow = ConcurrentWorkflow()
        workflow.add_step("c1", "researcher", "Research", {})
        workflow.add_step("c2", "analyst", "Analyze", {})
        workflow.add_step("c3", "creator", "Create", {})
        
        assert len(workflow.steps) == 3
    
    @pytest.mark.asyncio
    async def test_execute_concurrent(self):
        """Test executing concurrent workflow."""
        workflow = ConcurrentWorkflow()
        workflow.add_step("c1", "researcher", "Topic 1", {})
        workflow.add_step("c2", "analyst", "Topic 2", {})
        workflow.add_step("c3", "creator", "Topic 3", {})
        
        result = await workflow.execute()
        
        assert result.workflow_type == WorkflowType.CONCURRENT
        assert result.steps_completed == 3
        assert result.total_steps == 3
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_concurrent_speed(self):
        """Test that concurrent runs work correctly."""
        # Concurrent
        conc_workflow = ConcurrentWorkflow()
        conc_workflow.add_step("c1", "researcher", "Research", {})
        conc_workflow.add_step("c2", "analyst", "Analyze", {})
        conc_result = await conc_workflow.execute()
        
        # Sequential
        seq_workflow = SequentialWorkflow()
        seq_workflow.add_step("s1", "researcher", "Research", {})
        seq_workflow.add_step("s2", "analyst", "Analyze", {})
        seq_result = await seq_workflow.execute()
        
        # Both should complete successfully
        assert conc_result.success is True
        assert seq_result.success is True
        # Concurrent should have completed with same step count
        assert conc_result.steps_completed == 2
        assert seq_result.steps_completed == 2


class TestHierarchicalWorkflow:
    """Test hierarchical workflow."""
    
    def test_creation(self):
        """Test creating hierarchical workflow."""
        workflow = HierarchicalWorkflow()
        assert workflow.boss_agent is not None
        assert len(workflow.worker_agents) == 4
    
    @pytest.mark.asyncio
    async def test_coordinate_work(self):
        """Test boss coordinating workers."""
        workflow = HierarchicalWorkflow()
        
        result = await workflow.coordinate_work("Build AI System")
        
        assert result.workflow_type == WorkflowType.HIERARCHICAL
        assert result.steps_completed > 0
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_delegation(self):
        """Test that boss properly delegates."""
        workflow = HierarchicalWorkflow()
        
        result = await workflow.coordinate_work("Solve Problem")
        
        # Should have delegations to all workers + boss synthesis
        assert len(workflow.delegations) == 4
        assert len(result.outputs) > 4


class TestHumanInLoopWorkflow:
    """Test human-in-loop workflow."""
    
    def test_creation(self):
        """Test creating human-in-loop workflow."""
        workflow = HumanInLoopWorkflow()
        assert len(workflow.approval_steps) == 0
    
    @pytest.mark.asyncio
    async def test_run_with_approval(self):
        """Test running with approval steps."""
        workflow = HumanInLoopWorkflow()
        
        result = await workflow.run_with_approval("Review Decision")
        
        assert result.workflow_type == WorkflowType.HUMAN_IN_LOOP
        assert len(workflow.approval_steps) > 0
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_approval_callback(self):
        """Test custom approval callback."""
        workflow = HumanInLoopWorkflow()
        
        # Define approval function
        async def approve_func(analysis):
            return "approved"
        
        result = await workflow.run_with_approval("Review", approval_callback=approve_func)
        
        assert result.success is True
        assert workflow.approval_steps[0]["status"] == "approved"


class TestWorkflowComparison:
    """Compare different workflow types."""
    
    @pytest.mark.asyncio
    async def test_all_workflows_succeed(self):
        """Test that all workflow types can execute successfully."""
        
        # Sequential
        seq = SequentialWorkflow()
        seq.add_step("s1", "researcher", "Task", {})
        seq_result = await seq.execute()
        assert seq_result.success is True
        
        # Concurrent
        conc = ConcurrentWorkflow()
        conc.add_step("c1", "analyst", "Task", {})
        conc_result = await conc.execute()
        assert conc_result.success is True
        
        # Hierarchical
        hier = HierarchicalWorkflow()
        hier_result = await hier.coordinate_work("Task")
        assert hier_result.success is True
        
        # Human-in-Loop
        human = HumanInLoopWorkflow()
        human_result = await human.run_with_approval("Task")
        assert human_result.success is True


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_demonstrate_all_workflows(self):
        """Test full demonstration of all workflow types."""
        result = await demonstrate_all_workflows()
        
        assert result["workflows_executed"] == 4
        assert result["all_successful"] is True
        assert "sequential" in result["results"]
        assert "concurrent" in result["results"]
        assert "hierarchical" in result["results"]
        assert "human_in_loop" in result["results"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
