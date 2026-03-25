"""
Tests for PRAXIS behavioral contract system (F133–F158).

Test coverage:
- Contract DSL (creation, freezing, verification)
- Contract extraction (docstrings, signatures, traces)
- Runtime enforcement (preconditions, postconditions, resources)
- Audit trail and statistics
"""

import pytest
import time
import json
from unittest.mock import Mock, patch

from pradysagican.core.praxis import (
    BehavioralContract,
    Precondition,
    Postcondition,
    Invariant,
    ResourceLimit,
    ContractBuilder,
    ContractExtractor,
    ContractLibrary,
    ContractEnforcer,
    enforce_contract,
    get_enforcer,
)


class TestContractDSL:
    """Test contract DSL: creation, freezing, signature verification."""
    
    def test_contract_creation(self):
        """Create a simple contract."""
        contract = BehavioralContract(
            contract_id="test_contract",
            tool_name="test_tool",
            description="Test contract"
        )
        assert contract.contract_id == "test_contract"
        assert contract.tool_name == "test_tool"
        assert not contract.is_frozen()
    
    def test_contract_builder_fluent_api(self):
        """ContractBuilder provides fluent API."""
        contract = (ContractBuilder("my_contract", "my_tool", "Test tool")
            .add_precondition("input_valid", "len(x) > 0", "Input must be nonempty")
            .add_postcondition("output_valid", "len(result) > 0", "Output must be nonempty")
            .add_memory_limit(512)
            .add_time_limit(5000)
            .build())
        
        assert len(contract.preconditions) == 1
        assert len(contract.postconditions) == 1
        assert len(contract.resource_limits) == 2
        assert contract.is_frozen()
    
    def test_contract_freezing(self):
        """Contract can be frozen for immutability."""
        contract = BehavioralContract(
            contract_id="test",
            tool_name="test",
            description="Test"
        )
        
        # Before freeze, can modify
        contract.add_precondition(Precondition("p1", "test", "test"))
        assert len(contract.preconditions) == 1
        
        # Freeze
        contract.freeze()
        assert contract.is_frozen()
        assert contract.signature is not None
        
        # After freeze, cannot modify
        with pytest.raises(RuntimeError):
            contract.add_precondition(Precondition("p2", "test", "test"))
    
    def test_contract_signature_verification(self):
        """Contract signature verifies integrity."""
        contract = (ContractBuilder("my_contract", "my_tool")
            .add_precondition("p1", "test")
            .build())
        
        assert contract.verify_signature()
    
    def test_contract_to_dict(self):
        """Contract can be serialized to dict."""
        contract = (ContractBuilder("my_contract", "my_tool", "Test")
            .add_precondition("p1", "test")
            .build())
        
        d = contract.to_dict()
        assert d["contract_id"] == "my_contract"
        assert d["tool_name"] == "my_tool"
        assert len(d["preconditions"]) == 1


class TestContractExtraction:
    """Test automatic contract extraction."""
    
    def test_extract_from_docstring(self):
        """Extract contract from docstring."""
        docstring = """
        Tool for testing.
        
        Precondition: input must be nonempty
        Postcondition: output is list
        Memory limit: 512 MB
        Time limit: 5000 ms
        Latency: 100 ms
        """
        
        extractor = ContractExtractor()
        contract = extractor.extract_from_docstring(docstring, "test_tool")
        
        assert contract is not None
        assert contract.tool_name == "test_tool"
        assert len(contract.preconditions) >= 1
        assert len(contract.postconditions) >= 1
    
    def test_extract_from_signature(self):
        """Extract contract from function signature."""
        extractor = ContractExtractor()
        
        annotations = {
            "x": int,
            "y": int,
            "return": int,
        }
        
        contract = extractor.extract_from_signature("add", "def add(x: int, y: int) -> int", annotations)
        
        assert contract is not None
        assert contract.tool_name == "add"
        assert len(contract.preconditions) >= 2  # x and y parameters
        assert len(contract.postconditions) >= 1  # return type
    
    def test_extract_from_traces(self):
        """Extract contract from execution traces."""
        extractor = ContractExtractor()
        
        traces = [
            {
                "memory_used_mb": 100,
                "duration_ms": 50,
                "output_result": {"success": True},
            },
            {
                "memory_used_mb": 120,
                "duration_ms": 60,
                "output_result": {"success": True},
            },
            {
                "memory_used_mb": 110,
                "duration_ms": 55,
                "output_result": {"success": True},
            },
        ]
        
        contract = extractor.extract_from_traces(traces, "test_tool")
        
        assert contract is not None
        assert contract.tool_name == "test_tool"
        # Should have inferred limits based on trace stats
        assert len(contract.resource_limits) >= 2


class TestContractLibrary:
    """Test pre-built contract library."""
    
    def test_library_has_contracts(self):
        """Library contains standard contracts."""
        available = ContractLibrary.list_available()
        assert len(available) >= 3
        assert "model_query" in available
        assert "search" in available
        assert "code_execution" in available
    
    def test_get_library_contract(self):
        """Get contract from library."""
        contract = ContractLibrary.get("model_query")
        assert contract is not None
        assert contract.tool_name == "model_query"
        assert len(contract.preconditions) > 0
        assert len(contract.postconditions) > 0


