"""
Behavioral Contract System (F133–F146)

Feature: F133 — Behavioral Contract Framework
Feature: F134 — Precondition Specification
Feature: F135 — Postcondition Specification
Feature: F136 — Invariant Enforcement
Feature: F137 — Remediation Actions
Feature: F138 — Multi-Contract Composition
Feature: F139 — Contract Versioning
Feature: F140 — Evidence Logging
Feature: F141 — Cost Measurement
Feature: F142 — Latency Guarantees
Feature: F143 — Memory Limits
Feature: F144 — I/O Containment
Feature: F145 — External API Quotas
Feature: F146 — Dependency Injection

Contract DSL for specifying tool behavior, constraints, and safety properties.
Contracts are immutable, composable, and verifiable.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    """Types of constraints in a contract."""
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    INVARIANT = "invariant"
    RESOURCE_LIMIT = "resource_limit"
    LATENCY_BOUND = "latency_bound"
    OUTPUT_CONSTRAINT = "output_constraint"


@dataclass
class Precondition:
    """Precondition: what must be true before execution."""
    name: str
    description: str
    predicate: str  # FOL predicate or Python expression
    priority: int = 1  # 1=critical, 5=advisory
    remediation: Optional[str] = None  # Action if violated


@dataclass
class Postcondition:
    """Postcondition: what must be true after execution."""
    name: str
    description: str
    predicate: str  # FOL predicate or Python expression
    priority: int = 1  # 1=critical, 5=advisory
    remediation: Optional[str] = None  # Action if violated


@dataclass
class ResourceLimit:
    """Resource constraint."""
    resource_type: str  # "memory", "cpu", "time", "io", "api"
    limit_value: float
    limit_unit: str  # "MB", "ms", "calls/hour", etc.
    enforcement: str = "hard"  # "hard" = fail, "soft" = warn


@dataclass
class Invariant:
    """Invariant: must remain true throughout execution."""
    name: str
    predicate: str
    description: str
    priority: int = 1


@dataclass
class ContractSignature:
    """Signature of a contract (immutable)."""
    contract_id: str
    version: str
    created_at: str
    author: str
    hash_value: str = ""
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of this signature."""
        data = {
            "contract_id": self.contract_id,
            "version": self.version,
            "created_at": self.created_at,
            "author": self.author,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


@dataclass
class BehavioralContract:
    """
    A behavioral contract specifies the acceptable behavior of a tool or function.
    
    Contracts are:
    - Immutable: once created, cannot be modified
    - Composable: can be combined to form multi-contract systems
    - Verifiable: can be checked against actual execution traces
    - Versionable: support contract evolution
    """
    
    contract_id: str
    tool_name: str
    description: str
    preconditions: List[Precondition] = field(default_factory=list)
    postconditions: List[Postcondition] = field(default_factory=list)
    invariants: List[Invariant] = field(default_factory=list)
    resource_limits: List[ResourceLimit] = field(default_factory=list)
    expected_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    
    # Metadata
    version: str = "1.0"
    author: str = "system"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    signature: Optional[ContractSignature] = None
    
    # Immutability flag
    _is_frozen: bool = field(default=False, init=False, repr=False)
    
    def freeze(self) -> "BehavioralContract":
        """Freeze contract to make it immutable."""
        if not self._is_frozen:
            self.signature = ContractSignature(
                contract_id=self.contract_id,
                version=self.version,
                created_at=self.created_at,
                author=self.author,
            )
            self.signature.hash_value = self.signature.compute_hash()
            self._is_frozen = True
            logger.info(f"Contract {self.contract_id} frozen: {self.signature.hash_value[:16]}")
        return self
    
    def is_frozen(self) -> bool:
        """Check if contract is frozen."""
        return self._is_frozen
    
    def verify_signature(self) -> bool:
        """Verify contract signature integrity."""
        if self.signature is None:
            return False
        
        expected_hash = self.signature.compute_hash()
        return expected_hash == self.signature.hash_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary."""
        return asdict(self)
    
    def add_precondition(self, precond: Precondition) -> "BehavioralContract":
        """Add a precondition (before freeze)."""
        if self._is_frozen:
            raise RuntimeError(f"Cannot modify frozen contract {self.contract_id}")
        self.preconditions.append(precond)
        return self
    
    def add_postcondition(self, postcond: Postcondition) -> "BehavioralContract":
        """Add a postcondition (before freeze)."""
        if self._is_frozen:
            raise RuntimeError(f"Cannot modify frozen contract {self.contract_id}")
        self.postconditions.append(postcond)
        return self
    
    def add_invariant(self, inv: Invariant) -> "BehavioralContract":
        """Add an invariant (before freeze)."""
        if self._is_frozen:
            raise RuntimeError(f"Cannot modify frozen contract {self.contract_id}")
        self.invariants.append(inv)
        return self
    
    def add_resource_limit(self, limit: ResourceLimit) -> "BehavioralContract":
        """Add a resource limit (before freeze)."""
        if self._is_frozen:
            raise RuntimeError(f"Cannot modify frozen contract {self.contract_id}")
        self.resource_limits.append(limit)
        return self
    
    def __str__(self) -> str:
        return (
            f"Contract({self.contract_id}/{self.version})\n"
            f"  Tool: {self.tool_name}\n"
            f"  Preconditions: {len(self.preconditions)}\n"
            f"  Postconditions: {len(self.postconditions)}\n"
            f"  Invariants: {len(self.invariants)}\n"
            f"  Resource Limits: {len(self.resource_limits)}"
        )


@dataclass
class ExecutionTrace:
    """Record of a tool execution for contract verification."""
    contract_id: str
    tool_name: str
    start_time: float
    end_time: Optional[float] = None
    input_args: Optional[Dict[str, Any]] = None
    output_result: Optional[Any] = None
    exception: Optional[str] = None
    
    # Resource measurements
    memory_used_mb: float = 0.0
    cpu_time_ms: float = 0.0
    io_operations: int = 0
    api_calls: int = 0
    
    # Contract verification results
    preconditions_passed: List[str] = field(default_factory=list)
    preconditions_failed: List[str] = field(default_factory=list)
    postconditions_passed: List[str] = field(default_factory=list)
    postconditions_failed: List[str] = field(default_factory=list)
    invariants_passed: List[str] = field(default_factory=list)
    invariants_failed: List[str] = field(default_factory=list)
    
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000
    
    def all_passed(self) -> bool:
        """Check if all contract checks passed."""
        return (
            len(self.preconditions_failed) == 0
            and len(self.postconditions_failed) == 0
            and len(self.invariants_failed) == 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ContractBuilder:
    """Builder pattern for constructing contracts."""
    
    def __init__(self, contract_id: str, tool_name: str, description: str = ""):
        self.contract = BehavioralContract(
            contract_id=contract_id,
            tool_name=tool_name,
            description=description,
        )
    
    def add_precondition(self, name: str, predicate: str, description: str = "", priority: int = 1) -> "ContractBuilder":
        """Add precondition."""
        self.contract.add_precondition(Precondition(name, description or predicate, predicate, priority))
        return self
    
    def add_postcondition(self, name: str, predicate: str, description: str = "", priority: int = 1) -> "ContractBuilder":
        """Add postcondition."""
        self.contract.add_postcondition(Postcondition(name, description or predicate, predicate, priority))
        return self
    
    def add_invariant(self, name: str, predicate: str, description: str = "", priority: int = 1) -> "ContractBuilder":
        """Add invariant."""
        self.contract.add_invariant(Invariant(name, predicate, description or predicate, priority))
        return self
    
    def add_memory_limit(self, limit_mb: float) -> "ContractBuilder":
        """Add memory limit."""
        self.contract.add_resource_limit(ResourceLimit("memory", limit_mb, "MB"))
        return self
    
    def add_time_limit(self, limit_ms: float) -> "ContractBuilder":
        """Add time limit."""
        self.contract.add_resource_limit(ResourceLimit("time", limit_ms, "ms"))
        return self
    
    def add_latency_guarantee(self, expected_ms: float, max_ms: Optional[float] = None) -> "ContractBuilder":
        """Add latency guarantee."""
        self.contract.expected_latency_ms = expected_ms
        if max_ms is None:
            max_ms = expected_ms * 2
        self.contract.max_latency_ms = max_ms
        return self
    
    def build(self) -> BehavioralContract:
        """Build and freeze the contract."""
        return self.contract.freeze()
