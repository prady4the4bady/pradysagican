"""
PHASE 4C & 4D: Advanced Knowledge Systems & Stream Processing
==============================================================

Knowledge graph with causal inference + Real-time stream processing
with anomaly detection and continuous learning.

Attribution: Causal inference literature, knowledge graphs,
stream processing systems, anomaly detection algorithms
"""

import asyncio
import logging
import random
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Set
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# CAUSAL INFERENCE IN KNOWLEDGE GRAPHS
# ════════════════════════════════════════════════════════════════════════════

class RelationType(str, Enum):
    """Types of relationships"""
    CAUSAL = "causal"
    CORRELATIVE = "correlative"
    CONDITIONAL = "conditional"
    INVERSE = "inverse"


@dataclass
class CausalEdge:
    """Edge with causal information"""
    from_entity: str
    to_entity: str
    relation_type: RelationType
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)


class CausalGraph:
    """Knowledge graph with causal inference"""
    
    def __init__(self):
        self.entities: Set[str] = set()
        self.edges: List[CausalEdge] = []
        self.causal_paths: Dict[Tuple[str, str], List[List[str]]] = {}
    
    async def add_causal_relationship(self, from_ent: str, to_ent: str,
                                     relation_type: RelationType,
                                     strength: float, confidence: float):
        """Add causal relationship"""
        self.entities.add(from_ent)
        self.entities.add(to_ent)
        
        edge = CausalEdge(
            from_entity=from_ent,
            to_entity=to_ent,
            relation_type=relation_type,
            strength=strength,
            confidence=confidence,
        )
        
        self.edges.append(edge)
    
    async def infer_causality(self, from_ent: str, 
                             to_ent: str) -> Dict[str, Any]:
        """Infer causal pathways"""
        
        # BFS to find paths
        paths = await self._find_causal_paths(from_ent, to_ent)
        
        if not paths:
            return {'causal_link': False}
        
        # Calculate aggregate causal strength
        strengths = []
        for path in paths:
            path_strength = 1.0
            for i in range(len(path) - 1):
                edge = next((e for e in self.edges 
                           if e.from_entity == path[i] and e.to_entity == path[i+1]),
                           None)
                if edge:
                    path_strength *= edge.strength
            strengths.append(path_strength)
        
        avg_strength = statistics.mean(strengths) if strengths else 0.0
        
        return {
            'causal_link': True,
            'strength': avg_strength,
            'paths': paths[:5],  # Top 5 paths
            'confidence': avg_strength * 0.9,
        }
    
    async def _find_causal_paths(self, from_ent: str,
                                to_ent: str, max_depth: int = 5) -> List[List[str]]:
        """Find causal paths using BFS"""
        paths = []
        queue = deque([(from_ent, [from_ent])])
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            if current == to_ent:
                paths.append(path)
                continue
            
            # Find outgoing edges
            for edge in self.edges:
                if edge.from_entity == current and edge.to_entity not in path:
                    new_path = path + [edge.to_entity]
                    queue.append((edge.to_entity, new_path))
        
        return paths
    
    async def detect_feedback_loops(self) -> List[List[str]]:
        """Detect causal feedback loops"""
        loops = []
        
        for entity in self.entities:
            paths = await self._find_causal_paths(entity, entity, max_depth=10)
            if paths:
                loops.extend(paths)
        
        return loops


# ════════════════════════════════════════════════════════════════════════════
# REAL-TIME STREAM PROCESSING
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class StreamEvent:
    """Event in data stream"""
    event_id: str
    timestamp: datetime
    event_type: str
    value: float
    source: str
    is_anomaly: bool = False


