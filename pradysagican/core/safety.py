"""
PRADYSAGICAN v2.0 - PHASE 4: SAFETY & PRODUCTION HARDENING
Input validation, execution constraints, output filtering, audit trails
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Callable
from datetime import datetime
from enum import Enum
import json
import logging
import re
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security enforcement levels"""
    PERMISSIVE = "permissive"      # Log only
    MODERATE = "moderate"          # Warn and allow
    STRICT = "strict"              # Block dangerous operations
    PARANOID = "paranoid"          # Ultra-restrictive


@dataclass
class SecurityEvent:
    """Audit trail entry"""
    timestamp: datetime
    event_type: str  # 'input_validation', 'execution', 'output', 'error'
    severity: str    # 'info', 'warning', 'error', 'critical'
    source: str      # request ID or user
    details: Dict[str, Any]
    blocked: bool = False


class InputValidator:
    """Validates input queries for safety"""
    
    DANGEROUS_PATTERNS = {
        'sql_injection': [
            r"('\s*(OR|AND)\s*')",
            r"(DROP\s+TABLE|DELETE\s+FROM|INSERT\s+INTO)",
            r"(UNION\s+SELECT)",
        ],
        'command_injection': [
            r"([;&|`][\s]*(cat|rm|ls|curl|wget|python|bash|sh))",
            r"(\$\(.*\))",
            r"`.*`",
        ],
        'xss': [
            r"(<script[^>]*>.*?</script>)",
            r"(javascript:)",
            r"(onerror=|onclick=|onload=)",
        ],
        'path_traversal': [
            r"(\.\./|\.\.\\\)",
            r"(C:|/etc/|/root/)",
        ],
    }
    
    def __init__(self, level: SecurityLevel = SecurityLevel.MODERATE):
        self.level = level
        self.compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns"""
        for category, patterns in self.DANGEROUS_PATTERNS.items():
            self.compiled_patterns[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def validate(self, query: str) -> tuple[bool, Optional[str]]:
        """Check query for dangerous patterns"""
        
        if self.level == SecurityLevel.PERMISSIVE:
            return True, None
        
        # Check patterns
        findings = []
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    findings.append(category)
        
        if findings:
            message = f"Suspicious patterns detected: {', '.join(set(findings))}"
            
            if self.level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
                logger.warning(f"Blocked input: {message}")
                return False, message
            else:  # MODERATE
                logger.warning(f"Suspicious input: {message}")
                return True, message
        
        return True, None
    
    def sanitize(self, query: str) -> str:
        """Remove dangerous content"""
        sanitized = query
        
        # Remove common injection patterns
        sanitized = re.sub(r'[;&|`]', '', sanitized)
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized


class ExecutionConstraints:
    """Enforces limits on execution"""
    
    def __init__(self):
        self.limits = {
            'max_execution_time': 300,  # 5 minutes
            'max_memory_mb': 2048,      # 2GB
            'max_api_calls': 1000,      # Per execution
            'max_file_size_mb': 500,    # Per file operation
            'rate_limit_per_minute': 60,
        }
        self.execution_count = {}
        self.api_calls_this_execution = 0
    
    async def check_constraints(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if execution is allowed"""
        
        # Check rate limiting
        key = f"{user_id}:{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        count = self.execution_count.get(key, 0)
        
        if count >= self.limits['rate_limit_per_minute']:
            return False, f"Rate limit exceeded: {self.limits['rate_limit_per_minute']}/min"
        
        self.execution_count[key] = count + 1
        return True, None
    
    def check_api_call(self) -> tuple[bool, Optional[str]]:
        """Check if another API call is allowed"""
        if self.api_calls_this_execution >= self.limits['max_api_calls']:
            return False, f"API call limit exceeded: {self.limits['max_api_calls']}"
        
        self.api_calls_this_execution += 1
        return True, None


class OutputFilter:
    """Filters output for safety"""
    
    def __init__(self):
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'api_key': r'(api[_-]?key|apikey|access[_-]?token)["\s:=]+[A-Za-z0-9]{20,}',
        }
    
    def redact_pii(self, text: str) -> str:
        """Remove PII from text"""
        result = text
        
        for pii_type, pattern in self.pii_patterns.items():
            # Replace with placeholder
            result = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', result, flags=re.IGNORECASE)
        
        return result
    
    def verify_factual_claims(self, text: str) -> List[str]:
        """Flag unverified factual claims"""
        # Naive implementation: flag absolute claims
        warnings = []
        
        absolute_patterns = [
            r'\b(always|never|all|none|definitely|certainly|absolutely)\b',
        ]
        
        for pattern in absolute_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append("Contains absolute claim - may need verification")
        
        return warnings
    
    def filter_output(self, text: str) -> tuple[str, List[str]]:
        """Complete output filtering"""
        redacted = self.redact_pii(text)
        warnings = self.verify_factual_claims(text)
        
        return redacted, warnings


