import sys
import os
import json
import asyncio
import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from apex.config import Config, detect_hardware, validate_workspace_path
from apex.ui.tui import ApexInteractiveTUI
from apex.tools.git_checkpoint import GitCheckpointManager
from apex.memory.memory_manager import MemoryManager
from apex.tools.registry import ToolRegistry
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.core.governance import GovernancePolicyEngine

app = typer.Typer(
    name="apex",
    help="APEX CLI: Autonomous Agentic Platform powered by LATS Tree-Search, Cognitive Graph & DGX Engine."
)
console = Console(legacy_windows=False)

@app.command()
def init(
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Workspace directory to initialize.")
):
    """Initialize an APEX workspace configuration and memory structure."""
    target_workspace = validate_workspace_path(workspace)
    config = Config(apex_dir=target_workspace / ".apex")
    config.save()
    console.print(f"[bold green]✓ Successfully initialized APEX workspace at '{target_workspace}'[/bold green]")

@app.command()
def run(
    goal: str = typer.Argument(..., help="The goal or instruction for APEX to achieve."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory."),
    tree_search: bool = typer.Option(True, "--tree-search/--no-tree-search", help="Enable Language Agent Tree Search (LATS)."),
    local_only: bool = typer.Option(False, "--local-only", help="Force execution strictly using local DGX endpoints."),
    interactive: bool = typer.Option(True, "--interactive/--unattended", help="Interactive mode allowing manual approval prompts.")
):
    """Execute a task with APEX autonomous agent."""
    target_workspace = validate_workspace_path(workspace)
    config = Config.load(target_workspace / ".apex" / "config.yaml")
    if local_only:
        config.primary_provider = "local_dgx"
    
    def _prompt_approval(tool: str, args: dict, reason: str) -> bool:
        console.print(f"\n[bold yellow]⚠️ Governance Confirmation Required:[/bold yellow] Executing '{tool}' with args {json.dumps(args)}")
        console.print(f"[dim]Reason: {reason}[/dim]")
        return typer.confirm("Do you approve executing this action?")

    tui = ApexInteractiveTUI(config, workspace=target_workspace)
    tui.approval_callback = _prompt_approval
    asyncio.run(tui.run_goal(goal, is_interactive=interactive))

@app.command()
def read(
    file_path: str = typer.Argument(..., help="Path to PDF, PPTX, DOCX, or text file to parse and ingest into Knowledge Graph."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Parse PDF, PPTX, DOCX, or text reference files for knowledge synthesis."""
    target_workspace = validate_workspace_path(workspace)
    from apex.tools.document_ingestion import DocumentIngestionTool
    tool = DocumentIngestionTool(workspace=target_workspace)
    console.print(f"[bold cyan]📄 APEX Document Processor reading: {file_path}...[/bold cyan]")
    res = tool.ingest_and_index(file_path)
    console.print(res)

@app.command()
def ask(
    question: str = typer.Argument(..., help="Ask APEX anything in plain natural language."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Zero-friction plain English Q&A."""
    target_workspace = validate_workspace_path(workspace)
    config = Config.load(target_workspace / ".apex" / "config.yaml")
    tui = ApexInteractiveTUI(config, workspace=target_workspace)
    asyncio.run(tui.run_goal(question, is_interactive=False))

@app.command()
def intent(
    user_intent: str = typer.Argument(..., help="High-level human intent to execute through the Ephemeral Intent Engine."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Execute high-level human intent through Ephemeral Intent Workspaces."""
    target_workspace = validate_workspace_path(workspace)
    from apex.core.intent_engine import EphemeralIntentEngine
    config = Config.load(target_workspace / ".apex" / "config.yaml")
    engine = EphemeralIntentEngine(config)
    
    console.print(f"[bold magenta]⚡ APEX Intent Engine processing: '{user_intent}'...[/bold magenta]")
    
    async def _run_intent():
        async for event in engine.execute_intent(user_intent):
            ev_type = event.get("type")
            if ev_type == "status":
                console.print(f"[dim cyan]{event.get('message')}[/dim cyan]")
            elif ev_type == "action":
                tool = event.get("tool")
                risk = event.get("risk_level", "LOW")
                console.print(f"[bold yellow]▶ Action:[/bold yellow] {tool} [dim]({risk} Risk)[/dim]")
            elif ev_type == "final":
                console.print(f"[bold green]✓ Intent Complete:[/bold green]\n{event.get('content')}")

    asyncio.run(_run_intent())

@app.command()
def research(
    topic: str = typer.Argument(..., help="Topic for multi-query autonomous web search synthesis."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Run autonomous multi-query web search synthesis."""
    target_workspace = validate_workspace_path(workspace)
    from apex.tools.research_synthesis import ResearchSynthesisTool
    tool = ResearchSynthesisTool()
    console.print(f"[bold cyan]🔍 APEX Research Synthesizer running: '{topic}'...[/bold cyan]")
    
    async def _run_res():
        report = await tool.search_and_synthesize(topic)
        console.print(report)

    asyncio.run(_run_res())

@app.command()
def analyze(
    csv_or_json_path: str = typer.Argument(..., help="Path to CSV or JSON dataset for summary statistics."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Compute summary statistics for a dataset."""
    target_workspace = validate_workspace_path(workspace)
    from apex.tools.data_analysis import DataAnalysisTool
    tool = DataAnalysisTool(workspace=target_workspace)
    console.print(f"[bold green]📊 APEX Data Analyzer inspecting: '{csv_or_json_path}'...[/bold green]")
    res = tool.analyze_dataset(csv_or_json_path)
    console.print(res)

@app.command()
def sysadmin():
    """Display system hardware telemetry and top active processes."""
    from apex.tools.sysadmin import SysAdminTool
    tool = SysAdminTool()
    metrics = tool.get_system_metrics()
    processes = tool.list_running_processes(top_n=8)
    
    console.print("[bold cyan]💻 APEX SysAdmin Telemetry[/bold cyan]")
    console.print(f"CPU Utilization: [green]{metrics.get('cpu_utilization_pct')}%[/green]")
    console.print(f"Memory Usage: [green]{metrics.get('memory_used_gb')} GB / {metrics.get('memory_total_gb')} GB ({metrics.get('memory_used_pct')}%)[/green]")
    
    table = Table(title="Top Running System Processes", border_style="cyan")
    table.add_column("PID", style="bold yellow")
    table.add_column("Process Name", style="white")
    table.add_column("CPU %", style="green")
    table.add_column("Memory %", style="cyan")
    
    for p in processes:
        table.add_row(str(p.get("pid")), str(p.get("name")), f"{p.get('cpu_percent'):.1f}", f"{p.get('memory_percent'):.1f}")
    console.print(table)

@app.command()
def debate(
    goal: str = typer.Argument(..., help="Overall task goal for red-team cross-examination."),
    proposal: str = typer.Argument(..., help="Proposed technical solution to cross-examine.")
):
    """Run adversarial multi-model red-team audit of a proposed solution."""
    from apex.core.adversarial_debate import AdversarialDebateEngine
    config = Config.load()
    engine = AdversarialDebateEngine(config)
    console.print(f"[bold magenta]⚔️ APEX Adversarial Debate Engine auditing proposal...[/bold magenta]")
    
    async def _run_deb():
        result = await engine.conduct_debate(goal, proposal)
        console.print(f"[bold yellow]Audit Status:[/bold yellow] {result.get('consensus')}")
        console.print(f"[bold red]Identified Flaws:[/bold red]\n" + "\n".join(result.get("flaws", [])))
        console.print(f"[bold green]Refined Solution:[/bold green]\n{result.get('refined_solution')}")

    asyncio.run(_run_deb())

@app.command()
def digest(
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Generate a 2-minute daily productivity digest and activity summary."""
    target_workspace = validate_workspace_path(workspace)
    from apex.core.daily_digest import DailyDigestGenerator
    generator = DailyDigestGenerator(workspace=target_workspace)
    doc = generator.format_markdown_digest()
    console.print(doc)

@app.command()
def suggest(
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Display pre-emptive anticipatory intelligence recommendations."""
    target_workspace = validate_workspace_path(workspace)
    from apex.core.anticipatory import AnticipatoryEngine
    engine = AnticipatoryEngine(workspace=target_workspace)
    suggestions = engine.generate_proactive_suggestions()
    
    table = Table(title="💡 APEX Pre-Emptive Anticipatory Suggestions", border_style="yellow")
    table.add_column("Category", style="bold cyan")
    table.add_column("Recommendation", style="white")
    table.add_column("Suggested Action", style="bold green")
    
    for s in suggestions:
        table.add_row(s.get("title"), s.get("description"), s.get("action"))
    console.print(table)

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address to bind local web dashboard."),
    port: int = typer.Option(7860, "--port", "-p", help="Port to host local web dashboard."),
    token: str = typer.Option(None, "--token", "-t", help="Security token required for non-loopback binding.")
):
    """Launch APEX Local Web Dashboard."""
    from apex.ui.web_server import start_web_server
    start_web_server(host=host, port=port, auth_token=token)

@app.command()
def graph(
    query: str = typer.Argument(..., help="Search query for Omnipresent Cognitive Knowledge Graph."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Search and query the local Cognitive Knowledge Graph."""
    target_workspace = validate_workspace_path(workspace)
    graph_db = CognitiveKnowledgeGraph(db_path=target_workspace / ".apex" / "cognitive_graph.db")
    results = graph_db.search_graph(query)
    
    table = Table(title=f"🧠 Cognitive Knowledge Graph Results: '{query}'", border_style="magenta")
    table.add_column("Type", style="bold cyan")
    table.add_column("Title", style="yellow")
    table.add_column("Timestamp", style="white")
    
    for r in results:
        table.add_row(r.get("node_type"), r.get("title"), str(r.get("timestamp")))
    console.print(table)

@app.command()
def policy():
    """Display safety risk levels and policy governance rules."""
    gov = GovernancePolicyEngine()
    
    table = Table(title="🛡️ APEX Governance Policy & Risk Classifications", border_style="green")
    table.add_column("Tool Action", style="bold yellow")
    table.add_column("Risk Classification", style="cyan")
    
    for tool_name, risk in gov.risk_rules.items():
        table.add_row(tool_name, risk.value)
    console.print(table)

@app.command()
def undo(
    target: str = typer.Option(None, "--target", "-t", help="Target checkpoint SHA or index."),
    force: bool = typer.Option(False, "--force", "-f", help="Force rollback without interactive confirmation."),
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Rollback workspace to a previous Git checkpoint snapshot with file previews and confirmation."""
    target_workspace = validate_workspace_path(workspace)
    git_mgr = GitCheckpointManager(workspace_dir=target_workspace)
    snapshots = git_mgr.list_snapshots()
    if not snapshots:
        console.print("[yellow]No snapshots recorded in this workspace session.[/yellow]")
        return
        
    target_sha = target or snapshots[-1]["sha"]
    affected = git_mgr.get_rollback_affected_files(target_sha)
    
    console.print(f"[bold yellow]Affected Files for Rollback ({len(affected)} files):[/bold yellow]")
    for line in affected[:10]:
        console.print(f"  {line}")
    if len(affected) > 10:
        console.print(f"  ... and {len(affected)-10} more files.")
        
    if not force:
        confirm = typer.confirm("Are you sure you want to rollback workspace state?")
        if not confirm:
            console.print("[yellow]Rollback cancelled.[/yellow]")
            return
            
    ok, msg = git_mgr.rollback_to_snapshot(target_sha, confirm=True)
    if ok:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✗ {msg}[/bold red]")

@app.command()
def memory(
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """Display 4-Tier Cognitive Memory status (Episodic, Semantic, Procedural, Working)."""
    target_workspace = validate_workspace_path(workspace)
    mem = MemoryManager(workspace=target_workspace)
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
def skills(
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace directory.")
):
    """List synthesized procedural skills stored in .apex/skills/."""
    target_workspace = validate_workspace_path(workspace)
    mem = MemoryManager(workspace=target_workspace)
    skills_list = mem.procedural.list_skills()
    
    table = Table(title="🛠️ APEX Synthesized Procedural Skills", border_style="green")
    table.add_column("Skill Name", style="bold yellow")
    table.add_column("Path", style="cyan")
    
    for s in skills_list:
        table.add_row(s.get("name"), s.get("path"))
    console.print(table)

@app.command()
def dgx():
    """Inspect local NVIDIA DGX hardware specs and local model endpoints."""
    specs = detect_hardware()
    config = Config.load()
    
    console.print("[bold cyan]🎮 NVIDIA DGX Hardware & Local Engine Diagnostic[/bold cyan]")
    console.print(f"GPU Detected: [bold green]{specs.gpu_name}[/bold green]" if specs.has_nvidia_gpu else "[yellow]No NVIDIA GPU detected (CPU mode)[/yellow]")
    if specs.has_nvidia_gpu:
        vram_text = f"{specs.gpu_memory_free_mb:.0f} MB Free / {specs.gpu_memory_total_mb:.0f} MB Total"
        if specs.is_unified_memory:
            vram_text += " (Unified Memory)"
        console.print(f"VRAM / Memory: [green]{vram_text}[/green]")
    console.print(f"CPU Cores: {specs.cpu_cores} | RAM: {specs.total_ram_gb} GB")
    console.print(f"Local Endpoint: [bold blue]{config.local_dgx_endpoint}[/bold blue]")
    console.print(f"Local Model Target: [bold magenta]{config.local_model}[/bold magenta]")

@app.command()
def mesh():
    """Start ambient 24/7 background mesh service for continuous monitoring."""
    from apex.core.cognitive_mesh import CognitiveMeshSubstrate
    config = Config.load()
    mesh_service = CognitiveMeshSubstrate(config)
    console.print("[bold magenta]🌐 APEX Cognitive Mesh Substrate starting...[/bold magenta]")
    
    async def _run_mesh():
        await mesh_service.start_mesh_cycle()

    asyncio.run(_run_mesh())

@app.command()
def daemon():
    """Run autonomous watchdog daemon."""
    from apex.core.daemon import ApexAutonomousDaemon
    config = Config.load()
    daemon_svc = ApexAutonomousDaemon(config)
    console.print("[bold yellow]🐕 APEX Autonomous Watchdog Daemon starting...[/bold yellow]")
    
    async def _run_daemon():
        res = await daemon_svc.run_watchdog_cycle()
        console.print(f"Daemon Watchdog Cycle Result: {res}")

    asyncio.run(_run_daemon())

def main():
    app()

if __name__ == "__main__":
    main()