class AnomalyDetector:
    """Detect anomalies in streams"""
    
    def __init__(self, window_size: int = 100, 
                 threshold: float = 2.5):
        self.window_size = window_size
        self.threshold = threshold  # Standard deviations
        self.history: deque = deque(maxlen=window_size)
        self.anomalies: List[StreamEvent] = []
    
    async def add_value(self, value: float) -> Tuple[bool, float]:
        """Add value and detect anomaly"""
        
        if len(self.history) < 10:  # Need minimum history
            self.history.append(value)
            return False, 0.0
        
        # Calculate statistics
        mean = statistics.mean(self.history)
        stdev = statistics.stdev(self.history) if len(self.history) > 1 else 0
        
        # Z-score
        if stdev > 0:
            z_score = abs((value - mean) / stdev)
        else:
            z_score = 0
        
        is_anomaly = z_score > self.threshold
        
        self.history.append(value)
        
        return is_anomaly, z_score
    
    async def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get anomaly statistics"""
        return {
            'total_events': len(self.history),
            'anomalies_detected': len(self.anomalies),
            'anomaly_rate': len(self.anomalies) / len(self.history) if self.history else 0,
            'mean': statistics.mean(self.history) if self.history else 0,
            'stdev': statistics.stdev(self.history) if len(self.history) > 1 else 0,
        }


class StreamProcessor:
    """Process real-time data streams"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer: deque = deque(maxlen=buffer_size)
        self.anomaly_detector = AnomalyDetector()
        self.pattern_history: List[Dict[str, Any]] = []
        self.processed_count = 0
    
    async def process_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process single event"""
        
        # Detect anomaly
        is_anomaly, z_score = await self.anomaly_detector.add_value(event.value)
        event.is_anomaly = is_anomaly
        
        # Add to buffer
        self.buffer.append(event)
        self.processed_count += 1
        
        # Analyze patterns
        pattern = await self._detect_pattern()
        
        return {
            'event_id': event.event_id,
            'is_anomaly': is_anomaly,
            'z_score': z_score,
            'pattern': pattern,
            'buffer_size': len(self.buffer),
        }
    
    async def _detect_pattern(self) -> str:
        """Detect patterns in stream"""
        
        if len(self.buffer) < 5:
            return "insufficient_data"
        
        recent = [e.value for e in list(self.buffer)[-5:]]
        
        # Trend detection
        if recent[-1] > recent[0]:
            return "increasing"
        elif recent[-1] < recent[0]:
            return "decreasing"
        else:
            return "stable"
    
    async def get_stream_statistics(self) -> Dict[str, Any]:
        """Get stream statistics"""
        
        if not self.buffer:
            return {'status': 'no_data'}
        
        values = [e.value for e in self.buffer]
        anomalies = [e for e in self.buffer if e.is_anomaly]
        
        return {
            'processed_events': self.processed_count,
            'buffered_events': len(self.buffer),
            'anomalies': len(anomalies),
            'anomaly_rate': len(anomalies) / len(self.buffer),
            'mean': statistics.mean(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
        }


class ContinuousLearner:
    """Learn continuously from stream"""
    
    def __init__(self):
        self.model_parameters: Dict[str, float] = {}
        self.learning_history: List[Dict[str, Any]] = []
        self.update_count = 0
    
    async def update_from_stream(self, events: List[StreamEvent]) -> Dict[str, Any]:
        """Update model from stream events"""
        
        if not events:
            return {'status': 'no_events'}
        
        # Calculate statistics from events
        values = [e.value for e in events]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Update parameters with exponential moving average
        alpha = 0.1  # Learning rate
        
        if 'mean' not in self.model_parameters:
            self.model_parameters['mean'] = mean
            self.model_parameters['stdev'] = stdev
        else:
            self.model_parameters['mean'] = (
                alpha * mean +
                (1 - alpha) * self.model_parameters['mean']
            )
            self.model_parameters['stdev'] = (
                alpha * stdev +
                (1 - alpha) * self.model_parameters['stdev']
            )
        
        self.update_count += 1
        
        update_info = {
            'update_count': self.update_count,
            'events_processed': len(events),
            'model_parameters': self.model_parameters.copy(),
        }
        
        self.learning_history.append(update_info)
        
        return update_info


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATED SYSTEMS
# ════════════════════════════════════════════════════════════════════════════

class AdvancedKnowledgeStreamSystem:
    """Combined causal knowledge + stream processing"""
    
    def __init__(self):
        self.causal_graph = CausalGraph()
        self.stream_processor = StreamProcessor()
        self.continuous_learner = ContinuousLearner()
    
    async def build_causal_knowledge(self):
        """Build sample causal graph"""
        print("[Knowledge] Building causal relationships...")
        
        relationships = [
            ("temperature", "pressure", RelationType.CAUSAL, 0.8, 0.9),
            ("pressure", "altitude", RelationType.CAUSAL, 0.7, 0.85),
            ("altitude", "oxygen_level", RelationType.CAUSAL, 0.9, 0.95),
            ("oxygen_level", "performance", RelationType.CAUSAL, 0.6, 0.75),
            ("temperature", "humidity", RelationType.CORRELATIVE, 0.5, 0.7),
        ]
        
        for from_ent, to_ent, rel_type, strength, conf in relationships:
            await self.causal_graph.add_causal_relationship(
                from_ent, to_ent, rel_type, strength, conf
            )
        
        print(f"  Entities: {len(self.causal_graph.entities)}")
        print(f"  Relationships: {len(self.causal_graph.edges)}")
    
    async def process_event_stream(self, num_events: int = 100):
        """Process stream of events"""
        print(f"\n[Stream] Processing {num_events} events...")
        
        events = []
        for i in range(num_events):
            event = StreamEvent(
                event_id=f"event_{i}",
                timestamp=datetime.now(),
                event_type="sensor_reading",
                value=random.gauss(100, 10),  # Normal distribution
                source="sensor_1"
            )
            
            # Inject some anomalies
            if i % 20 == 0:
                event.value = random.gauss(150, 5)
            
            result = await self.stream_processor.process_event(event)
            events.append(event)
        
        stats = await self.stream_processor.get_stream_statistics()
        print(f"  Processed: {stats['processed_events']}")
        print(f"  Anomalies: {stats['anomalies']} ({stats['anomaly_rate']:.1%})")
        
        # Continuous learning
        await self.continuous_learner.update_from_stream(events)
    
    async def infer_causal_effects(self):
        """Infer causal effects"""
        print(f"\n[Causal] Inferring causal pathways...")
        
        causality = await self.causal_graph.infer_causality("temperature", "oxygen_level")
        print(f"  Causal Link: {causality.get('causal_link', False)}")
        print(f"  Strength: {causality.get('strength', 0):.2%}")
        print(f"  Paths: {len(causality.get('paths', []))}")
        
        loops = await self.causal_graph.detect_feedback_loops()
        print(f"  Feedback Loops: {len(loops)}")
    
    async def comprehensive_analysis(self):
        """Run comprehensive analysis"""
        
        print(f"\n{'='*70}")
        print(f"ADVANCED KNOWLEDGE SYSTEMS & STREAM PROCESSING - PHASE 4C & 4D")
        print(f"{'='*70}\n")
        
        await self.build_causal_knowledge()
        await self.process_event_stream(100)
        await self.infer_causal_effects()
        
        print(f"\n[Learning] Continuous Learning Status:")
        print(f"  Updates: {self.continuous_learner.update_count}")
        print(f"  Current Mean: {self.continuous_learner.model_parameters.get('mean', 0):.2f}")
        print(f"  Current Stdev: {self.continuous_learner.model_parameters.get('stdev', 0):.2f}")


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_knowledge_stream_system():
    """Demonstrate system"""
    system = AdvancedKnowledgeStreamSystem()
    await system.comprehensive_analysis()


if __name__ == "__main__":
    asyncio.run(demo_knowledge_stream_system())
