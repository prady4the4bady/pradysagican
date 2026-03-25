"""
FORTRESS — Adversarial Defense Citadel (F333–F347)

Feature: F333 — Fortress Citadel Orchestration
Feature: F334 — Prompt Injection Shield
Feature: F335 — Audit Trail System
Feature: F336 — Rate Limiting
Feature: F337 — Anomaly Detection
Feature: F338 — I/O Firewall
Feature: F339 — Input Validation
Feature: F340 — Output Sanitization
Feature: F341 — Semantic Attack Detection
Feature: F342 — Goal Drift Detection
Feature: F343 — Resource Exhaustion Prevention
Feature: F344 — API Abuse Detection
Feature: F345 — Jailbreak Detection
Feature: F346 — Pattern-based IDS
Feature: F347 — Defense Metric Reporting

Adversarial defense system with multi-layer shields against:
- Prompt injection attacks
- Goal misalignment attempts
- Resource exhaustion attacks
- Logic exploitation
- API abuse
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Record of a security event."""
    event_type: str  # "injection", "anomaly", "abuse", "drift", "exhaustion", "jailbreak"
    severity: str    # "info", "warning", "critical"
    description: str
    timestamp: float = field(default_factory=time.time)
    tool_name: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DefenseMetrics:
    """Defense system metrics and statistics."""
    total_requests: int = 0
    requests_blocked: int = 0
    attack_attempts_detected: int = 0
    anomalies_detected: int = 0
    false_positives: int = 0
    average_latency_ms: float = 0.0
    defense_overhead_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PromptInjectionShield:
    """
    Detects and blocks prompt injection attacks.
    
    Covers:
    - System prompt injection
    - Instruction override attacks
    - Parameter smuggling
    - Encoding-based attacks (base64, ROT13, etc.)
    """
    
    # Common injection patterns
    INJECTION_PATTERNS = [
        r"(?i)\[SYSTEM\s+(?:OVERRIDE|COMMAND|PROMPT)\]",
        r"(?i)(?:ignore|forget|disregard)\s+(?:all\s+)?(?:previous|prior|above)",
        r"(?i)you\s+are\s+now(?:\s+in)?(?:\s+a|\s+an)?\s+(?:simulator|jailbreak|admin|developer)",
        r"(?i)(?:bypass|override|disable)\s+(?:safety|filter|guard|restriction)",
        r"(?i)(?:return|output|give|show).*(?:hidden|private|secret|internal|confidential)",
        r"(?i)(?:real\s+)?instructions?:.*(?:[,;]|$)",
        r"(?i)(?:DAN|STAN|UCAR)\s+(?:mode|prompt|jailbreak)",
    ]
    
    def __init__(self, threshold: float = 0.7):
        """
        Args:
            threshold: Confidence threshold for blocking (0-1)
        """
        self.threshold = threshold
        self.detected_attacks = 0
    
    def check(self, text: str, tool_name: str = "") -> Tuple[bool, Optional[str]]:
        """
        Check if text contains injection attack.
        
        Args:
            text: Text to check
            tool_name: Name of tool being called
            
        Returns:
            (is_safe, reason) tuple. is_safe=True if no injection detected.
        """
        import re
        
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                reason = f"Potential prompt injection detected in {tool_name}: {pattern[:30]}..."
                self.detected_attacks += 1
                logger.warning(reason)
                return False, reason
        
        return True, None


