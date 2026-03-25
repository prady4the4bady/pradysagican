"""
F615: Tool-R0 Evolution - Recursive Tool Building Agent
========================================================

Recursive agent that builds tools to solve problems through:
- Tool composition from smaller tools
- Meta-learning of effective tool patterns
- Archive of successful tool combinations
- Recursive problem decomposition
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Types of tools that can be built."""
    ATOMIC = "atomic"          # Cannot be decomposed
    COMPOSITE = "composite"    # Combination of other tools
    RECURSIVE = "recursive"    # Calls itself
    ADAPTIVE = "adaptive"      # Changes behavior based on context
    LEARNED = "learned"        # From successful patterns


@dataclass
class ToolSpecification:
    """Specification for a tool."""
    tool_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_type: str = "atomic"
    name: str = ""
    description: str = ""
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    implementation: Optional[Callable] = None
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    success_count: int = 0
    failure_count: int = 0
    usage_count: int = 0


@dataclass
class ToolComposition:
    """Combination of tools to solve a problem."""
    composition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_ids: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    total_trials: int = 0
    successful_trials: int = 0
    avg_execution_time_ms: float = 0.0
    discovered_timestamp: datetime = field(default_factory=datetime.utcnow)
    problem_domain: str = ""
    generalization_score: float = 0.0


@dataclass
class ToolLearning:
    """Meta-learning record for tool patterns."""
    learning_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_description: str = ""
    tool_combinations: List[ToolComposition] = field(default_factory=list)
    pattern_effectiveness: float = 0.0
    domain_applicability: Dict[str, float] = field(default_factory=dict)
    success_metrics: Dict[str, float] = field(default_factory=dict)


