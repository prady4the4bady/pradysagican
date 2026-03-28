"""
PHASE 9: RECURSIVE SELF-IMPROVEMENT — TEST SUITE
Test trace analysis, principle extraction, code generation, and meta-learning
"""

import pytest
from datetime import datetime
from typing import List

from pradysagican.evolution.recursive_improvement import (
    TraceEvent,
    ExecutionTrace,
    TraceAnalyzer,
    PrincipleExtractor,
    CodeGenerator,
    MetaLearner,
    TraceType,
    initialize_self_improvement,
    demonstrate_self_improvement
)


class TestTraceEvent:
    """Test trace event creation."""
    
    def test_create_event(self):
        """Test creating a trace event."""
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            trace_type=TraceType.REASONING,
            component="analyzer",
            input_data={"query": "test"},
            output_data={"result": "ok"},
            duration_ms=100.0,
            success=True
        )
        assert event.component == "analyzer"
        assert event.success is True


class TestExecutionTrace:
    """Test execution trace."""
    
    def test_create_trace(self):
        """Test creating an execution trace."""
        trace = ExecutionTrace(
            trace_id="test_001",
            task_description="Test task"
        )
        assert trace.trace_id == "test_001"
        assert len(trace.events) == 0
    
    def test_add_events_to_trace(self):
        """Test adding events to trace."""
        trace = ExecutionTrace("test_002", "Test")
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            trace_type=TraceType.TOOL_CALL,
            component="tool",
            input_data={},
            output_data={},
            duration_ms=50.0,
            success=True
        )
        trace.events.append(event)
        assert len(trace.events) == 1


class TestTraceAnalyzer:
    """Test trace analyzer."""
    
    def test_analyzer_creation(self):
        """Test creating analyzer."""
        analyzer = TraceAnalyzer()
        assert len(analyzer.traces) == 0
    
    def test_record_trace(self):
        """Test recording a trace."""
        analyzer = TraceAnalyzer()
        trace = ExecutionTrace("test_003", "Test")
        trace_id = analyzer.record_trace(trace)
        assert trace_id in analyzer.traces
    
    @pytest.mark.asyncio
    async def test_analyze_trace(self):
        """Test analyzing a trace."""
        analyzer = TraceAnalyzer()
        trace = ExecutionTrace("test_004", "Analysis test", total_duration_ms=1000.0, quality_score=0.9)
        
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            trace_type=TraceType.SUCCESS,
            component="comp1",
            input_data={},
            output_data={},
            duration_ms=500.0,
            success=True
        )
        trace.events.append(event)
        
        analyzer.record_trace(trace)
        analysis = await analyzer.analyze_trace("test_004")
        
        assert analysis["trace_id"] == "test_004"
        assert "quality" in analysis
        assert "bottlenecks" in analysis
    
    def test_calculate_success_rate(self):
        """Test success rate calculation."""
        analyzer = TraceAnalyzer()
        trace = ExecutionTrace("test_005", "Test")
        
        for i in range(3):
            event = TraceEvent(
                timestamp=datetime.now().isoformat(),
                trace_type=TraceType.REASONING,
                component="comp",
                input_data={},
                output_data={},
                duration_ms=10.0,
                success=i < 2  # 2 successes, 1 failure
            )
            trace.events.append(event)
        
        success_rate = analyzer._calculate_success_rate(trace)
        assert success_rate == 2/3
    
    @pytest.mark.asyncio
    async def test_analyze_batch(self):
        """Test batch analysis."""
        analyzer = TraceAnalyzer()
        
        for i in range(3):
            trace = ExecutionTrace(f"batch_{i}", "Batch test", quality_score=0.8)
            analyzer.record_trace(trace)
        
        batch_result = await analyzer.analyze_batch(["batch_0", "batch_1", "batch_2"])
        assert batch_result["total_traces"] == 3


