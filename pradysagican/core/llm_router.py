"""
PRADYSAGICAN v2.0 - Universal LLM Router
Multi-provider support with automatic fallback and cost tracking
"""

import asyncio
import logging
import time
from typing import Optional, List
from enum import Enum
import httpx

from .config import PradysagiConfig, LLMProviderType

logger = logging.getLogger(__name__)


class LLMException(Exception):
    """Base exception for LLM operations"""
    pass


class ProviderUnavailableError(LLMException):
    """Provider is not available or not configured"""
    pass


class RateLimitError(LLMException):
    """Provider rate limit hit"""
    pass


class APIError(LLMException):
    """API call failed"""
    pass


class TimeoutError(LLMException):
    """API call timed out"""
    pass


class AllProvidersFailedError(LLMException):
    """All configured providers failed"""
    pass


class CostTracker:
    """Track and report LLM costs across providers"""
    
    def __init__(self):
        self.calls = {}  # {provider: {model: [costs]}}
        self.total_cost = 0.0
        
    def record(self, provider: str, model: str, input_tokens: int, output_tokens: int, cost: float):
        """Record a single call"""
        if provider not in self.calls:
            self.calls[provider] = {}
        if model not in self.calls[provider]:
            self.calls[provider][model] = []
        
        self.calls[provider][model].append({
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
            'timestamp': time.time()
        })
        self.total_cost += cost
        
        logger.debug(f"Recorded: {provider}/{model} - ${cost:.6f} ({input_tokens} in, {output_tokens} out)")
    
    def get_summary(self) -> dict:
        """Get cost summary"""
        summary = {
            'total_cost': self.total_cost,
            'total_calls': sum(len(v) for provider in self.calls.values() for v in provider.values()),
            'by_provider': {}
        }
        
        for provider, models in self.calls.items():
            provider_cost = sum(call['cost'] for model in models.values() for call in model)
            summary['by_provider'][provider] = {
                'calls': sum(len(calls) for calls in models.values()),
                'cost': provider_cost
            }
        
        return summary


class RateLimiter:
    """Track rate limits per provider"""
    
    LIMITS = {
        LLMProviderType.GROQ: {'requests': 30, 'window': 60},      # 30 req/min
        LLMProviderType.NVIDIA: {'requests': 240, 'window': 86400}, # 240 req/day
        LLMProviderType.TOGETHER: {'requests': 1000, 'window': 3600}, # 1000 req/hour
        LLMProviderType.OLLAMA: {'requests': 10000, 'window': 60},  # Very permissive
    }
    
    def __init__(self):
        self.calls = {}  # {provider: [timestamps]}
    
    def can_call(self, provider: LLMProviderType) -> bool:
        """Check if provider can be called within rate limit"""
        if provider not in self.LIMITS:
            return True  # No limit
        
        limit = self.LIMITS[provider]
        now = time.time()
        
        if provider not in self.calls:
            self.calls[provider] = []
        
        # Remove old calls outside window
        self.calls[provider] = [
            t for t in self.calls[provider] 
            if now - t < limit['window']
        ]
        
        # Check if we can make another call
        can_call = len(self.calls[provider]) < limit['requests']
        
        if not can_call:
            remaining_wait = limit['window'] - (now - self.calls[provider][0])
            logger.warning(
                f"{provider.value}: Rate limit approaching. "
                f"Calls: {len(self.calls[provider])}/{limit['requests']}, "
                f"Reset in {remaining_wait:.1f}s"
            )
        
        return can_call
    
    def record_call(self, provider: LLMProviderType):
        """Record a call for rate limiting"""
        if provider not in self.calls:
            self.calls[provider] = []
        self.calls[provider].append(time.time())


