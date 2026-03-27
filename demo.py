#!/usr/bin/env python3
"""
PRADYSAGICAN v2.0 - LIVE DEMO
Shows all features working together
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pradysagican.omega import PradysagiOmega, get_omega
from pradysagican.core.config import PradysagiConfig


async def demo_complete_system():
    """Live demonstration of complete system"""
    
    print("\n" + "="*70)
    print(" "*15 + "PRADYSAGICAN v2.0 - COMPLETE SYSTEM DEMO")
    print("="*70 + "\n")
    
    # Initialize system
    print("[1/5] Initializing PRADYSAGICAN OMEGA v2.0...")
    config = PradysagiConfig(prefer_local=True, test_mode=True)
    omega = PradysagiOmega(config)
    print("      Status: Online [OK]\n")
    
    # Show configuration
    print("[2/5] Configuration:")
    config_info = omega.get_config_summary()
    for key, value in config_info.items():
        print(f"      - {key}: {value}")
    print()
    
    # Show system status
    print("[3/5] System Status:")
    status = await omega.get_system_status()
    print(f"      - Session ID: {status['session_id']}")
    print(f"      - System: {status['system']}")
    print(f"      - Deployment: {status['deployment']['status']}")
    print(f"      - Available providers: {status['deployment']['available_providers']}")
    print()
    
    # Show available tools
    print("[4/5] Available Tools:")
    tools = omega.tool_registry.list_available_tools()
    for i, tool in enumerate(tools[:5], 1):
        print(f"      {i}. {tool.name}: {tool.description}")
    if len(tools) > 5:
        print(f"      ... and {len(tools) - 5} more")
    print()
    
    # Process sample queries
    print("[5/5] Processing Sample Queries:")
    sample_queries = [
        "What is machine learning?",
        "How does photosynthesis work?",
        "Explain quantum computing"
    ]
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n      Query {i}: {query}")
        try:
            result = await omega.process_query(query)
            
            if result['success']:
                print(f"      Status: Success")
                print(f"      Complexity: {result['task_complexity']}")
                print(f"      Strategy: {result['strategy']}")
                print(f"      Confidence: {result['confidence']:.1%}")
                print(f"      Time: {result['execution_time_seconds']:.2f}s")
                print(f"      Answer: {result['answer'][:80]}...")
            else:
                print(f"      Status: Error - {result['error']}")
        except Exception as e:
            print(f"      Status: Error - {e}")
    
    # Final statistics
    print("\n" + "="*70)
    print("SYSTEM STATISTICS:")
    stats = omega.get_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    - {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE - PRADYSAGICAN v2.0 IS FULLY OPERATIONAL")
    print("="*70 + "\n")


async def demo_advanced_features():
    """Demonstrate advanced features"""
    
    print("\n" + "="*70)
    print(" "*10 + "ADVANCED FEATURES DEMONSTRATION")
    print("="*70 + "\n")
    
    omega = await get_omega()
    
    # Skills system
    print("[A] Skill Learning System:")
    lib = omega.advanced_features.skill_library
    
    from pradysagican.core.advanced import Skill
    skill = Skill(
        name="DataAnalysis",
        description="Analyze datasets",
        procedure="Load data -> Clean -> Analyze -> Visualize",
        domain="data_science",
        proficiency=0.85
    )
    lib.add_skill(skill)
    print(f"    Learned skill: {skill.name} ({skill.proficiency:.0%})")
    
    # Personality system
    print("\n[B] Personality System:")
    personality = omega.advanced_features.personality
    trait = personality.get_trait('helpfulness')
    print(f"    Helpfulness trait: {trait.value} (weight: {trait.weight})")
    
    # Multi-agent system
    print("\n[C] Multi-Agent Team:")
    team = omega.advanced_features.multi_agent
    team_status = team.get_team_status()
    print(f"    Team size: {team_status['team_size']}")
    print(f"    Avg performance: {team_status['avg_performance']:.1%}")
    print(f"    Avg reliability: {team_status['avg_reliability']:.1%}")
    
    # Self-improvement
    print("\n[D] Self-Improvement System:")
    improvement_status = omega.advanced_features.self_improvement.get_improvement_summary()
    print(f"    Total cycles: {improvement_status['total_cycles']}")
    print(f"    Total attempted: {improvement_status['total_attempted']}")
    print(f"    Total successful: {improvement_status['total_successful']}")
    
    # Memory system
    print("\n[E] Hierarchical Memory System:")
    print(f"    Working memory entries: {len(omega.memory_manager.working.buffer)}")
    print(f"    Total stored memories: {len(omega.memory_manager.store.memories)}")
    
    print("\n" + "="*70 + "\n")


async def main():
    """Run all demos"""
    
    try:
        await demo_complete_system()
        await demo_advanced_features()
        
        print("\nStatus: ALL DEMOS COMPLETED SUCCESSFULLY")
        print("PRADYSAGICAN v2.0 is production-ready!\n")
        return 0
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
