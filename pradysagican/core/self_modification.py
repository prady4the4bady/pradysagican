#!/usr/bin/env python3
"""
PHASE 5A: SELF-MODIFYING CODE ENGINE
Self-referential evolution with 7-layer safety gates
"""

import asyncio
import ast
import inspect
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional, Callable
from enum import Enum
from datetime import datetime
from collections import defaultdict


# ════════════════════════════════════════════════════════════════════════════
# SAFETY GATES & APPROVAL LAYERS
# ════════════════════════════════════════════════════════════════════════════

class ApprovalLevel(Enum):
    """7-layer approval hierarchy"""
    LAYER_1_IMMUTABLE = "immutable"           # Cannot be modified
    LAYER_2_CORE_SAFETY = "core_safety"       # Requires multiple approvals
    LAYER_3_MEMORY_ACCESS = "memory_access"   # Memory ops only
    LAYER_4_TOOL_OPS = "tool_operations"      # Tool modifications
    LAYER_5_LEARNING = "learning_system"      # Learning updates
    LAYER_6_OPTIMIZATION = "optimization"     # Performance tuning
    LAYER_7_EXPERIMENTAL = "experimental"     # Experimental features


class ModificationRisk(Enum):
    """Risk assessment for code modifications"""
    SAFE = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    CRITICAL = 0.9


@dataclass
class SafetyGate:
    """Single approval gate in safety stack"""
    layer: ApprovalLevel
    risk_threshold: float
    requires_voting: bool
    min_approvers: int
    inspection_rules: List[str]
    approved: bool = False
    approver_count: int = 0
    
    async def inspect_code(self, code: str) -> Tuple[bool, str]:
        """Inspect code against rules"""
        for rule in self.inspection_rules:
            if rule == "no_network":
                if any(x in code for x in ["requests.", "urllib", "socket."]):
                    return False, "Network access prohibited"
            elif rule == "no_file_ops":
                if any(x in code for x in ["open(", "write(", "remove(", "rmdir("]):
                    return False, "File operations prohibited"
            elif rule == "no_eval":
                if any(x in code for x in ["eval(", "exec(", "compile(", "__import__"]):
                    return False, "Dynamic execution prohibited"
            elif rule == "no_infinite_loops":
                if "while True" in code or "for _ in iter(int, 1)" in code:
                    return False, "Infinite loops prohibited"
            elif rule == "memory_bounded":
                # Check for reasonable memory usage
                if "append" in code and code.count("append") > 1000:
                    return False, "Unbounded memory growth"
        return True, "Safe"
    
    async def vote(self, approve: bool) -> None:
        """Add approval vote"""
        if approve:
            self.approver_count += 1
        self.approved = self.approver_count >= self.min_approvers


