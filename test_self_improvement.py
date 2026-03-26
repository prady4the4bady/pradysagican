#!/usr/bin/env python3
"""
Comprehensive Self-Improvement Feature Test Suite
===================================================
Tests all self-improvement mechanisms in PRADYSAGICAN:
- Learning episodes and heuristic distillation
- Skill tree progression
- Self-modification tracking
- Co-evolution orchestration
- Archive quality diversity scoring
- Reflection and meta-learning
"""

import asyncio
import sys
from pathlib import Path

# Add pradysagican to path
sys.path.insert(0, str(Path(__file__).parent))

from pradysagican.god import PradysagicanGod
from pradysagican.agents.learner import (
    SelfImprovementEngine,
    LearningEpisode,
    SkillTree,
    Heuristic,
)
from pradysagican.core.co_evolution.orchestrator import CoEvolutionOrchestrator
from pradysagican.core.evolution.archive import DGMArchive
# Prometheus import removed - will test via god-layer instead


async def test_learning_engine():
    """Test self-improvement learning engine."""
    print("\n" + "="*70)
    print("TEST 1: Self-Improvement Learning Engine (EDITH v2.0)")
    print("="*70)
    
    learner = SelfImprovementEngine()
    
    # Create a learning episode
    print("\n✓ Creating learning episode...")
    episode = LearningEpisode(
        id="test_1",
        task="solve_complex_problem",
        actions=[
            "decomposed problem",
            "applied RL heuristics",
            "verified solution",
        ],
        outcome="optimal_solution_found",
        success=True,
        reward=0.95,
        difficulty=0.8,
    )
    
    print(f"  Episode ID: {episode.id}")
    print(f"  Task: {episode.task}")
    print(f"  Success: {episode.success}")
    print(f"  Reward: {episode.reward}")
    print(f"  Difficulty: {episode.difficulty}")
    
    # Record episode
    print("\n✓ Recording episode...")
    await learner.record_episode(episode)
    print(f"  Episodes in memory: {len(learner._episodes)}")
    
    # Distill heuristics
    print("\n✓ Extracting heuristics...")
    heuristics = await learner.distill_heuristics(min_episodes=0)
    print(f"  Heuristics extracted: {len(heuristics.get('heuristics', []))}")
    for h in heuristics.get("heuristics", [])[:3]:
        print(f"    - {h.get('rule', 'N/A')}: confidence {h.get('confidence', 0):.2f}")
    
    return True


async def test_skill_tree():
    """Test skill tree progression with XP and leveling."""
    print("\n" + "="*70)
    print("TEST 2: Skill Tree Progression & XP System")
    print("="*70)
    
    tree = SkillTree()
    
    print("\n✓ Creating skill hierarchy...")
    # Root skill
    root = tree.add_skill("problem_solving", unlocked=True)
    print(f"  Created: {root.name} (level {root.level})")
    
    # Child skills
    tree.add_skill("decomposition", parent="problem_solving", unlocked=False)
    tree.add_skill("reasoning", parent="problem_solving", unlocked=False)
    print(f"  Added 2 child skills (initially locked)")
    
    # Award XP to root skill
    print("\n✓ Awarding XP to skill...")
    result = await tree.gain_xp("problem_solving", 150.0)
    print(f"  Skill: {result['skill']}")
    print(f"  Level: {result['level']}")
    print(f"  XP: {result['xp']}/{result['xp_to_next']}")
    print(f"  Leveled up: {result['leveled_up']}")
    
    # Check if children unlocked
    print("\n✓ Checking child skill unlock...")
    children = tree._nodes["problem_solving"].children
    for child_name in children:
        child = tree._nodes[child_name]
        print(f"  {child_name}: unlocked={child.unlocked}, level={child.level}")
    
    return True


async def test_self_modification_tracking():
    """Test self-modification tracking and acceptance."""
    print("\n" + "="*70)
    print("TEST 3: Self-Modification Tracking")
    print("="*70)
    
    learner = SelfImprovementEngine()
    
    print("\n✓ Creating self-modification record...")
    modification = {
        "target": "reasoning_weight",
        "change_description": "increase causal reasoning weight from 0.5 to 0.7",
        "before_score": 0.65,
        "after_score": 0.72,
        "accepted": True,
    }
    
    mod_id = await learner.propose_self_modification(
        target=modification["target"],
        change_description=modification["change_description"],
        before_score=modification["before_score"],
        after_score=modification["after_score"],
    )
    
    print(f"  Modification ID: {mod_id}")
    print(f"  Target: {modification['target']}")
    print(f"  Change: {modification['change_description']}")
    print(f"  Score improvement: {modification['before_score']:.2f} → {modification['after_score']:.2f}")
    print(f"  Improvement: +{(modification['after_score']-modification['before_score'])*100:.1f}%")
    
    return True


async def test_reflection_cycle():
    """Test reflection and introspection cycle."""
    print("\n" + "="*70)
    print("TEST 4: Reflection & Introspection Cycle")
    print("="*70)
    
    learner = SelfImprovementEngine()
    
    print("\n✓ Running reflection cycle...")
    reflection = await learner.reflect(
        task="complex reasoning task",
        actions=[
            "applied causal inference",
            "checked logical consistency",
            "generated creative alternatives",
        ],
        outcome="high_quality_reasoning_produced",
        success=True,
    )
    
    print(f"  Reflection type: {type(reflection).__name__}")
    if isinstance(reflection, dict):
        print(f"  Episode recorded: {reflection.get('episode_id', 'N/A')}")
        print(f"  Lessons extracted: {len(reflection.get('lessons', []))}")
        for lesson in reflection.get("lessons", [])[:3]:
            print(f"    - {lesson}")
    
    return True


