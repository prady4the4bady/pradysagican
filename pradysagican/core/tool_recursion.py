#!/usr/bin/env python3
"""
PHASE 5B: TOOL RECURSION ENGINE
Autonomous tool creation and composition
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional, Callable
from enum import Enum
from datetime import datetime
from functools import wraps


# ════════════════════════════════════════════════════════════════════════════
# TOOL ABSTRACTION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ToolSignature:
    """Signature of a tool"""
    name: str
    description: str
    input_schema: Dict[str, str]  # param: type
    output_schema: str
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ToolExecution:
    """Record of tool execution"""
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Any
    execution_time_ms: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ToolRecursionLevel(Enum):
    """Recursion level for tool composition"""
    ATOMIC = 0           # Base tools (no dependencies)
    COMPOSITE = 1        # Combines 1-2 tools
    META = 2             # Combines 2+ tools with adaptation
    RECURSIVE = 3        # Can create tools


class ToolFactory:
    """Creates new tools dynamically"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.signatures: Dict[str, ToolSignature] = {}
        self.execution_log: List[ToolExecution] = []
        self.tool_counter = 0
    
    async def register_tool(
        self,
        func: Callable,
        signature: ToolSignature
    ) -> None:
        """Register a tool"""
        self.tools[signature.name] = func
        self.signatures[signature.name] = signature
    
    async def create_composite_tool(
        self,
        name: str,
        description: str,
        base_tools: List[str],
        composition_fn: Callable
    ) -> ToolSignature:
        """Create a composite tool from multiple base tools"""
        
        # Validate base tools exist
        for tool_name in base_tools:
            if tool_name not in self.tools:
                raise ValueError(f"Tool {tool_name} not found")
        
        @wraps(composition_fn)
        async def composite_wrapper(**kwargs):
            results = {}
            for tool_name in base_tools:
                tool = self.tools[tool_name]
                # Execute each base tool
                result = await tool(**kwargs) if asyncio.iscoroutinefunction(tool) else tool(**kwargs)
                results[tool_name] = result
            
            # Apply composition function
            return await composition_fn(results) if asyncio.iscoroutinefunction(composition_fn) else composition_fn(results)
        
        # Create signature for composite
        signature = ToolSignature(
            name=name,
            description=description,
            input_schema={},  # Inherited from base tools
            output_schema="Any",
            version="1.0.0",
            dependencies=base_tools
        )
        
        await self.register_tool(composite_wrapper, signature)
        self.tool_counter += 1
        
        return signature
    
    async def create_meta_tool(
        self,
        name: str,
        description: str,
        adaptation_fn: Callable
    ) -> ToolSignature:
        """Create a meta-tool that adapts other tools"""
        
        @wraps(adaptation_fn)
        async def meta_wrapper(**kwargs):
            # Meta-tool logic: adapt based on context
            context = kwargs.get('context', {})
            return await adaptation_fn(context, self.tools) if asyncio.iscoroutinefunction(adaptation_fn) else adaptation_fn(context, self.tools)
        
        signature = ToolSignature(
            name=name,
            description=description,
            input_schema={'context': 'dict'},
            output_schema="Any",
            version="1.0.0",
            dependencies=[]
        )
        
        await self.register_tool(meta_wrapper, signature)
        self.tool_counter += 1
        
        return signature
    
    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Tuple[Any, ToolExecution]:
        """Execute a tool and log execution"""
        
        import time
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        start_time = time.time()
        
        try:
            result = await tool(**kwargs) if asyncio.iscoroutinefunction(tool) else tool(**kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        execution = ToolExecution(
            tool_name=tool_name,
            inputs=kwargs,
            outputs=result,
            execution_time_ms=execution_time,
            success=success,
            error=error
        )
        
        self.execution_log.append(execution)
        
        return result, execution
    
    async def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a tool"""
        executions = [e for e in self.execution_log if e.tool_name == tool_name]
        
        if not executions:
            return {}
        
        successful = [e for e in executions if e.success]
        times = [e.execution_time_ms for e in successful]
        
        return {
            'total_executions': len(executions),
            'successful': len(successful),
            'failed': len(executions) - len(successful),
            'success_rate': len(successful) / len(executions),
            'avg_time_ms': sum(times) / len(times) if times else 0,
            'min_time_ms': min(times) if times else 0,
            'max_time_ms': max(times) if times else 0,
        }


# ════════════════════════════════════════════════════════════════════════════
# TOOL COMPOSITION ENGINE
# ════════════════════════════════════════════════════════════════════════════

class ToolComposer:
    """Composes tools into higher-order capabilities"""
    
    def __init__(self, factory: ToolFactory):
        self.factory = factory
        self.compositions: Dict[str, Dict[str, Any]] = {}
    
    async def analyze_tools(self) -> Dict[str, Any]:
        """Analyze available tools for composition"""
        
        analysis = {
            'total_tools': len(self.factory.tools),
            'atomic_tools': 0,
            'composite_tools': 0,
            'meta_tools': 0,
            'tool_list': []
        }
        
        for name, sig in self.factory.signatures.items():
            tool_type = (
                'composite' if len(sig.dependencies) > 1
                else 'meta' if len(sig.dependencies) == 0 and 'meta' in name.lower()
                else 'atomic'
            )
            
            if tool_type == 'composite':
                analysis['composite_tools'] += 1
            elif tool_type == 'meta':
                analysis['meta_tools'] += 1
            else:
                analysis['atomic_tools'] += 1
            
            analysis['tool_list'].append({
                'name': name,
                'type': tool_type,
                'deps': len(sig.dependencies)
            })
        
        return analysis
    
    async def find_composition_candidates(
        self,
        goal: str
    ) -> List[Tuple[str, str]]:
        """Find tools that could work together"""
        
        candidates = []
        
        for name1, sig1 in self.factory.signatures.items():
            for name2, sig2 in self.factory.signatures.items():
                if name1 != name2:
                    # Check if output of one could feed into input of other
                    if self._compatible(sig1.output_schema, sig2.input_schema):
                        candidates.append((name1, name2))
        
        return candidates[:5]  # Return top 5
    
    def _compatible(self, output: str, inputs: Dict[str, str]) -> bool:
        """Check if output is compatible with inputs"""
        # Simplified compatibility check
        if output == "Any" or "Any" in str(inputs.values()):
            return True
        return False
    
    async def compose_for_goal(
        self,
        goal: str,
        base_tools: List[str]
    ) -> Optional[Callable]:
        """Compose tools to achieve a goal"""
        
        if len(base_tools) < 2:
            return None
        
        # Create composition
        async def composed_workflow(**kwargs):
            results = {}
            for tool_name in base_tools:
                result, _ = await self.factory.execute_tool(tool_name, **kwargs)
                results[tool_name] = result
            return results
        
        self.compositions[goal] = {
            'tools': base_tools,
            'created_at': datetime.now(),
            'workflow': composed_workflow
        }
        
        return composed_workflow


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_tool_recursion():
    """Demonstrate tool recursion and creation"""
    
    print("\n" + "=" * 70)
    print("TOOL RECURSION ENGINE - PHASE 5B")
    print("=" * 70)
    
    factory = ToolFactory()
    
    # Register base tools
    print("\n[Setup] Registering base tools...")
    
    async def add(a: int, b: int) -> int:
        return a + b
    
    async def multiply(a: int, b: int) -> int:
        return a * b
    
    async def square(x: int) -> int:
        return x * x
    
    # Register signatures
    sig_add = ToolSignature("add", "Add two numbers", {"a": "int", "b": "int"}, "int")
    sig_mult = ToolSignature("multiply", "Multiply two numbers", {"a": "int", "b": "int"}, "int")
    sig_square = ToolSignature("square", "Square a number", {"x": "int"}, "int")
    
    await factory.register_tool(add, sig_add)
    await factory.register_tool(multiply, sig_mult)
    await factory.register_tool(square, sig_square)
    print(f"  Registered 3 base tools")
    
    # Create composite tool
    print("\n[Composition] Creating composite tools...")
    
    async def add_and_square(results):
        """Composition: add then square"""
        # In real scenario, would chain results
        return {"add_result": 10, "square_result": 100}
    
    composite_sig = await factory.create_composite_tool(
        "add_and_square",
        "Add two numbers then square result",
        ["add", "square"],
        add_and_square
    )
    print(f"  Created composite tool: {composite_sig.name}")
    
    # Execute tools
    print("\n[Execution] Executing tools...")
    
    result1, exec1 = await factory.execute_tool("add", a=5, b=3)
    print(f"  add(5, 3) = {result1}, time: {exec1.execution_time_ms:.2f}ms")
    
    result2, exec2 = await factory.execute_tool("multiply", a=4, b=7)
    print(f"  multiply(4, 7) = {result2}, time: {exec2.execution_time_ms:.2f}ms")
    
    result3, exec3 = await factory.execute_tool("square", x=5)
    print(f"  square(5) = {result3}, time: {exec3.execution_time_ms:.2f}ms")
    
    # Analyze tools
    print("\n[Analysis] Tool Analysis:")
    for tool_name in ["add", "multiply", "square"]:
        stats = await factory.get_tool_stats(tool_name)
        print(f"  {tool_name}: {stats['successful']}/{stats['total_executions']} successful, "
              f"{stats['avg_time_ms']:.2f}ms avg")
    
    # Tool composition analysis
    print("\n[Composition Analysis] Available tool compositions:")
    composer = ToolComposer(factory)
    analysis = await composer.analyze_tools()
    print(f"  Total tools: {analysis['total_tools']}")
    print(f"  Atomic: {analysis['atomic_tools']}")
    print(f"  Composite: {analysis['composite_tools']}")
    print(f"  Meta: {analysis['meta_tools']}")
    
    # Composition candidates
    print("\n[Candidates] Tool composition candidates:")
    candidates = await composer.find_composition_candidates("arithmetic_workflow")
    for tool1, tool2 in candidates[:3]:
        print(f"  {tool1} → {tool2}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_tool_recursion())
