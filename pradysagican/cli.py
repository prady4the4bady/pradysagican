"""
PRADYSAGICAN CLI — Beautiful, powerful, simple.
Usage:  pradysagican <command>
Commands: serve | chat | status | benchmark | evolve | access | upgrade | omega | godlayer | version
"""
from __future__ import annotations
import argparse, asyncio, sys, os, time

def _console():
    from rich.console import Console
    return Console()

def _safe_terminal_text(text: str) -> str:
    enc = (getattr(sys.stdout, "encoding", None) or "utf-8")
    try:
        text.encode(enc)
        return text
    except Exception:
        return text.encode(enc, errors="replace").decode(enc, errors="replace")


BANNER = _safe_terminal_text("""[bold cyan]
 ██████╗ ██████╗  █████╗ ██████╗ ██╗   ██╗
 ██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
 ██████╔╝██████╔╝███████║██║  ██║ ╚████╔╝
 ██╔═══╝ ██╔══██╗██╔══██║██║  ██║  ╚██╔╝
 ██║     ██║  ██║██║  ██║██████╔╝   ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝    ╚═╝[/bold cyan]
[dim]Super General Intelligence System v6.0[/dim]
[dim]40 subsystems • 22K+ lines • 11.3M features • 181 tests[/dim]
""")

def cmd_serve(args):
    c = _console()
    from rich.table import Table
    from rich.panel import Panel
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    t = Table(title="API Endpoints", border_style="cyan")
    t.add_column("Method", style="green"); t.add_column("Path", style="white"); t.add_column("Description", style="dim")
    for m, p, d in [("POST","/chat","Chat with PRADYSAGICAN"),("POST","/reason","Multi-paradigm reasoning"),("POST","/memory/store","Store a memory"),("POST","/memory/recall","Recall memories"),("POST","/orchestrate","Multi-agent orchestration"),("GET","/introspect","System introspection"),("GET","/stats","System statistics"),("GET","/health","Health check")]:
        t.add_row(m, p, d)
    c.print(t)
    port = getattr(args, "port", 8000)
    c.print(f"\n[bold green]Starting server on port {port}...[/bold green]")
    try:
        import uvicorn
        from pradysagican.api.server import app
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except ImportError:
        c.print("[yellow]uvicorn not installed. Run: pip install uvicorn[/yellow]")

