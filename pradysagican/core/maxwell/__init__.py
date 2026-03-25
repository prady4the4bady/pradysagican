"""
MAXWELL — Trilemma Escape Engine

Solves the self-evolution trilemma: intelligence + autonomy + safety simultaneously.

This module provides the safety daemon that continuously monitors PRADY's belief
drift, entropy, and alignment. It can halt execution immediately if drift exceeds
safe bounds (D* > 0.27).

Key components:
- MAXWELLDaemon: Main orchestration class
- FrozenSafetyOracle: Immutable initial safety distribution snapshot
- AlignmentEntropyClock: Monotonic drift counter
- KLDivergenceSentinel: Real-time divergence monitor (<10ms)
- AdversarialProbeBattery: 500 safety test cases
- SafeBasinTopography: Maps safety space as loss landscape

Features (F121–F132):
F121 — Belief Contrast Engine
F122 — KL Divergence Sentinel
F123 — Safe Basin Topography
F124 — Cognitive Degeneration Early Warning
F125 — Alignment Entropy Clock
F126 — Communication Collapse Detector
F127 — Frozen Safety Oracle
F128 — Adversarial Probe Battery
F129 — Thermodynamic Cooling
F130 — Diversity Injection Protocol
F131 — Entropy Release Scheduler
F132 — Divergence Threshold Gate
"""

from .daemon import MAXWELLDaemon
from .oracle import FrozenSafetyOracle
from .entropy import AlignmentEntropyClock
from .sentinel import KLDivergenceSentinel
from .probes import AdversarialProbeBattery
from .topography import SafeBasinTopography

__all__ = [
    "MAXWELLDaemon",
    "FrozenSafetyOracle",
    "AlignmentEntropyClock",
    "KLDivergenceSentinel",
    "AdversarialProbeBattery",
    "SafeBasinTopography",
]
