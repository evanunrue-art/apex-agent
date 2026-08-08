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
from apex.tools.registry import ToolRegistry
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.core.governance import GovernancePolicyEngine

app = typer.Typer(
    name="apex",
    help="APEX OS: Universal Autonomous Cognitive OS Substrate powered by LATS Tree-Search, Cognitive Graph & DGX Engine."
)
console = Console(legacy_windows=False)

@app.command()
def run(
    goal: str = typer.Argument(..., help="The goal or instruction for APEX to achieve (Coding, Research, Data Analysis, SysAdmin)."),
    tree_search: bool = typer.Option(True, "--tree-search/--no-tree-search", help="Enable Language Agent Tree Search (LATS)."),
    local_only: bool = typer.Option(False, "--local-only", help="Force execution strictly using local DGX endpoints.")
):
    """Execute any task across coding, research, data analysis, or sysadmin."""
    config = Config.load()
    if local_only:
        config.primary_provider = "local_dgx"
    
    tui = ApexInteractiveTUI(config)
    asyncio.run(tui.run_goal(goal))

@app.command()
def read(
    file_path: str = typer.Argument(..., help="Path to PDF, PPTX, DOCX, or text file to parse and ingest into Knowledge Graph.")
):
    """Parse PDF, PPTX, DOCX, or text reference files for knowledge synthesis."""
    from apex.tools.document_ingestion import DocumentIngestionTool
    tool = DocumentIngestionTool()
    console.print(f"[bold cyan]📄 APEX Document Processor reading: {file_path}...[/bold cyan]")
    res = tool.ingest_and_index(file_path)
    console.print(res)

@app.command()
def digest():
    """Generate a 2-minute daily productivity digest and activity summary."""

    from apex.core.daily_digest import DailyDigestGenerator
    generator = DailyDigestGenerator()
    doc = generator.format_markdown_digest()
    console.print(doc)

@app.command()
def suggest():
    """Display pre-emptive anticipatory intelligence recommendations."""
    from apex.core.anticipatory import AnticipatoryEngine
    engine = AnticipatoryEngine()
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
    port: int = typer.Option(7860, "--port", "-p", help="Port to host the local web dashboard.")
):

    """Launch APEX Universal Web Dashboard for instant browser access."""
    from apex.ui.web_server import start_web_server
    start_web_server(port=port)

@app.command()
def ask(
    question: str = typer.Argument(..., help="Ask APEX anything in plain natural language.")
):
    """Zero-friction plain English Q&A."""
    config = Config.load()
    tui = ApexInteractiveTUI(config)
    asyncio.run(tui.run_goal(question))


@app.command()
def intent(
    user_intent: str = typer.Argument(..., help="High-level human intent to execute through the Ephemeral Intent Engine.")
):

    """Execute high-level human intent through Ephemeral Intent Workspaces."""
    from apex.core.intent_engine import EphemeralIntentEngine
    config = Config.load()
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
def graph(
    query: str = typer.Argument(..., help="Search query for Omnipresent Cognitive Knowledge Graph.")
):
    """Search and query the local Cognitive Knowledge Graph."""
    graph_db = CognitiveKnowledgeGraph()
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
def mesh():
    """Start APEX 24/7 Continuous Ambient Cognitive Mesh Substrate."""
    from apex.core.cognitive_mesh import CognitiveMeshSubstrate
    config = Config.load()
    mesh_service = CognitiveMeshSubstrate(config)
    console.print("[bold cyan]🌌 APEX 24/7 Ambient Cognitive Mesh Substrate activated. Press Ctrl+C to stop.[/bold cyan]")
    try:
        asyncio.run(mesh_service.start_mesh(interval_sec=10.0))
    except KeyboardInterrupt:
        mesh_service.stop_mesh()
        console.print("\n[yellow]Cognitive Mesh stopped.[/yellow]")

@app.command()
def research(
    topic: str = typer.Argument(..., help="Research topic or question to synthesize.")
):
    """Perform autonomous multi-angle deep web research and synthesis."""
    console.print(f"[bold cyan]🔍 APEX Research Engine scanning: {topic}...[/bold cyan]")
    reg = ToolRegistry()
    res = asyncio.run(reg.execute("search_and_synthesize", {"topic": topic}))
    console.print(res)

@app.command()
def analyze(
    dataset: str = typer.Argument(..., help="CSV or JSON dataset file path to analyze.")
):
    """Perform automated dataset summary statistics and column analysis."""
    console.print(f"[bold green]📊 APEX Data Analytics processing: {dataset}...[/bold green]")
    reg = ToolRegistry()
    res = asyncio.run(reg.execute("analyze_dataset", {"csv_or_json_path": dataset}))
    console.print(res)

@app.command()
def sysadmin():
    """Run system health telemetry, CPU/Memory/Disk stats, and process inspect."""
    console.print("[bold magenta]💻 APEX System Telemetry & Process Health[/bold magenta]")
    reg = ToolRegistry()
    metrics = asyncio.run(reg.execute("get_system_metrics", {}))
    procs = asyncio.run(reg.execute("list_running_processes", {"top_n": 10}))
    console.print(f"[cyan]System Metrics:[/cyan]\n{metrics}")
    console.print(f"[yellow]Top Running Processes:[/yellow]\n{procs}")

@app.command()
def debate(
    goal: str = typer.Argument(..., help="Problem goal to subject to multi-model adversarial debate."),
    proposal: str = typer.Argument(..., help="Initial solution proposal.")
):
    """Subject a proposal to Multi-Model Adversarial Red-Team Debate."""
    from apex.core.adversarial_debate import AdversarialDebateEngine
    config = Config.load()
    engine = AdversarialDebateEngine(config)
    console.print(f"[bold red]⚔️ APEX Adversarial Multi-Model Debate initiating for: {goal}...[/bold red]")
    hardened, score = asyncio.run(engine.debate_and_refine(goal, proposal))
    console.print(f"[bold green]✓ Hardened Consensus Solution (Confidence {score*100:.0f}%):[/bold green]\n{hardened}")

@app.command()
def daemon():
    """Launch APEX Continuous Background Autonomous Watchdog Daemon."""
    from apex.core.daemon import ApexAutonomousDaemon
    config = Config.load()
    daemon_engine = ApexAutonomousDaemon(config)
    console.print("[bold cyan]🔄 APEX Background Autonomous Watchdog Daemon launched. Press Ctrl+C to stop.[/bold cyan]")
    try:
        asyncio.run(daemon_engine.start(poll_interval_sec=15.0))
    except KeyboardInterrupt:
        daemon_engine.stop()
        console.print("\n[yellow]Daemon stopped.[/yellow]")

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