class TestRuntimeEnforcement:
    """Test contract enforcement at runtime."""
    
    def test_enforcer_basic(self):
        """Basic contract enforcement works."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .add_precondition("input_valid", "len(x) > 0")
            .build())
        
        def test_func(x):
            return x.upper()
        
        wrapped = enforcer.enforce(contract, test_func)
        result = wrapped("hello")
        assert result == "HELLO"
    
    def test_enforcer_records_traces(self):
        """Enforcer records execution traces."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .build())
        
        def test_func():
            return "result"
        
        wrapped = enforcer.enforce(contract, test_func)
        result = wrapped()
        
        traces = enforcer.get_trace_history("test_func")
        assert len(traces) >= 1
        assert traces[0].tool_name == "test_func"
        assert traces[0].output_result == "result"
    
    def test_enforcer_measures_latency(self):
        """Enforcer measures latency."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .build())
        
        def test_func():
            time.sleep(0.01)  # 10ms
            return "result"
        
        wrapped = enforcer.enforce(contract, test_func)
        wrapped()
        
        traces = enforcer.get_trace_history("test_func")
        assert len(traces) >= 1
        assert traces[0].duration_ms() >= 10
    
    def test_enforcer_tracks_violations(self):
        """Enforcer records contract violations."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .build())
        
        def test_func():
            raise ValueError("Test error")
        
        wrapped = enforcer.enforce(contract, test_func)
        
        with pytest.raises(ValueError):
            wrapped()
        
        violations = enforcer.get_violations()
        assert len(violations) >= 1
    
    def test_enforcer_statistics(self):
        """Enforcer provides statistics."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .build())
        
        def test_func():
            return "ok"
        
        wrapped = enforcer.enforce(contract, test_func)
        for _ in range(5):
            wrapped()
        
        stats = enforcer.get_statistics()
        assert stats["total_traces"] >= 5
        assert "by_tool" in stats
        assert "test_func" in stats["by_tool"]
        assert stats["by_tool"]["test_func"]["count"] >= 5
    
    def test_enforce_contract_decorator(self):
        """@enforce_contract decorator works."""
        contract = (ContractBuilder("test", "add")
            .add_precondition("inputs_valid", "a > 0 and b > 0")
            .build())
        
        @enforce_contract(contract)
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 5
        
        # Check that trace was recorded
        enforcer = get_enforcer()
        traces = enforcer.get_trace_history("add")
        assert len(traces) >= 1


class TestResourceEnforcement:
    """Test resource limit enforcement."""
    
    def test_memory_limit_tracking(self):
        """Memory usage is tracked."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .add_memory_limit(1024)  # 1GB
            .build())
        
        def test_func():
            data = [0] * 1000  # Allocate some memory
            return len(data)
        
        wrapped = enforcer.enforce(contract, test_func)
        wrapped()
        
        traces = enforcer.get_trace_history("test_func")
        assert len(traces) >= 1
        assert traces[0].memory_used_mb >= 0
    
    def test_time_limit_tracking(self):
        """Execution time is tracked."""
        enforcer = ContractEnforcer()
        contract = (ContractBuilder("test", "test_func")
            .add_time_limit(5000)  # 5 seconds
            .build())
        
        def test_func():
            time.sleep(0.01)
            return "done"
        
        wrapped = enforcer.enforce(contract, test_func)
        wrapped()
        
        traces = enforcer.get_trace_history("test_func")
        assert len(traces) >= 1
        assert traces[0].duration_ms() >= 10


class TestExecutionTrace:
    """Test execution trace recording and serialization."""
    
    def test_trace_creation(self):
        """Create execution trace."""
        from pradysagican.core.praxis import ExecutionTrace
        
        trace = ExecutionTrace(
            contract_id="test",
            tool_name="test_tool",
            start_time=time.time(),
        )
        
        assert trace.contract_id == "test"
        assert trace.tool_name == "test_tool"
        assert trace.duration_ms() == 0
    
    def test_trace_serialization(self):
        """Trace can be serialized to dict."""
        from pradysagican.core.praxis import ExecutionTrace
        
        trace = ExecutionTrace(
            contract_id="test",
            tool_name="test_tool",
            start_time=time.time(),
            output_result={"key": "value"},
        )
        
        d = trace.to_dict()
        assert d["contract_id"] == "test"
        assert d["tool_name"] == "test_tool"
        assert d["output_result"] == {"key": "value"}
    
    def test_trace_all_passed_check(self):
        """Trace can check if all checks passed."""
        from pradysagican.core.praxis import ExecutionTrace
        
        trace = ExecutionTrace(
            contract_id="test",
            tool_name="test_tool",
            start_time=time.time(),
        )
        
        # Initially passed
        assert trace.all_passed()
        
        # Add failures
        trace.preconditions_failed.append("p1")
        assert not trace.all_passed()
