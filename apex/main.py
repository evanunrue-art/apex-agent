import sys
import os
import asyncio
import typer
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from apex.config import Config, detect_hardware
from apex.ui.tui import ApexInteractiveTUI
from apex.tools.git_checkpoint import GitCheckpointManager
from apex.memory.memory_manager import MemoryManager

app = typer.Typer(
    name="apex",
    help="APEX: Next-Gen Autonomous CLI Agent powered by LATS Tree-Search, Tiered Memory & DGX Hybrid Engine."
)
console = Console()

@app.command()
def run(
    goal: str = typer.Argument(..., help="The coding goal or instruction for APEX to achieve."),
    tree_search: bool = typer.Option(True, "--tree-search/--no-tree-search", help="Enable Language Agent Tree Search (LATS)."),
    local_only: bool = typer.Option(False, "--local-only", help="Force execution strictly using local DGX endpoints.")
):
    """Execute a task with APEX autonomous agent."""
    config = Config.load()
    if local_only:
        config.primary_provider = "local_dgx"
    
    tui = ApexInteractiveTUI(config)
    asyncio.run(tui.run_goal(goal))

@app.command()
def undo():
    """Rollback workspace to the previous shadow Git checkpoint snapshot."""
    git_mgr = GitCheckpointManager()
    snapshots = git_mgr.list_snapshots()
    if not snapshots:
        console.print("[yellow]No snapshots recorded in this session.[/yellow]")
        return
    latest = snapshots[-1]
    ok = git_mgr.rollback_to_snapshot(latest["sha"])
    if ok:
        console.print(f"[bold green]✓ Successfully rolled back to snapshot #{latest['id']}: {latest['label']}[/bold green]")
    else:
        console.print("[bold red]✗ Failed to rollback workspace state.[/bold red]")

@app.command()
def memory():
    """Display 4-Tier Cognitive Memory status (Episodic, Semantic, Procedural, Working)."""
    mem = MemoryManager()
    mem.initialize()
    
    table = Table(title="🧠 APEX 4-Tier Cognitive Memory Status", border_style="cyan")
    table.add_column("Tier", style="bold magenta")
    table.add_column("Description", style="white")
    table.add_column("Current State", style="green")
    
    table.add_row("Working Memory", "Dynamic context budget & compressed message window", "Active (128k max tokens)")
    table.add_row("Episodic Memory", "Session trajectory vector/JSON store", f"{len(mem.episodic.episodes)} episodes recorded")
    table.add_row("Semantic Memory", "Codebase symbol & AST dependency graph", mem.semantic.get_summary())
    table.add_row("Procedural Memory", "Voyager dynamic skill store (.apex/skills/)", f"{len(mem.procedural.list_skills())} synthesized skills")
    
    console.print(table)

@app.command()
def skills():
    """List dynamically synthesized Voyager skills."""
    mem = MemoryManager()
    skills_list = mem.procedural.list_skills()
    if not skills_list:
        console.print("[dim]No procedural skills synthesized yet. APEX automatically synthesizes skills during task execution.[/dim]")
        return
        
    table = Table(title="⚡ Synthesized Procedural Skills", border_style="green")
    table.add_column("Name", style="bold yellow")
    table.add_column("Language", style="cyan")
    table.add_column("File", style="white")
    
    for sk in skills_list:
        table.add_row(sk.get("name"), sk.get("language"), sk.get("file"))
    console.print(table)

@app.command()
def dgx():
    """Inspect local NVIDIA DGX hardware specs and local model endpoints."""
    specs = detect_hardware()
    config = Config.load()
    
    console.print("[bold cyan]🎮 NVIDIA DGX Hardware & Local Engine Diagnostic[/bold cyan]")
    console.print(f"GPU Detected: [bold green]{specs.gpu_name}[/bold green]" if specs.has_nvidia_gpu else "[yellow]No NVIDIA GPU detected (CPU mode)[/yellow]")
    if specs.has_nvidia_gpu:
        console.print(f"VRAM Free: [green]{specs.gpu_memory_free_mb:.0f} MB[/green] / [cyan]{specs.gpu_memory_total_mb:.0f} MB[/cyan]")
    console.print(f"CPU Cores: {specs.cpu_cores} | RAM: {specs.total_ram_gb} GB")
    console.print(f"Local Endpoint: [bold blue]{config.local_dgx_endpoint}[/bold blue]")
    console.print(f"Local Model Target: [bold magenta]{config.local_model}[/bold magenta]")

def main():
    app()

if __name__ == "__main__":
    main()