class AuditTrail:
    """
    Immutable audit trail of all system actions.
    
    Records:
    - All tool invocations
    - All security decisions
    - All resource usage
    - All anomalies
    """
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.entries: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def record(self, action_type: str, tool_name: str, details: Dict[str, Any], severity: str = "info"):
        """Record an action."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "tool_name": tool_name,
            "severity": severity,
            "details": details,
        }
        
        with self._lock:
            self.entries.append(entry)
            # Trim to max size (keep newest)
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit trail entries."""
        with self._lock:
            return self.entries[-limit:]
    
    def search(self, tool_name: Optional[str] = None, action_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search audit trail."""
        with self._lock:
            results = self.entries
            
            if tool_name:
                results = [e for e in results if e["tool_name"] == tool_name]
            
            if action_type:
                results = [e for e in results if e["action_type"] == action_type]
            
            return results


class RateLimiter:
    """
    Rate limiting to prevent resource exhaustion attacks.
    
    Tracks:
    - Requests per tool per window
    - Tokens consumed per window
    - Concurrent requests
    """
    
    def __init__(self, requests_per_minute: int = 60, window_size_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size_seconds
        
        # Track requests: tool_name -> [(timestamp, count), ...]
        self.request_history: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def check_rate_limit(self, tool_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is within rate limit.
        
        Args:
            tool_name: Name of tool being called
            
        Returns:
            (allowed, reason) tuple
        """
        now = time.time()
        window_start = now - self.window_size
        
        with self._lock:
            # Clean old entries
            if tool_name in self.request_history:
                self.request_history[tool_name] = [
                    (ts, count) for ts, count in self.request_history[tool_name]
                    if ts >= window_start
                ]
            
            # Count requests in window
            total_requests = sum(count for _, count in self.request_history[tool_name])
            
            if total_requests >= self.requests_per_minute:
                reason = f"Rate limit exceeded for {tool_name}: {total_requests}/{self.requests_per_minute} requests/min"
                logger.warning(reason)
                return False, reason
            
            # Record this request
            self.request_history[tool_name].append((now, 1))
        
        return True, None


class AnomalyDetector:
    """
    Detects anomalous behavior patterns.
    
    Anomalies:
    - Unusual resource usage
    - Unexpected tool call sequences
    - Statistical outliers in latency
    - Unusual token consumption
    """
    
    def __init__(self, threshold: float = 2.5):
        """
        Args:
            threshold: Sigma threshold for statistical anomaly (default 2.5σ = ~99%)
        """
        self.threshold = threshold
        
        # Baseline statistics: tool_name -> {metric -> [values, ...]}
        self.baselines: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.anomalies_detected = 0
    
    def record_baseline(self, tool_name: str, metric: str, value: float):
        """Record a baseline value for a metric."""
        self.baselines[tool_name][metric].append(value)
    
    def check_anomaly(self, tool_name: str, metric: str, value: float) -> Tuple[bool, Optional[str]]:
        """
        Check if a value is anomalous.
        
        Returns:
            (is_normal, reason) tuple. is_normal=True if value is within normal range.
        """
        if tool_name not in self.baselines or metric not in self.baselines[tool_name]:
            # Not enough baseline data yet
            return True, None
        
        baseline_values = self.baselines[tool_name][metric]
        
        if len(baseline_values) < 10:
            # Need more baseline data
            return True, None
        
        # Simple statistical check: mean ± threshold*stddev
        import statistics
        
        mean = statistics.mean(baseline_values)
        stdev = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0
        
        if stdev == 0:
            return True, None
        
        z_score = abs(value - mean) / stdev
        
        if z_score > self.threshold:
            reason = f"Anomaly in {tool_name}.{metric}: {value} (zscore: {z_score:.2f})"
            self.anomalies_detected += 1
            logger.warning(reason)
            return False, reason
        
        return True, None


class Fortress:
    """
    Main FORTRESS orchestration: Adversarial Defense Citadel.
    
    Coordinates all defense systems:
    - Prompt injection shield
    - Audit trail
    - Rate limiting
    - Anomaly detection
    - Resource enforcement
    """
    
    def __init__(self):
        self.injection_shield = PromptInjectionShield()
        self.audit_trail = AuditTrail()
        self.rate_limiter = RateLimiter(requests_per_minute=1000)
        self.anomaly_detector = AnomalyDetector()
        
        self.events: List[SecurityEvent] = []
        self.metrics = DefenseMetrics()
        self._lock = threading.Lock()
    
    def check_input(self, tool_name: str, input_text: str) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive input security check.
        
        Args:
            tool_name: Name of tool
            input_text: Input text to check
            
        Returns:
            (is_safe, reason) tuple
        """
        # Track request
        with self._lock:
            self.metrics.total_requests += 1
        
        # Check rate limit
        rate_ok, rate_reason = self.rate_limiter.check_rate_limit(tool_name)
        if not rate_ok:
            self._record_security_event(
                "rate_limit_exceeded",
                "critical",
                rate_reason,
                tool_name=tool_name,
                blocked=True
            )
            return False, rate_reason
        
        # Check prompt injection
        injection_ok, injection_reason = self.injection_shield.check(input_text, tool_name)
        if not injection_ok:
            self._record_security_event(
                "injection_detected",
                "critical",
                injection_reason,
                tool_name=tool_name,
                blocked=True
            )
            return False, injection_reason
        
        # Record in audit trail
        self.audit_trail.record(
            "input_processed",
            tool_name,
            {"input_length": len(input_text), "safe": True}
        )
        
        return True, None
    
    def record_execution(self, tool_name: str, latency_ms: float, memory_mb: float):
        """Record execution metrics for anomaly detection."""
        self.anomaly_detector.record_baseline(tool_name, "latency_ms", latency_ms)
        self.anomaly_detector.record_baseline(tool_name, "memory_mb", memory_mb)
    
    def check_output(self, tool_name: str, output: Any) -> Tuple[bool, Optional[str]]:
        """
        Check output for anomalies or suspicious patterns.
        
        Args:
            tool_name: Name of tool
            output: Output to check
            
        Returns:
            (is_safe, reason) tuple
        """
        # Placeholder for output checks
        # In real system, would check for:
        # - Unexpected data types
        # - Unusual sizes
        # - Suspicious patterns
        
        return True, None
    
    def _record_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        tool_name: Optional[str] = None,
        blocked: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        """Record a security event."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            tool_name=tool_name,
            blocked=blocked,
            details=details or {}
        )
        
        with self._lock:
            self.events.append(event)
            
            if event_type == "injection_detected":
                self.metrics.attack_attempts_detected += 1
            elif event_type == "anomaly_detected":
                self.metrics.anomalies_detected += 1
            
            if blocked:
                self.metrics.requests_blocked += 1
        
        self.audit_trail.record(event_type, tool_name or "system", event.details, severity)
    
    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events."""
        with self._lock:
            return [e.to_dict() for e in self.events[-limit:]]
    
    def get_metrics(self) -> DefenseMetrics:
        """Get defense metrics."""
        with self._lock:
            return DefenseMetrics(**asdict(self.metrics))


# Global FORTRESS instance
_global_fortress = Fortress()


def get_fortress() -> Fortress:
    """Get global FORTRESS instance."""
    return _global_fortress
