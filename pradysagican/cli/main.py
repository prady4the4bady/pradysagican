"""
Phase D: CLI Tool - Command-line interface for PRADYSAGI

Provides full system control via terminal:
- pradysagi chat - Interactive chat mode
- pradysagi agent <task> - Autonomous agent mode
- pradysagi server - Start API server
- pradysagi configure - Setup wizard
- pradysagi status - System status
"""

import click
import asyncio
import json
from typing import Optional
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Import PRADYSAGI components
from pradysagican.core.integration import (
    pradysagi,
    initialize_pradysagi,
    IntegratedRequest,
    IntegrationMode,
)


console = Console()


# ============================================================================
# Utilities
# ============================================================================

def print_header(title: str, subtitle: str = ""):
    """Print formatted header"""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]")
    console.print("[dim]" + "─" * 60 + "[/dim]")


def print_success(message: str):
    """Print success message"""
    console.print(f"[green]✅ {message}[/green]")


def print_error(message: str):
    """Print error message"""
    console.print(f"[red]❌ {message}[/red]")


def print_info(message: str):
    """Print info message"""
    console.print(f"[blue]ℹ️  {message}[/blue]")


async def ensure_initialized():
    """Ensure PRADYSAGI is initialized"""
    if not pradysagi or not hasattr(pradysagi, 'mode'):
        print_info("Initializing PRADYSAGI...")
        await initialize_pradysagi({
            "local_models": True,
            "mode": IntegrationMode.HYBRID,
        })
        print_success("PRADYSAGI initialized")


# ============================================================================
# Main CLI Group
# ============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="pradysagi")
def cli():
    """
    🤖 PRADYSAGI - Superintelligent Agent System
    
    A complete AI system with 34 phases of intelligence, 
    multi-model support, and tool integration.
    """
    pass


# ============================================================================
# Chat Command
# ============================================================================

@cli.command()
@click.option(
    "--enable-rag",
    default=True,
    type=bool,
    help="Enable RAG context augmentation"
)
@click.option(
    "--enable-tools",
    default=True,
    type=bool,
    help="Enable MCP tool execution"
)
@click.option(
    "--system-prompt",
    default=None,
    type=str,
    help="Custom system prompt"
)
def chat(enable_rag: bool, enable_tools: bool, system_prompt: Optional[str]):
    """
    💬 Start interactive chat mode
    
    Provides a conversational interface to PRADYSAGI.
    Type 'quit' or 'exit' to exit.
    """
    async def async_chat():
        await ensure_initialized()
        
        print_header("Chat Mode", "Type messages and press Enter. Type 'quit' to exit.")
        
        while True:
            try:
                # Get user input
                user_input = console.input("[bold cyan]You:[/bold cyan] ")
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    print_success("Goodbye!")
                    break
                
                if not user_input.strip():
                    continue
                
                # Show thinking indicator
                with console.status("[bold cyan]🤔 Thinking..."):
                    # Process request
                    request = IntegratedRequest(
                        user_input=user_input,
                        system_prompt=system_prompt,
                        enable_rag=enable_rag,
                        enable_tools=enable_tools,
                    )
                    
                    response = await pradysagi.process(request)
                
                # Display response
                console.print(f"\n[bold green]PRADYSAGI:[/bold green]")
                console.print(response.response)
                
                # Show metadata
                if click.confirm("\nShow metadata?", default=False):
                    print_info(f"Model: {response.model_used}")
                    print_info(f"Duration: {response.duration_ms:.1f}ms")
                    if response.retrieval_method:
                        print_info(f"Retrieval: {response.retrieval_method}")
                    if response.tools_executed:
                        print_info(f"Tools: {', '.join(response.tools_executed)}")
                
                console.print()
            
            except KeyboardInterrupt:
                print_success("Chat interrupted")
                break
            
            except Exception as e:
                print_error(f"Error: {str(e)}")
    
    asyncio.run(async_chat())


# ============================================================================
# Agent Command
# ============================================================================

