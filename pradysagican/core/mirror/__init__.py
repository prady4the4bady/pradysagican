"""
MIRROR — Metacognitive Calibration System (F271–F280)

Monitors system self-assessment accuracy:
- Confidence calibration tracking
- Blindsight detection (unknown unknowns)
- Stability and drift monitoring
- Vital signs dashboard for system health
"""

from .calibration import (
    Mirror,
    CalibrationEngine,
    CalibrationCurve,
    StabilityModel,
    VitalSignsMonitor,
    ConfidenceEstimate,
    CalibrationMetrics,
    VitalSign,
    get_mirror,
)

__all__ = [
    "Mirror",
    "CalibrationEngine",
    "CalibrationCurve",
    "StabilityModel",
    "VitalSignsMonitor",
    "ConfidenceEstimate",
    "CalibrationMetrics",
    "VitalSign",
    "get_mirror",
]
