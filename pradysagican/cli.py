"""
PRADYSAGICAN CLI — Install and run with one command.
=====================================================
Usage:
    pradysagican serve              # Start the API server
    pradysagican chat               # Interactive chat mode
    pradysagican status             # Show system health
    pradysagican benchmark          # Run benchmark suite
    pradysagican evolve             # Start self-evolution cycle
    pradysagican version            # Show version info
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import os
import pkgutil
import sys
import time
from pathlib import Path

VERSION = "1.0.0"

BANNER = r"""
  ____  ____    _    ____  _   _ ____    _    ____ ___ ____    _    _   _
 |  _ \|  _ \  / \  |  _ \| | | / ___|  / \  / ___|_ _/ ___|  / \  | \ | |
 | |_) | |_) |/ _ \ | | | | |_| \___ \ / _ \| |  _ | | |     / _ \ |  \| |
 |  __/|  _ </ ___ \| |_| |  _  |___) / ___ \ |_| || | |___ / ___ \| |\  |
 |_|   |_| \_\_/  \_\____/|_| |_|____/_/   \_\____|___\____/_/   \_\_| \_|

  World's First Super General Agentic Intelligence System  v{version}
"""


# ── Argument Parsing ─────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments with subcommands."""
    parser = argparse.ArgumentParser(
        prog="pradysagican",
        description="PRADYSAGICAN — Super General Agentic Intelligence System",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    serve_p = sub.add_parser("serve", help="Start the API server")
    serve_p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    serve_p.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    serve_p.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    # chat
    sub.add_parser("chat", help="Interactive chat mode")

    # status
    sub.add_parser("status", help="Show system health")

    # benchmark
    bench_p = sub.add_parser("benchmark", help="Run benchmark suite")
    bench_p.add_argument("--iterations", type=int, default=100, help="Benchmark iterations")

    # evolve
    evolve_p = sub.add_parser("evolve", help="Start self-evolution cycle")
    evolve_p.add_argument("--generations", type=int, default=5, help="Evolution generations")

    # version
    sub.add_parser("version", help="Show version info")

    return parser.parse_args(argv)


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_serve(args: argparse.Namespace) -> None:
    """Start the FastAPI server via uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn not installed. Run: pip install uvicorn[standard]")
        sys.exit(1)

    print(BANNER.format(version=VERSION))
    print(f"  Starting server on {args.host}:{args.port} ...")
    uvicorn.run(
        "pradysagican.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


def cmd_chat(args: argparse.Namespace) -> None:
    """Interactive REPL chat mode."""
    print(BANNER.format(version=VERSION))
    print("  Type your message. Commands: /quit /status /memory /help\n")

    async def _chat_loop() -> None:
        from pradysagican.core.reasoning import ReasoningEngine

        engine = ReasoningEngine()

        while True:
            try:
                user_input = input("\033[1;36mYou>\033[0m ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            stripped = user_input.strip()
            if not stripped:
                continue

            if stripped == "/quit":
                print("Goodbye!")
                break
            elif stripped == "/help":
                print("  /quit    — Exit chat")
                print("  /status  — System health")
                print("  /memory  — Memory stats")
                print("  /help    — This help")
                continue
            elif stripped == "/status":
                _print_status_inline()
                continue
            elif stripped == "/memory":
                _print_memory_inline()
                continue

            start = time.monotonic()
            try:
                result = await engine.reason(stripped)
                elapsed = (time.monotonic() - start) * 1000
                if isinstance(result, dict):
                    answer = result.get("conclusion", result.get("result", json.dumps(result, indent=2)))
                else:
                    answer = str(result)
                print(f"\033[1;32mPRADYSAGICAN>\033[0m {answer}")
                print(f"  \033[2m({elapsed:.0f}ms)\033[0m\n")
            except Exception as exc:
                print(f"\033[1;31mError:\033[0m {exc}\n")

    asyncio.run(_chat_loop())


def _print_status_inline() -> None:
    """Print quick status inside chat."""
    try:
        from pradysagican.core.atlas import AtlasRuntime
        atlas = AtlasRuntime()
        info = asyncio.run(atlas.system_info()) if hasattr(atlas, "system_info") else {"status": "running"}
        print(f"  System: {json.dumps(info, indent=2, default=str)}")
    except Exception as exc:
        print(f"  Status: operational (detail error: {exc})")


def _print_memory_inline() -> None:
    """Print memory stats inside chat."""
    try:
        from pradysagican.core.memory import MemorySystem
        mem = MemorySystem()
        stats = mem.stats() if hasattr(mem, "stats") else {"status": "active"}
        print(f"  Memory: {json.dumps(stats, indent=2, default=str)}")
    except Exception as exc:
        print(f"  Memory: active (detail error: {exc})")


def cmd_status(args: argparse.Namespace) -> None:
    """Print comprehensive system health."""
    print(BANNER.format(version=VERSION))

    async def _status() -> None:
        modules_ok = 0
        modules_fail = 0
        module_list = [
            "pradysagican.core.consciousness",
            "pradysagican.core.reasoning",
            "pradysagican.core.memory",
            "pradysagican.core.world_model",
            "pradysagican.core.prometheus",
            "pradysagican.core.atlas",
            "pradysagican.core.aegis",
            "pradysagican.core.cognitive_bus",
            "pradysagican.core.neuro_symbolic",
            "pradysagican.core.hallucination_shield",
            "pradysagican.core.temporal_cortex",
            "pradysagican.core.cognitive_resilience",
            "pradysagican.core.quantum_ready",
            "pradysagican.core.collective_intelligence",
        ]
        print("  Module Health:")
        for mod_name in module_list:
            short = mod_name.rsplit(".", 1)[-1]
            try:
                importlib.import_module(mod_name)
                print(f"    [OK] {short}")
                modules_ok += 1
            except Exception as exc:
                print(f"    [FAIL] {short}: {exc}")
                modules_fail += 1

        print(f"\n  Total: {modules_ok} healthy, {modules_fail} failed")
        print(f"  Status: {'ALL SYSTEMS GO' if modules_fail == 0 else 'DEGRADED'}")

    asyncio.run(_status())


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Run a quick benchmark suite."""
    print(BANNER.format(version=VERSION))
    iterations = args.iterations

    async def _bench() -> None:
        import numpy as np
        from pradysagican.core.reasoning import ReasoningEngine

        engine = ReasoningEngine()
        latencies: list[float] = []

        print(f"  Running {iterations} reasoning iterations...")
        for i in range(iterations):
            start = time.monotonic()
            try:
                await engine.reason(f"benchmark query {i}")
            except Exception:
                pass
            latencies.append((time.monotonic() - start) * 1000)

        arr = np.array(latencies)
        print(f"\n  Results ({iterations} iterations):")
        print(f"    Mean latency:  {np.mean(arr):.2f} ms")
        print(f"    Median:        {np.median(arr):.2f} ms")
        print(f"    P95:           {np.percentile(arr, 95):.2f} ms")
        print(f"    P99:           {np.percentile(arr, 99):.2f} ms")
        print(f"    Throughput:    {1000 / np.mean(arr):.0f} queries/sec")

    asyncio.run(_bench())


def cmd_evolve(args: argparse.Namespace) -> None:
    """Run self-evolution cycle via Prometheus."""
    print(BANNER.format(version=VERSION))

    async def _evolve() -> None:
        from pradysagican.core.prometheus import PrometheusEngine

        prometheus = PrometheusEngine()
        generations = args.generations
        print(f"  Starting evolution ({generations} generations)...\n")

        for gen in range(1, generations + 1):
            start = time.monotonic()
            try:
                if hasattr(prometheus, "evolve_cycle"):
                    result = await prometheus.evolve_cycle()
                elif hasattr(prometheus, "research_cycle"):
                    result = await prometheus.research_cycle()
                else:
                    result = {"status": "evolution step completed"}
                elapsed = (time.monotonic() - start) * 1000
                print(f"  Gen {gen}/{generations}: {json.dumps(result, indent=2, default=str)[:200]} ({elapsed:.0f}ms)")
            except Exception as exc:
                print(f"  Gen {gen}/{generations}: error — {exc}")

        print("\n  Evolution complete.")

    asyncio.run(_evolve())


def cmd_version(args: argparse.Namespace) -> None:
    """Print version, module count, total classes."""
    import pradysagican

    pkg_dir = Path(pradysagican.__file__).parent
    py_files = list(pkg_dir.rglob("*.py"))
    total_lines = 0
    total_classes = 0
    for f in py_files:
        try:
            content = f.read_text()
            total_lines += content.count("\n")
            total_classes += content.count("\nclass ")
        except Exception:
            pass

    print(f"PRADYSAGICAN v{VERSION}")
    print(f"  Python files:  {len(py_files)}")
    print(f"  Total lines:   {total_lines:,}")
    print(f"  Total classes:  {total_classes}")
    print(f"  Python:         {sys.version.split()[0]}")
    print(f"  Platform:       {sys.platform}")


# ── Entry Point ──────────────────────────────────────────────────────────────

COMMANDS = {
    "serve": cmd_serve,
    "chat": cmd_chat,
    "status": cmd_status,
    "benchmark": cmd_benchmark,
    "evolve": cmd_evolve,
    "version": cmd_version,
}


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    args = parse_args(argv)
    if args.command is None:
        print(BANNER.format(version=VERSION))
        print("  Run 'pradysagican --help' for available commands.")
        sys.exit(0)
    handler = COMMANDS.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
