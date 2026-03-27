"""
PRADYSAGICAN v2.0 - Production-Grade Configuration Management
Implements 5-level hierarchical config merging (Gemini CLI pattern)
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum
import json
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"       # Local: unlimited, free
    GROQ = "groq"           # Free tier: 30 req/min
    OPENAI = "openai"       # Paid
    ANTHROPIC = "anthropic" # Paid
    NVIDIA = "nvidia"       # Free tier: 240 req/day
    TOGETHER = "together"   # Paid with free credits


class SafetyLevel(str, Enum):
    """Safety modes"""
    GUARDIAN = "guardian"       # Restricted mode
    SOVEREIGN = "sovereign"     # Unrestricted


class PradysagiConfig(BaseSettings):
    """
    PRADYSAGICAN v2.0 Configuration
    
    5-Level Hierarchy (in order of priority):
    1. Runtime flags (highest priority)
    2. Environment variables
    3. Workspace config (.pradysagi/config.json in project)
    4. User config (~/.pradysagi/config.json)
    5. System config (/etc/pradysagi/config.json or Windows registry)
    6. Built-in defaults (lowest priority)
    """

    # ===== SYSTEM IDENTITY =====
    name: str = Field(default="PRADYSAGICAN", description="Agent name")
    version: str = Field(default="2.0.0", description="Version")
    
    # ===== LLM CONFIGURATION =====
    primary_model: str = Field(
        default="llama2",
        description="Default model name"
    )
    primary_provider: LLMProviderType = Field(
        default=LLMProviderType.OLLAMA,
        description="Primary LLM provider"
    )
    fallback_providers: List[LLMProviderType] = Field(
        default=[LLMProviderType.GROQ, LLMProviderType.TOGETHER],
        description="Fallback provider chain"
    )
    prefer_local: bool = Field(
        default=True,
        description="Prefer Ollama if available"
    )
    
    # ===== LLM PARAMETERS =====
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096,
        ge=100,
        le=100000,
        description="Maximum tokens to generate"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    
    # ===== API KEYS (loaded from env) =====
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    nvidia_api_key: Optional[str] = Field(default=None, description="NVIDIA API key")
    together_api_key: Optional[str] = Field(default=None, description="Together API key")
    
    # ===== OLLAMA CONFIGURATION =====
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_pull_on_startup: bool = Field(
        default=True,
        description="Auto-pull model if missing"
    )
    
    # ===== TOOLS CONFIGURATION =====
    tools_enabled: List[str] = Field(
        default=["filesystem", "browser", "code_execution", "web_search"],
        description="Enabled tool categories"
    )
    max_tool_calls_per_step: int = Field(
        default=3,
        description="Max parallel tool calls"
    )
    tool_timeout_seconds: int = Field(
        default=30,
        description="Tool execution timeout"
    )
    
    # ===== MCP SERVERS =====
    mcp_servers: Dict[str, str] = Field(
        default_factory=dict,
        description="MCP servers to connect {name: url}"
    )
    
    # ===== MEMORY CONFIGURATION =====
    memory_backend: str = Field(
        default="sqlite",
        description="Memory storage backend"
    )
    memory_db_path: Path = Field(
        default_factory=lambda: Path.home() / ".pradysagi" / "memory.db",
        description="Path to memory database"
    )
    vector_db_path: Path = Field(
        default_factory=lambda: Path.home() / ".pradysagi" / "vectors",
        description="Path to vector database"
    )
    semantic_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Embedding model for semantic memory"
    )
    
    # ===== SAFETY CONFIGURATION =====
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.GUARDIAN,
        description="Safety mode (guardian/sovereign)"
    )
    enable_audit: bool = Field(
        default=True,
        description="Enable immutable audit trail"
    )
    audit_log_path: Path = Field(
        default_factory=lambda: Path.home() / ".pradysagi" / "audit.log",
        description="Audit log file path"
    )
    
    # ===== REASONING CONFIGURATION =====
    max_reasoning_steps: int = Field(
        default=20,
        description="Max steps in reasoning loop"
    )
    reasoning_timeout_seconds: int = Field(
        default=300,
        description="Max time for reasoning"
    )
    enable_tree_search: bool = Field(
        default=True,
        description="Enable tree search for complex tasks"
    )
    tree_search_depth: int = Field(
        default=3,
        description="Tree search depth"
    )
    
    # ===== OBSERVABILITY =====
    enable_telemetry: bool = Field(
        default=False,
        description="Send usage telemetry"
    )
    langfuse_public_key: Optional[str] = Field(
        default=None,
        description="Langfuse public key for observability"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG/INFO/WARNING/ERROR)"
    )
    
    # ===== DEVELOPMENT =====
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    test_mode: bool = Field(
        default=False,
        description="Test mode (no external calls)"
    )

    class Config:
        env_prefix = "PRADYSAGI_"
        env_file = ".env"
        case_sensitive = False
        
    @validator('temperature')
    def validate_temperature(cls, v):
        if not (0.0 <= v <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @classmethod
    def load_hierarchical(cls, override_config: Optional[Dict[str, Any]] = None) -> "PradysagiConfig":
        """
        Load configuration with 5-level hierarchical merging.
        
        Priority (highest to lowest):
        1. Programmatic overrides (override_config parameter)
        2. Environment variables (.env or system env)
        3. Workspace config (.pradysagi/config.json)
        4. User config (~/.pradysagi/config.json)
        5. System config (platform-specific)
        6. Built-in defaults
        """
        
        # Load .env file if exists
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        # Start with defaults
        config_data = {}
        
        # Level 5: System config
        system_configs = [
            Path("/etc/pradysagi/config.json"),  # Linux/macOS
            Path("C:\\ProgramData\\pradysagi\\config.json") if os.name == "nt" else None,  # Windows
        ]
        for path in system_configs:
            if path and path.exists():
                logger.info(f"Loading system config from {path}")
                with open(path) as f:
                    system_data = json.load(f)
                    config_data.update(system_data)
        
        # Level 4: User config
        user_config_path = Path.home() / ".pradysagi" / "config.json"
        if user_config_path.exists():
            logger.info(f"Loading user config from {user_config_path}")
            with open(user_config_path) as f:
                user_data = json.load(f)
                config_data.update(user_data)
        
        # Level 3: Workspace config
        workspace_config_path = Path.cwd() / ".pradysagi" / "config.json"
        if workspace_config_path.exists():
            logger.info(f"Loading workspace config from {workspace_config_path}")
            with open(workspace_config_path) as f:
                workspace_data = json.load(f)
                config_data.update(workspace_data)
        
        # Level 2: Environment variables (Pydantic handles this automatically)
        # Level 1: Programmatic overrides (applied after instantiation)
        
        # Create config instance
        config = cls(**config_data)
        
        # Apply programmatic overrides if provided
        if override_config:
            for key, value in override_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(f"Unknown config key: {key}")
        
        return config

    def save_to_file(self, path: Path, level: str = "user"):
        """
        Save configuration to file.
        
        Args:
            path: File path to save to
            level: Config level ("system", "user", "workspace")
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.dict(exclude_none=True)
        
        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
        
        logger.info(f"Saved {level} config to {path}")

    def get_available_providers(self) -> List[LLMProviderType]:
        """Get list of providers with API keys configured"""
        available = []
        
        # Check local first
        if self.prefer_local:
            available.append(LLMProviderType.OLLAMA)
        
        # Check for API keys
        if self.groq_api_key:
            available.append(LLMProviderType.GROQ)
        if self.openai_api_key:
            available.append(LLMProviderType.OPENAI)
        if self.anthropic_api_key:
            available.append(LLMProviderType.ANTHROPIC)
        if self.nvidia_api_key:
            available.append(LLMProviderType.NVIDIA)
        if self.together_api_key:
            available.append(LLMProviderType.TOGETHER)
        
        return available

    def get_provider_api_key(self, provider: LLMProviderType) -> Optional[str]:
        """Get API key for a specific provider"""
        if provider == LLMProviderType.GROQ:
            return self.groq_api_key
        elif provider == LLMProviderType.OPENAI:
            return self.openai_api_key
        elif provider == LLMProviderType.ANTHROPIC:
            return self.anthropic_api_key
        elif provider == LLMProviderType.NVIDIA:
            return self.nvidia_api_key
        elif provider == LLMProviderType.TOGETHER:
            return self.together_api_key
        return None


# Global config instance (lazy loaded)
_config_instance: Optional[PradysagiConfig] = None


def get_config(override: Optional[Dict[str, Any]] = None) -> PradysagiConfig:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = PradysagiConfig.load_hierarchical(override)
    return _config_instance


def reload_config(override: Optional[Dict[str, Any]] = None):
    """Reload config instance"""
    global _config_instance
    _config_instance = PradysagiConfig.load_hierarchical(override)
    return _config_instance
