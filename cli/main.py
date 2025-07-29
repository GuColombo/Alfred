#!/usr/bin/env python3

import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import sys
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.core import TaskOrchestrator
from config.settings import load_config
from loguru import logger

app = typer.Typer(help="Alfred - Personal AI Operator System")
console = Console()

# Initialize global orchestrator
orchestrator = None

def init_orchestrator():
    """Initialize the task orchestrator with configuration."""
    global orchestrator
    try:
        config = load_config()
        orchestrator = TaskOrchestrator(config)
        logger.info("Alfred orchestrator initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        console.print(f"[red]Error: Failed to initialize Alfred: {e}[/red]")
        return False

@app.command()
def task(
    prompt: str = typer.Argument(help="Task description or query"),
    model: str = typer.Option("auto", help="LLM model to use (auto, claude, gpt4, gemini)"),
    memory: bool = typer.Option(True, help="Use persistent memory"),
    plugins: bool = typer.Option(True, help="Enable plugin execution"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output")
):
    """Execute a task through Alfred's orchestrator."""
    if not orchestrator and not init_orchestrator():
        raise typer.Exit(1)
    
    console.print(Panel(f"[bold blue]Alfred Task Execution[/bold blue]\n{prompt}", expand=False))
    
    try:
        result = orchestrator.execute_task(
            prompt=prompt,
            model=model,
            use_memory=memory,
            enable_plugins=plugins,
            verbose=verbose
        )
        
        console.print("\n[green]✓[/green] [bold]Task completed successfully[/bold]")
        console.print(Panel(result, title="Result", border_style="green"))
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        console.print(f"[red]✗ Task failed: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def memory(
    action: str = typer.Argument(help="Action: search, list, clear, inspect"),
    query: str = typer.Option(None, help="Search query for memory"),
    limit: int = typer.Option(10, help="Number of results to return")
):
    """Manage Alfred's persistent memory."""
    if not orchestrator and not init_orchestrator():
        raise typer.Exit(1)
    
    try:
        if action == "search":
            if not query:
                console.print("[red]Error: Search requires a query[/red]")
                raise typer.Exit(1)
            results = orchestrator.memory_search(query, limit)
            console.print(Panel(f"[bold]Memory Search Results[/bold]\nQuery: {query}", expand=False))
            for i, result in enumerate(results, 1):
                console.print(f"{i}. {result}")
        
        elif action == "list":
            memories = orchestrator.list_memories(limit)
            console.print(Panel("[bold]Recent Memories[/bold]", expand=False))
            for memory in memories:
                console.print(f"• {memory}")
        
        elif action == "clear":
            confirm = typer.confirm("Are you sure you want to clear all memory?")
            if confirm:
                orchestrator.clear_memory()
                console.print("[green]✓ Memory cleared[/green]")
        
        elif action == "inspect":
            stats = orchestrator.memory_stats()
            console.print(Panel(f"[bold]Memory Statistics[/bold]\n{stats}", expand=False))
        
        else:
            console.print("[red]Error: Invalid action. Use: search, list, clear, inspect[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        logger.error(f"Memory operation failed: {e}")
        console.print(f"[red]✗ Memory operation failed: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def plugin(
    action: str = typer.Argument(help="Action: list, enable, disable, install"),
    name: str = typer.Option(None, help="Plugin name"),
    path: str = typer.Option(None, help="Plugin path for installation")
):
    """Manage Alfred's plugins."""
    if not orchestrator and not init_orchestrator():
        raise typer.Exit(1)
    
    try:
        if action == "list":
            plugins = orchestrator.list_plugins()
            console.print(Panel("[bold]Available Plugins[/bold]", expand=False))
            for plugin_name, status in plugins.items():
                status_icon = "✓" if status else "✗"
                status_color = "green" if status else "red"
                console.print(f"[{status_color}]{status_icon}[/{status_color}] {plugin_name}")
        
        elif action in ["enable", "disable"]:
            if not name:
                console.print(f"[red]Error: {action} requires plugin name[/red]")
                raise typer.Exit(1)
            success = orchestrator.toggle_plugin(name, action == "enable")
            if success:
                console.print(f"[green]✓ Plugin {name} {action}d[/green]")
            else:
                console.print(f"[red]✗ Failed to {action} plugin {name}[/red]")
        
        elif action == "install":
            if not path:
                console.print("[red]Error: Install requires plugin path[/red]")
                raise typer.Exit(1)
            success = orchestrator.install_plugin(path)
            if success:
                console.print(f"[green]✓ Plugin installed from {path}[/green]")
            else:
                console.print(f"[red]✗ Failed to install plugin from {path}[/red]")
        
        else:
            console.print("[red]Error: Invalid action. Use: list, enable, disable, install[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        logger.error(f"Plugin operation failed: {e}")
        console.print(f"[red]✗ Plugin operation failed: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def status():
    """Show Alfred system status."""
    if not orchestrator and not init_orchestrator():
        raise typer.Exit(1)
    
    try:
        status_info = orchestrator.get_status()
        console.print(Panel(f"[bold green]Alfred System Status[/bold green]\n{status_info}", expand=False))
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        console.print(f"[red]✗ Status check failed: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def config(
    action: str = typer.Argument(help="Action: show, set, reset"),
    key: str = typer.Option(None, help="Configuration key"),
    value: str = typer.Option(None, help="Configuration value")
):
    """Manage Alfred configuration."""
    try:
        config_manager = load_config()
        
        if action == "show":
            if key:
                val = config_manager.get(key)
                console.print(f"{key}: {val}")
            else:
                console.print(Panel("[bold]Alfred Configuration[/bold]", expand=False))
                for k, v in config_manager.items():
                    console.print(f"{k}: {v}")
        
        elif action == "set":
            if not key or not value:
                console.print("[red]Error: Set requires key and value[/red]")
                raise typer.Exit(1)
            config_manager.set(key, value)
            console.print(f"[green]✓ Set {key} = {value}[/green]")
        
        elif action == "reset":
            confirm = typer.confirm("Are you sure you want to reset configuration?")
            if confirm:
                config_manager.reset()
                console.print("[green]✓ Configuration reset[/green]")
        
        else:
            console.print("[red]Error: Invalid action. Use: show, set, reset[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        logger.error(f"Config operation failed: {e}")
        console.print(f"[red]✗ Config operation failed: {e}[/red]")
        raise typer.Exit(1)

@app.callback()
def main():
    """Alfred - Personal AI Operator System"""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Show welcome banner on first run
    if len(sys.argv) == 1:
        console.print(Panel(
            "[bold blue]Alfred - Personal AI Operator System[/bold blue]\n\n"
            "Available commands:\n"
            "• [cyan]task[/cyan] - Execute tasks through Alfred\n"
            "• [cyan]memory[/cyan] - Manage persistent memory\n"
            "• [cyan]plugin[/cyan] - Manage plugins\n"
            "• [cyan]status[/cyan] - System status\n"
            "• [cyan]config[/cyan] - Configuration management\n\n"
            "Use [yellow]alfred --help[/yellow] for detailed help.",
            title="Welcome to Alfred",
            border_style="blue"
        ))

if __name__ == "__main__":
    app()