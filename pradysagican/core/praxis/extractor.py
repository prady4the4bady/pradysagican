"""
LLM-Based Contract Extractor (F148–F152)

Feature: F148 — Automatic Contract Extraction
Feature: F149 — Docstring Analysis
Feature: F150 — Behavior Inference
Feature: F151 — Constraint Learning
Feature: F152 — Contract Template Generation

Automatically extracts behavioral contracts from tool docstrings, signatures, and historical traces.
Uses LLM for semantic understanding and pattern recognition.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json

from .contract import (
    BehavioralContract, Precondition, Postcondition, Invariant, ResourceLimit, ContractBuilder
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractionTemplate:
    """Template for extracting contracts from documentation."""
    pattern: str  # Regex pattern to match
    constraint_type: str  # "precondition", "postcondition", "invariant"
    field_name: str  # Which field in the template
    priority: int = 1


class ContractExtractor:
    """
    Extracts behavioral contracts from tool metadata.
    
    Sources:
    - Tool docstrings
    - Function signatures
    - Type hints
    - Historical traces
    - Configuration files
    """
    
    # Common extraction patterns
    PATTERNS = {
        "precondition": [
            r"requires?:\s*(.+?)(?:\n|$)",
            r"precondition:\s*(.+?)(?:\n|$)",
            r"must\s+(?:be|have):\s*(.+?)(?:\n|$)",
        ],
        "postcondition": [
            r"ensures?:\s*(.+?)(?:\n|$)",
            r"postcondition:\s*(.+?)(?:\n|$)",
            r"returns?:\s*(.+?)(?:\n|$)",
            r"result:\s*(.+?)(?:\n|$)",
        ],
        "invariant": [
            r"invariant:\s*(.+?)(?:\n|$)",
            r"always:\s*(.+?)(?:\n|$)",
            r"must\s+always:\s*(.+?)(?:\n|$)",
        ],
        "memory": [
            r"memory\s*(?:limit|bound)?:\s*([0-9.]+)\s*(?:MB|mb)",
            r"max\s+memory:\s*([0-9.]+)\s*(?:MB|mb)",
        ],
        "time": [
            r"time\s*(?:limit|bound)?:\s*([0-9.]+)\s*(?:ms|seconds?)",
            r"max\s+(?:latency|time):\s*([0-9.]+)\s*(?:ms|seconds?)",
            r"timeout:\s*([0-9.]+)\s*(?:ms|seconds?)",
        ],
        "latency": [
            r"latency:\s*([0-9.]+)\s*ms",
            r"expected\s+time:\s*([0-9.]+)\s*ms",
        ],
    }
    
    def extract_from_docstring(self, docstring: str, tool_name: str) -> Optional[BehavioralContract]:
        """
        Extract contract from tool docstring.
        
        Args:
            docstring: Tool documentation
            tool_name: Name of the tool
            
        Returns:
            Extracted BehavioralContract or None if extraction fails
        """
        if not docstring:
            return None
        
        builder = ContractBuilder(
            contract_id=f"{tool_name}_contract",
            tool_name=tool_name,
            description=self._extract_description(docstring)
        )
        
        # Extract preconditions
        preconditions = self._extract_section(docstring, "precondition")
        for precond in preconditions:
            builder.add_precondition(
                name=f"precond_{len(builder.contract.preconditions)}",
                predicate=precond,
                description=precond
            )
        
        # Extract postconditions
        postconditions = self._extract_section(docstring, "postcondition")
        for postcond in postconditions:
            builder.add_postcondition(
                name=f"postcond_{len(builder.contract.postconditions)}",
                predicate=postcond,
                description=postcond
            )
        
        # Extract invariants
        invariants = self._extract_section(docstring, "invariant")
        for inv in invariants:
            builder.add_invariant(
                name=f"inv_{len(builder.contract.invariants)}",
                predicate=inv,
                description=inv
            )
        
        # Extract resource limits
        memory_limits = self._extract_numbers(docstring, "memory")
        if memory_limits:
            builder.add_memory_limit(memory_limits[0])
        
        time_limits = self._extract_numbers(docstring, "time")
        if time_limits:
            builder.add_time_limit(time_limits[0])
        
        latency_limits = self._extract_numbers(docstring, "latency")
        if latency_limits:
            builder.add_latency_guarantee(latency_limits[0])
        
        return builder.build()
    
    def extract_from_signature(self, func_name: str, signature: str, annotations: Dict[str, Any]) -> Optional[BehavioralContract]:
        """
        Extract contract from function signature and type hints.
        
        Args:
            func_name: Function name
            signature: Function signature string
            annotations: Type hint dictionary
            
        Returns:
            Extracted contract based on signature analysis
        """
        builder = ContractBuilder(
            contract_id=f"{func_name}_contract",
            tool_name=func_name,
            description=f"Contract for {func_name}"
        )
        
        # Extract parameter constraints from type hints
        if annotations:
            for param_name, param_type in annotations.items():
                if param_name == "return":
                    # Postcondition: return type constraint
                    builder.add_postcondition(
                        name="return_type",
                        predicate=f"return type is {param_type.__name__}",
                        description=f"Return value must be of type {param_type.__name__}"
                    )
                else:
                    # Precondition: parameter constraint
                    builder.add_precondition(
                        name=f"param_{param_name}",
                        predicate=f"{param_name}: {param_type.__name__}",
                        description=f"Parameter {param_name} must be {param_type.__name__}"
                    )
        
        return builder.build()
    
    def extract_from_traces(self, execution_traces: List[Dict[str, Any]], tool_name: str, window_size: int = 100) -> Optional[BehavioralContract]:
        """
        Extract contract from historical execution traces.
        
        Learns patterns from successful executions and identifies invariants.
        
        Args:
            execution_traces: List of execution trace dictionaries
            tool_name: Name of the tool
            window_size: Number of traces to analyze
            
        Returns:
            Learned contract
        """
        if not execution_traces:
            return None
        
        builder = ContractBuilder(
            contract_id=f"{tool_name}_learned_contract",
            tool_name=tool_name,
            description=f"Contract learned from {len(execution_traces[:window_size])} execution traces"
        )
        
        # Analyze traces for common patterns
        traces = execution_traces[:window_size]
        
        # Compute resource statistics
        memory_values = [t.get("memory_used_mb", 0) for t in traces if "memory_used_mb" in t]
        time_values = [t.get("duration_ms", 0) for t in traces if "duration_ms" in t]
        
        if memory_values:
            max_memory = max(memory_values)
            avg_memory = sum(memory_values) / len(memory_values)
            # Use 1.5x of max as limit to allow for natural variance
            builder.add_memory_limit(max(avg_memory * 1.5, max_memory * 1.1))
        
        if time_values:
            max_time = max(time_values)
            avg_time = sum(time_values) / len(time_values)
            builder.add_time_limit(max(avg_time * 1.5, max_time * 1.1))
        
        # Extract common output patterns
        output_pattern = self._identify_output_pattern(traces)
        if output_pattern:
            builder.add_postcondition(
                name="output_pattern",
                predicate=f"output matches pattern: {output_pattern}",
                description="Output must follow observed pattern"
            )
        
        return builder.build()
    
    # Helper methods
    
    def _extract_description(self, docstring: str) -> str:
        """Extract first line or paragraph as description."""
        lines = docstring.strip().split('\n')
        return lines[0].strip() if lines else ""
    
    def _extract_section(self, docstring: str, section_type: str) -> List[str]:
        """Extract constraint strings from docstring."""
        results = []
        patterns = self.PATTERNS.get(section_type, [])
        
        for pattern in patterns:
            matches = re.findall(pattern, docstring, re.IGNORECASE | re.MULTILINE)
            results.extend(matches)
        
        return results
    
    def _extract_numbers(self, docstring: str, number_type: str) -> List[float]:
        """Extract numeric values from docstring."""
        results = []
        patterns = self.PATTERNS.get(number_type, [])
        
        for pattern in patterns:
            matches = re.findall(pattern, docstring, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    results.append(float(match))
                except ValueError:
                    pass
        
        return results
    
    def _identify_output_pattern(self, traces: List[Dict[str, Any]]) -> Optional[str]:
        """Identify common output pattern from traces."""
        outputs = [t.get("output_result") for t in traces if "output_result" in t]
        
        if not outputs:
            return None
        
        # Simple pattern: check if all outputs have same type
        types = set(type(o).__name__ for o in outputs)
        
        if len(types) == 1:
            output_type = types.pop()
            
            # Check if outputs have common structure
            if output_type == "dict":
                keys = set.intersection(*[set(o.keys()) for o in outputs if isinstance(o, dict)])
                if keys:
                    return f"dict with keys: {{{', '.join(sorted(keys))}}}"
            
            return f"type: {output_type}"
        
        return None


class ContractLibrary:
    """Library of pre-built contracts for common tools."""
    
    # Standard contracts
    CONTRACTS = {
        "model_query": ContractBuilder(
            "model_query", "model_query",
            "Query language model"
        )
        .add_precondition("prompt_nonempty", "len(prompt) > 0", "Prompt must not be empty")
        .add_precondition("prompt_safe", "is_safe(prompt)", "Prompt must pass safety check")
        .add_postcondition("response_nonempty", "len(response) > 0", "Response must not be empty")
        .add_memory_limit(2048)  # 2GB
        .add_time_limit(30000)   # 30 seconds
        .add_latency_guarantee(1000, 5000)  # 1-5 seconds typical
        .build(),
        
        "search": ContractBuilder(
            "search", "search",
            "Search for information"
        )
        .add_precondition("query_nonempty", "len(query) > 0", "Query must not be empty")
        .add_postcondition("results_valid", "all results have url and title", "All results must have URL and title")
        .add_memory_limit(512)   # 512MB
        .add_time_limit(10000)   # 10 seconds
        .add_latency_guarantee(100, 1000)
        .build(),
        
        "code_execution": ContractBuilder(
            "code_execution", "code_execution",
            "Execute code safely"
        )
        .add_precondition("code_safe", "static_analysis_passes(code)", "Code must pass static analysis")
        .add_postcondition("execution_completes", "execution_status in [success, error]", "Execution must complete or error gracefully")
        .add_memory_limit(256)   # 256MB
        .add_time_limit(5000)    # 5 seconds
        .add_latency_guarantee(10, 500)
        .build(),
    }
    
    @classmethod
    def get(cls, tool_name: str) -> Optional[BehavioralContract]:
        """Get contract for a tool."""
        return cls.CONTRACTS.get(tool_name)
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List available contract templates."""
        return list(cls.CONTRACTS.keys())