class SafetyStack:
    """7-layer safety approval system"""
    
    def __init__(self):
        self.gates: Dict[ApprovalLevel, SafetyGate] = {}
        self._initialize_gates()
    
    def _initialize_gates(self) -> None:
        """Set up all 7 safety layers"""
        self.gates[ApprovalLevel.LAYER_1_IMMUTABLE] = SafetyGate(
            layer=ApprovalLevel.LAYER_1_IMMUTABLE,
            risk_threshold=0.0,
            requires_voting=True,
            min_approvers=999,  # Cannot be approved (immutable)
            inspection_rules=["no_network", "no_file_ops", "no_eval", "no_infinite_loops"]
        )
        
        self.gates[ApprovalLevel.LAYER_2_CORE_SAFETY] = SafetyGate(
            layer=ApprovalLevel.LAYER_2_CORE_SAFETY,
            risk_threshold=0.1,
            requires_voting=True,
            min_approvers=5,
            inspection_rules=["no_network", "no_eval", "memory_bounded"]
        )
        
        self.gates[ApprovalLevel.LAYER_3_MEMORY_ACCESS] = SafetyGate(
            layer=ApprovalLevel.LAYER_3_MEMORY_ACCESS,
            risk_threshold=0.3,
            requires_voting=True,
            min_approvers=3,
            inspection_rules=["memory_bounded"]
        )
        
        self.gates[ApprovalLevel.LAYER_4_TOOL_OPS] = SafetyGate(
            layer=ApprovalLevel.LAYER_4_TOOL_OPS,
            risk_threshold=0.5,
            requires_voting=True,
            min_approvers=2,
            inspection_rules=[]
        )
        
        self.gates[ApprovalLevel.LAYER_5_LEARNING] = SafetyGate(
            layer=ApprovalLevel.LAYER_5_LEARNING,
            risk_threshold=0.6,
            requires_voting=False,
            min_approvers=1,
            inspection_rules=[]
        )
        
        self.gates[ApprovalLevel.LAYER_6_OPTIMIZATION] = SafetyGate(
            layer=ApprovalLevel.LAYER_6_OPTIMIZATION,
            risk_threshold=0.7,
            requires_voting=False,
            min_approvers=0,
            inspection_rules=[]
        )
        
        self.gates[ApprovalLevel.LAYER_7_EXPERIMENTAL] = SafetyGate(
            layer=ApprovalLevel.LAYER_7_EXPERIMENTAL,
            risk_threshold=0.8,
            requires_voting=False,
            min_approvers=0,
            inspection_rules=[]
        )
    
    async def evaluate_modification(
        self, 
        code: str, 
        layer: ApprovalLevel,
        risk: float
    ) -> Tuple[bool, str]:
        """Evaluate modification through safety gates"""
        
        # Check immutable layer
        if layer == ApprovalLevel.LAYER_1_IMMUTABLE:
            return False, "Cannot modify immutable code"
        
        gate = self.gates[layer]
        
        # Check risk threshold
        if risk > gate.risk_threshold:
            return False, f"Risk {risk:.2f} exceeds threshold {gate.risk_threshold:.2f}"
        
        # Inspect code
        safe, reason = await gate.inspect_code(code)
        if not safe:
            return False, f"Code inspection failed: {reason}"
        
        return True, "Approved"


# ════════════════════════════════════════════════════════════════════════════
# CODE ANALYSIS & MODIFICATION ENGINE
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class CodeMutation:
    """Represents a single code modification"""
    original_hash: str
    mutated_hash: str
    mutation_type: str  # "rename_var", "change_param", "add_line", etc.
    description: str
    risk_score: float
    layer: ApprovalLevel
    timestamp: datetime = field(default_factory=datetime.now)
    approved: bool = False


class CodeAnalyzer:
    """Analyze code for optimization opportunities"""
    
    async def analyze_function(self, func: Callable) -> Dict[str, Any]:
        """Analyze function for improvement opportunities"""
        source = inspect.getsource(func)
        
        # Remove leading whitespace for parsing
        import textwrap
        source = textwrap.dedent(source)
        
        # Parse AST
        tree = ast.parse(source)
        func_def = tree.body[0]
        
        analysis = {
            'function_name': func.__name__,
            'complexity': await self._calculate_complexity(func_def),
            'optimization_potential': 0.0,
            'suggestions': [],
            'metrics': {
                'lines': len(source.split('\n')),
                'parameters': len(func_def.args.args),
                'decorators': len(func_def.decorator_list),
            }
        }
        
        # Find optimization opportunities
        for node in ast.walk(func_def):
            if isinstance(node, ast.For):
                analysis['suggestions'].append("Consider vectorization for loops")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["len", "type", "isinstance"]:
                        analysis['suggestions'].append(f"Minimize {node.func.id} calls")
            elif isinstance(node, ast.ListComp):
                analysis['suggestions'].append("List comprehension is efficient ✓")
        
        # Calculate potential improvement
        analysis['optimization_potential'] = min(0.9, len(analysis['suggestions']) * 0.15)
        
        return analysis
    
    async def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1.0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1.0
        return complexity
    
    async def propose_mutation(self, func: Callable) -> Optional[CodeMutation]:
        """Propose a safe mutation to improve function"""
        analysis = await self.analyze_function(func)
        
        if analysis['optimization_potential'] < 0.3:
            return None
        
        original_hash = hashlib.sha256(inspect.getsource(func).encode()).hexdigest()[:16]
        
        # Propose parameter tuning
        mutation = CodeMutation(
            original_hash=original_hash,
            mutated_hash=hashlib.sha256(
                (original_hash + "_mutated").encode()
            ).hexdigest()[:16],
            mutation_type="parameter_optimization",
            description=f"Optimize {func.__name__} parameters",
            risk_score=0.2,
            layer=ApprovalLevel.LAYER_6_OPTIMIZATION,
            approved=False
        )
        
        return mutation