@cli.command()
@click.argument("task", required=True)
@click.option(
    "--iterations",
    default=3,
    type=int,
    help="Max refinement iterations"
)
@click.option(
    "--enable-tools",
    default=True,
    type=bool,
    help="Enable MCP tool execution"
)
def agent(task: str, iterations: int, enable_tools: bool):
    """
    🤖 Run autonomous agent mode
    
    Executes a task autonomously with multi-step reasoning.
    """
    async def async_agent():
        await ensure_initialized()
        
        print_header("Autonomous Agent Mode", f"Task: {task}")
        
        try:
            with console.status("[bold cyan]🚀 Agent executing task..."):
                # Enhance task with reasoning prefix
                enhanced_task = f"""Please solve the following task step by step:

Task: {task}

Use the following approach:
1. Break down the task into steps
2. Execute each step carefully
3. Verify results
4. Provide final answer

Be thorough and systematic."""
                
                request = IntegratedRequest(
                    user_input=enhanced_task,
                    enable_rag=True,
                    enable_tools=enable_tools,
                    max_iterations=iterations,
                )
                
                response = await pradysagi.process(request)
            
            # Display results
            console.print("\n[bold green]Agent Response:[/bold green]")
            console.print(Markdown(response.response))
            
            # Summary table
            table = Table(title="Execution Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Duration", f"{response.duration_ms:.1f}ms")
            table.add_row("Model", response.model_used)
            table.add_row("Tools Used", str(len(response.tools_executed)))
            table.add_row("Confidence", f"{response.confidence:.0%}")
            
            console.print(table)
        
        except Exception as e:
            print_error(f"Agent error: {str(e)}")
    
    asyncio.run(async_agent())


# ============================================================================
# Server Command
# ============================================================================

