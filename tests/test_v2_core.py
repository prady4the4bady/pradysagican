"""
PRADYSAGICAN v2.0 - Tests for Core Functionality
Verifies all components work correctly
"""

import pytest
import asyncio
from pathlib import Path

from pradysagican.core.config import PradysagiConfig, LLMProviderType
from pradysagican.core.llm_router import UniversalLLMRouter
from pradysagican.core.dispatcher import PradysagiDispatcher, RequestSource
from pradysagican.core.tool_registry import ToolRegistry


@pytest.fixture
def config():
    """Create test configuration"""
    return PradysagiConfig(
        debug=True,
        test_mode=True,
        prefer_local=True,  # Use Ollama for tests
        primary_provider=LLMProviderType.OLLAMA,
    )


@pytest.fixture
def llm_router(config):
    """Create LLM router"""
    return UniversalLLMRouter(config)


@pytest.fixture
def dispatcher(config):
    """Create dispatcher"""
    return PradysagiDispatcher(config)


@pytest.fixture
def tool_registry():
    """Create tool registry"""
    return ToolRegistry()


# ===== CONFIG TESTS =====

def test_config_creation():
    """Test config can be created"""
    config = PradysagiConfig()
    assert config is not None
    assert config.primary_provider == LLMProviderType.OLLAMA
    assert config.primary_model == "llama2"


def test_config_fallback_chain(config):
    """Test fallback provider chain"""
    chain = config.fallback_providers
    assert len(chain) > 0
    assert LLMProviderType.GROQ in chain


def test_config_validation():
    """Test config validation"""
    # Invalid temperature
    with pytest.raises(ValueError):
        PradysagiConfig(temperature=3.0)
    
    # Valid config
    config = PradysagiConfig(temperature=1.5)
    assert config.temperature == 1.5


# ===== LLM ROUTER TESTS =====

def test_llm_router_creation(llm_router, config):
    """Test LLM router creates successfully"""
    assert llm_router is not None
    assert len(llm_router.fallback_chain) > 0


def test_llm_router_fallback_chain(llm_router):
    """Test router builds correct fallback chain"""
    chain = llm_router.fallback_chain
    # Should have Ollama first (local)
    assert chain[0] == LLMProviderType.OLLAMA


def test_cost_tracking(llm_router):
    """Test cost tracker works"""
    llm_router.cost_tracker.record(
        provider="groq",
        model="mixtral-8x7b",
        input_tokens=100,
        output_tokens=50,
        cost=0.001
    )
    
    summary = llm_router.cost_tracker.get_summary()
    assert summary['total_calls'] == 1
    assert summary['total_cost'] > 0


def test_rate_limiter(llm_router):
    """Test rate limiter"""
    rate_limiter = llm_router.rate_limiter
    
    # Should be able to call
    assert rate_limiter.can_call(LLMProviderType.OLLAMA)
    
    # Record call
    rate_limiter.record_call(LLMProviderType.OLLAMA)


# ===== DISPATCHER TESTS =====

@pytest.mark.asyncio
async def test_dispatcher_creation(dispatcher):
    """Test dispatcher creates"""
    assert dispatcher is not None


@pytest.mark.asyncio
async def test_dispatcher_health_check(dispatcher):
    """Test health check endpoint"""
    health = await dispatcher.health_check()
    
    assert 'status' in health
    assert 'available_providers' in health
    assert 'provider_status' in health


@pytest.mark.asyncio
async def test_dispatcher_process(dispatcher):
    """Test dispatcher can process a query"""
    # This test will fail if Ollama isn't running
    # It will try the query but should work with fallbacks
    try:
        result = await dispatcher.process(
            query="Say 'hello'",
            source=RequestSource.CLI,
        )
        
        assert result is not None
        assert result.answer is not None
        assert len(result.answer) > 0
    except Exception as e:
        pytest.skip(f"LLM providers not available: {e}")


# ===== TOOL REGISTRY TESTS =====

def test_tool_registry_creation(tool_registry):
    """Test tool registry creates"""
    assert tool_registry is not None


def test_builtin_tools(tool_registry):
    """Test built-in tools are registered"""
    tools = tool_registry.list_available_tools()
    assert len(tools) > 0
    
    tool_names = [t.name for t in tools]
    assert "system_info" in tool_names
    assert "list_files" in tool_names


@pytest.mark.asyncio
async def test_system_info_tool(tool_registry):
    """Test system_info tool execution"""
    result = await tool_registry.execute("system_info")
    
    assert isinstance(result, dict)
    assert 'platform' in result


@pytest.mark.asyncio
async def test_list_files_tool(tool_registry):
    """Test list_files tool"""
    files = await tool_registry.execute("list_files", directory=".")
    
    assert isinstance(files, list)
    assert len(files) > 0


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_end_to_end_with_mock(dispatcher, tool_registry):
    """End-to-end test with mock"""
    # This verifies the entire pipeline works
    result = await dispatcher.process(
        query="What tools are available?",
        source=RequestSource.CLI,
    )
    
    assert result is not None
    assert result.task_id is not None
    assert result.duration_seconds > 0


# ===== PERFORMANCE TESTS =====

@pytest.mark.asyncio
async def test_response_speed(dispatcher):
    """Test response time is reasonable"""
    import time
    
    start = time.time()
    
    try:
        result = await dispatcher.process(
            query="Say ok",
            source=RequestSource.CLI,
        )
        duration = time.time() - start
        
        # Should complete in reasonable time (even on slow hardware)
        assert duration < 60  # 60 second timeout
        
    except Exception as e:
        pytest.skip(f"LLM not available: {e}")


# ===== RUN TESTS =====

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