class ToolR0Evolution:
    """Tool-R0: Recursive tool-building evolution system."""

    def __init__(self, max_recursion_depth: int = 5):
        """Initialize Tool-R0 Evolution.

        Args:
            max_recursion_depth: Maximum recursion depth for tool building
        """
        self.max_recursion_depth = max_recursion_depth
        self.tool_registry: Dict[str, ToolSpecification] = {}
        self.tool_compositions: Dict[str, ToolComposition] = {}
        self.learned_patterns: List[ToolLearning] = []
        self.composition_archive: Dict[str, ToolComposition] = {}
        self.build_history: List[Dict[str, Any]] = []
        self.recursion_counter = 0

    async def build_tool(
        self,
        problem: str,
        available_tools: Optional[List[str]] = None,
        recursion_depth: int = 0,
    ) -> Optional[ToolSpecification]:
        """Recursively build a tool to solve a problem.

        Args:
            problem: Problem description
            available_tools: List of tool IDs available for composition
            recursion_depth: Current recursion depth

        Returns:
            New tool specification or None if unable to build
        """
        if recursion_depth >= self.max_recursion_depth:
            logger.warning(
                f"Max recursion depth {self.max_recursion_depth} reached"
            )
            return None

        self.recursion_counter += 1
        tool_id = f"tool_r0_{self.recursion_counter}_{uuid.uuid4().hex[:8]}"

        try:
            # Check if problem can be solved with existing tools
            composition = await self._find_or_create_composition(
                problem, available_tools
            )

            if composition:
                # Create composite tool from composition
                tool = ToolSpecification(
                    tool_id=tool_id,
                    tool_type=ToolType.COMPOSITE.value,
                    name=f"Composite_{problem[:20]}",
                    description=f"Composed tool for: {problem}",
                    dependencies=composition.tool_ids,
                )
                self.tool_registry[tool_id] = tool
                self.build_history.append({
                    "action": "composite_created",
                    "tool_id": tool_id,
                    "composition_id": composition.composition_id,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return tool

            # If no composition found, try recursive decomposition
            subproblems = await self._decompose_problem(problem)
            if subproblems:
                subtools = []
                for subproblem in subproblems:
                    subtool = await self.build_tool(
                        subproblem,
                        available_tools,
                        recursion_depth + 1
                    )
                    if subtool:
                        subtools.append(subtool.tool_id)

                if len(subtools) == len(subproblems):
                    # Successfully created all subtools
                    recursive_tool = ToolSpecification(
                        tool_id=tool_id,
                        tool_type=ToolType.RECURSIVE.value,
                        name=f"Recursive_{problem[:20]}",
                        description=f"Recursive tool for: {problem}",
                        dependencies=subtools,
                    )
                    self.tool_registry[tool_id] = recursive_tool
                    self.build_history.append({
                        "action": "recursive_created",
                        "tool_id": tool_id,
                        "subtools": subtools,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    return recursive_tool

            # Create atomic tool as fallback
            atomic_tool = ToolSpecification(
                tool_id=tool_id,
                tool_type=ToolType.ATOMIC.value,
                name=f"Atomic_{problem[:20]}",
                description=f"Atomic tool for: {problem}",
            )
            self.tool_registry[tool_id] = atomic_tool
            self.build_history.append({
                "action": "atomic_created",
                "tool_id": tool_id,
                "timestamp": datetime.utcnow().isoformat(),
            })
            return atomic_tool

        except Exception as e:
            logger.error(f"Error building tool for {problem}: {e}")
            return None

    async def _find_or_create_composition(
        self,
        problem: str,
        available_tools: Optional[List[str]]
    ) -> Optional[ToolComposition]:
        """Find existing or create new tool composition."""
        available = available_tools or list(self.tool_registry.keys())

        # Check learned patterns
        for pattern in self.learned_patterns:
            for composition in pattern.tool_combinations:
                # Check if pattern applies to this problem domain
                if composition.problem_domain in problem.lower():
                    if composition.success_rate > 0.7:
                        return composition

        # Try to create new composition from available tools
        if available:
            composition = ToolComposition(
                tool_ids=available[:3],  # Use up to 3 tools
                problem_domain=self._extract_domain(problem),
            )
            return composition

        return None

    async def _decompose_problem(self, problem: str) -> List[str]:
        """Decompose problem into subproblems."""
        # Simple heuristic-based decomposition
        subproblems = []

        keywords = ["and", "then", "also", "plus", "+"]
        for keyword in keywords:
            if keyword in problem.lower():
                parts = problem.lower().split(keyword)
                subproblems = [p.strip() for p in parts if p.strip()]
                break

        # If no natural decomposition, create generic subproblems
        if not subproblems:
            subproblems = [
                f"Analyze {problem}",
                f"Process {problem}",
                f"Validate {problem}",
            ]

        return subproblems[:self.max_recursion_depth]

    async def register_tool(self, tool: ToolSpecification) -> str:
        """Register a new tool.

        Args:
            tool: Tool specification

        Returns:
            Tool ID
        """
        self.tool_registry[tool.tool_id] = tool
        logger.info(f"Registered tool: {tool.tool_id}")
        return tool.tool_id

    async def execute_tool(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a tool.

        Args:
            tool_id: Tool to execute
            inputs: Input data

        Returns:
            Tool outputs
        """
        tool = self.tool_registry.get(tool_id)
        if not tool:
            return {"error": f"Tool {tool_id} not found"}

        try:
            tool.usage_count += 1

            if tool.implementation:
                result = await tool.implementation(inputs)
            else:
                result = {"inputs": inputs, "tool_id": tool_id}

            tool.success_count += 1
            return result

        except Exception as e:
            tool.failure_count += 1
            logger.error(f"Error executing tool {tool_id}: {e}")
            return {"error": str(e), "tool_id": tool_id}

    async def learn_tool_pattern(
        self,
        compositions: List[ToolComposition],
        pattern_name: str,
        problem_domain: str,
    ) -> ToolLearning:
        """Learn effective tool composition patterns.

        Args:
            compositions: List of successful compositions
            pattern_name: Name of pattern
            problem_domain: Domain where pattern applies

        Returns:
            Learning record
        """
        success_rates = [c.success_rate for c in compositions]
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 0.0

        learning = ToolLearning(
            pattern_description=pattern_name,
            tool_combinations=compositions,
            pattern_effectiveness=avg_success,
            domain_applicability={problem_domain: avg_success},
        )

        self.learned_patterns.append(learning)
        logger.info(f"Learned pattern: {pattern_name} (effectiveness={avg_success:.3f})")
        return learning

    async def archive_composition(self, composition: ToolComposition) -> None:
        """Archive a successful composition.

        Args:
            composition: Composition to archive
        """
        key = f"{composition.problem_domain}_{len(self.composition_archive)}"
        self.composition_archive[key] = composition

    def get_tool_registry(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools."""
        return {
            tool_id: {
                "name": tool.name,
                "type": tool.tool_type,
                "dependencies": tool.dependencies,
                "success_rate": (
                    tool.success_count / max(1, tool.usage_count)
                ),
                "usage_count": tool.usage_count,
            }
            for tool_id, tool in self.tool_registry.items()
        }

    def get_learned_patterns(self) -> List[Dict[str, Any]]:
        """Get learned tool patterns."""
        return [
            {
                "pattern": learning.pattern_description,
                "effectiveness": learning.pattern_effectiveness,
                "domains": learning.domain_applicability,
                "num_compositions": len(learning.tool_combinations),
            }
            for learning in self.learned_patterns
        ]

    def _extract_domain(self, problem: str) -> str:
        """Extract problem domain from description."""
        domains = [
            "search", "sort", "filter", "transform",
            "validate", "analyze", "process", "format"
        ]
        for domain in domains:
            if domain in problem.lower():
                return domain
        return "general"

    def get_build_history(self) -> List[Dict[str, Any]]:
        """Get history of tool builds."""
        return self.build_history.copy()
