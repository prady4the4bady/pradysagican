#!/usr/bin/env python3
"""
PRADYSAGI Complete System - Core Model Router
Routes requests to best available model (local or cloud)
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Supported model types"""
    CLAUDE = "claude"
    GPT = "gpt"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    KIMI = "kimi"
    COHERE = "cohere"
    TOGETHER = "together"


class ModelMode(str, Enum):
    """Execution mode"""
    LOCAL = "local"
    CLOUD = "cloud"
    AUTO = "auto"


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    type: ModelType
    mode: ModelMode
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    enabled: bool = True


class LLMBackend(ABC):
    """Abstract base class for LLM backends"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs):
        """Stream response from prompt"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get backend status"""
        pass


class LocalClaudeBackend(LLMBackend):
    """Local Claude via Ollama"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = "claude-local"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with local Claude"""
        try:
            import ollama
            response = await asyncio.to_thread(
                ollama.generate,
                model='mistral',  # Fallback
                prompt=prompt,
                **kwargs
            )
            return response['response']
        except Exception as e:
            logger.error(f"Local Claude error: {e}")
            raise
    
    async def stream(self, prompt: str, **kwargs):
        """Stream local Claude response"""
        try:
            import ollama
            stream = await asyncio.to_thread(
                ollama.generate,
                model='mistral',
                prompt=prompt,
                stream=True,
                **kwargs
            )
            for chunk in stream:
                yield chunk['response']
        except Exception as e:
            logger.error(f"Local Claude stream error: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Check if local Claude is available"""
        try:
            import ollama
            tags = await asyncio.to_thread(ollama.list)
            available = any('mistral' in m.model for m in tags.models)
            return {
                'available': available,
                'status': 'running' if available else 'offline'
            }
        except Exception as e:
            logger.warning(f"Local Claude unavailable: {e}")
            return {'available': False, 'status': 'offline'}


class DeepSeekBackend(LLMBackend):
    """DeepSeek local backend"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = "deepseek"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with DeepSeek"""
        try:
            import ollama
            response = await asyncio.to_thread(
                ollama.generate,
                model='deepseek-coder',
                prompt=prompt,
                **kwargs
            )
            return response['response']
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            raise
    
    async def stream(self, prompt: str, **kwargs):
        """Stream DeepSeek response"""
        try:
            import ollama
            stream = await asyncio.to_thread(
                ollama.generate,
                model='deepseek-coder',
                prompt=prompt,
                stream=True,
                **kwargs
            )
            for chunk in stream:
                yield chunk['response']
        except Exception as e:
            logger.error(f"DeepSeek stream error: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Check DeepSeek availability"""
        try:
            import ollama
            tags = await asyncio.to_thread(ollama.list)
            available = any('deepseek' in m.model for m in tags.models)
            return {
                'available': available,
                'status': 'running' if available else 'offline'
            }
        except Exception as e:
            logger.warning(f"DeepSeek unavailable: {e}")
            return {'available': False, 'status': 'offline'}


class OpenAIBackend(LLMBackend):
    """OpenAI cloud backend"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = "openai"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with OpenAI"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.config.api_key)
            response = await client.chat.completions.create(
                model='gpt-4',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
    
    async def stream(self, prompt: str, **kwargs):
        """Stream OpenAI response"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.config.api_key)
            stream = await client.chat.completions.create(
                model='gpt-4',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Check OpenAI API status"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.config.api_key)
            # Quick health check
            await client.chat.completions.create(
                model='gpt-4',
                messages=[{'role': 'user', 'content': 'ping'}],
                max_tokens=1
            )
            return {'available': True, 'status': 'active'}
        except Exception as e:
            logger.warning(f"OpenAI unavailable: {e}")
            return {'available': False, 'status': 'offline'}


class AnthropicBackend(LLMBackend):
    """Anthropic Claude cloud backend"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = "anthropic"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with Claude (Anthropic)"""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.config.api_key)
            message = await client.messages.create(
                model='claude-3-opus-20240229',
                max_tokens=self.config.max_tokens,
                messages=[{'role': 'user', 'content': prompt}],
                **kwargs
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
    
    async def stream(self, prompt: str, **kwargs):
        """Stream Claude response"""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.config.api_key)
            async with client.messages.stream(
                model='claude-3-opus-20240229',
                max_tokens=self.config.max_tokens,
                messages=[{'role': 'user', 'content': prompt}],
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Check Anthropic API status"""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.config.api_key)
            # Quick health check
            await client.messages.create(
                model='claude-3-opus-20240229',
                max_tokens=1,
                messages=[{'role': 'user', 'content': 'ping'}]
            )
            return {'available': True, 'status': 'active'}
        except Exception as e:
            logger.warning(f"Anthropic unavailable: {e}")
            return {'available': False, 'status': 'offline'}


class ModelRouter:
    """Route requests to best available model"""
    
    def __init__(self):
        self.backends: Dict[str, LLMBackend] = {}
        self.configs: Dict[str, ModelConfig] = {}
        self.preference_order = [
            'claude-local',
            'deepseek',
            'anthropic',
            'openai'
        ]
    
    def register_model(self, config: ModelConfig):
        """Register a model backend"""
        backend = self._create_backend(config)
        self.backends[config.name] = backend
        self.configs[config.name] = config
        logger.info(f"Registered model: {config.name}")
    
    def _create_backend(self, config: ModelConfig) -> LLMBackend:
        """Create appropriate backend for config"""
        if config.type == ModelType.CLAUDE and config.mode == ModelMode.LOCAL:
            return LocalClaudeBackend(config)
        elif config.type == ModelType.DEEPSEEK and config.mode == ModelMode.LOCAL:
            return DeepSeekBackend(config)
        elif config.type == ModelType.GPT:
            return OpenAIBackend(config)
        elif config.type == ModelType.CLAUDE and config.mode == ModelMode.CLOUD:
            return AnthropicBackend(config)
        else:
            raise ValueError(f"Unsupported model config: {config}")
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        available = []
        for name, backend in self.backends.items():
            status = await backend.get_status()
            if status['available']:
                available.append(name)
        return available
    
    async def select_best_model(self, mode: ModelMode = ModelMode.AUTO) -> Optional[str]:
        """Select best model based on availability and preference"""
        available = await self.get_available_models()
        
        if not available:
            logger.warning("No models available")
            return None
        
        if mode == ModelMode.LOCAL:
            for model in self.preference_order:
                if model in available and self.configs[model].mode == ModelMode.LOCAL:
                    return model
            return None
        
        if mode == ModelMode.CLOUD:
            for model in self.preference_order:
                if model in available and self.configs[model].mode == ModelMode.CLOUD:
                    return model
            return None
        
        # AUTO: prefer local, then cloud
        for model in self.preference_order:
            if model in available:
                return model
        
        return available[0] if available else None
    
    async def generate(self, prompt: str, model: Optional[str] = None, mode: ModelMode = ModelMode.AUTO, **kwargs) -> str:
        """Generate response using best available model"""
        if not model:
            model = await self.select_best_model(mode)
        
        if not model:
            raise ValueError("No models available")
        
        backend = self.backends.get(model)
        if not backend:
            raise ValueError(f"Unknown model: {model}")
        
        logger.info(f"Generating with model: {model}")
        return await backend.generate(prompt, **kwargs)
    
    async def stream(self, prompt: str, model: Optional[str] = None, mode: ModelMode = ModelMode.AUTO, **kwargs):
        """Stream response using best available model"""
        if not model:
            model = await self.select_best_model(mode)
        
        if not model:
            raise ValueError("No models available")
        
        backend = self.backends.get(model)
        if not backend:
            raise ValueError(f"Unknown model: {model}")
        
        logger.info(f"Streaming with model: {model}")
        async for chunk in backend.stream(prompt, **kwargs):
            yield chunk
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {}
        for name, backend in self.backends.items():
            status[name] = await backend.get_status()
        return status


# Global instance
model_router = ModelRouter()


async def initialize_models(config: Dict[str, Any]):
    """Initialize available models from config"""
    
    # Local models (always available if Ollama installed)
    if config.get('local_models', True):
        model_router.register_model(ModelConfig(
            name='claude-local',
            type=ModelType.CLAUDE,
            mode=ModelMode.LOCAL
        ))
        model_router.register_model(ModelConfig(
            name='deepseek',
            type=ModelType.DEEPSEEK,
            mode=ModelMode.LOCAL
        ))
    
    # Cloud models (if API keys provided)
    if openai_key := config.get('OPENAI_API_KEY'):
        model_router.register_model(ModelConfig(
            name='gpt-4',
            type=ModelType.GPT,
            mode=ModelMode.CLOUD,
            api_key=openai_key
        ))
    
    if anthropic_key := config.get('ANTHROPIC_API_KEY'):
        model_router.register_model(ModelConfig(
            name='claude-cloud',
            type=ModelType.CLAUDE,
            mode=ModelMode.CLOUD,
            api_key=anthropic_key
        ))
    
    available = await model_router.get_available_models()
    logger.info(f"Initialized {len(available)} models: {available}")


# Demo
if __name__ == "__main__":
    async def demo():
        import os
        
        config = {
            'local_models': True,
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        }
        
        await initialize_models(config)
        
        # Check status
        status = await model_router.get_status()
        print(f"\nModel Status:\n{status}\n")
        
        # Select best model
        best = await model_router.select_best_model()
        print(f"Best model: {best}\n")
        
        # Generate
        if best:
            response = await model_router.generate("Hello, who are you?", model=best)
            print(f"Response: {response}")
    
    asyncio.run(demo())