class UniversalLLMRouter:
    """
    Route LLM requests to best available provider with automatic fallback.
    
    Supports:
    - Ollama (local, unlimited)
    - Groq (free tier)
    - OpenAI
    - Anthropic
    - NVIDIA NIM
    - Together AI
    """
    
    def __init__(self, config: PradysagiConfig):
        self.config = config
        self.cost_tracker = CostTracker()
        self.rate_limiter = RateLimiter()
        self.fallback_chain = self._build_fallback_chain()
        self.http_client = None
        
        logger.info(f"Initialized LLM router with providers: {[p.value for p in self.fallback_chain]}")
    
    def _build_fallback_chain(self) -> List[LLMProviderType]:
        """Build provider priority chain"""
        chain = []
        
        # Prefer local if enabled
        if self.config.prefer_local:
            chain.append(LLMProviderType.OLLAMA)
        
        # Add primary
        if self.config.primary_provider not in chain:
            chain.append(self.config.primary_provider)
        
        # Add configured fallbacks
        for provider in self.config.fallback_providers:
            if provider not in chain:
                chain.append(provider)
        
        # Add any available with API keys
        for provider in LLMProviderType:
            if provider not in chain:
                api_key = self.config.get_provider_api_key(provider)
                if api_key:
                    chain.append(provider)
        
        return chain
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Get LLM completion with automatic provider fallback.
        
        Args:
            prompt: User prompt
            model: Specific model to use (defaults to config primary)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            system_prompt: System context
        
        Returns:
            LLM response text
        
        Raises:
            AllProvidersFailedError: If all providers fail
        """
        
        model = model or self.config.primary_model
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        last_error = None
        
        for provider in self.fallback_chain:
            try:
                # Check rate limit
                if not self.rate_limiter.can_call(provider):
                    logger.debug(f"{provider.value}: Rate limited, trying next provider")
                    continue
                
                # Call provider
                logger.debug(f"Calling {provider.value} with model {model}")
                start_time = time.time()
                
                response = await self._call_provider(
                    provider=provider,
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                )
                
                duration = time.time() - start_time
                self.rate_limiter.record_call(provider)
                
                # Track cost
                input_tokens = len(prompt.split())
                output_tokens = len(response.split())
                cost = self._estimate_cost(provider, model, input_tokens, output_tokens)
                self.cost_tracker.record(provider.value, model, input_tokens, output_tokens, cost)
                
                logger.info(
                    f"✓ {provider.value}/{model} completed in {duration:.2f}s "
                    f"({input_tokens} in, {output_tokens} out, ${cost:.6f})"
                )
                
                return response
                
            except RateLimitError as e:
                logger.warning(f"{provider.value}: Rate limit hit - {e}")
                last_error = e
                await asyncio.sleep(1)  # Wait before trying next
                continue
                
            except ProviderUnavailableError as e:
                logger.warning(f"{provider.value}: Unavailable - {e}")
                last_error = e
                continue
                
            except APIError as e:
                logger.warning(f"{provider.value}: API error - {e}")
                last_error = e
                continue
                
            except TimeoutError as e:
                logger.warning(f"{provider.value}: Timeout - {e}")
                last_error = e
                continue
                
            except Exception as e:
                logger.warning(f"{provider.value}: Unexpected error - {type(e).__name__}: {e}")
                last_error = e
                continue
        
        # All providers exhausted
        raise AllProvidersFailedError(
            f"All LLM providers exhausted. Tried: {[p.value for p in self.fallback_chain]}. "
            f"Last error: {last_error}"
        )
    
    async def _call_provider(
        self,
        provider: LLMProviderType,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str],
    ) -> str:
        """Call specific provider"""
        
        if provider == LLMProviderType.OLLAMA:
            return await self._call_ollama(model, prompt, temperature, max_tokens, system_prompt)
        elif provider == LLMProviderType.GROQ:
            return await self._call_groq(model, prompt, temperature, max_tokens, system_prompt)
        elif provider == LLMProviderType.OPENAI:
            return await self._call_openai(model, prompt, temperature, max_tokens, system_prompt)
        elif provider == LLMProviderType.ANTHROPIC:
            return await self._call_anthropic(model, prompt, temperature, max_tokens, system_prompt)
        elif provider == LLMProviderType.NVIDIA:
            return await self._call_nvidia(model, prompt, temperature, max_tokens, system_prompt)
        elif provider == LLMProviderType.TOGETHER:
            return await self._call_together(model, prompt, temperature, max_tokens, system_prompt)
        else:
            raise ProviderUnavailableError(f"Unknown provider: {provider}")
    
    async def _call_ollama(
        self, model: str, prompt: str, temperature: float, max_tokens: int, system_prompt: Optional[str]
    ) -> str:
        """Call Ollama (local LLM)"""
        try:
            # Use ollama Python library
            import ollama
            
            # Build full prompt with system
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await asyncio.to_thread(
                ollama.generate,
                model=model,
                prompt=full_prompt,
                temperature=temperature,
                num_predict=max_tokens,
                stream=False,
            )
            
            return response.get('response', '').strip()
            
        except Exception as e:
            raise ProviderUnavailableError(f"Ollama error: {e}")
    
    async def _call_groq(
        self, model: str, prompt: str, temperature: float, max_tokens: int, system_prompt: Optional[str]
    ) -> str:
        """Call Groq API"""
        try:
            from groq import Groq
            
            client = Groq(api_key=self.config.groq_api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"Groq rate limit: {e}")
            raise APIError(f"Groq API error: {e}")
    
    async def _call_openai(
        self, model: str, prompt: str, temperature: float, max_tokens: int, system_prompt: Optional[str]
    ) -> str:
        """Call OpenAI API"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.openai_api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"OpenAI rate limit: {e}")
            raise APIError(f"OpenAI API error: {e}")
    
    async def _call_anthropic(
        self, model: str, prompt: str, temperature: float, max_tokens: int, system_prompt: Optional[str]
    ) -> str:
        """Call Anthropic Claude API"""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.config.anthropic_api_key)
            
            response = await asyncio.to_thread(
                client.messages.create,
                model=model,
                max_tokens=max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"Anthropic rate limit: {e}")
            raise APIError(f"Anthropic API error: {e}")
    
    async def _call_nvidia(
        self, model: str, prompt: str, temperature: float, max_tokens: int, system_prompt: Optional[str]
    ) -> str:
        """Call NVIDIA NIM API"""
        try:
            # NVIDIA NIM uses OpenAI-compatible API
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                api_key=self.config.nvidia_api_key,
                base_url="https://integrate.api.nvidia.com/v1",
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"NVIDIA rate limit: {e}")
            raise APIError(f"NVIDIA API error: {e}")
    
    async def _call_together(
        self, model: str, prompt: str, temperature: float, max_tokens: int, system_prompt: Optional[str]
    ) -> str:
        """Call Together AI API"""
        try:
            from together import Together
            
            client = Together(api_key=self.config.together_api_key)
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"Together rate limit: {e}")
            raise APIError(f"Together API error: {e}")
    
    def _estimate_cost(self, provider: LLMProviderType, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a single API call"""
        # Approximate costs (in USD)
        costs = {
            LLMProviderType.GROQ: {'input': 0, 'output': 0},  # Groq is free
            LLMProviderType.OLLAMA: {'input': 0, 'output': 0},  # Local, free
            LLMProviderType.OPENAI: {
                'gpt-4': {'input': 0.00003, 'output': 0.00006},
                'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
            },
            LLMProviderType.ANTHROPIC: {
                'claude-3-opus': {'input': 0.000015, 'output': 0.000075},
                'claude-3-sonnet': {'input': 0.000003, 'output': 0.000015},
            },
            LLMProviderType.NVIDIA: {'input': 0, 'output': 0},  # Free tier
            LLMProviderType.TOGETHER: {'input': 0.0000008, 'output': 0.0000008},
        }
        
        provider_costs = costs.get(provider, {'input': 0, 'output': 0})
        
        if isinstance(provider_costs, dict) and 'input' in provider_costs:
            input_cost = provider_costs['input']
            output_cost = provider_costs['output']
        else:
            # Model-specific pricing
            model_costs = provider_costs.get(model, {'input': 0, 'output': 0})
            input_cost = model_costs.get('input', 0)
            output_cost = model_costs.get('output', 0)
        
        total = (input_tokens * input_cost) + (output_tokens * output_cost)
        return max(0, total)
    
    async def close(self):
        """Cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()
