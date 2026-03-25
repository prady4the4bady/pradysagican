"""
MIRROR — Metacognitive Calibration System (F271–F280)

Feature: F271 — Confidence Calibration
Feature: F272 — Calibration Curves
Feature: F273 — Blindsight Detection
Feature: F274 — Vital Signs Dashboard
Feature: F275 — Stability Model
Feature: F276 — Confidence Tracking
Feature: F277 — Epistemic Uncertainty
Feature: F278 — Metacognitive Audit
Feature: F279 — Self-Assessment Engine
Feature: F280 — Confidence Correction

Metacognitive calibration: comparing confidence estimates with actual accuracy.
Detects overconfidence, underconfidence, and blindspots (unknown unknowns).
"""

import logging
import json
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime, timezone
import threading

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceEstimate:
    """A confidence estimate for a tool output."""
    tool_name: str
    task_id: str
    estimated_confidence: float  # 0-1
    actual_accuracy: Optional[float] = None  # 0-1 (filled in later when ground truth known)
    output_value: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CalibrationMetrics:
    """Calibration accuracy metrics for a tool."""
    tool_name: str
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    average_confidence: float = 0.0
    calibration_error: float = 0.0  # |accuracy - average_confidence|
    overconfidence: float = 0.0  # average_confidence - accuracy (>0 = overconfident)
    underconfidence: float = 0.0  # accuracy - average_confidence (>0 = underconfident)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class VitalSign:
    """System vital sign for health monitoring."""
    metric_name: str
    current_value: float
    normal_range: Tuple[float, float]
    severity: str = "ok"  # "ok", "warning", "critical"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def is_healthy(self) -> bool:
        """Check if vital sign is healthy."""
        return self.severity == "ok"


class CalibrationCurve:
    """
    Calibration curve for a tool.
    
    Maps confidence levels to actual accuracy levels.
    Perfect calibration: confidence == accuracy at all levels.
    """
    
    def __init__(self, tool_name: str, bins: int = 10):
        """
        Args:
            tool_name: Name of tool
            bins: Number of confidence bins (0-1 range)
        """
        self.tool_name = tool_name
        self.bins = bins
        self.bin_size = 1.0 / bins
        
        # Bin index -> (confidence_total, accuracy_total, count)
        self.bin_data: Dict[int, Tuple[float, float, int]] = defaultdict(lambda: (0.0, 0.0, 0))
    
    def add_prediction(self, confidence: float, accuracy: float):
        """Record a prediction."""
        bin_idx = min(int(confidence / self.bin_size), self.bins - 1)
        
        conf_total, acc_total, count = self.bin_data[bin_idx]
        self.bin_data[bin_idx] = (conf_total + confidence, acc_total + accuracy, count + 1)
    
    def get_calibration_data(self) -> Dict[int, Dict[str, float]]:
        """Get calibration data for plotting."""
        result = {}
        
        for bin_idx in range(self.bins):
            if bin_idx in self.bin_data:
                conf_total, acc_total, count = self.bin_data[bin_idx]
                result[bin_idx] = {
                    "confidence": conf_total / count if count > 0 else 0.0,
                    "accuracy": acc_total / count if count > 0 else 0.0,
                    "count": count,
                }
        
        return result
    
    def get_calibration_error(self) -> float:
        """Compute overall calibration error (Expected Calibration Error)."""
        errors = []
        
        for conf_total, acc_total, count in self.bin_data.values():
            if count > 0:
                avg_conf = conf_total / count
                avg_acc = acc_total / count
                errors.append(abs(avg_conf - avg_acc))
        
        return statistics.mean(errors) if errors else 0.0


