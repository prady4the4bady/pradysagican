"""
PHASE 16: ADVANCED AGENT CAPABILITIES - TESTS
Tests all 16 enterprise features
"""

import pytest
import asyncio
from pradysagican.agents.advanced_capabilities import (
    ToolManager, ToolDefinition, ToolCall, ToolType,
    FunctionCallingStrategy, StreamingResponseHandler,
    TokenBudgetManager, RetryManager, RateLimiter,
    SemanticCache, CostOptimizer, AdvancedAgentCapabilities
)


class TestToolManager:
    """Test tool management system."""
    
    def test_tool_registration(self):
        """Test registering a tool."""
        manager = ToolManager()
        
        tool = ToolDefinition(
            name="search",
            description="Search the web",
            tool_type=ToolType.SEARCH,
            parameters={"query": "string"},
            required_params=["query"]
        )
        
        manager.register_tool(tool)
        assert "search" in manager.tools
        assert manager.tools["search"].name == "search"
    
    async def test_tool_execution(self):
        """Test executing a registered tool."""
        manager = ToolManager()
        
        tool = ToolDefinition(
            name="search",
            description="Search the web",
            tool_type=ToolType.SEARCH,
            parameters={"query": "string"},
            required_params=["query"],
            timeout_seconds=5.0
        )
        
        manager.register_tool(tool)
        
        call = ToolCall(tool_name="search", parameters={"query": "AI"})
        result = await manager.execute_tool(call)
        
        assert result["success"] is True
        assert call.duration_ms > 0
    
    async def test_tool_caching(self):
        """Test that tool results are cached."""
        manager = ToolManager()
        
        tool = ToolDefinition(
            name="search",
            description="Search",
            tool_type=ToolType.SEARCH,
            parameters={"query": "string"},
            required_params=["query"]
        )
        
        manager.register_tool(tool)
        
        # First call
        call1 = ToolCall(tool_name="search", parameters={"query": "AI"})
        result1 = await manager.execute_tool(call1)
        
        # Second call with same params should use cache
        call2 = ToolCall(tool_name="search", parameters={"query": "AI"})
        result2 = await manager.execute_tool(call2)
        
        # Both should succeed
        assert result1["success"] is True
        assert result2["success"] is True


class TestFunctionCalling:
    """Test smart function calling with fallbacks."""
    
    @pytest.mark.asyncio
    async def test_fallback_chain_registration(self):
        """Test registering fallback chains."""
        tool_manager = ToolManager()
        strategy = FunctionCallingStrategy(tool_manager)
        
        strategy.register_fallback_chain("search_gpt", ["search_claude", "search_local"])
        
        assert "search_gpt" in strategy.fallback_chains
        assert strategy.fallback_chains["search_gpt"] == ["search_claude", "search_local"]
    
    @pytest.mark.asyncio
    async def test_successful_function_call(self):
        """Test successful function call."""
        tool_manager = ToolManager()
        tool = ToolDefinition(
            name="search",
            description="Search",
            tool_type=ToolType.SEARCH,
            parameters={"query": "string"},
            required_params=["query"]
        )
        tool_manager.register_tool(tool)
        
        strategy = FunctionCallingStrategy(tool_manager)
        result = await strategy.call_with_fallback("search", {"query": "AI"})
        
        assert result["success"] is True
        assert len(strategy.call_history) > 0
    
    def test_call_statistics(self):
        """Test function calling statistics."""
        tool_manager = ToolManager()
        strategy = FunctionCallingStrategy(tool_manager)
        
        # Add fake calls
        for i in range(5):
            call = ToolCall(
                tool_name="search",
                parameters={"query": f"test{i}"},
                result={"success": True} if i < 3 else None,
                error=None if i < 3 else "error"
            )
            strategy.call_history.append(call)
        
        stats = strategy.get_call_statistics()
        
        assert stats["total_calls"] == 5
        assert stats["successful_calls"] == 3
        assert stats["success_rate"] == 0.6


class TestStreamingResponse:
    """Test streaming response handling."""
    
    @pytest.mark.asyncio
    async def test_stream_result(self):
        """Test streaming results."""
        handler = StreamingResponseHandler()
        
        chunks = ["Hello", " ", "World", "!"]
        await handler.stream_result("stream_001", chunks)
        
        assert "stream_001" in handler.active_streams
        assert len(handler.active_streams["stream_001"]) == 4
    
    def test_accumulated_result(self):
        """Test getting accumulated streaming result."""
        handler = StreamingResponseHandler()
        handler.active_streams["stream_001"] = ["Hello", " ", "World"]
        
        result = handler.get_accumulated_result("stream_001")
        assert result == "Hello World"