async def test_meta_learning():
    """Test meta-learning capability."""
    print("\n" + "="*70)
    print("TEST 5: Meta-Learning (Learning How To Learn)")
    print("="*70)
    
    learner = SelfImprovementEngine()
    
    print("\n✓ Running meta-learning cycle...")
    meta_result = await learner.meta_learn()
    
    print(f"  Meta-learning result type: {type(meta_result).__name__}")
    if isinstance(meta_result, dict):
        print(f"  Learning strategies updated: {meta_result.get('strategies_updated', 0)}")
        print(f"  Heuristic improvements: {meta_result.get('heuristic_improvements', [])}")
    
    return True


async def test_co_evolution():
    """Test co-evolution orchestrator."""
    print("\n" + "="*70)
    print("TEST 6: Co-Evolution Orchestrator (Multi-Population)")
    print("="*70)
    
    print("\n✓ Initializing co-evolution orchestrator...")
    orchestrator = CoEvolutionOrchestrator(
        num_populations=3,
        population_size=10,
        max_generations=5,
        elite_rate=0.2,
    )
    print(f"  Populations: {orchestrator.num_populations}")
    print(f"  Population size: {orchestrator.population_size}")
    print(f"  Max generations: {orchestrator.max_generations}")
    
    print("\n✓ Initializing populations...")
    def make_agent():
        return {
            "id": f"agent_{asyncio.current_task().get_name() if asyncio.current_task() else 'default'}",
            "fitness": 0.5,
            "code": "default_agent_code",
        }
    
    state = await orchestrator.initialize_evolution(make_agent)
    print(f"  Initial state generation: {state.current_generation}")
    print(f"  Populations created: {len(state.populations)}")
    for pop_id in list(state.populations.keys())[:3]:
        print(f"    - {pop_id}: {len(state.populations[pop_id])} agents")
    
    return True


async def test_quality_diversity_archive():
    """Test evolutionary archive with Quality Diversity scoring."""
    print("\n" + "="*70)
    print("TEST 7: Quality-Diversity Evolutionary Archive")
    print("="*70)
    
    print("\n✓ Initializing DGM Archive...")
    archive = DGMArchive(max_variants=100)
    print(f"  Max variants: {archive.max_variants}")
    
    print("\n✓ Adding evolved variants...")
    for i in range(5):
        variant_id = await archive.add_variant(
            variant_type="evolved",
            code=f"evolved_code_v{i}",
            fitness_score=0.5 + (i * 0.1),
            novelty_score=0.3 + (i * 0.08),
        )
        print(f"  Added variant {i+1}: ID={variant_id[:8]}..., fitness={0.5 + (i * 0.1):.2f}")
    
    print("\n✓ Archive statistics...")
    stats = archive.get_stats()
    print(f"  Variants in archive: {stats['total_variants']}")
    print(f"  Best fitness: {stats.get('best_fitness_score', 0):.2f}")
    print(f"  Average novelty: {stats.get('avg_novelty', 0):.2f}")
    print(f"  QD score: {stats.get('qd_score', 0):.2f}")
    
    return True


async def test_god_layer_evolve():
    """Test god-layer evolve() method end-to-end."""
    print("\n" + "="*70)
    print("TEST 8: God-Layer Evolution Cycle (/evolve)")
    print("="*70)
    
    print("\n✓ Initializing God-layer...")
    god = PradysagicanGod()
    await god.initialize()
    print(f"  God-layer initialized")
    print(f"  Subsystems online: {god.status()['subsystems_online']}")
    
    print("\n✓ Running evolution cycle...")
    result = await god.evolve()
    
    print(f"  Evolution cycle completed in {result.elapsed_ms}ms")
    print(f"  Reflections: {bool(result.reflections)}")
    print(f"  Heuristics learned: {len(result.heuristics_learned)}")
    print(f"  Prometheus cycle: {bool(result.prometheus_cycle)}")
    print(f"  Bio-cycle: {bool(result.bio_cycle)}")
    print(f"  Moral growth: {bool(result.moral_growth)}")
    print(f"  Meta-learning: {bool(result.meta_learning)}")
    
    return True


async def main():
    """Run all self-improvement tests."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "PRADYSAGICAN SELF-IMPROVEMENT FEATURE TEST SUITE" + " "*5 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Learning Engine (EDITH v2.0)", test_learning_engine),
        ("Skill Tree & XP System", test_skill_tree),
        ("Self-Modification Tracking", test_self_modification_tracking),
        ("Reflection Cycle", test_reflection_cycle),
        ("Meta-Learning", test_meta_learning),
        ("Co-Evolution Orchestrator", test_co_evolution),
        ("Quality-Diversity Archive", test_quality_diversity_archive),
        ("God-Layer Evolution", test_god_layer_evolve),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = await test_func()
            print(f"\n✅ {name}: PASSED")
        except Exception as e:
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {str(e)}")
            results[name] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print("\n" + "="*70)
    if passed == total:
        print("🎉 ALL SELF-IMPROVEMENT TESTS PASSED! 🎉")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