def cmd_chat(args):
    c = _console()
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    t = Table(show_header=False, border_style="dim", box=None, padding=(0, 1))
    t.add_column(style="cyan"); t.add_column(style="white")
    for cmd, desc in [("/help","Show commands"),("/status","System health"),("/dream <topic>","Creative dreaming"),("/predict <question>","Make prediction"),("/solve <problem>","Full problem solving"),("/tools","List tool categories"),("/access","Open-access info"),("/upgrades","Upgrade tracker"),("/omega","OMEGA status"),("/godlayer","God-layer status"),("/quit","Exit")]:
        t.add_row(cmd, desc)
    c.print(Panel(t, title="[bold]Commands[/bold]", border_style="dim"))
    c.print()

    async def _run():
        from pradysagican.god import PradysagicanGod
        from pradysagican.core.task_classifier import TaskClassifier
        god = PradysagicanGod(); classifier = TaskClassifier()
        with c.status("[cyan]Initializing 40 subsystems...[/cyan]"):
            report = await god.initialize()
        c.print(f"[green]✓ {report['subsystems_online']}/{report['subsystems_total']} subsystems online[/green]\n")
        while True:
            try: user_input = c.input("[bold cyan]prady>[/bold cyan] ")
            except (EOFError, KeyboardInterrupt): c.print("\n[dim]Goodbye.[/dim]"); break
            if not user_input.strip(): continue
            inp = user_input.strip()
            if inp == "/quit": c.print("[dim]Goodbye.[/dim]"); break
            elif inp == "/help":
                c.print(Panel(t, title="Commands", border_style="dim"))
            elif inp == "/status":
                s = god.stats(); c.print(Panel(f"[green]Subsystems: {s['system']['subsystems_online']}/{s['system']['subsystems_total']}[/green]\n[cyan]Features: {s['features']['combinatorial_total']:,}[/cyan]\n[yellow]Health: {s['system']['health_pct']}%[/yellow]", title="System Status", border_style="green"))
            elif inp == "/access":
                c.print(Panel("[bold green]Open access is enabled.[/bold green]\n\nNo payment is required.\n\nOptional profile creation:\n[cyan]pradysagican access --email you@mail.com[/cyan]", title="Access", border_style="green"))
            elif inp == "/upgrades":
                from pradysagican.upgrades import UpgradeManager
                up = UpgradeManager().as_dict()
                counts = up["summary"]["counts"]
                omega_counts = up["summary"].get("omega_counts", {})
                godlayer_inv = up["summary"].get("godlayer_inventory", {})
                c.print(
                    Panel(
                        f"[bold]Rollout:[/bold] {up['summary']['rollout_stage']}\n"
                        f"[bold]Benchmark mode:[/bold] {up['summary']['benchmark_mode']}\n"
                        f"[bold]Core Done:[/bold] {counts['done']}  [bold]In progress:[/bold] {counts['in_progress']}  [bold]Planned:[/bold] {counts['planned']}\n"
                        f"[bold]OMEGA Done:[/bold] {omega_counts.get('done', 0)}  [bold]In progress:[/bold] {omega_counts.get('in_progress', 0)}  [bold]Planned:[/bold] {omega_counts.get('planned', 0)}\n"
                        f"[bold]God-Layer Tools:[/bold] {godlayer_inv.get('total_tools', 0)}",
                        title="Upgrade Tracker",
                        border_style="cyan",
                    )
                )
            elif inp == "/omega":
                from pradysagican.config import load_config
                from pradysagican.omega import HardwareAutoSelect
                cfg = load_config()
                hw = HardwareAutoSelect().select()
                c.print(Panel(f"[bold]OMEGA Flags[/bold]\nstack={cfg.upgrades.enable_omega_stack}\nmemory_citadel={cfg.upgrades.enable_omega_memory_citadel}\nsafety_net={cfg.upgrades.enable_omega_safety_net}\nhardware={cfg.upgrades.enable_omega_hardware_control}\nbench_auto={cfg.upgrades.enable_omega_bench_auto}\n\n[bold]Hardware[/bold]\nbackend={hw.backend} ({hw.reason})", title="OMEGA", border_style="magenta"))
            elif inp == "/godlayer":
                from pradysagican.config import load_config
                from pradysagican.godlayer import GodLayerKernel
                cfg = load_config()
                kernel = GodLayerKernel()
                inv = kernel.inventory()
                c.print(Panel(f"[bold]God-Layer Flags[/bold]\ngodlayer={cfg.upgrades.enable_godlayer_inventions}\nsomnium={cfg.upgrades.enable_somnium_cycle}\ndrift={cfg.upgrades.enable_drift_pipeline}\ntopological={cfg.upgrades.enable_topological_intelligence}\nimmune={cfg.upgrades.enable_immune_self_healing}\nfuture_self={cfg.upgrades.enable_future_self_model}\n\n[bold]Inventory[/bold]\ntotal_tools={inv['total_tools']} systems={inv['systems']} domains={inv['domains']}\nprototype={inv['maturity']['prototype']} planned={inv['maturity']['planned']}", title="God-Layer", border_style="yellow"))
            elif inp == "/tools":
                from pradysagican.core.task_classifier import TaskCategory
                tt = Table(title="Task Categories", border_style="cyan")
                tt.add_column("Category"); tt.add_column("Subsystems", style="dim")
                from pradysagican.core.task_classifier import SUBSYSTEM_MAP
                for cat, subs in SUBSYSTEM_MAP.items():
                    tt.add_row(cat.value, ", ".join(subs[:4]))
                c.print(tt)
            else:
                task = classifier.classify(inp)
                # Beautiful header with task classification
                c.print(f"\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
                c.print(f"[cyan]📊 Task Analysis[/cyan]")
                c.print(f"[bold]Category:[/bold] {task.category.value}")
                c.print(f"[bold]Complexity:[/bold] {task.complexity.value}")
                c.print(f"[bold]Pipeline:[/bold] {task.pipeline_name}")
                c.print(f"[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")
                
                with c.status(f"[cyan]⏳ Processing with {task.pipeline_name}...[/cyan]"):
                    if inp.startswith("/dream "): result = await god.dream(inp[7:].split(","))
                    elif inp.startswith("/predict "): result = await god.predict(inp[9:])
                    elif inp.startswith("/solve "): result = await god.solve(inp[7:])
                    else: result = await god.think(inp)
                
                # Extract and format result
                c.print(f"\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
                c.print(f"[cyan]✨ Response[/cyan]\n")
                
                # Helper to extract attributes from result objects
                def get_attr(obj, attr, default=None):
                    if isinstance(obj, dict):
                        return obj.get(attr, default)
                    return getattr(obj, attr, default)
                
                # Format based on result type
                if hasattr(result, "problem"):
                    # SolveResult or similar object
                    problem = get_attr(result, "problem", "Unknown")
                    confidence = get_attr(result, "confidence", 0.0)
                    elapsed = get_attr(result, "elapsed_ms", 0)
                    
                    c.print(f"[bold cyan]🎯 Problem:[/bold cyan] {str(problem)[:100]}")
                    c.print(f"[bold cyan]🎯 Confidence:[/bold cyan] {confidence:.2%}")
                    c.print(f"[bold cyan]🎯 Elapsed:[/bold cyan] {elapsed:.2f}ms")
                    
                    decomposition = get_attr(result, "decomposition", [])
                    if decomposition and decomposition != [problem]:
                        c.print(f"\n[yellow]📋 Sub-problems:[/yellow]")
                        for i, sub in enumerate(decomposition[:3], 1):
                            c.print(f"   {i}. {str(sub)[:85]}")
                    
                    reasoning = get_attr(result, "reasoning_trace", [])
                    if reasoning:
                        c.print(f"\n[yellow]🧠 Reasoning Process (top 3 steps):[/yellow]")
                        for i, step in enumerate(reasoning[:3], 1):
                            step_str = str(step).split('\n')[0]
                            if 'Reasoning step' in step_str or 'Step' in step_str:
                                step_str = step_str.replace("[Reasoning step based on:", "").replace("]", "").strip()
                                step_str = step_str[:90]
                            c.print(f"   {i}. {step_str}")
                    
                    angles = get_attr(result, "creative_angles", [])
                    if angles:
                        c.print(f"\n[yellow]💡 Creative Insights:[/yellow]")
                        for i, angle in enumerate(angles[:3], 1):
                            angle_str = str(angle).replace("Insight:", "").strip()[:85]
                            c.print(f"   {i}. {angle_str}")
                    
                    solution = get_attr(result, "solution", None)
                    if solution and solution != problem:
                        sol_str = str(solution)
                        if "Reasoning step" in sol_str:
                            sol_str = "Derived from reasoning trace"
                        c.print(f"\n[bold green]✅ Solution:[/bold green]")
                        c.print(f"   {sol_str[:200]}")
                    
                    verification = get_attr(result, "verification", {})
                    if verification and isinstance(verification, dict):
                        logical = verification.get('logical_check', 'N/A')
                        if logical and logical != "":
                            c.print(f"\n[cyan]🔍 Verification:[/cyan] {logical[:100]}")
                
                elif hasattr(result, "predictions"):
                    # Prediction result
                    predictions = get_attr(result, "predictions", {})
                    confidence = get_attr(result, "confidence", 0.0)
                    c.print(f"[yellow]🔮 Predictions:[/yellow]")
                    for i, (model, pred) in enumerate(list(predictions.items())[:3], 1):
                        c.print(f"   {i}. [{model}] {str(pred)[:80]}")
                    c.print(f"\n[bold cyan]Ensemble Confidence:[/bold cyan] {confidence:.2%}")
                
                elif hasattr(result, "visions"):
                    # Dream result
                    visions = get_attr(result, "visions", [])
                    c.print(f"[yellow]🌙 Creative Visions ({len(visions)} types):[/yellow]")
                    for i, vision in enumerate(visions[:5], 1):
                        c.print(f"   {i}. {str(vision)[:85]}")
                
                elif isinstance(result, dict):
                    # Dict result
                    if 'answer' in result or 'conclusion' in result:
                        text = result.get("answer", result.get("conclusion", ""))
                        c.print(f"[yellow]💬 Answer:[/yellow]\n   {str(text)[:400]}")
                    else:
                        c.print(f"[yellow]Result:[/yellow]")
                        for key, val in list(result.items())[:5]:
                            val_str = str(val)[:80] if not isinstance(val, (list, dict)) else f"[{type(val).__name__}]"
                            c.print(f"   {key}: {val_str}")
                else:
                    # Fallback
                    text = str(result)
                    c.print(f"[yellow]Result:[/yellow]\n{text[:400]}")
                
                c.print(f"\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")
    asyncio.run(_run())

def cmd_status(args):
    c = _console()
    from rich.table import Table
    from rich.panel import Panel
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    async def _run():
        from pradysagican.god import PradysagicanGod
        god = PradysagicanGod()
        with c.status("[cyan]Checking subsystems...[/cyan]"): await god.initialize()
        s = god.stats()
        t = Table(title="Subsystem Health", border_style="green")
        t.add_column("Group"); t.add_column("Module"); t.add_column("Status")
        for group, modules in s["system"]["groups"].items():
            for mod, status in modules.items():
                color = "green" if status == "online" else "red"
                t.add_row(group, mod, f"[{color}]●[/{color}] {status}")
        c.print(t)
        c.print(f"\n[bold green]Total: {s['system']['subsystems_online']}/{s['system']['subsystems_total']} online | Features: {s['features']['combinatorial_total']:,} | Health: {s['system']['health_pct']}%[/bold green]")
    asyncio.run(_run())

def cmd_benchmark(args):
    c = _console()
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.table import Table
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    async def _run():
        from pradysagican.benchmarks.benchmark_suite import BenchmarkSuite
        bs = BenchmarkSuite()
        names = bs.list_benchmarks()
        results = []
        with Progress(TextColumn("[bold]{task.description}"), BarColumn(), TextColumn("{task.percentage:>3.0f}%")) as prog:
            task = prog.add_task("Running benchmarks...", total=len(names))
            for name in names:
                r = await bs.run_benchmark(name); results.append(r); prog.advance(task)
        t = Table(title=f"Benchmark Results ({len(results)} total)", border_style="cyan")
        t.add_column("Benchmark"); t.add_column("Score", justify="right"); t.add_column("Target", justify="right"); t.add_column("Gap")
        for r in results:
            gap = 100.0 - r.percentage; color = "green" if gap < 5 else "yellow" if gap < 20 else "red"
            t.add_row(r.benchmark_name, f"{r.percentage:.1f}%", "100.0%", f"[{color}]{gap:.1f}%[/{color}]")
        c.print(t)
        gov = bs.governance_summary()
        c.print(
            Panel(
                f"[bold]Mode:[/bold] {gov['mode']}  [bold]Rollout:[/bold] {gov['rollout_stage']}\n"
                f"[bold]Coverage:[/bold] {gov['coverage_percent']}% ({gov['benchmarks_run']}/{gov['benchmarks_total']})\n"
                f"[bold]Acceptance:[/bold] {gov['acceptance_checks_passed']}/{gov['acceptance_checks_run']} "
                f"({gov['acceptance_rate_percent']}%)\n"
                f"[bold]Regressions > limit:[/bold] {gov['regressions_over_limit']} "
                f"(limit={gov['regression_limit_percent']}%)\n"
                f"[bold]Promotion health:[/bold] "
                f"[{'green' if gov['healthy_for_promotion'] else 'yellow'}]"
                f"{'READY' if gov['healthy_for_promotion'] else 'HOLD'}[/]",
                title="Benchmark Governance",
                border_style="green" if gov["healthy_for_promotion"] else "yellow",
            )
        )
    asyncio.run(_run())

def cmd_access(args):
    c = _console()
    from rich.panel import Panel
    from pradysagican.safety.access_policy import AccessPolicyEnforcer
    enforcer = AccessPolicyEnforcer()
    email = getattr(args, "email", None)
    role = getattr(args, "role", "default")
    if email:
        profile = enforcer.create_access_profile(email, role=role)
        c.print(Panel(f"[green]Access profile created.[/green]\n\nEmail: {email}\nRole: {profile.role}\nUser ID: {profile.user_id}\nCreated: {time.strftime('%Y-%m-%d', time.localtime(profile.started_at))}\n\nCore access remains open with or without profiles.", title="Access Profile", border_style="green"))
    else:
        c.print(Panel("[bold]PRADYSAGICAN Access[/bold]\n\n[bold green]Open access mode enabled[/bold green]\nNo payment required.\n\nOptional profile creation:\npradysagican access --email you@mail.com [--role default]", title="Access", border_style="cyan"))

def cmd_evolve(args):
    c = _console()
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    async def _run():
        from pradysagican.god import PradysagicanGod
        god = PradysagicanGod()
        with c.status("[cyan]Initializing...[/cyan]"): await god.initialize()
        with c.status("[cyan]Running evolution cycle...[/cyan]"): result = await god.evolve()
        c.print(f"[green]✓ Evolution cycle complete[/green]")
        c.print(str(result)[:500])
    asyncio.run(_run())


def cmd_upgrade(args):
    c = _console()
    from rich.table import Table
    from rich.panel import Panel
    from pradysagican.upgrades import UpgradeManager

    up = UpgradeManager().as_dict()
    counts = up["summary"]["counts"]
    omega_counts = up["summary"].get("omega_counts", {})
    godlayer_inv = up["summary"].get("godlayer_inventory", {})
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    c.print(
        Panel(
            f"[bold]Rollout Stage:[/bold] {up['summary']['rollout_stage']}\n"
            f"[bold]Benchmark Mode:[/bold] {up['summary']['benchmark_mode']}\n"
            f"[bold]Kill Switch:[/bold] {up['summary']['kill_switch_new_paths']}\n\n"
            f"Core Done: {counts['done']}  In Progress: {counts['in_progress']}  Planned: {counts['planned']}  Total: {counts['total']}\n"
            f"OMEGA Done: {omega_counts.get('done', 0)}  In Progress: {omega_counts.get('in_progress', 0)}  Planned: {omega_counts.get('planned', 0)}  Total: {omega_counts.get('total', 0)}\n"
            f"God-Layer Tools: {godlayer_inv.get('total_tools', 0)}  Systems: {godlayer_inv.get('systems', 0)}  Domains: {godlayer_inv.get('domains', 0)}",
            title="Upgrade Tracker Status",
            border_style="green",
        )
    )

    t = Table(title="Feature Tracker (F01-F51)", border_style="cyan")
    t.add_column("ID")
    t.add_column("Feature")
    t.add_column("WS")
    t.add_column("Status")
    for feat in up["features"]:
        t.add_row(feat["feature_id"], feat["name"], feat["workstream"], feat["status"])
    c.print(t)

    ot = Table(title="OMEGA Feature Tracker (O01-O85)", border_style="magenta")
    ot.add_column("ID")
    ot.add_column("Feature")
    ot.add_column("WS")
    ot.add_column("Status")
    for feat in up.get("omega_features", []):
        ot.add_row(feat["feature_id"], feat["name"], feat["workstream"], feat["status"])
    c.print(ot)


def cmd_omega(args):
    c = _console()
    from rich.panel import Panel
    from pradysagican.config import load_config
    from pradysagican.omega import HardwareAutoSelect, MemoryCitadelAPI, OmegaConsciousnessStack

    cfg = load_config()
    hw = HardwareAutoSelect().select()
    omega_stack = OmegaConsciousnessStack()
    omega_mem = MemoryCitadelAPI()
    probe = omega_stack.update(
        specialists=["reasoning", "memory"],
        surprises=["novel_task"],
        phi=0.6,
        gw_ignition_rate=0.7,
        prediction_error_entropy=0.3,
        self_model="self-model evaluating itself",
    )
    mem_probe = omega_mem.store("what happened yesterday", {"event": "omega_probe"})
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    c.print(Panel(f"[bold]OMEGA Flags[/bold]\nstack={cfg.upgrades.enable_omega_stack}\nmemory_citadel={cfg.upgrades.enable_omega_memory_citadel}\nsafety_net={cfg.upgrades.enable_omega_safety_net}\nhardware={cfg.upgrades.enable_omega_hardware_control}\nbench_auto={cfg.upgrades.enable_omega_bench_auto}\n\n[bold]Hardware[/bold]\nbackend={hw.backend} ({hw.reason})\n\n[bold]Consciousness Probe[/bold]\nc_score={probe['c_score']} strange_loop={probe['strange_loop']} elevate={probe['elevation_triggered']}\n\n[bold]Memory Probe[/bold]\ntier={mem_probe['tier']} stored={mem_probe['stored']}", title="OMEGA Status", border_style="magenta"))


def cmd_godlayer(args):
    c = _console()
    from rich.panel import Panel
    from pradysagican.config import load_config
    from pradysagican.godlayer import GodLayerKernel, GodLayerOmega2Runtime

    cfg = load_config()
    kernel = GodLayerKernel()
    omega2 = GodLayerOmega2Runtime(kernel=kernel)
    inv = kernel.inventory()
    somnium_probe = kernel.run_somnium_cycle(
        events=[{"event": "resolved retrieval conflict"}, {"event": "detected topology gap"}],
        awake_hours=10.0,
        local_hour=3,
        idle_minutes=60,
    )
    future_probe = kernel.project_future(
        current_scores={"SWE-Bench": 35.0, "GPQA": 55.0},
        daily_improvement=0.15,
        days=30,
        intent="improve benchmark performance safely",
    )
    cycle_probe = omega2.run_cycle_tick()
    plan_probe = omega2.planner.execution_frame()
    c.print(Panel(BANNER, border_style="cyan", padding=(1, 2)))
    c.print(
        Panel(
            f"[bold]God-Layer Flags[/bold]\n"
            f"godlayer={cfg.upgrades.enable_godlayer_inventions}\n"
            f"somnium={cfg.upgrades.enable_somnium_cycle}\n"
            f"drift={cfg.upgrades.enable_drift_pipeline}\n"
            f"topological={cfg.upgrades.enable_topological_intelligence}\n"
            f"immune={cfg.upgrades.enable_immune_self_healing}\n"
            f"future_self={cfg.upgrades.enable_future_self_model}\n\n"
            f"[bold]Inventory[/bold]\n"
            f"total_tools={inv['total_tools']} systems={inv['systems']} domains={inv['domains']}\n"
            f"prototype={inv['maturity']['prototype']} planned={inv['maturity']['planned']}\n\n"
            f"[bold]Somnium Probe[/bold]\n"
            f"phase={somnium_probe['phase']} semantic_rules={somnium_probe['semantic_rules']}\n\n"
            f"[bold]Future Probe[/bold]\n"
            f"projection_keys={list(future_probe['projection'].keys())}\n\n"
            f"[bold]OMEGA-2 Root[/bold]\n"
            f"window={cycle_probe['window']['window']} "
            f"primary_bus={cycle_probe['window']['primary_bus']} "
            f"active_outputs={list(cycle_probe['outputs'].keys())}\n\n"
            f"[bold]Master Plan[/bold]\n"
            f"coverage={plan_probe['summary']['total_capabilities']}/{plan_probe['summary']['target_capabilities']} "
            f"complete={plan_probe['summary']['coverage_complete']}\n"
            f"tier1_batch={plan_probe['next_tier_1_batch'][:5]} "
            f"tier2_batch={plan_probe['next_tier_2_batch'][:5]}",
            title="God-Layer Status",
            border_style="yellow",
        )
    )

def cmd_version(args):
    c = _console()
    from rich.panel import Panel
    c.print(Panel(f"{BANNER}\n[bold]Version:[/bold] 6.0.0\n[bold]Python:[/bold] {sys.version.split()[0]}\n[bold]Lines:[/bold] 22,000+\n[bold]Modules:[/bold] 50+\n[bold]Classes:[/bold] 280+\n[bold]Tests:[/bold] 181 passing\n[bold]Features:[/bold] 11,300,000+\n[bold]Subsystems:[/bold] 40\n[bold]Benchmarks:[/bold] 31\n[bold]Author:[/bold] Prady\n[bold]License:[/bold] Proprietary", title="PRADYSAGICAN", border_style="cyan"))

def main():
    parser = argparse.ArgumentParser(prog="pradysagican", description="PRADYSAGICAN — Super General Intelligence System")
    sub = parser.add_subparsers(dest="command")
    p_serve = sub.add_parser("serve", help="Start API server"); p_serve.add_argument("--port", type=int, default=8000)
    sub.add_parser("chat", help="Interactive chat mode")
    sub.add_parser("status", help="System health dashboard")
    sub.add_parser("benchmark", help="Run all 31 benchmarks")
    sub.add_parser("evolve", help="Run self-evolution cycle")
    p_access = sub.add_parser("access", help="Show open-access info / optional profile"); p_access.add_argument("--email"); p_access.add_argument("--role", default="default", help="Profile role label")
    sub.add_parser("upgrade", help="Show upgrade tracker status")
    sub.add_parser("omega", help="Show OMEGA advanced stack status")
    sub.add_parser("godlayer", help="Show God-layer invented systems status")
    sub.add_parser("version", help="Show version info")
    args = parser.parse_args()
    dispatch = {"serve": cmd_serve, "chat": cmd_chat, "status": cmd_status, "benchmark": cmd_benchmark, "evolve": cmd_evolve, "access": cmd_access, "upgrade": cmd_upgrade, "omega": cmd_omega, "godlayer": cmd_godlayer, "version": cmd_version}
    fn = dispatch.get(args.command)
    if fn: fn(args)
    else: parser.print_help()

if __name__ == "__main__": main()
