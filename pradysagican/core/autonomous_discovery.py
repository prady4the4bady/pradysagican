#!/usr/bin/env python3
"""
PHASE 9B: AUTONOMOUS DISCOVERY
Automatic discovery of new capabilities and patterns
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum


class DiscoveryType(Enum):
    """Types of autonomous discoveries"""
    PATTERN = "pattern"              # Recurring pattern in data
    ANOMALY = "anomaly"              # Unexpected deviation
    CORRELATION = "correlation"      # Relationship between variables
    CAUSATION = "causation"          # Causal relationship discovered
    CAPABILITY = "capability"        # New system capability
    SYNERGY = "synergy"              # Two systems work together better


@dataclass
class Discovery:
    """A discovered pattern or capability"""
    discovery_id: str
    discovery_type: DiscoveryType
    description: str
    confidence: float
    impact_potential: float
    resources_required: float
    discovery_date: str = "2026-03-28"


@dataclass
class DiscoveryOptimization:
    """Track how to optimize for discovering new things"""
    discovery_frequency: List[float] = field(default_factory=list)
    discovery_quality: List[float] = field(default_factory=list)
    search_strategies: List[str] = field(default_factory=list)


class PatternDiscoverer:
    """Discovers patterns in system behavior"""
    
    def __init__(self):
        self.discovered_patterns: List[Discovery] = []
        self.pattern_archive: Dict[str, List[float]] = {}
    
    async def analyze_timeseries(self, timeseries: List[float], 
                                min_period: int = 3) -> List[str]:
        """Analyze timeseries for patterns"""
        
        patterns = []
        
        # Check for periodicity
        for period in range(min_period, len(timeseries) // 2):
            matches = 0
            for i in range(period, len(timeseries)):
                if abs(timeseries[i] - timeseries[i - period]) < 0.1:
                    matches += 1
            
            if matches >= period:
                patterns.append(f"period_{period}")
        
        # Check for trend
        if len(timeseries) > 2:
            deltas = [timeseries[i] - timeseries[i-1] for i in range(1, len(timeseries))]
            if all(d > 0 for d in deltas):
                patterns.append("increasing_trend")
            elif all(d < 0 for d in deltas):
                patterns.append("decreasing_trend")
        
        return patterns
    
    async def discover_from_logs(self, logs: List[Dict]) -> List[Discovery]:
        """Discover patterns from system logs"""
        
        discoveries = []
        
        # Extract timeseries from logs
        performance_series = [log.get('performance', 0.5) for log in logs]
        
        # Find patterns
        patterns = await self.analyze_timeseries(performance_series)
        
        for i, pattern in enumerate(patterns):
            discovery = Discovery(
                discovery_id=f"pat_{i}",
                discovery_type=DiscoveryType.PATTERN,
                description=f"Discovered pattern: {pattern}",
                confidence=0.7,
                impact_potential=0.5,
                resources_required=1.0
            )
            discoveries.append(discovery)
        
        self.discovered_patterns.extend(discoveries)
        return discoveries


class AnomalyDetector:
    """Detects anomalies in system behavior"""
    
    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity
        self.baseline: Optional[float] = None
        self.anomalies: List[Discovery] = []
    
    async def set_baseline(self, samples: List[float]) -> None:
        """Set baseline from samples"""
        self.baseline = sum(samples) / len(samples) if samples else 0.5
    
    async def detect(self, value: float) -> Optional[Discovery]:
        """Detect if value is anomalous"""
        
        if self.baseline is None:
            return None
        
        # Calculate deviation
        deviation = abs(value - self.baseline) / self.baseline if self.baseline > 0 else 0
        
        # Threshold
        if deviation > self.sensitivity * 0.1:
            discovery = Discovery(
                discovery_id=f"anom_{len(self.anomalies)}",
                discovery_type=DiscoveryType.ANOMALY,
                description=f"Anomaly: value {value:.3f} vs baseline {self.baseline:.3f}",
                confidence=min(1.0, deviation),
                impact_potential=deviation,
                resources_required=0.5
            )
            
            self.anomalies.append(discovery)
            return discovery
        
        return None
    
    async def batch_detect(self, values: List[float]) -> List[Discovery]:
        """Detect anomalies in batch"""
        
        if not values:
            return []
        
        await self.set_baseline(values[:-5])  # Use first N-5 as baseline
        
        anomalies = []
        for value in values[-5:]:  # Check last 5
            anom = await self.detect(value)
            if anom:
                anomalies.append(anom)
        
        return anomalies


class CapabilityDiscovery:
    """Discovers new capabilities from existing systems"""
    
    def __init__(self):
        self.system_capabilities: Dict[str, Set[str]] = {}
        self.discovered_capabilities: List[Discovery] = []
    
    async def register_system(self, system_name: str, 
                             capabilities: List[str]) -> None:
        """Register system and its capabilities"""
        self.system_capabilities[system_name] = set(capabilities)
    
    async def discover_synergies(self) -> List[Discovery]:
        """Discover when systems work better together"""
        
        discoveries = []
        systems = list(self.system_capabilities.keys())
        
        # Check all pairs
        for i in range(len(systems)):
            for j in range(i + 1, len(systems)):
                sys_a = systems[i]
                sys_b = systems[j]
                
                caps_a = self.system_capabilities[sys_a]
                caps_b = self.system_capabilities[sys_b]
                
                # Complementarity = overlap suggests synergy
                overlap = len(caps_a & caps_b)
                total = len(caps_a | caps_b)
                
                if overlap > 0 and overlap / total > 0.3:
                    discovery = Discovery(
                        discovery_id=f"syn_{sys_a}_{sys_b}",
                        discovery_type=DiscoveryType.SYNERGY,
                        description=f"Synergy between {sys_a} and {sys_b}",
                        confidence=overlap / total,
                        impact_potential=overlap / total,
                        resources_required=2.0
                    )
                    discoveries.append(discovery)
        
        self.discovered_capabilities.extend(discoveries)
        return discoveries
    
    async def discover_capability_gaps(self) -> List[Discovery]:
        """Discover what capabilities are missing"""
        
        discoveries = []
        
        # Common capabilities we might be missing
        important_capabilities = [
            "real_time_learning",
            "distributed_execution",
            "multi_modal_reasoning",
            "zero_shot_adaptation",
            "uncertainty_quantification"
        ]
        
        all_caps = set()
        for caps in self.system_capabilities.values():
            all_caps.update(caps)
        
        missing = set(important_capabilities) - all_caps
        
        for cap in missing:
            discovery = Discovery(
                discovery_id=f"gap_{cap}",
                discovery_type=DiscoveryType.CAPABILITY,
                description=f"Missing capability: {cap}",
                confidence=0.6,
                impact_potential=0.8,
                resources_required=5.0
            )
            discoveries.append(discovery)
        
        self.discovered_capabilities.extend(discoveries)
        return discoveries


class AutonomousDiscoveryEngine:
    """Orchestrates autonomous discovery"""
    
    def __init__(self):
        self.pattern_discoverer = PatternDiscoverer()
        self.anomaly_detector = AnomalyDetector()
        self.capability_discovery = CapabilityDiscovery()
        self.all_discoveries: List[Discovery] = []
    
    async def run_discovery_cycle(self, logs: List[Dict],
                                 system_registry: Dict[str, List[str]]) -> Dict:
        """Run complete discovery cycle"""
        
        results = {
            'patterns': [],
            'anomalies': [],
            'capabilities': [],
            'total_discoveries': 0,
            'impact_potential': 0.0
        }
        
        # Pattern discovery
        pattern_discoveries = await self.pattern_discoverer.discover_from_logs(logs)
        results['patterns'] = [d.description for d in pattern_discoveries]
        
        # Anomaly detection
        values = [log.get('performance', 0.5) for log in logs]
        anomaly_discoveries = await self.anomaly_detector.batch_detect(values)
        results['anomalies'] = [d.description for d in anomaly_discoveries]
        
        # Capability discovery
        for system_name, caps in system_registry.items():
            await self.capability_discovery.register_system(system_name, caps)
        
        synergy_discoveries = await self.capability_discovery.discover_synergies()
        gap_discoveries = await self.capability_discovery.discover_capability_gaps()
        
        results['capabilities'] = [d.description for d in synergy_discoveries + gap_discoveries]
        
        # Aggregate
        all_disc = pattern_discoveries + anomaly_discoveries + synergy_discoveries + gap_discoveries
        self.all_discoveries.extend(all_disc)
        
        results['total_discoveries'] = len(all_disc)
        results['impact_potential'] = sum(d.impact_potential for d in all_disc) / len(all_disc) if all_disc else 0.0
        
        return results
    
    async def prioritize_discoveries(self) -> List[Discovery]:
        """Prioritize discoveries by impact"""
        
        # Sort by impact_potential * confidence, weighted by resources
        scored = [(d, d.impact_potential * d.confidence / (d.resources_required + 1)) 
                  for d in self.all_discoveries]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [d for d, score in scored]


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_autonomous_discovery():
    """Demonstrate autonomous discovery"""
    
    print("\n" + "=" * 70)
    print("AUTONOMOUS DISCOVERY (PHASE 9B)")
    print("=" * 70)
    
    # Initialize engine
    print("\n[Setup] Initializing discovery engine...")
    engine = AutonomousDiscoveryEngine()
    
    # Create sample logs
    print("\n[Data] Generating system logs...")
    logs = []
    for i in range(20):
        # Create periodic + noise pattern
        value = 0.5 + 0.2 * (i % 5) / 5 + random.gauss(0, 0.05)
        logs.append({'performance': value, 'timestamp': i})
    
    # Add anomaly
    logs[15]['performance'] = 0.9
    
    print(f"  Generated {len(logs)} log entries")
    
    # System registry
    registry = {
        'causal_reasoner': ['causality', 'intervention', 'counterfactual'],
        'transfer_learner': ['domain_adaptation', 'few_shot', 'transfer'],
        'coevolution': ['population', 'speciation', 'fitness'],
        'safety_monitor': ['monitoring', 'alerting', 'enforcement'],
        'meta_learner': ['learning_to_learn', 'task_adaptation']
    }
    
    print("\n[Discovery] Running discovery cycle...")
    results = await engine.run_discovery_cycle(logs, registry)
    
    print(f"\n[Patterns] Found {len(results['patterns'])} patterns:")
    for pattern in results['patterns'][:3]:
        print(f"  - {pattern}")
    
    print(f"\n[Anomalies] Found {len(results['anomalies'])} anomalies:")
    for anom in results['anomalies'][:3]:
        print(f"  - {anom}")
    
    print(f"\n[Capabilities] Found {len(results['capabilities'])} discoveries:")
    for cap in results['capabilities'][:5]:
        print(f"  - {cap}")
    
    # Prioritize
    print("\n[Prioritization] Top discoveries by impact:")
    prioritized = await engine.prioritize_discoveries()
    for i, discovery in enumerate(prioritized[:5]):
        print(f"  {i+1}. {discovery.description}")
        print(f"     Impact: {discovery.impact_potential:.3f}, Cost: {discovery.resources_required:.1f}")
    
    # Statistics
    print("\n[Statistics]:")
    print(f"  Total discoveries: {results['total_discoveries']}")
    print(f"  Avg impact potential: {results['impact_potential']:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_autonomous_discovery())
