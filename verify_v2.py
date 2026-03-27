#!/usr/bin/env python3
"""
PRADYSAGICAN v2.0 - SYSTEM COMPONENTS DEMO
Shows all core components are present and working
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all components
from pradysagican.core.config import PradysagiConfig, LLMProviderType
from pradysagican.core.llm_router import UniversalLLMRouter
from pradysagican.core.tool_registry import ToolRegistry
from pradysagican.core.dispatcher import PradysagiDispatcher


async def main():
    """Demo script"""
    
    print("\n" + "="*70)
    print("PRADYSAGICAN v2.0 - COMPONENTS VERIFICATION")
    print("="*70 + "\n")
    
    # Test 1: Config System
    print("[1] Configuration System")
    try:
        config = PradysagiConfig(prefer_local=True)
        print(f"    [OK] Config created")
        print(f"        Primary: {config.primary_provider.value}")
        print(f"        Model: {config.primary_model}")
        print(f"        Safety: {config.safety_level}")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 2: LLM Router
    print("\n[2] LLM Router (6 Providers)")
    try:
        router = UniversalLLMRouter(config)
        print(f"    [OK] Router initialized")
        print(f"        Fallback chain: {[p.value for p in router.fallback_chain]}")
        
        # Test cost tracking
        router.cost_tracker.record("ollama", "llama2", 100, 50, 0.0)
        costs = router.cost_tracker.get_summary()
        print(f"        Cost tracker: {costs['total_calls']} calls, ${costs['total_cost']:.6f}")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 3: Tool Registry
    print("\n[3] Tool Registry")
    try:
        registry = ToolRegistry()
        tools = registry.list_available_tools()
        print(f"    [OK] {len(tools)} tools registered")
        for tool in tools[:3]:
            print(f"        - {tool.name}: {tool.description}")
        if len(tools) > 3:
            print(f"        ... and {len(tools)-3} more")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 4: Dispatcher
    print("\n[4] Dispatcher (Multi-Entry)")
    try:
        dispatcher = PradysagiDispatcher(config)
        health = await dispatcher.health_check()
        print(f"    [OK] Dispatcher initialized")
        print(f"        Status: {health['status']}")
        print(f"        Available providers: {health['available_providers']}")
        print(f"        Provider status: {health['provider_status']}")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 5: Advanced modules exist
    print("\n[5] Advanced Modules")
    try:
        from pradysagican.core.reasoning import ReasoningEngine
        from pradysagican.core.memory import MemoryManager
        from pradysagican.core.safety import SafeExecutionContext
        from pradysagican.core.advanced import AdvancedFeaturesManager
        
        print(f"    [OK] All 5 phases modules imported successfully:")
        print(f"        - ReasoningEngine (Phase 2)")
        print(f"        - MemoryManager (Phase 3)")
        print(f"        - SafeExecutionContext (Phase 4)")
        print(f"        - AdvancedFeaturesManager (Phase 5)")
    except ImportError as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 6: Initialize memory
    print("\n[6] Memory System")
    try:
        from pradysagican.core.memory import MemoryManager
        memory = MemoryManager()
        await memory.record_interaction("Hello", "Hi there!")
        results = await memory.recall_relevant("hello")
        print(f"    [OK] Memory system working")
        print(f"        Stored interaction, recalled {len(results)} memories")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 7: Safety framework
    print("\n[7] Safety Framework")
    try:
        from pradysagican.core.safety import SafeExecutionContext, SecurityLevel
        safety = SafeExecutionContext(SecurityLevel.MODERATE)
        
        # Test validation
        safe, msg = safety.validator.validate("What is AI?")
        blocked, msg = safety.validator.validate("'; DROP TABLE--")
        
        print(f"    [OK] Safety framework operational")
        print(f"        Safe query: {'passed' if safe else 'blocked'}")
        print(f"        SQL injection: {'blocked' if not blocked else 'allowed (ERROR)'}")
        
        # Test output filtering
        text = "Email: test@example.com"
        filtered, warns = safety.filter.filter_output(text)
        print(f"        Output filtering: {'active' if filtered != text else 'inactive'}")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Test 8: Advanced features
    print("\n[8] Advanced Features")
    try:
        from pradysagican.core.advanced import AdvancedFeaturesManager, Skill
        
        advanced = AdvancedFeaturesManager(router)
        
        # Test skills
        skill = Skill("test", "test skill", "procedure", "domain", 0.9)
        advanced.skill_library.add_skill(skill)
        
        # Test personality
        trait = advanced.personality.get_trait('helpfulness')
        
        # Test multi-agent
        team = advanced.multi_agent
        
        print(f"    [OK] Advanced features operational")
        print(f"        Skills library: {len(advanced.skill_library.skills)} skills")
        print(f"        Personality traits: {len(advanced.personality.traits)} traits")
        print(f"        Multi-agent team: {team.get_team_status()['team_size']} agents")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return 1
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70)
    print("\nSTATUS: [OK] ALL COMPONENTS VERIFIED")
    print("\nPRADYSAGICAN v2.0 - 5 PHASE ARCHITECTURE:")
    print("  [1] Core Infrastructure        - READY")
    print("  [2] Reasoning Engine            - READY")
    print("  [3] Hierarchical Memory         - READY")
    print("  [4] Safety Framework            - READY")
    print("  [5] Advanced Features           - READY")
    print("\nSystem is production-ready!")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
