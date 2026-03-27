#!/usr/bin/env python3
"""Test all Phase 4 systems"""
import asyncio
from pradysagican.core.neural_architecture_search import NeuralArchitectureSearch
from pradysagican.core.swarm_intelligence import SwarmIntelligenceSystem
from pradysagican.core.knowledge_stream_system import CausalGraph, StreamProcessor, RelationType, StreamEvent

async def test_phase4():
    print("PHASE 4 SYSTEM VERIFICATION")
    print("=" * 60)
    
    # Test 1: NAS
    print("\n1. Testing Neural Architecture Search (NAS)...")
    try:
        nas = NeuralArchitectureSearch()
        result = await nas.full_search(num_generations=2, num_hp_trials=5)
        print(f"   ✅ NAS Complete")
        arch = result['architecture']
        print(f"      Fitness: {arch['fitness_score']:.4f}")
        print(f"      Accuracy: {arch['accuracy']:.2%}")
    except Exception as e:
        print(f"   ❌ NAS Failed: {e}")
        return False
    
    # Test 2: Swarm
    print("\n2. Testing Swarm Intelligence...")
    try:
        swarm = SwarmIntelligenceSystem()
        
        result = await swarm.comprehensive_swarm_study()
        pso = result['pso']
        print(f"   ✅ PSO Complete")
        print(f"      Best Fitness: {pso['best_fitness']:.6f}")
        
        aco = result['aco']
        print(f"   ✅ ACO Complete")
        print(f"      Best Cost: {aco['best_cost']:.4f}")
        
        emergence = result['emergence']
        print(f"   ✅ Emergence Detection Complete")
        print(f"      Cooperation: {emergence['cooperation_level']:.2%}")
    except Exception as e:
        print(f"   ❌ Swarm Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Causal Graph
    print("\n3. Testing Causal Knowledge Graph...")
    try:
        graph = CausalGraph()
        await graph.add_causal_relationship("A", "B", RelationType.CAUSAL, 0.8, 0.9)
        await graph.add_causal_relationship("B", "C", RelationType.CAUSAL, 0.7, 0.85)
        
        causal = await graph.infer_causality("A", "C")
        print(f"   ✅ Causal Inference Complete")
        print(f"      Path Exists: {causal['causal_link']}")
        print(f"      Strength: {causal['strength']:.2%}")
        print(f"      Paths Found: {len(causal['paths'])}")
    except Exception as e:
        print(f"   ❌ Causal Graph Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Stream Processing
    print("\n4. Testing Stream Processing...")
    try:
        processor = StreamProcessor()
        
        # Process multiple events
        for i in range(15):
            event = StreamEvent(
                event_id=f"evt_{i}",
                timestamp=None,
                event_type="metric",
                value=100 + i,
                source="test_system"
            )
            result = await processor.process_event(event)
        
        print(f"   ✅ Stream Processing Complete")
        stats = await processor.get_stream_statistics()
        print(f"      Events: {stats['processed_events']}")
        print(f"      Mean: {stats['mean']:.2f}")
        print(f"      Stdev: {stats['stdev']:.2f}")
    except Exception as e:
        print(f"   ❌ Stream Processing Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL PHASE 4 SYSTEMS VERIFIED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_phase4())
    exit(0 if success else 1)
