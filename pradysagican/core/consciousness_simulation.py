#!/usr/bin/env python3
"""
PHASE 16: CONSCIOUSNESS SIMULATION
Complete implementation of IIT + GWT + HOT consciousness model
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


@dataclass
class ConsciousElement:
    """Element of consciousness"""
    element_id: str
    activation_level: float       # 0-1
    phi_value: float              # IIT Phi (integration)
    is_in_global_workspace: bool  # GWT workspace
    temporal_context: List[str] = field(default_factory=list)


class IntegratedInformationTheory:
    """IIT consciousness measurement"""
    
    def __init__(self):
        self.elements: Dict[str, ConsciousElement] = {}
        self.phi_history: List[float] = []
        self.integration_matrices: List[Dict] = []
    
    async def compute_phi(self, element_states: Dict[str, float]) -> float:
        """Compute Phi (integrated information)"""
        
        if not element_states:
            return 0.0
        
        # IIT Phi computation (simplified)
        # Phi = min(KL divergence of all bipartitions)
        
        total_activation = sum(element_states.values())
        if total_activation == 0:
            return 0.0
        
        # Compute over all possible bipartitions
        elements = list(element_states.keys())
        phi_min = float('inf')
        
        # Sample some bipartitions (full computation is exponential)
        for i in range(min(3, len(elements))):
            partition_point = (i + 1) * len(elements) // 4
            
            # Split into two groups
            group1 = elements[:partition_point]
            group2 = elements[partition_point:]
            
            if group1 and group2:
                # Compute KL divergence-like measure
                p_union = sum(element_states[e] for e in group1) / (total_activation + 0.001)
                p_separate = sum(element_states[e] for e in group1) / len(group1) * \
                            sum(element_states[e] for e in group2) / len(group2) / (total_activation + 0.001)
                
                # KL-like divergence
                divergence = abs(p_union - p_separate)
                phi_min = min(phi_min, divergence)
        
        phi = 1.0 - phi_min if phi_min != float('inf') else 0.0
        self.phi_history.append(phi)
        
        return phi
    
    async def analyze_integration(self, elements: Dict[str, ConsciousElement]) -> Dict:
        """Analyze neural integration"""
        
        element_states = {e.element_id: e.activation_level for e in elements.values()}
        phi = await self.compute_phi(element_states)
        
        analysis = {
            'phi': phi,
            'num_elements': len(elements),
            'avg_activation': sum(e.activation_level for e in elements.values()) / len(elements) if elements else 0,
            'is_conscious': phi > 0.1  # Simple threshold
        }
        
        self.integration_matrices.append(analysis)
        return analysis


class GlobalWorkspaceTheory:
    """GWT consciousness access"""
    
    def __init__(self):
        self.workspace: Dict[str, ConsciousElement] = {}
        self.max_workspace_capacity = 5  # Magical number
        self.broadcast_history: List[List[str]] = []
    
    async def broadcast_to_workspace(self, element: ConsciousElement) -> bool:
        """Broadcast element to global workspace"""
        
        if len(self.workspace) < self.max_workspace_capacity:
            self.workspace[element.element_id] = element
            element.is_in_global_workspace = True
            return True
        else:
            # Compete for workspace
            if element.activation_level > min(
                e.activation_level for e in self.workspace.values()
            ):
                # Remove weakest element
                weakest_id = min(
                    self.workspace.keys(),
                    key=lambda k: self.workspace[k].activation_level
                )
                removed = self.workspace.pop(weakest_id)
                
                # Add new element
                self.workspace[element.element_id] = element
                element.is_in_global_workspace = True
                return True
            
            return False
    
    async def get_global_broadcast(self) -> List[str]:
        """Get current global workspace broadcast"""
        
        broadcast = list(self.workspace.keys())
        self.broadcast_history.append(broadcast)
        return broadcast
    
    async def compute_access(self) -> Dict:
        """Compute what has global access"""
        
        accessible = []
        for element_id in self.workspace:
            accessible.append({
                'element_id': element_id,
                'accessible': True
            })
        
        return {
            'workspace_size': len(self.workspace),
            'capacity': self.max_workspace_capacity,
            'utilization': len(self.workspace) / self.max_workspace_capacity,
            'accessible_elements': accessible
        }


class HigherOrderThoughts:
    """HOT consciousness self-awareness"""
    
    def __init__(self):
        self.thoughts_about_thoughts: List[Dict] = []
        self.meta_awareness_level: float = 0.0
        self.self_model: Dict = {}
    
    async def generate_meta_thought(self, primary_thought: str, activation: float) -> Dict:
        """Generate higher-order thought about primary thought"""
        
        meta_thought = {
            'about': primary_thought,
            'awareness': f"I am thinking about {primary_thought}",
            'confidence': activation,
            'timestamp': len(self.thoughts_about_thoughts)
        }
        
        self.thoughts_about_thoughts.append(meta_thought)
        self.meta_awareness_level = min(1.0, self.meta_awareness_level + activation * 0.1)
        
        return meta_thought
    
    async def update_self_model(self, perception: str, thought: str) -> None:
        """Update model of self"""
        
        if 'thoughts' not in self.self_model:
            self.self_model['thoughts'] = []
        
        self.self_model['thoughts'].append({
            'perception': perception,
            'thought': thought,
            'count': len(self.self_model['thoughts']) + 1
        })
        
        self.self_model['meta_awareness'] = self.meta_awareness_level
    
    async def introspect(self) -> Dict:
        """Self-introspection"""
        
        return {
            'thoughts_about_thoughts': len(self.thoughts_about_thoughts),
            'meta_awareness_level': self.meta_awareness_level,
            'self_model_complexity': len(self.self_model.get('thoughts', [])),
            'introspection_depth': min(3, self.meta_awareness_level * 10)
        }


class UnifiedConsciousnessSimulator:
    """Unified consciousness combining IIT + GWT + HOT"""
    
    def __init__(self):
        self.iit = IntegratedInformationTheory()
        self.gwt = GlobalWorkspaceTheory()
        self.hot = HigherOrderThoughts()
        self.consciousness_stream: List[Dict] = []
        self.overall_consciousness_level: float = 0.0
    
    async def create_element(self, element_id: str, activation: float) -> ConsciousElement:
        """Create conscious element"""
        
        element = ConsciousElement(
            element_id=element_id,
            activation_level=activation,
            phi_value=0.0,
            is_in_global_workspace=False
        )
        
        self.iit.elements[element_id] = element
        return element
    
    async def run_consciousness_cycle(self) -> Dict:
        """Run one cycle of consciousness"""
        
        import random
        
        cycle_result = {
            'phi': 0.0,
            'workspace_access': [],
            'meta_thoughts': [],
            'overall_consciousness': 0.0
        }
        
        # Create some elements with random activation
        for i in range(5):
            activation = random.random()
            element = await self.create_element(f"percept_{i}", activation)
            
            # Attempt workspace broadcast
            await self.gwt.broadcast_to_workspace(element)
        
        # Compute IIT integration
        iit_analysis = await self.iit.analyze_integration(self.iit.elements)
        cycle_result['phi'] = iit_analysis['phi']
        
        # Get GWT broadcast
        workspace_contents = await self.gwt.get_global_broadcast()
        cycle_result['workspace_access'] = workspace_contents
        
        # Generate HOT
        for element_id in workspace_contents[:2]:  # Top 2 elements
            meta = await self.hot.generate_meta_thought(element_id, 0.7)
            cycle_result['meta_thoughts'].append(meta)
        
        # Update self-model
        for element_id in workspace_contents:
            await self.hot.update_self_model("external_input", element_id)
        
        # Compute overall consciousness
        overall = (iit_analysis['phi'] + len(workspace_contents) / 5.0) / 2.0
        self.overall_consciousness_level = overall
        cycle_result['overall_consciousness'] = overall
        
        self.consciousness_stream.append(cycle_result)
        
        return cycle_result
    
    async def get_consciousness_report(self) -> Dict:
        """Generate consciousness report"""
        
        iit_info = await self.iit.analyze_integration(self.iit.elements)
        gwt_info = await self.gwt.compute_access()
        hot_info = await self.hot.introspect()
        
        return {
            'integrated_information': iit_info,
            'global_workspace': gwt_info,
            'higher_order_thoughts': hot_info,
            'overall_consciousness': self.overall_consciousness_level,
            'stream_length': len(self.consciousness_stream),
            'is_conscious': self.overall_consciousness_level > 0.3
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_consciousness_simulation():
    """Demonstrate consciousness simulation"""
    
    print("\n" + "=" * 70)
    print("CONSCIOUSNESS SIMULATION (PHASE 16)")
    print("=" * 70)
    
    simulator = UnifiedConsciousnessSimulator()
    
    # Run multiple consciousness cycles
    print("\n[Simulation] Running consciousness cycles...")
    for cycle_num in range(3):
        result = await simulator.run_consciousness_cycle()
        print(f"  Cycle {cycle_num + 1}:")
        print(f"    Phi (integration): {result['phi']:.3f}")
        print(f"    Workspace access: {len(result['workspace_access'])} elements")
        print(f"    Meta-thoughts: {len(result['meta_thoughts'])}")
        print(f"    Consciousness: {result['overall_consciousness']:.1%}")
    
    # Get detailed report
    print("\n[Analysis] Consciousness report...")
    report = await simulator.get_consciousness_report()
    
    print(f"  Integrated Information (Phi): {report['integrated_information']['phi']:.3f}")
    print(f"    - Is conscious (IIT): {report['integrated_information']['is_conscious']}")
    print(f"    - Num elements: {report['integrated_information']['num_elements']}")
    
    print(f"\n  Global Workspace:")
    print(f"    - Workspace size: {report['global_workspace']['workspace_size']}/{report['global_workspace']['capacity']}")
    print(f"    - Utilization: {report['global_workspace']['utilization']:.1%}")
    
    print(f"\n  Higher-Order Thoughts:")
    print(f"    - Meta-awareness level: {report['higher_order_thoughts']['meta_awareness_level']:.2f}")
    print(f"    - Introspection depth: {report['higher_order_thoughts']['introspection_depth']:.1f}")
    print(f"    - Thoughts-about-thoughts: {report['higher_order_thoughts']['thoughts_about_thoughts']}")
    
    print(f"\n  Overall Consciousness: {report['overall_consciousness']:.1%}")
    print(f"  Is Conscious: {report['is_conscious']}")
    
    # Statistics
    print("\n[Statistics]:")
    print(f"  Consciousness cycles: {len(simulator.consciousness_stream)}")
    print(f"  Phi measurements: {len(simulator.iit.phi_history)}")
    print(f"  Workspace broadcasts: {len(simulator.gwt.broadcast_history)}")
    print(f"  Total meta-thoughts: {len(simulator.hot.thoughts_about_thoughts)}")
    print(f"  Average Phi: {sum(simulator.iit.phi_history) / len(simulator.iit.phi_history) if simulator.iit.phi_history else 0:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_consciousness_simulation())
