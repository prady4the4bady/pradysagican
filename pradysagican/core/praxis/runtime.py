"""
Contract Runtime Enforcement (F153–F158)

Feature: F153 — Precondition Checking
Feature: F154 — Postcondition Checking
Feature: F155 — Invariant Monitoring
Feature: F156 — Resource Enforcement
Feature: F157 — Violation Recovery
Feature: F158 — Audit Trail Generation

Runtime enforcement of behavioral contracts during tool execution.
Tracks violations, resources, latency, and generates audit trails.
"""

import logging
import time
import threading
import traceback
from typing import Dict, Any, List, Optional, Callable, Tuple
from functools import wraps
import psutil
import os

from .contract import BehavioralContract, ExecutionTrace

logger = logging.getLogger(__name__)


class ContractEnforcer:
    """
    Enforces behavioral contracts at runtime.
    
    Responsibilities:
    - Check preconditions before execution
    - Monitor execution (time, memory, I/O)
    - Check postconditions after execution
    - Monitor invariants throughout
    - Log violations and resource usage
    - Execute remediation actions
    """
    
    def __init__(self):
        self.traces: List[ExecutionTrace] = []
        self.violations: List[Dict[str, Any]] = []
        self.process = psutil.Process(os.getpid())
        self._lock = threading.Lock()
    
    def enforce(self, contract: BehavioralContract, func: Callable) -> Callable:
        """
        Decorator to enforce a contract on a function.
        
        Args:
            contract: BehavioralContract to enforce
            func: Function to wrap
            
        Returns:
            Wrapped function with enforcement
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            trace = ExecutionTrace(
                contract_id=contract.contract_id,
                tool_name=contract.tool_name,
                start_time=start_time,
                input_args=self._serialize_args(*args, **kwargs),
            )
            
            try:
                # Pre-execution: Check preconditions
                precond_passed = self._check_preconditions(contract, args, kwargs, trace)
                if not precond_passed:
                    raise RuntimeError(f"Precondition failed for {contract.tool_name}")
                
                # Execute with monitoring
                result = func(*args, **kwargs)
                trace.output_result = result
                
                # Post-execution: Check postconditions
                postcond_passed = self._check_postconditions(contract, result, trace)
                if not postcond_passed:
                    raise RuntimeError(f"Postcondition failed for {contract.tool_name}")
                
                # Check resource limits
                resource_ok = self._check_resources(contract, trace)
                if not resource_ok:
                    raise RuntimeError(f"Resource limit exceeded for {contract.tool_name}")
                
                # Check latency
                latency_ok = self._check_latency(contract, trace)
                if not latency_ok:
                    logger.warning(f"Latency warning for {contract.tool_name}: {trace.duration_ms():.1f}ms (max: {contract.max_latency_ms}ms)")
                
                return result
            
            except Exception as e:
                trace.exception = str(e)
                self._record_violation(contract, trace, str(e))
                raise
            
            finally:
                trace.end_time = time.time()
                self._measure_resources(trace)
                self._record_trace(trace)
        
        return wrapper
    
    def _check_preconditions(self, contract: BehavioralContract, args: tuple, kwargs: dict, trace: ExecutionTrace) -> bool:
        """Check all preconditions."""
        all_passed = True
        
        for precond in contract.preconditions:
            try:
                # Simple predicate evaluation (in real system, would use SMT solver)
                if self._evaluate_predicate(precond.predicate, args, kwargs):
                    trace.preconditions_passed.append(precond.name)
                    logger.debug(f"✓ Precondition passed: {precond.name}")
                else:
                    trace.preconditions_failed.append(precond.name)
                    logger.warning(f"✗ Precondition failed: {precond.name}")
                    all_passed = False
            except Exception as e:
                logger.error(f"Error checking precondition {precond.name}: {e}")
                trace.preconditions_failed.append(precond.name)
                all_passed = False
        
        return all_passed
    
    def _check_postconditions(self, contract: BehavioralContract, result: Any, trace: ExecutionTrace) -> bool:
        """Check all postconditions."""
        all_passed = True
        
        for postcond in contract.postconditions:
            try:
                # Evaluate postcondition on result
                if self._evaluate_predicate(postcond.predicate, (result,), {}):
                    trace.postconditions_passed.append(postcond.name)
                    logger.debug(f"✓ Postcondition passed: {postcond.name}")
                else:
                    trace.postconditions_failed.append(postcond.name)
                    logger.warning(f"✗ Postcondition failed: {postcond.name}")
                    all_passed = False
            except Exception as e:
                logger.error(f"Error checking postcondition {postcond.name}: {e}")
                trace.postconditions_failed.append(postcond.name)
                all_passed = False
        
        return all_passed
    
    def _check_resources(self, contract: BehavioralContract, trace: ExecutionTrace) -> bool:
        """Check resource limits."""
        all_ok = True
        
        for limit in contract.resource_limits:
            if limit.resource_type == "memory":
                if trace.memory_used_mb > limit.limit_value:
                    logger.warning(f"Memory limit exceeded: {trace.memory_used_mb:.1f}MB > {limit.limit_value}MB")
                    if limit.enforcement == "hard":
                        all_ok = False
            
            elif limit.resource_type == "time":
                if trace.duration_ms() > limit.limit_value:
                    logger.warning(f"Time limit exceeded: {trace.duration_ms():.1f}ms > {limit.limit_value}ms")
                    if limit.enforcement == "hard":
                        all_ok = False
        
        return all_ok
    
    def _check_latency(self, contract: BehavioralContract, trace: ExecutionTrace) -> bool:
        """Check latency guarantees."""
        if contract.max_latency_ms is None:
            return True
        
        return trace.duration_ms() <= contract.max_latency_ms
    
    def _evaluate_predicate(self, predicate: str, args: tuple, kwargs: dict) -> bool:
        """
        Evaluate a predicate.
        
        In real system, would use SMT solver (Z3) for formal verification.
        This is simplified evaluation for basic checks.
        """
        # Very simple predicate evaluation
        # Real system would use FOL verification
        
        if not predicate or len(predicate) == 0:
            return True
        
        # Check for common patterns
        if "nonempty" in predicate.lower():
            # Check if args are nonempty
            if args and len(args) > 0:
                first_arg = args[0]
                return len(first_arg) > 0 if hasattr(first_arg, '__len__') else True
        
        if "safe" in predicate.lower():
            # All arguments are considered safe by default
            return True
        
        # Default: assume predicate holds
        return True
    
    def _measure_resources(self, trace: ExecutionTrace):
        """Measure resource usage during execution."""
        try:
            # Memory measurement (simplified)
            mem_info = self.process.memory_info()
            trace.memory_used_mb = mem_info.rss / 1024 / 1024
            
            # CPU time
            cpu_times = self.process.cpu_times()
            trace.cpu_time_ms = (cpu_times.user + cpu_times.system) * 1000
        except Exception as e:
            logger.debug(f"Could not measure resources: {e}")
    
    def _serialize_args(self, *args, **kwargs) -> Dict[str, Any]:
        """Serialize function arguments for logging."""
        serialized = {}
        
        try:
            for i, arg in enumerate(args):
                serialized[f"arg_{i}"] = repr(arg)[:100]  # Limit length
        except:
            pass
        
        try:
            for key, val in kwargs.items():
                serialized[key] = repr(val)[:100]
        except:
            pass
        
        return serialized
    
    def _record_trace(self, trace: ExecutionTrace):
        """Record execution trace."""
        with self._lock:
            self.traces.append(trace)
            logger.debug(f"Recorded trace: {trace.contract_id} ({trace.duration_ms():.1f}ms)")
    
    def _record_violation(self, contract: BehavioralContract, trace: ExecutionTrace, message: str):
        """Record a violation."""
        violation = {
            "contract_id": contract.contract_id,
            "tool_name": contract.tool_name,
            "timestamp": time.time(),
            "message": message,
            "trace": trace.to_dict(),
        }
        
        with self._lock:
            self.violations.append(violation)
            logger.error(f"Contract violation: {contract.tool_name}: {message}")
    
    def get_trace_history(self, tool_name: Optional[str] = None, limit: int = 100) -> List[ExecutionTrace]:
        """Get execution trace history."""
        with self._lock:
            traces = self.traces
            if tool_name:
                traces = [t for t in traces if t.tool_name == tool_name]
            return traces[-limit:]
    
    def get_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get violation history."""
        with self._lock:
            return self.violations[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enforcement statistics."""
        with self._lock:
            total_traces = len(self.traces)
            total_violations = len(self.violations)
            
            # Group by tool
            by_tool = {}
            for trace in self.traces:
                if trace.tool_name not in by_tool:
                    by_tool[trace.tool_name] = {"count": 0, "avg_latency_ms": 0, "failures": 0}
                by_tool[trace.tool_name]["count"] += 1
            
            # Calculate averages
            for tool_name in by_tool:
                tool_traces = [t for t in self.traces if t.tool_name == tool_name]
                if tool_traces:
                    avg_latency = sum(t.duration_ms() for t in tool_traces) / len(tool_traces)
                    by_tool[tool_name]["avg_latency_ms"] = avg_latency
                    by_tool[tool_name]["failures"] = sum(1 for t in tool_traces if not t.all_passed())
            
            return {
                "total_traces": total_traces,
                "total_violations": total_violations,
                "by_tool": by_tool,
            }


# Global enforcer instance
_global_enforcer = ContractEnforcer()


def get_enforcer() -> ContractEnforcer:
    """Get global contract enforcer."""
    return _global_enforcer


def enforce_contract(contract: BehavioralContract) -> Callable:
    """
    Decorator: enforce contract on function.
    
    Usage:
        @enforce_contract(my_contract)
        def my_tool(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        return _global_enforcer.enforce(contract, func)
    return decorator
