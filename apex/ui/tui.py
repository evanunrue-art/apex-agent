import asyncio
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from apex.config import Config, detect_hardware
from apex.core.orchestrator import AgentOrchestrator
from apex.ui.views import render_banner, render_status_bar, render_thought_panel, render_observation_panel

console = Console(legacy_windows=False)

class ApexInteractiveTUI:
    """Interactive TUI Dashboard for APEX with workspace and governance propagation."""

    def __init__(self, config: Config, workspace: Optional[Path] = None):
        self.config = config
        self.orchestrator = AgentOrchestrator(config, workspace=workspace)
        self.hardware = detect_hardware()
        self.approval_callback = None

    async def run_goal(self, goal: str, is_interactive: bool = True):
        layout = Layout()
        layout.split(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["header"].update(render_banner())
        layout["footer"].update(render_status_bar(self.hardware, self.config.primary_provider))
        
        layout["main"].split_column(
            Layout(name="thought", ratio=1),
            Layout(name="observation", ratio=1)
        )
        
        layout["thought"].update(render_thought_panel("Initializing goal..."))
        layout["observation"].update(render_observation_panel("Awaiting agent actions..."))

        with Live(layout, refresh_per_second=4, console=console):
            async for event in self.orchestrator.run(
                goal, 
                is_interactive=is_interactive, 
                approval_callback=self.approval_callback
            ):
                event_type = event.get("type")
                if event_type == "thought":
                    layout["thought"].update(render_thought_panel(event.get("text", "")))
                elif event_type == "observation":
                    layout["observation"].update(render_observation_panel(event.get("observation", "")))
                elif event_type == "governance_denial":
                    layout["observation"].update(render_observation_panel(f"⚠️ {event.get('reason', '')}"))
                elif event_type == "final":
                    layout["thought"].update(render_thought_panel(f"🎉 COMPLETED:\n{event.get('content', '')}"))
                await asyncio.sleep(0.05)
