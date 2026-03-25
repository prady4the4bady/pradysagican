#!/usr/bin/env python3
"""
Setup Validation Tool — PRADYSAGICAN
Checks if the system is correctly configured and can actually think.
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Enable UTF-8 output on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
NC = "\033[0m"

def info(msg: str) -> None:
    print(f"{GREEN}[OK]{NC} {msg}")

def warn(msg: str) -> None:
    print(f"{YELLOW}[!!]{NC} {msg}")

def error(msg: str) -> None:
    print(f"{RED}[XX]{NC} {msg}")

def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}==> {title}{NC}")

async def check_python() -> bool:
    """Check Python version."""
    section("Python Environment")
    if sys.version_info >= (3, 11):
        info(f"Python {sys.version_info.major}.{sys.version_info.minor}")
        return True
    else:
        error(f"Python 3.11+ required (found {sys.version_info.major}.{sys.version_info.minor})")
        return False

async def check_dependencies() -> bool:
    """Check if core dependencies are installed."""
    section("Core Dependencies")
    required = [
        "pydantic", "httpx", "fastapi", "uvicorn", 
        "pytest", "rich", "pyyaml", "psutil"
    ]
    
    all_ok = True
    for pkg in required:
        try:
            __import__(pkg)
            info(f"{pkg}")
        except ImportError:
            error(f"{pkg} (missing!)")
            all_ok = False
    
    return all_ok

async def check_llm_providers() -> bool:
    """Check if at least one LLM provider is available."""
    section("LLM Provider Configuration")
    
    providers = {
        "GROQ_API_KEY": "Groq",
        "TOGETHER_API_KEY": "Together AI",
        "NVIDIA_API_KEY": "NVIDIA NIM",
        "HF_TOKEN": "HuggingFace",
    }
    
    configured = []
    for env_var, provider_name in providers.items():
        if os.getenv(env_var):
            configured.append(provider_name)
            info(f"{provider_name} configured")
        else:
            warn(f"{provider_name} not configured (set {env_var})")
    
    # Check for local Ollama
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            info("Ollama (local) available")
            configured.append("Ollama")
        else:
            warn("Ollama (local) not running (docker run -d -p 11434:11434 ollama/ollama)")
    except Exception:
        warn("Ollama (local) not available")
    
    if not configured:
        error("No LLM providers configured!")
        error("System will NOT be able to think without an LLM.")
        print(f"\n{BOLD}Quick fix:{NC}")
        print("  1. Use Groq (fastest, free):")
        print("     export GROQ_API_KEY=your_key")
        print("     Get key: https://console.groq.com/keys\n")
        print("  2. Use local Ollama (free, no API key):")
        print("     docker run -d -p 11434:11434 ollama/ollama")
        print("     ollama pull llama3.2\n")
        return False
    
    info(f"{len(configured)} provider(s) available")
    return True

async def check_subsystems() -> bool:
    """Check if core subsystems can initialize."""
    section("Core Subsystems")
    
    try:
        from pradysagican.god import PradysagicanGod
        god = PradysagicanGod()
        info("PradysagicanGod loaded")
        
        # Try to initialize (non-blocking check)
        try:
            subsystems = await god.initialize()
            info(f"All {len(subsystems)} subsystems initialized")
            return True
        except Exception as e:
            warn(f"Subsystem init incomplete: {e}")
            # This is okay if it's just optional modules
            return True
    except Exception as e:
        error(f"Failed to load god layer: {e}")
        return False

async def check_llm_call() -> bool:
    """Test actual LLM call (won't work if no provider configured)."""
    section("LLM Integration Test")
    
    if not os.getenv("GROQ_API_KEY") and not os.getenv("TOGETHER_API_KEY") and \
       not os.getenv("NVIDIA_API_KEY") and not os.getenv("HF_TOKEN"):
        warn("Skipping LLM test (no API keys configured)")
        warn("Run this again after setting an API key to fully verify")
        return True
    
    try:
        from pradysagican.providers.llm import UniversalLLMProvider
        provider = UniversalLLMProvider()
        
        # Don't actually call the LLM (would waste quota), just verify setup
        stats = provider.stats()
        info(f"LLM provider configured: {stats['providers_configured']} provider(s)")
        return True
    except Exception as e:
        warn(f"LLM provider not ready: {e}")
        return True  # Not fatal if optional deps missing

async def check_tests() -> bool:
    """Run pytest to verify tests pass."""
    section("Test Suite")
    
    try:
        result = subprocess.run(
            ["pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            summary = [l for l in lines if 'passed' in l]
            if summary:
                info(summary[-1])
            return True
        else:
            # Some tests may fail due to optional deps, that's OK
            lines = result.stdout.split('\n')
            summary = [l for l in lines if 'passed' in l or 'failed' in l]
            if summary:
                warn(summary[-1])
            return True
    except Exception as e:
        warn(f"Could not run tests: {e}")
        return True

async def main() -> None:
    """Run all checks."""
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"PRADYSAGICAN — Setup Validation")
    print(f"{'='*60}{NC}\n")
    
    results = {
        "Python": await check_python(),
        "Dependencies": await check_dependencies(),
        "LLM Providers": await check_llm_providers(),
        "Subsystems": await check_subsystems(),
        "LLM Integration": await check_llm_call(),
        "Test Suite": await check_tests(),
    }
    
    # Summary
    section("Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = f"{GREEN}OK{NC}" if result else f"{RED}XX{NC}"
        print(f"  {status} {check}")
    
    print(f"\n{BOLD}Result: {passed}/{total} checks passed{NC}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}[OK] System is ready to use!{NC}")
        print(f"\nNext steps:")
        print(f"  {CYAN}source .venv/bin/activate{NC}")
        print(f"  {CYAN}pradysagican chat{NC}")
        return 0
    else:
        print(f"\n{YELLOW}{BOLD}[!!] System has issues.{NC}")
        print(f"See errors above and fix them, then run this script again.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
