from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.syntax import Syntax
from apex.config import detect_hardware, HardwareSpecs

console = Console(legacy_windows=False)


def render_banner() -> Panel:
    banner_text = Text()
    banner_text.append("⚡ APEX AGENTIC CLI ", style="bold magenta")
    banner_text.append("v0.1.0\n", style="dim white")
    banner_text.append("Autonomous Tree-Search (LATS) • 4-Tier Cognitive Memory • DGX Local/Cloud Hybrid Engine", style="italic cyan")
    return Panel(banner_text, border_style="bright_blue", title="APEX Cognitive Terminal", title_align="left")

def render_status_bar(gpu_info: HardwareSpecs, active_model: str = "Hybrid (DGX/Cloud)") -> Table:
    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="center")
    table.add_column(justify="right")
    
    gpu_status = f"🎮 GPU: {gpu_info.gpu_name} ({gpu_info.gpu_memory_free_mb:.0f}MB Free)" if gpu_info.has_nvidia_gpu else "💻 CPU Mode"
    cpu_status = f"🖥️ CPU: {gpu_info.cpu_cores} Cores | RAM: {gpu_info.total_ram_gb}GB"
    model_status = f"🤖 Engine: {active_model}"
    
    table.add_row(
        Text(gpu_status, style="green" if gpu_info.has_nvidia_gpu else "yellow"),
        Text(cpu_status, style="cyan"),
        Text(model_status, style="bold magenta")
    )
    return table

def render_thought_panel(thought_text: str) -> Panel:
    return Panel(
        Text(thought_text, style="white"),
        title="🧠 Agent Reasoning Stream",
        border_style="magenta"
    )

def render_observation_panel(observation_text: str) -> Panel:
    return Panel(
        Text(observation_text[:1500], style="green"),
        title="👁️ Environment Observation",
        border_style="green"
    )
