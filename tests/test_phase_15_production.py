"""
PHASE 15: AGENT FRAMEWORK TIER 4 — TEST SUITE
Test Production Deployment: Server, Tracing, Evaluation, Health Monitoring
"""

import pytest
from datetime import datetime

from pradysagican.agents.production_server import (
    TracingLevel,
    TraceEvent,
    ExecutionTrace,
    AgentMetrics,
    SystemHealth,
    TracingSystem,
    EvaluationFramework,
    HealthMonitor,
    ProductionAgentServer,
    initialize_production_server,
    demonstrate_production_deployment
)
from pradysagican.agents.super_intelligence_agent import (
    Task,
    TaskType,
    ExecutionResult
)


class TestTracingSystem:
    """Test tracing system."""
    
    def test_creation(self):
        """Test creating tracing system."""
        tracing = TracingSystem(TracingLevel.STANDARD)
        assert tracing.level == TracingLevel.STANDARD
    
    def test_start_trace(self):
        """Test starting a trace."""
        tracing = TracingSystem()
        trace = tracing.start_trace("test_001")
        
        assert trace.trace_id == "test_001"
        assert trace.status == "running"
    
    def test_log_event(self):
        """Test logging events."""
        tracing = TracingSystem()
        tracing.start_trace("test_001")
        
        tracing.log_event("component", "event_type", "Test event")
        tracing.log_event("component", "event_type", "Another event", {"data": "value"})
        
        trace = tracing.current_trace
        assert len(trace.events) == 2
    
    def test_end_trace(self):
        """Test ending a trace."""
        tracing = TracingSystem()
        tracing.start_trace("test_001")
        tracing.log_event("comp", "event", "message")
        
        ended_trace = tracing.end_trace()
        
        assert ended_trace.status == "completed"
        assert ended_trace.end_time is not None
    
    def test_get_trace(self):
        """Test retrieving a trace."""
        tracing = TracingSystem()
        tracing.start_trace("test_001")
        tracing.log_event("comp", "event", "msg")
        tracing.end_trace()
        
        trace_info = tracing.get_trace("test_001")
        
        assert trace_info["trace_id"] == "test_001"
        assert trace_info["status"] == "completed"


class TestEvaluationFramework:
    """Test evaluation framework."""
    
    def test_creation(self):
        """Test creating evaluation framework."""
        eval_fw = EvaluationFramework()
        assert len(eval_fw.evaluations) == 0
    
    @pytest.mark.asyncio
    async def test_evaluate_task(self):
        """Test evaluating a task."""
        eval_fw = EvaluationFramework()
        
        result = ExecutionResult(
            task_id="task_001",
            success=True,
            output_data={"result": "ok"},
            execution_time_ms=100.0,
            confidence=0.95
        )
        
        evaluation = await eval_fw.evaluate_task(result)
        
        assert evaluation["task_id"] == "task_001"
        assert evaluation["quality_met"] is True
    
    @pytest.mark.asyncio
    async def test_evaluate_workflow(self):
        """Test evaluating workflow."""
        eval_fw = EvaluationFramework()
        
        results = [
            ExecutionResult("task_1", True, {}, 100.0, confidence=0.9),
            ExecutionResult("task_2", True, {}, 150.0, confidence=0.85),
            ExecutionResult("task_3", True, {}, 120.0, confidence=0.88),
        ]
        
        evaluation = await eval_fw.evaluate_workflow(results)
        
        assert evaluation["total_steps"] == 3
        assert evaluation["successful_steps"] == 3
        assert evaluation["success_rate"] == 1.0


class TestHealthMonitor:
    """Test health monitoring."""
    
    def test_creation(self):
        """Test creating health monitor."""
        monitor = HealthMonitor()
        assert monitor.total_tasks == 0
    
    def test_get_health_status(self):
        """Test getting health status."""
        monitor = HealthMonitor()
        monitor.total_tasks = 100
        monitor.failed_tasks = 2
        monitor.agents_online = 6
        monitor.workflows_active = 2
        
        health = monitor.get_health_status()
        
        assert health.status == "healthy"
        assert health.agents_online == 6
        assert health.error_rate < 0.1


class TestProductionAgentServer:
    """Test production agent server."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test initializing server."""
        server = await initialize_production_server()
        
        assert server.name == "PRADYSAGICAN-Production"
        assert server.main_agent is not None
        assert len(server.specialized_agents) == 5
    
    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test executing a task."""
        server = await initialize_production_server()
        
        task = Task(
            task_id="test_001",
            task_type=TaskType.REASONING,
            description="Test task",
            input_data={"test": True}
        )
        
        result = await server.execute_task(task)
        
        assert result["success"] is True
        assert "trace_id" in result
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test executing a workflow."""
        server = await initialize_production_server()
        
        steps = [
            {"step_id": "s1", "agent_type": "researcher", "task": "Research", "input_data": {}},
            {"step_id": "s2", "agent_type": "analyst", "task": "Analyze", "input_data": {}},
        ]
        
        result = await server.execute_workflow("sequential", steps)
        
        assert result["success"] is True
        assert result["workflow_type"] == "sequential"
        assert "trace_id" in result
    
    @pytest.mark.asyncio
    async def test_server_status(self):
        """Test getting server status."""
        server = await initialize_production_server()
        
        # Execute some tasks
        task = Task("t1", TaskType.REASONING, "Test", {})
        await server.execute_task(task)
        
        status = server.get_server_status()
        
        assert status["status"] in ["healthy", "degraded", "unhealthy"]
        assert status["requests_processed"] > 0
        assert "agents_online" in status
    
    @pytest.mark.asyncio
    async def test_get_trace(self):
        """Test retrieving a trace."""
        server = await initialize_production_server()
        
        task = Task("t1", TaskType.REASONING, "Test", {})
        result = await server.execute_task(task)
        
        trace = server.get_trace(result["trace_id"])
        
        assert trace["trace_id"] == result["trace_id"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in server."""
        server = await initialize_production_server()
        
        # Create task with invalid type
        task = Task("t1", TaskType.PREDICTION, "Test", {})
        result = await server.execute_task(task)
        
        # Should still complete (may succeed or fail gracefully)
        assert "trace_id" in result
    
    @pytest.mark.asyncio
    async def test_tracing_integration(self):
        """Test tracing integration in server."""
        server = await initialize_production_server()
        
        task = Task("t1", TaskType.REASONING, "Test task", {})
        result = await server.execute_task(task)
        
        # Should have tracing
        assert result["success"] is True
        trace_id = result["trace_id"]
        trace = server.get_trace(trace_id)
        assert trace is not None


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_demonstrate_production_deployment(self):
        """Test full production deployment demonstration."""
        result = await demonstrate_production_deployment()
        
        assert result["server_initialized"] is True
        assert result["task_executed"] is True
        assert result["workflow_executed"] is True
        assert result["production_ready"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
