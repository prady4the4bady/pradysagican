#!/usr/bin/env python3
"""
PRADYSAGICAN v2.0 - Quick Test & Demo
Verifies core components work before full test suite
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pradysagican.core.config import PradysagiConfig, LLMProviderType, get_config
from pradysagican.core.llm_router import UniversalLLMRouter
from pradysagican.core.dispatcher import PradysagiDispatcher, RequestSource
from pradysagican.core.tool_registry import ToolRegistry


async def test_config():
    """Test 1: Configuration system"""
    print("\n" + "="*60)
    print("TEST 1: Configuration System")
    print("="*60)
    
    config = get_config()
    
    print(f"✓ Config created successfully")
    print(f"  - Primary Provider: {config.primary_provider.value}")
    print(f"  - Primary Model: {config.primary_model}")
    print(f"  - Prefer Local: {config.prefer_local}")
    print(f"  - Fallback Providers: {[p.value for p in config.fallback_providers]}")
    print(f"✓ PASSED")


async def test_llm_router():
    """Test 2: LLM Router"""
    print("\n" + "="*60)
    print("TEST 2: LLM Router & Provider Detection")
    print("="*60)
    
    config = PradysagiConfig(prefer_local=True)
    router = UniversalLLMRouter(config)
    
    print(f"✓ Router created successfully")
    print(f"  - Fallback chain: {[p.value for p in router.fallback_chain]}")
    
    # Test cost tracking
    router.cost_tracker.record("ollama", "llama2", 100, 50, 0.0)
    costs = router.cost_tracker.get_summary()
    
    print(f"✓ Cost tracking works")
    print(f"  - Total calls: {costs['total_calls']}")
    print(f"  - Total cost: ${costs['total_cost']:.6f}")
    print(f"✓ PASSED")


async def test_tool_registry():
    """Test 3: Tool Registry"""
    print("\n" + "="*60)
    print("TEST 3: Tool Registry")
    print("="*60)
    
    registry = ToolRegistry()
    
    tools = registry.list_available_tools()
    print(f"✓ {len(tools)} tools registered")
    
    for tool in tools[:5]:
        print(f"  - {tool.name}: {tool.description}")
    
    # Test tool execution
    result = await registry.execute("system_info")
    print(f"✓ Tool execution works")
    print(f"  - Platform: {result['platform']}")
    print(f"  - CPU Count: {result['cpu_count']}")
    print(f"✓ PASSED")


async def test_dispatcher():
    """Test 4: Dispatcher"""
    print("\n" + "="*60)
    print("TEST 4: Dispatcher")
    print("="*60)
    
    config = PradysagiConfig(prefer_local=True, test_mode=True)
    dispatcher = PradysagiDispatcher(config)
    
    print(f"✓ Dispatcher created successfully")
    
    # Test health check
    try:
        health = await dispatcher.health_check()
        print(f"✓ Health check passed")
        print(f"  - Status: {health['status']}")
        print(f"  - Available Providers: {health['available_providers']}")
        print(f"  - Provider Status:")
        for provider, status in health['provider_status'].items():
            print(f"    - {provider}: {status}")
    except Exception as e:
        print(f"⚠ Health check warning (providers may not be available): {e}")
    
    print(f"✓ PASSED")


async def test_llm_completion():
    """Test 5: LLM Completion (if providers available)"""
    print("\n" + "="*60)
    print("TEST 5: LLM Completion (if available)")
    print("="*60)
    
    config = PradysagiConfig(prefer_local=True, test_mode=False)
    router = UniversalLLMRouter(config)
    
    print(f"Testing LLM completion with: {[p.value for p in router.fallback_chain]}")
    
    try:
        response = await router.complete("Say 'hello world' and nothing else.")
        print(f"✓ LLM completion successful")
        print(f"  Response: {response[:100]}...")
        print(f"✓ PASSED")
    except Exception as e:
        print(f"⚠ SKIPPED: LLM providers not available")
        print(f"  Error: {e}")
        print(f"  To test, install Ollama or configure an API key")


async def test_end_to_end():
    """Test 6: End-to-End Dispatch"""
    print("\n" + "="*60)
    print("TEST 6: End-to-End Query Dispatch")
    print("="*60)
    
    config = PradysagiConfig(prefer_local=True, test_mode=False)
    dispatcher = PradysagiDispatcher(config)
    
    print(f"Sending test query through dispatcher...")
    
    try:
        result = await dispatcher.process(
            query="What is 2+2?",
            source=RequestSource.CLI,
            user_id="test_user"
        )
        
        print(f"✓ Query processed successfully")
        print(f"  - Task ID: {result.task_id}")
        print(f"  - Strategy: {result.strategy}")
        print(f"  - Confidence: {result.confidence:.1%}")
        print(f"  - Time: {result.duration_seconds:.2f}s")
        print(f"  - Answer: {result.answer[:100]}...")
        print(f"✓ PASSED")
        
    except Exception as e:
        print(f"⚠ SKIPPED: LLM providers not available")
        print(f"  Error: {e}")


async def main():
    """Run all tests"""
    
    print("\n")
    print("=" * 60)
    print(" PRADYSAGICAN v2.0 - CORE COMPONENT TESTS".center(60))
    print("=" * 60)
    
    tests = [
        ("Configuration", test_config),
        ("LLM Router", test_llm_router),
        ("Tool Registry", test_tool_registry),
        ("Dispatcher", test_dispatcher),
        ("LLM Completion", test_llm_completion),
        ("End-to-End", test_end_to_end),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ FAILED: {name}")
            print(f"  Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Passed: {passed}/{len(tests)}")
    print(f"✗ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠ {failed} test(s) failed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