# ════════════════════════════════════════════════════════════════════════════
# EVOLUTIONARY ARCHIVES
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class EvolutionRecord:
    """Record of code evolution"""
    generation: int
    code_hash: str
    fitness: float
    mutations: List[CodeMutation]
    parent_hash: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvolutionaryArchive:
    """Maintains history of code evolution"""
    
    def __init__(self):
        self.records: List[EvolutionRecord] = []
        self.generation: int = 0
        self.best_fitness: float = 0.0
        self.fitness_history: List[float] = []
    
    async def record_generation(
        self,
        code_hash: str,
        fitness: float,
        mutations: List[CodeMutation],
        parent_hash: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> EvolutionRecord:
        """Record a generation in the archive"""
        
        record = EvolutionRecord(
            generation=self.generation,
            code_hash=code_hash,
            fitness=fitness,
            mutations=mutations,
            parent_hash=parent_hash,
            metadata=metadata or {}
        )
        
        self.records.append(record)
        self.fitness_history.append(fitness)
        
        if fitness > self.best_fitness:
            self.best_fitness = fitness
        
        self.generation += 1
        
        return record
    
    async def get_lineage(self, code_hash: str) -> List[EvolutionRecord]:
        """Get full evolutionary lineage for code"""
        lineage = []
        current_hash = code_hash
        
        while current_hash:
            record = next(
                (r for r in self.records if r.code_hash == current_hash),
                None
            )
            if not record:
                break
            lineage.append(record)
            current_hash = record.parent_hash
        
        return list(reversed(lineage))
    
    async def get_best_versions(self, top_k: int = 5) -> List[EvolutionRecord]:
        """Get top performing versions"""
        sorted_records = sorted(self.records, key=lambda r: r.fitness, reverse=True)
        return sorted_records[:top_k]
    
    async def rollback_to(self, generation: int) -> Optional[EvolutionRecord]:
        """Rollback to specific generation"""
        record = next(
            (r for r in self.records if r.generation == generation),
            None
        )
        return record


# ════════════════════════════════════════════════════════════════════════════
# SELF-MODIFYING CODE ENGINE
# ════════════════════════════════════════════════════════════════════════════

class SelfModifyingEngine:
    """Core engine for autonomous code modification"""
    
    def __init__(self):
        self.safety_stack = SafetyStack()
        self.code_analyzer = CodeAnalyzer()
        self.archive = EvolutionaryArchive()
        self.pending_modifications: List[CodeMutation] = []
        self.approved_modifications: List[CodeMutation] = []
    
    async def propose_improvement(self, func: Callable) -> Optional[CodeMutation]:
        """Propose improvement to a function"""
        mutation = await self.code_analyzer.propose_mutation(func)
        
        if mutation:
            self.pending_modifications.append(mutation)
        
        return mutation
    
    async def evaluate_modification(
        self,
        mutation: CodeMutation,
        code: str
    ) -> Tuple[bool, str]:
        """Evaluate modification through safety stack"""
        
        # Calculate risk based on mutation type
        risk_map = {
            "parameter_optimization": 0.2,
            "code_refactoring": 0.3,
            "algorithm_change": 0.6,
            "feature_addition": 0.7,
        }
        
        mutation.risk_score = risk_map.get(mutation.mutation_type, 0.5)
        
        # Evaluate through safety gates
        approved, reason = await self.safety_stack.evaluate_modification(
            code,
            mutation.layer,
            mutation.risk_score
        )
        
        return approved, reason
    
    async def approve_modification(
        self,
        mutation: CodeMutation,
        approver_id: str = "system"
    ) -> bool:
        """Approve a modification through voting"""
        
        gate = self.safety_stack.gates[mutation.layer]
        await gate.vote(True)
        
        if gate.approver_count >= gate.min_approvers:
            mutation.approved = True
            self.approved_modifications.append(mutation)
            return True
        
        return False
    
    async def record_modification(
        self,
        code_hash: str,
        fitness: float,
        mutation: CodeMutation,
        parent_hash: Optional[str] = None
    ) -> EvolutionRecord:
        """Record successful modification in archive"""
        
        record = await self.archive.record_generation(
            code_hash=code_hash,
            fitness=fitness,
            mutations=[mutation],
            parent_hash=parent_hash,
            metadata={
                'mutation_type': mutation.mutation_type,
                'description': mutation.description,
                'risk_score': mutation.risk_score,
            }
        )
        
        return record
    
    async def get_evolution_stats(self) -> Dict[str, Any]:
        """Get statistics on evolution"""
        
        if not self.archive.records:
            return {}
        
        fitnesses = [r.fitness for r in self.archive.records]
        
        return {
            'generations': self.archive.generation,
            'best_fitness': self.archive.best_fitness,
            'avg_fitness': sum(fitnesses) / len(fitnesses),
            'total_mutations': sum(len(r.mutations) for r in self.archive.records),
            'approved_modifications': len(self.approved_modifications),
            'pending_modifications': len(self.pending_modifications),
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_self_modification():
    """Demonstrate self-modification capabilities"""
    
    print("\n" + "=" * 70)
    print("SELF-MODIFYING CODE ENGINE - PHASE 5A")
    print("=" * 70)
    
    engine = SelfModifyingEngine()
    
    # Define a sample function to optimize
    def sample_function(x: int) -> int:
        """Simple function for demonstration"""
        result = 0
        for i in range(x):
            result += i
        return result
    
    # Analyze function
    print("\n[Analysis] Analyzing function for optimization...")
    analysis = await engine.code_analyzer.analyze_function(sample_function)
    print(f"  Function: {analysis['function_name']}")
    print(f"  Complexity: {analysis['complexity']:.2f}")
    print(f"  Optimization Potential: {analysis['optimization_potential']:.2%}")
    
    # Propose improvements
    print("\n[Proposal] Proposing improvements...")
    mutation = await engine.propose_improvement(sample_function)
    if mutation:
        print(f"  Type: {mutation.mutation_type}")
        print(f"  Description: {mutation.description}")
        print(f"  Risk Score: {mutation.risk_score:.2f}")
        print(f"  Layer: {mutation.layer.value}")
        
        # Evaluate modification
        print("\n[Evaluation] Evaluating safety...")
        import textwrap
        source = textwrap.dedent(inspect.getsource(sample_function))
        approved, reason = await engine.evaluate_modification(mutation, source)
        print(f"  Approved: {approved}")
        print(f"  Reason: {reason}")
        
        # Approve modification
        if approved:
            print("\n[Approval] Processing approval votes...")
            success = await engine.approve_modification(mutation)
            print(f"  Approved: {success}")
        
        # Record in archive
        if mutation and mutation.approved:
            print("\n[Archive] Recording in evolutionary archive...")
            record = await engine.record_modification(
                code_hash="abc123def456",
                fitness=0.87,
                mutation=mutation,
                parent_hash=None
            )
            print(f"  Generation: {record.generation}")
            print(f"  Fitness: {record.fitness:.2f}")
    else:
        print("  No improvements proposed (optimization potential too low)")
        # Create demo mutation for testing
        mutation = CodeMutation(
            original_hash="abc123",
            mutated_hash="def456",
            mutation_type="parameter_optimization",
            description="Demo parameter tuning",
            risk_score=0.2,
            layer=ApprovalLevel.LAYER_6_OPTIMIZATION,
            approved=False
        )
        
        print("\n[Demo] Using demo mutation for illustration...")
        
        # Approve it
        success = await engine.approve_modification(mutation)
        print(f"  Approved: {success}")
        
        # Record
        print("\n[Archive] Recording demo modification...")
        record = await engine.record_modification(
            code_hash="abc123def456",
            fitness=0.85,
            mutation=mutation,
            parent_hash=None
        )
        print(f"  Generation: {record.generation}")
        print(f"  Fitness: {record.fitness:.2f}")
    
    # Show statistics
    print("\n[Statistics] Evolution Statistics:")
    stats = await engine.get_evolution_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_self_modification())