class TestPrincipleExtractor:
    """Test principle extraction."""
    
    def test_extractor_creation(self):
        """Test creating extractor."""
        extractor = PrincipleExtractor()
        assert len(extractor.principles) == 0
    
    @pytest.mark.asyncio
    async def test_extract_principles(self):
        """Test principle extraction from trace."""
        extractor = PrincipleExtractor()
        trace = ExecutionTrace("principle_test", "Extract principles")
        
        for i in range(3):
            event = TraceEvent(
                timestamp=datetime.now().isoformat(),
                trace_type=TraceType.REASONING,
                component=f"comp_{i}",
                input_data={},
                output_data={},
                duration_ms=50.0 + i*10,
                success=True
            )
            trace.events.append(event)
        
        principles = await extractor.extract_principles(trace)
        assert len(principles) > 0
    
    @pytest.mark.asyncio
    async def test_rank_principles(self):
        """Test principle ranking."""
        extractor = PrincipleExtractor()
        
        # Create traces with events
        for i in range(2):
            trace = ExecutionTrace(f"rank_test_{i}", "Rank test")
            event = TraceEvent(
                timestamp=datetime.now().isoformat(),
                trace_type=TraceType.REASONING,
                component="comp",
                input_data={},
                output_data={},
                duration_ms=50.0,
                success=True
            )
            trace.events.append(event)
            await extractor.extract_principles(trace)
        
        ranked = await extractor.rank_principles(min_frequency=1)
        assert len(ranked) > 0
        assert "principle" in ranked[0]
        assert "frequency" in ranked[0]


class TestCodeGenerator:
    """Test code generation."""
    
    @pytest.mark.asyncio
    async def test_generator_creation(self):
        """Test creating code generator."""
        generator = CodeGenerator()
        assert generator.generation_count == 0
    
    @pytest.mark.asyncio
    async def test_generate_improvement(self):
        """Test generating improved code."""
        generator = CodeGenerator()
        
        principles = ["Fast path uses: analyzer"]
        result = await generator.generate_improvement("test_component", principles)
        
        assert result["component"] == "test_component"
        assert result["code_generated"] is True
        assert "test_component" in generator.generated_code
    
    @pytest.mark.asyncio
    async def test_generation_count(self):
        """Test generation count tracking."""
        generator = CodeGenerator()
        
        for i in range(3):
            await generator.generate_improvement(f"comp_{i}", [])
        
        assert generator.generation_count == 3


class TestMetaLearner:
    """Test meta-learning."""
    
    def test_meta_learner_creation(self):
        """Test creating meta-learner."""
        learner = MetaLearner()
        assert len(learner.learning_history) == 0
    
    @pytest.mark.asyncio
    async def test_assess_effectiveness(self):
        """Test effectiveness assessment."""
        learner = MetaLearner()
        
        effectiveness = await learner.assess_learning_effectiveness(0.5, 0.8)
        assert 0 <= effectiveness <= 1
        assert effectiveness > 0  # Improvement detected
    
    @pytest.mark.asyncio
    async def test_adapt_strategy(self):
        """Test strategy adaptation."""
        learner = MetaLearner()
        
        strategy = await learner.adapt_strategy(0.8)
        assert "learning_rate" in strategy
        assert "batch_size" in strategy
        assert "exploration_factor" in strategy
    
    @pytest.mark.asyncio
    async def test_meta_insights(self):
        """Test meta insights generation."""
        learner = MetaLearner()
        
        # Add some learning history
        for i in range(5):
            await learner.adapt_strategy(0.7 + i*0.05)
        
        insights = await learner.get_meta_insights()
        assert "average_effectiveness" in insights
        assert insights["total_learning_iterations"] > 0


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_self_improvement_initialization(self):
        """Test initializing self-improvement system."""
        analyzer, extractor, learner = await initialize_self_improvement()
        
        assert analyzer is not None
        assert extractor is not None
        assert learner is not None
    
    @pytest.mark.asyncio
    async def test_demonstrate_self_improvement(self):
        """Test demonstration workflow."""
        result = await demonstrate_self_improvement()
        
        assert "trace_id" in result
        assert "analysis" in result
        assert "principles" in result
        assert len(result["principles"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