class CalibrationEngine:
    """
    Main calibration engine: tracks and measures calibration of all tools.
    """
    
    def __init__(self):
        self.estimates: List[ConfidenceEstimate] = []
        self.curves: Dict[str, CalibrationCurve] = {}
        self.metrics: Dict[str, CalibrationMetrics] = defaultdict(lambda: CalibrationMetrics(tool_name=""))
        self._lock = threading.Lock()
    
    def record_estimate(self, tool_name: str, task_id: str, confidence: float, output_value: Any = None, metadata: Optional[Dict[str, Any]] = None):
        """Record a confidence estimate."""
        estimate = ConfidenceEstimate(
            tool_name=tool_name,
            task_id=task_id,
            estimated_confidence=confidence,
            output_value=output_value,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.estimates.append(estimate)
            
            # Create curve if needed
            if tool_name not in self.curves:
                self.curves[tool_name] = CalibrationCurve(tool_name)
    
    def record_ground_truth(self, tool_name: str, task_id: str, accuracy: float):
        """Record ground truth accuracy for an estimate."""
        with self._lock:
            # Find matching estimate
            for est in self.estimates:
                if est.tool_name == tool_name and est.task_id == task_id and est.actual_accuracy is None:
                    est.actual_accuracy = accuracy
                    
                    # Update calibration curve
                    if tool_name in self.curves:
                        self.curves[tool_name].add_prediction(est.estimated_confidence, accuracy)
                    
                    # Update metrics
                    self._update_metrics(tool_name, est.estimated_confidence, accuracy)
                    break
    
    def _update_metrics(self, tool_name: str, confidence: float, accuracy: float):
        """Update calibration metrics."""
        if tool_name not in self.metrics:
            self.metrics[tool_name] = CalibrationMetrics(tool_name=tool_name)
        
        m = self.metrics[tool_name]
        m.total_predictions += 1
        m.correct_predictions += int(accuracy > 0.5)
        m.accuracy = m.correct_predictions / m.total_predictions if m.total_predictions > 0 else 0.0
        
        # Update average confidence
        all_conf = [e.estimated_confidence for e in self.estimates if e.tool_name == tool_name and e.estimated_confidence]
        m.average_confidence = statistics.mean(all_conf) if all_conf else 0.0
        
        # Update calibration error
        m.calibration_error = abs(m.accuracy - m.average_confidence)
        m.overconfidence = max(0, m.average_confidence - m.accuracy)
        m.underconfidence = max(0, m.accuracy - m.average_confidence)
    
    def get_metrics(self, tool_name: str) -> Optional[CalibrationMetrics]:
        """Get calibration metrics for a tool."""
        with self._lock:
            return self.metrics.get(tool_name)
    
    def get_all_metrics(self) -> Dict[str, CalibrationMetrics]:
        """Get metrics for all tools."""
        with self._lock:
            return dict(self.metrics)
    
    def get_calibration_curve(self, tool_name: str) -> Optional[CalibrationCurve]:
        """Get calibration curve for a tool."""
        with self._lock:
            return self.curves.get(tool_name)
    
    def detect_overconfidence(self, threshold: float = 0.1) -> List[str]:
        """Detect tools that are overconfident."""
        overconfident = []
        
        with self._lock:
            for tool_name, m in self.metrics.items():
                if m.overconfidence > threshold:
                    overconfident.append(tool_name)
        
        return overconfident
    
    def detect_blindsights(self) -> Dict[str, float]:
        """
        Detect blindsights: areas where system confidence is high but accuracy is low.
        
        Returns:
            Dict of tool_name -> blindsight_severity
        """
        blindsights = {}
        
        with self._lock:
            for tool_name, curve in self.curves.items():
                data = curve.get_calibration_data()
                
                # Check high-confidence, low-accuracy bins
                for bin_idx, bin_info in data.items():
                    if bin_info["count"] >= 5:  # Enough samples
                        conf = bin_info["confidence"]
                        acc = bin_info["accuracy"]
                        
                        # If high confidence but low accuracy: blindsight
                        if conf > 0.8 and acc < 0.5:
                            blindsights[f"{tool_name}_bin_{bin_idx}"] = conf - acc
        
        return blindsights


class StabilityModel:
    """
    Monitors system stability: detection of sudden accuracy drops, drift, etc.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Args:
            window_size: Moving window for stability analysis
        """
        self.window_size = window_size
        self.accuracy_history: Dict[str, List[float]] = defaultdict(list)
    
    def record_accuracy(self, tool_name: str, accuracy: float):
        """Record accuracy measurement."""
        self.accuracy_history[tool_name].append(accuracy)
        
        # Trim to window
        if len(self.accuracy_history[tool_name]) > self.window_size:
            self.accuracy_history[tool_name] = self.accuracy_history[tool_name][-self.window_size:]
    
    def detect_drift(self, tool_name: str, threshold: float = 0.1) -> bool:
        """Detect if accuracy is drifting downward."""
        history = self.accuracy_history.get(tool_name, [])
        
        if len(history) < 10:
            return False
        
        # Compare first half vs second half
        mid = len(history) // 2
        first_half_avg = statistics.mean(history[:mid])
        second_half_avg = statistics.mean(history[mid:])
        
        drift = first_half_avg - second_half_avg
        return drift > threshold
    
    def get_trend(self, tool_name: str) -> str:
        """Get accuracy trend."""
        history = self.accuracy_history.get(tool_name, [])
        
        if len(history) < 2:
            return "insufficient_data"
        
        if history[-1] > history[0] + 0.05:
            return "improving"
        elif history[-1] < history[0] - 0.05:
            return "declining"
        else:
            return "stable"


class VitalSignsMonitor:
    """
    Monitors vital signs of system health.
    """
    
    def __init__(self):
        self.vital_signs: Dict[str, VitalSign] = {}
    
    def set_vital_sign(self, metric_name: str, value: float, normal_range: Tuple[float, float]):
        """Set a vital sign value."""
        # Determine severity
        low, high = normal_range
        if low <= value <= high:
            severity = "ok"
        elif low * 0.5 <= value <= high * 1.5:
            severity = "warning"
        else:
            severity = "critical"
        
        sign = VitalSign(
            metric_name=metric_name,
            current_value=value,
            normal_range=normal_range,
            severity=severity
        )
        
        self.vital_signs[metric_name] = sign
    
    def get_vital_signs(self) -> Dict[str, VitalSign]:
        """Get all vital signs."""
        return dict(self.vital_signs)
    
    def health_status(self) -> str:
        """Overall system health status."""
        if not self.vital_signs:
            return "unknown"
        
        severities = [v.severity for v in self.vital_signs.values()]
        
        if "critical" in severities:
            return "critical"
        elif "warning" in severities:
            return "warning"
        else:
            return "healthy"


# Global MIRROR instance
_global_mirror = None


def get_mirror() -> 'Mirror':
    """Get global MIRROR instance."""
    global _global_mirror
    if _global_mirror is None:
        _global_mirror = Mirror()
    return _global_mirror


class Mirror:
    """
    Main MIRROR metacognitive system.
    
    Coordinates:
    - Calibration tracking
    - Blindsight detection
    - Stability monitoring
    - Vital signs dashboard
    """
    
    def __init__(self):
        self.calibration = CalibrationEngine()
        self.stability = StabilityModel()
        self.vital_signs = VitalSignsMonitor()
    
    def record_estimate_and_truth(self, tool_name: str, task_id: str, confidence: float, accuracy: float, metadata: Optional[Dict] = None):
        """Record both estimate and ground truth."""
        self.calibration.record_estimate(tool_name, task_id, confidence, metadata=metadata)
        self.calibration.record_ground_truth(tool_name, task_id, accuracy)
        self.stability.record_accuracy(tool_name, accuracy)
    
    def get_calibration_report(self) -> Dict[str, Any]:
        """Get comprehensive calibration report."""
        metrics = self.calibration.get_all_metrics()
        
        return {
            "total_tools": len(metrics),
            "metrics": {k: v.to_dict() for k, v in metrics.items()},
            "overconfident_tools": self.calibration.detect_overconfidence(),
            "blindsights": self.calibration.detect_blindsights(),
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get system health report."""
        return {
            "vital_signs": {k: asdict(v) for k, v in self.vital_signs.get_vital_signs().items()},
            "health_status": self.vital_signs.health_status(),
        }
    
    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive MIRROR report."""
        return {
            "calibration": self.get_calibration_report(),
            "health": self.get_health_report(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
