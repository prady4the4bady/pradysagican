"""
PRAXIS — Behavioral Contracts System

Features F133–F158: Complete behavioral contract framework for runtime safety.

Core components:
- contract.py: Contract DSL (preconditions, postconditions, invariants, resources)
- extractor.py: LLM-based automatic contract extraction
- runtime.py: Runtime enforcement with audit trails
- verifier.py: SMT-based formal verification (Z3)
- composer.py: Multi-contract composition and conflict resolution
"""

from .contract import (
    BehavioralContract,
    Precondition,
    Postcondition,
    Invariant,
    ResourceLimit,
    ContractSignature,
    ExecutionTrace,
    ContractBuilder,
    ConstraintType,
)

from .extractor import (
    ContractExtractor,
    ContractLibrary,
    ExtractionTemplate,
)

from .runtime import (
    ContractEnforcer,
    enforce_contract,
    get_enforcer,
)

__all__ = [
    # Contract types
    "BehavioralContract",
    "Precondition",
    "Postcondition",
    "Invariant",
    "ResourceLimit",
    "ContractSignature",
    "ExecutionTrace",
    "ContractBuilder",
    "ConstraintType",
    
    # Extraction
    "ContractExtractor",
    "ContractLibrary",
    "ExtractionTemplate",
    
    # Runtime
    "ContractEnforcer",
    "enforce_contract",
    "get_enforcer",
]
