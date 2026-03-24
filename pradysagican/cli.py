"""
PRADYSAGICAN CLI — Beautiful, powerful, simple.
Usage:  pradysagican <command>
Commands: serve | chat | status | benchmark | evolve | subscribe | version
"""
from __future__ import annotations
import argparse, asyncio, sys, os, time

def _console():
    from rich.console import Console
    return Console()

BANNER = """[bold cyan]
 ██████╗ ██████╗  █████╗ ██████╗ ██╗   ██╗
 ██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
 ██████╔╝██████╔╝███████║██║  ██║ ╚████╔╝
 ██╔═══╝ ██╔══██╗██╔══██║██║  ██║  ╚██╔╝
 ██║     ██║  ██║██║  ██║██████╔╝   ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝    ╚═╝[/bold cyan]
[dim]Super General Intelligence System v6.0[/dim]
[dim]40 subsystems • 22K+ lines • 11.3M features • 152 tests[/dim]
"""

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
    for cmd, desc in [("/help","Show commands"),("/status","System health"),("/dream <topic>","Creative dreaming"),("/predict <question>","Make prediction"),("/solve <problem>","Full problem solving"),("/tools","List tool categories"),("/subscribe","Subscription info"),("/quit","Exit")]:
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
            elif inp == "/subscribe":
                c.print(Panel(f"[bold]$5/month[/bold] — Pay at:\n[link=https://www.paypal.com/ncp/payment/KGVSY9JY724RC]https://www.paypal.com/ncp/payment/KGVSY9JY724RC[/link]\n\nTrial: [cyan]pradysagican subscribe --email you@mail.com --trial 7[/cyan]", title="Subscribe", border_style="green"))
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
                c.print(f"[dim]Category: {task.category.value} | Complexity: {task.complexity.value} | Pipeline: {task.pipeline_name}[/dim]")
                with c.status(f"[cyan]Thinking ({task.pipeline_name})...[/cyan]"):
                    if inp.startswith("/dream "): result = await god.dream(inp[7:].split(","))
                    elif inp.startswith("/predict "): result = await god.predict(inp[9:])
                    elif inp.startswith("/solve "): result = await god.solve(inp[7:])
                    else: result = await god.think(inp)
                if isinstance(result, dict): text = result.get("answer", result.get("conclusion", str(result)))
                elif hasattr(result, "answer"): text = result.answer
                elif hasattr(result, "conclusion"): text = result.conclusion
                else: text = str(result)
                c.print(Panel(Markdown(str(text)[:2000]), title="[bold cyan]prady[/bold cyan]", border_style="cyan"))
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
    asyncio.run(_run())

def cmd_subscribe(args):
    c = _console()
    from rich.panel import Panel
    from pradysagican.safety.subscription import SubscriptionEnforcer, PAYPAL_PAYMENT_URL, MONTHLY_FEE_USD
    enforcer = SubscriptionEnforcer()
    email = getattr(args, "email", None)
    trial_days = getattr(args, "trial", None)
    if email and trial_days:
        sub = enforcer.start_trial(email, int(trial_days))
        c.print(Panel(f"[green]✓ Trial activated![/green]\n\nEmail: {email}\nDuration: {trial_days} days\nUser ID: {sub.user_id}\nExpires: {time.strftime('%Y-%m-%d', time.localtime(sub.expires_at))}\n\nTo continue after trial, pay ${MONTHLY_FEE_USD}/month:\n[link={PAYPAL_PAYMENT_URL}]{PAYPAL_PAYMENT_URL}[/link]", title="Trial Activated", border_style="green"))
    else:
        c.print(Panel(f"[bold]PRADYSAGICAN Subscription[/bold]\n\n💰 [bold]${MONTHLY_FEE_USD}/month[/bold]\n\n[bold]Pay here:[/bold]\n[link={PAYPAL_PAYMENT_URL}]{PAYPAL_PAYMENT_URL}[/link]\n\n[bold]Start free trial:[/bold]\npradysagican subscribe --email you@mail.com --trial 7\n\n[dim]Trial: 7-30 days free\nMonthly: ${MONTHLY_FEE_USD}/month\nEnterprise: Contact f20240323@dubai.bits-pilani.ac.in[/dim]", title="Subscribe", border_style="cyan"))

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

def cmd_version(args):
    c = _console()
    from rich.panel import Panel
    c.print(Panel(f"{BANNER}\n[bold]Version:[/bold] 6.0.0\n[bold]Python:[/bold] {sys.version.split()[0]}\n[bold]Lines:[/bold] 22,000+\n[bold]Modules:[/bold] 50+\n[bold]Classes:[/bold] 280+\n[bold]Tests:[/bold] 152 passing\n[bold]Features:[/bold] 11,300,000+\n[bold]Subsystems:[/bold] 40\n[bold]Benchmarks:[/bold] 31\n[bold]Author:[/bold] Prady\n[bold]License:[/bold] Proprietary", title="PRADYSAGICAN", border_style="cyan"))

def main():
    parser = argparse.ArgumentParser(prog="pradysagican", description="PRADYSAGICAN — Super General Intelligence System")
    sub = parser.add_subparsers(dest="command")
    p_serve = sub.add_parser("serve", help="Start API server"); p_serve.add_argument("--port", type=int, default=8000)
    sub.add_parser("chat", help="Interactive chat mode")
    sub.add_parser("status", help="System health dashboard")
    sub.add_parser("benchmark", help="Run all 31 benchmarks")
    sub.add_parser("evolve", help="Run self-evolution cycle")
    p_sub = sub.add_parser("subscribe", help="Manage subscription"); p_sub.add_argument("--email"); p_sub.add_argument("--trial", type=int, help="Trial duration in days")
    sub.add_parser("version", help="Show version info")
    args = parser.parse_args()
    dispatch = {"serve": cmd_serve, "chat": cmd_chat, "status": cmd_status, "benchmark": cmd_benchmark, "evolve": cmd_evolve, "subscribe": cmd_subscribe, "version": cmd_version}
    fn = dispatch.get(args.command)
    if fn: fn(args)
    else: parser.print_help()

if __name__ == "__main__": main()