class AuditTrail:
    """Immutable audit log of all operations"""
    
    def __init__(self, max_entries: int = 100000):
        self.events: List[SecurityEvent] = []
        self.max_entries = max_entries
    
    def log_event(self, event_type: str, severity: str, source: str, details: Dict, blocked: bool = False):
        """Log security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            source=source,
            details=details,
            blocked=blocked
        )
        
        self.events.append(event)
        
        # Keep only recent events
        if len(self.events) > self.max_entries:
            self.events = self.events[-self.max_entries:]
        
        # Log to logger
        log_level = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"[{event_type}] {details}")
    
    def get_events(self, source: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve audit events"""
        events = self.events
        
        if source:
            events = [e for e in events if e.source == source]
        
        return [{
            'timestamp': e.timestamp.isoformat(),
            'event_type': e.event_type,
            'severity': e.severity,
            'source': e.source,
            'details': e.details,
            'blocked': e.blocked
        } for e in events[-limit:]]


class SafeExecutionContext:
    """Combines all safety measures"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MODERATE):
        self.validator = InputValidator(security_level)
        self.constraints = ExecutionConstraints()
        self.filter = OutputFilter()
        self.audit_trail = AuditTrail()
        self.security_level = security_level
    
    async def validate_input(self, query: str, user_id: str) -> tuple[bool, Optional[str]]:
        """Validate input safely"""
        
        # Check constraints first
        allowed, msg = await self.constraints.check_constraints(user_id)
        if not allowed:
            self.audit_trail.log_event('execution', 'warning', user_id, {
                'reason': 'rate_limit',
                'message': msg
            }, blocked=True)
            return False, msg
        
        # Validate content
        valid, msg = self.validator.validate(query)
        if not valid:
            self.audit_trail.log_event('input_validation', 'warning', user_id, {
                'reason': 'dangerous_patterns',
                'message': msg
            }, blocked=True)
            return False, msg
        
        self.audit_trail.log_event('input_validation', 'info', user_id, {
            'query_length': len(query),
            'result': 'accepted'
        })
        
        return True, None
    
    async def validate_execution(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if execution should proceed"""
        allowed, msg = self.constraints.check_api_call()
        
        if not allowed:
            self.audit_trail.log_event('execution', 'error', user_id, {
                'reason': 'api_limit',
                'message': msg
            }, blocked=True)
        
        return allowed, msg
    
    def filter_output(self, text: str, user_id: str) -> str:
        """Filter output and log"""
        redacted, warnings = self.filter.filter_output(text)
        
        if warnings:
            self.audit_trail.log_event('output', 'warning', user_id, {
                'warnings': warnings,
                'redacted': redacted != text
            })
        
        return redacted
    
    def log_error(self, user_id: str, error: Exception):
        """Log error to audit trail"""
        self.audit_trail.log_event('error', 'error', user_id, {
            'error_type': type(error).__name__,
            'message': str(error)
        })
    
    def get_audit_report(self, user_id: Optional[str] = None) -> Dict:
        """Generate audit report"""
        events = self.audit_trail.get_events(source=user_id, limit=1000)
        
        # Summary stats
        total = len(events)
        blocked = sum(1 for e in events if e['blocked'])
        by_type = {}
        
        for event in events:
            event_type = event['event_type']
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        return {
            'total_events': total,
            'blocked_events': blocked,
            'by_type': by_type,
            'recent_events': events[:20],
            'timestamp': datetime.now().isoformat()
        }


class SafetyMonitor:
    """Continuous monitoring of safety metrics"""
    
    def __init__(self, context: SafeExecutionContext):
        self.context = context
        self.alerts = []
    
    def check_health(self) -> Dict[str, Any]:
        """Check system health"""
        audit_events = self.context.audit_trail.events
        
        # Calculate metrics
        total_events = len(audit_events)
        recent_events = [e for e in audit_events if (
            datetime.now() - e.timestamp
        ).total_seconds() < 3600]  # Last hour
        
        blocked_recent = sum(1 for e in recent_events if e.blocked)
        error_rate = blocked_recent / len(recent_events) if recent_events else 0
        
        status = 'healthy'
        if error_rate > 0.1:
            status = 'warning'
        elif error_rate > 0.2:
            status = 'critical'
        
        return {
            'status': status,
            'total_events': total_events,
            'recent_events': len(recent_events),
            'blocked_recent': blocked_recent,
            'error_rate': error_rate,
            'timestamp': datetime.now().isoformat()
        }