@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    type=str,
    help="Server host"
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Server port"
)
@click.option(
    "--reload",
    default=False,
    type=bool,
    help="Auto-reload on code changes"
)
def server(host: str, port: int, reload: bool):
    """
    🚀 Start API server
    
    Runs the FastAPI server with REST and WebSocket endpoints.
    """
    import subprocess
    
    print_header("Starting PRADYSAGI API Server")
    
    print_info(f"Host: {host}")
    print_info(f"Port: {port}")
    print_info(f"Auto-reload: {reload}")
    
    print("\n" + "=" * 60)
    print("📚 API Endpoints:")
    print(f"  REST API:   http://{host}:{port}/api/v2/chat")
    print(f"  WebSocket:  ws://{host}:{port}/ws/v2/chat")
    print(f"  Docs:       http://{host}:{port}/docs")
    print(f"  ReDoc:      http://{host}:{port}/redoc")
    print("=" * 60 + "\n")
    
    # Run server
    cmd = [
        "python", "-m", "uvicorn",
        "pradysagican.api.server:app",
        f"--host={host}",
        f"--port={port}",
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print_success("Server stopped")
    except Exception as e:
        print_error(f"Server error: {str(e)}")


# ============================================================================
# Configure Command
# ============================================================================

@cli.command()
def configure():
    """
    ⚙️  Configuration wizard
    
    Setup and configure PRADYSAGI system interactively.
    """
    async def async_configure():
        print_header("PRADYSAGI Configuration Wizard")
        
        # Mode selection
        console.print("\n[bold]Select operation mode:[/bold]")
        console.print("1. Local only (free, no API keys needed)")
        console.print("2. Cloud only (requires API keys)")
        console.print("3. Hybrid (local first, cloud fallback) [recommended]")
        
        mode_choice = click.prompt("Enter choice", type=click.Choice(["1", "2", "3"]), default="3")
        
        modes = {
            "1": IntegrationMode.LOCAL_ONLY,
            "2": IntegrationMode.CLOUD_ONLY,
            "3": IntegrationMode.HYBRID,
        }
        selected_mode = modes[mode_choice]
        
        # Feature selection
        console.print("\n[bold]Select features:[/bold]")
        enable_rag = click.confirm("Enable RAG context augmentation", default=True)
        enable_tools = click.confirm("Enable MCP tool execution", default=True)
        
        # API keys (if cloud)
        if selected_mode != IntegrationMode.LOCAL_ONLY:
            console.print("\n[bold]API Keys (optional, press Enter to skip):[/bold]")
            openai_key = click.prompt("OpenAI API key", default="", hide_input=True)
            anthropic_key = click.prompt("Anthropic API key", default="", hide_input=True)
        
        # Save configuration
        config_file = Path(".env")
        config_content = f"""# PRADYSAGI Configuration
MODE={selected_mode.value}
ENABLE_RAG={enable_rag}
ENABLE_TOOLS={enable_tools}
"""
        
        if selected_mode != IntegrationMode.LOCAL_ONLY:
            if openai_key:
                config_content += f"OPENAI_API_KEY={openai_key}\n"
            if anthropic_key:
                config_content += f"ANTHROPIC_API_KEY={anthropic_key}\n"
        
        config_file.write_text(config_content)
        print_success(f"Configuration saved to {config_file}")
        
        # Test configuration
        console.print("\n[bold]Testing configuration...[/bold]")
        try:
            await initialize_pradysagi({
                "local_models": selected_mode in [IntegrationMode.LOCAL_ONLY, IntegrationMode.HYBRID],
                "mode": selected_mode,
            })
            print_success("Configuration working!")
        except Exception as e:
            print_error(f"Configuration test failed: {str(e)}")
    
    asyncio.run(async_configure())


# ============================================================================
# Status Command
# ============================================================================

@cli.command()
def status():
    """
    📊 Show system status
    
    Displays health and statistics of all components.
    """
    async def async_status():
        await ensure_initialized()
        
        print_header("PRADYSAGI System Status", datetime.now().isoformat())
        
        # Health check
        console.print("\n[bold]Component Health:[/bold]")
        health = await pradysagi.health_check()
        
        table = Table(title="Health Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        for component, is_healthy in health.items():
            status = "[green]✅ Healthy[/green]" if is_healthy else "[red]❌ Error[/red]"
            table.add_row(component, status)
        
        console.print(table)
        
        # Statistics
        console.print("\n[bold]Statistics:[/bold]")
        stats = pradysagi.get_stats()
        
        stats_table = Table(title="System Stats")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Requests", str(stats["total_requests"]))
        stats_table.add_row("RAG Documents", str(stats["rag_documents"]))
        stats_table.add_row("Available Tools", str(stats["tools_available"]))
        stats_table.add_row("Avg Response Time", f"{stats['average_response_time_ms']:.1f}ms")
        stats_table.add_row("Mode", stats["mode"])
        
        console.print(stats_table)
        
        # Available tools
        console.print("\n[bold]Available Tools:[/bold]")
        tools = await pradysagi.get_available_tools()
        for backend_name, tool_names in tools.items():
            console.print(f"  {backend_name}: {len(tool_names)} tools")
            for tool_name in tool_names[:3]:
                console.print(f"    - {tool_name}")
            if len(tool_names) > 3:
                console.print(f"    ... +{len(tool_names)-3} more")
    
    asyncio.run(async_status())


# ============================================================================
# Help Command
# ============================================================================

@cli.command()
def help():
    """Show detailed help"""
    help_text = """
    # PRADYSAGI CLI Documentation
    
    ## Quick Start
    
    ```bash
    # Interactive chat
    pradysagi chat
    
    # Autonomous agent
    pradysagi agent "Solve this problem"
    
    # Start API server
    pradysagi server
    
    # Check status
    pradysagi status
    ```
    
    ## Commands
    
    - **chat**: Interactive chat mode
    - **agent <task>**: Autonomous agent mode
    - **server**: Start FastAPI server
    - **configure**: Setup wizard
    - **status**: System status
    
    ## Environment Variables
    
    - `OPENAI_API_KEY`: For cloud models
    - `ANTHROPIC_API_KEY`: For Claude cloud
    - `MODE`: local_only, cloud_only, or hybrid
    
    ## Examples
    
    ```bash
    # Chat with RAG disabled
    pradysagi chat --enable-rag=False
    
    # Agent with custom system prompt
    pradysagi agent "Task" --system-prompt "You are expert"
    
    # Server on custom port
    pradysagi server --port 9000
    ```
    """
    
    console.print(Markdown(help_text))


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print_success("CLI interrupted by user")
        print("=" * 60)
    except Exception as e:
        print_error(f"CLI error: {str(e)}")
