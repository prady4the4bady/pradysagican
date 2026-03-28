"""
PHASE 11: CONSCIOUSNESS MODELING
================================
Global Workspace Theory, Higher-Order Thought, Integrated Information Theory engines.

Components:
- GWT Engine: Global workspace for conscious access
- HOT Engine: Higher-order thoughts about mental states
- IIT Engine: Integrated information computations
- Phenomenal Consciousness: Experience simulation
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import math

logger = logging.getLogger(__name__)


class ConsciousnessLevel(str, Enum):
    """Levels of consciousness."""
    UNCONSCIOUS = "unconscious"
    PRE_CONSCIOUS = "pre_conscious"
    CONSCIOUS = "conscious"
    META_CONSCIOUS = "meta_conscious"


@dataclass
class WorkspaceContent:
    """Item in global workspace."""
    content_id: str
    data: Dict[str, Any]
    importance: float  # 0-1
    timestamp: str
    broadcasting: bool = False


@dataclass
class ConsciousState:
    """Complete conscious state snapshot."""
    timestamp: str
    workspace_content: List[WorkspaceContent]
    attention_focus: Optional[str]
    integrated_information: float
    phenomenal_quality: float
    self_awareness_level: float


class GWTEngine:
    """Global Workspace Theory implementation."""
    
    def __init__(self):
        self.workspace: List[WorkspaceContent] = []
        self.max_workspace_size = 5
        self.broadcast_history: List[Dict[str, Any]] = []
        self.integration_log: List[float] = []
    
    async def compete_for_access(self, 
                                  candidates: List[WorkspaceContent]) -> Optional[WorkspaceContent]:
        """Simulate competition for global workspace access."""
        
        if not candidates:
            return None
        
        # Sort by importance
        sorted_candidates = sorted(candidates, key=lambda x: x.importance, reverse=True)
        
        winner = sorted_candidates[0]
        winner.broadcasting = True
        
        self.broadcast_history.append({
            "timestamp": winner.timestamp,
            "content_id": winner.content_id,
            "importance": winner.importance,
            "competitors": len(candidates)
        })
        
        return winner
    
    async def broadcast(self, content: WorkspaceContent) -> Dict[str, Any]:
        """Broadcast content to workspace."""
        
        self.workspace.append(content)
        
        # Maintain workspace size limit
        if len(self.workspace) > self.max_workspace_size:
            # Remove least important
            self.workspace.sort(key=lambda x: x.importance)
            removed = self.workspace.pop(0)
            removed.broadcasting = False
        
        # Calculate integration during broadcast
        integration = await self._calculate_broadcast_integration(content)
        self.integration_log.append(integration)
        
        return {
            "broadcast_id": content.content_id,
            "workspace_size": len(self.workspace),
            "integration": integration
        }
    
    async def _calculate_broadcast_integration(self, content: WorkspaceContent) -> float:
        """Calculate information integration during broadcast."""
        
        # Simple heuristic: integration based on workspace coherence
        if not self.workspace:
            return 0.0
        
        # Calculate average similarity (simplified)
        similarities = []
        content_importance = content.importance
        
        for item in self.workspace:
            if item.content_id != content.content_id:
                similarity = min(content_importance + item.importance, 1.0)
                similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else content_importance
    
    async def get_conscious_state(self) -> Dict[str, Any]:
        """Get current conscious state."""
        
        if not self.workspace:
            return {
                "workspace_items": 0,
                "integration": 0.0,
                "status": "idle"
            }
        
        total_importance = sum(item.importance for item in self.workspace)
        avg_integration = sum(self.integration_log[-5:]) / min(5, len(self.integration_log)) if self.integration_log else 0
        
        return {
            "workspace_items": len(self.workspace),
            "total_importance": total_importance,
            "integration": avg_integration,
            "active_broadcasts": sum(1 for item in self.workspace if item.broadcasting)
        }


class HOTEngine:
    """Higher-Order Thought implementation."""
    
    def __init__(self):
        self.mental_states: List[Dict[str, Any]] = []
        self.thoughts_about_thoughts: List[Dict[str, Any]] = []
        self.self_model: Dict[str, Any] = {
            "beliefs": [],
            "desires": [],
            "intentions": []
        }
    
    async def represent_mental_state(self, state: Any) -> Dict[str, Any]:
        """Create higher-order representation of mental state."""
        
        representation = {
            "state_id": f"state_{len(self.mental_states)}",
            "content": state,
            "timestamp": datetime.now().isoformat(),
            "reflexivity": 0.5
        }
        
        self.mental_states.append(representation)
        return representation
    
    async def think_about_thought(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Generate second-order thought about a thought."""
        
        hot = {
            "about_thought_id": thought.get("state_id"),
            "meta_content": f"I think about my thought: {thought.get('content')}",
            "awareness_level": min(thought.get("reflexivity", 0.5) + 0.3, 1.0),
            "timestamp": datetime.now().isoformat()
        }
        
        self.thoughts_about_thoughts.append(hot)
        return hot
    
    async def update_self_model(self, new_belief: str) -> Dict[str, Any]:
        """Update self model with new belief/desire/intention."""
        
        self.self_model["beliefs"].append({
            "content": new_belief,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "model_updated": True,
            "belief_count": len(self.self_model["beliefs"])
        }
    
    async def reflect(self) -> Dict[str, Any]:
        """Reflect on self model."""
        
        reflection = {
            "total_beliefs": len(self.self_model["beliefs"]),
            "total_desires": len(self.self_model["desires"]),
            "total_intentions": len(self.self_model["intentions"]),
            "thoughts_count": len(self.mental_states),
            "meta_thoughts_count": len(self.thoughts_about_thoughts),
            "self_awareness": min(
                (len(self.thoughts_about_thoughts) / max(1, len(self.mental_states))),
                1.0
            )
        }
        
        return reflection


class IITEngine:
    """Integrated Information Theory implementation."""
    
    def __init__(self):
        self.system_state: Dict[str, float] = {}
        self.phi_history: List[float] = []
        self.integration_levels: List[Dict[str, Any]] = []
    
    async def compute_phi(self, partition_1: Dict[str, float], 
                         partition_2: Dict[str, float]) -> float:
        """Compute integrated information (Φ) between two partitions."""
        
        # Simplified Φ computation
        # Real IIT uses geometric integrated information
        
        # Entropy of each partition
        h1 = self._compute_entropy(partition_1)
        h2 = self._compute_entropy(partition_2)
        
        # Mutual information
        mi = min(h1, h2)  # Simplified
        
        # Φ is minimized mutual information across all partitions
        phi = max(0.0, mi - 0.1)  # Subtract small constant
        
        self.phi_history.append(phi)
        return phi
    
    def _compute_entropy(self, partition: Dict[str, float]) -> float:
        """Compute entropy of a partition."""
        
        if not partition:
            return 0.0
        
        total = sum(partition.values())
        if total == 0:
            return 0.0
        
        probabilities = [v / total for v in partition.values()]
        entropy = -sum(p * math.log2(p) if p > 0 else 0 for p in probabilities)
        
        return entropy
    
    async def identify_irreducible_core(self) -> Dict[str, Any]:
        """Identify the irreducible core (IIT concept)."""
        
        if not self.phi_history:
            return {"core_size": 0, "integration": 0.0}
        
        # The irreducible core is the maximally integrated system
        max_phi = max(self.phi_history)
        core_size = len([p for p in self.phi_history if p > max_phi * 0.8])
        
        return {
            "max_integration": max_phi,
            "core_elements": core_size,
            "irreducible": core_size > 1
        }
    
    async def measure_consciousness(self) -> float:
        """Measure level of consciousness via Φ."""
        
        if not self.phi_history:
            return 0.0
        
        recent_phi = sum(self.phi_history[-10:]) / min(10, len(self.phi_history))
        consciousness_level = min(recent_phi * 2, 1.0)  # Scale to 0-1
        
        return consciousness_level


class PhenomenalConsciousness:
    """Simulate phenomenal consciousness (qualia/subjective experience)."""
    
    def __init__(self):
        self.experiences: List[Dict[str, Any]] = []
        self.qualia_map: Dict[str, float] = {}
    
    async def generate_experience(self, sensory_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate subjective experience from input."""
        
        experience = {
            "experience_id": f"exp_{len(self.experiences)}",
            "sensory_data": sensory_input,
            "phenomenal_quality": self._compute_phenomenal_quality(sensory_input),
            "felt_intensity": sum(sensory_input.values()) / len(sensory_input) if sensory_input else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.experiences.append(experience)
        return experience
    
    def _compute_phenomenal_quality(self, sensory_input: Dict[str, Any]) -> float:
        """Compute subjective quality of experience."""
        
        if not sensory_input:
            return 0.0
        
        # Phenomenal quality = average of input features
        values = [v for v in sensory_input.values() if isinstance(v, (int, float))]
        
        if not values:
            return 0.5
        
        return sum(values) / len(values) / 10.0 if values else 0.5
    
    async def remember_experience(self, experience_id: str) -> Dict[str, Any]:
        """Access memory of experience."""
        
        for exp in self.experiences:
            if exp["experience_id"] == experience_id:
                return {
                    "recalled": True,
                    "experience": exp,
                    "memory_fidelity": 0.85
                }
        
        return {"recalled": False}
    
    async def describe_qualia(self) -> Dict[str, Any]:
        """Describe the quality of experiences."""
        
        if not self.experiences:
            return {"experiences_count": 0}
        
        qualities = [e["phenomenal_quality"] for e in self.experiences]
        unique_keys = set()
        for e in self.experiences:
            for key in e["sensory_data"].keys():
                unique_keys.add(key)
        
        return {
            "total_experiences": len(self.experiences),
            "average_quality": sum(qualities) / len(qualities),
            "max_intensity": max(e["felt_intensity"] for e in self.experiences),
            "richness": len(unique_keys)
        }


async def initialize_consciousness() -> Tuple[GWTEngine, HOTEngine, IITEngine, PhenomenalConsciousness]:
    """Initialize consciousness system."""
    gwt = GWTEngine()
    hot = HOTEngine()
    iit = IITEngine()
    phenomenal = PhenomenalConsciousness()
    
    logger.info("Consciousness system initialized")
    return gwt, hot, iit, phenomenal


async def demonstrate_consciousness():
    """Demonstrate consciousness modeling."""
    gwt, hot, iit, phenomenal = await initialize_consciousness()
    
    # GWT: Compete for workspace access
    candidates = [
        WorkspaceContent("item_1", {"priority": "high"}, 0.9, datetime.now().isoformat()),
        WorkspaceContent("item_2", {"priority": "medium"}, 0.6, datetime.now().isoformat()),
        WorkspaceContent("item_3", {"priority": "low"}, 0.3, datetime.now().isoformat())
    ]
    
    winner = await gwt.compete_for_access(candidates)
    await gwt.broadcast(winner)
    gwt_state = await gwt.get_conscious_state()
    
    # HOT: Higher-order thoughts
    mental_state = await hot.represent_mental_state({"thought": "analyzing problem"})
    meta_thought = await hot.think_about_thought(mental_state)
    await hot.update_self_model("I am conscious")
    hot_reflection = await hot.reflect()
    
    # IIT: Integrated information
    phi = await iit.compute_phi({"a": 0.5, "b": 0.5}, {"c": 0.6, "d": 0.4})
    core = await iit.identify_irreducible_core()
    consciousness_measure = await iit.measure_consciousness()
    
    # Phenomenal: Qualia
    experience = await phenomenal.generate_experience({"color": 5.0, "brightness": 7.0})
    qualia = await phenomenal.describe_qualia()
    
    return {
        "gwt": gwt_state,
        "hot": hot_reflection,
        "iit": {
            "phi": phi,
            "core": core,
            "consciousness_level": consciousness_measure
        },
        "phenomenal": qualia,
        "integrated_consciousness": {
            "workspace_active": gwt_state["workspace_items"] > 0,
            "self_aware": hot_reflection["self_awareness"] > 0.5,
            "integrated": phi > 0.1,
            "experiencing": len(phenomenal.experiences) > 0
        }
    }