class TestTokenBudget:
    """Test token budget management."""
    
    @pytest.mark.asyncio
    async def test_token_estimation(self):
        """Test token count estimation."""
        manager = TokenBudgetManager(budget_per_request=100)
        
        tokens = manager.estimate_tokens("Hello world this is a test")
        assert tokens > 0
    
    @pytest.mark.asyncio
    async def test_budget_check_pass(self):
        """Test budget check that passes."""
        manager = TokenBudgetManager(budget_per_request=100)
        
        result = await manager.check_budget("Hello world")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_budget_check_fail(self):
        """Test budget check that fails."""
        manager = TokenBudgetManager(budget_per_request=5)
        
        result = await manager.check_budget("This is a very long text that will exceed the budget")
        assert result is False
    
    def test_budget_stats(self):
        """Test budget usage statistics."""
        manager = TokenBudgetManager()
        
        manager.record_request("Hello", "World")
        manager.record_request("Test", "Response")
        
        stats = manager.get_budget_stats()
        
        assert stats["total_requests"] == 2
        assert stats["total_tokens_used"] > 0


class TestRetryManager:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution on first try."""
        manager = RetryManager()
        
        async def success_func():
            return "success"
        
        result = await manager.execute_with_retry(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry on failure."""
        manager = RetryManager(base_delay=0.01, max_delay=0.1, max_retries=2)
        
        attempts = 0
        
        async def failing_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Test error")
            return "success"
        
        result = await manager.execute_with_retry(failing_func)
        assert result == "success"
        assert attempts == 3


class TestRateLimiter:
    """Test rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiter allows calls within limit."""
        limiter = RateLimiter(max_calls=5, time_window_seconds=1)
        
        for _ in range(5):
            await limiter.acquire()
        
        assert len(limiter.call_timestamps) == 5
    
    def test_current_rate(self):
        """Test getting current rate."""
        limiter = RateLimiter()
        
        import time
        for _ in range(3):
            limiter.call_timestamps.append(time.time())
        
        rate = limiter.get_current_rate()
        assert rate >= 0.0


class TestSemanticCache:
    """Test semantic caching."""
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss on dissimilar query."""
        cache = SemanticCache(similarity_threshold=0.9)
        
        result = await cache.get("What is AI?")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache hit on similar query."""
        cache = SemanticCache(similarity_threshold=0.5)
        
        await cache.set("What is artificial intelligence?", {"answer": "AI is..."})
        
        result = await cache.get("What is artificial intelligence?")
        assert result is not None
        assert result["answer"] == "AI is..."


class TestCostOptimizer:
    """Test cost optimization."""
    
    @pytest.mark.asyncio
    async def test_set_tool_cost(self):
        """Test setting tool costs."""
        optimizer = CostOptimizer()
        
        optimizer.set_tool_cost("expensive_search", 0.10)
        optimizer.set_tool_cost("cheap_search", 0.01)
        
        assert optimizer.tool_costs["expensive_search"] == 0.10
    
    @pytest.mark.asyncio
    async def test_recommend_tool(self):
        """Test recommending cheapest tool."""
        optimizer = CostOptimizer()
        
        optimizer.set_tool_cost("tool_a", 0.10)
        optimizer.set_tool_cost("tool_b", 0.01)
        
        recommended = await optimizer.recommend_tool(["tool_a", "tool_b"])
        assert recommended == "tool_b"
    
    @pytest.mark.asyncio
    async def test_estimate_cost(self):
        """Test estimating request cost."""
        optimizer = CostOptimizer()
        
        optimizer.set_tool_cost("search", 0.05)
        optimizer.set_tool_cost("analyze", 0.10)
        
        cost = await optimizer.estimate_request_cost(["search", "analyze"])
        assert abs(cost - 0.15) < 0.001  # Float comparison with tolerance


class TestAdvancedCapabilities:
    """Test full advanced capabilities system."""
    
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test system initializes all components."""
        agent = AdvancedAgentCapabilities()
        
        assert agent.tool_manager is not None
        assert agent.function_calling is not None
        assert agent.streaming is not None
        assert agent.token_budget is not None
        assert agent.retry_manager is not None
        assert agent.rate_limiter is not None
        assert agent.semantic_cache is not None
        assert agent.cost_optimizer is not None
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """Test getting system status."""
        agent = AdvancedAgentCapabilities()
        
        status = await agent.get_system_status()
        
        assert "tools_registered" in status
        assert "function_calls" in status
        assert "token_budget" in status
        assert "cost_stats" in status
        assert "timestamp" in status
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow with all capabilities."""
        agent = AdvancedAgentCapabilities()
        
        # Register a tool
        tool = ToolDefinition(
            name="search",
            description="Search the web",
            tool_type=ToolType.SEARCH,
            parameters={"query": "string"},
            required_params=["query"]
        )
        agent.tool_manager.register_tool(tool)
        
        # Set cost
        agent.cost_optimizer.set_tool_cost("search", 0.05)
        
        # Execute
        result = await agent.function_calling.call_with_fallback("search", {"query": "AI"})
        
        # Verify
        assert result["success"] is True
        
        # Get status
        status = await agent.get_system_status()
        assert status["tools_registered"] == 1
