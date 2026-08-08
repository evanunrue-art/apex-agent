import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from apex.config import Config
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.core.speculative_sandbox import SpeculativeSandboxEngine
from apex.tools.sysadmin import SysAdminTool

logger = logging.getLogger("apex.mesh")

class CognitiveMeshSubstrate:
    """24/7 Continuous Ambient Cognitive Mesh Substrate."""

    def __init__(self, config: Config, workspace: Optional[Path] = None):
        self.config = config
        self.workspace = workspace or Path.cwd()
        self.graph = CognitiveKnowledgeGraph(self.workspace / ".apex" / "cognitive_graph.db")
        self.sandbox = SpeculativeSandboxEngine(self.workspace)
        self.sys_tool = SysAdminTool()
        self.running = False

    async def start_mesh(self, interval_sec: float = 20.0):
        """Starts ambient mesh service."""
        self.running = True
        logger.info("APEX Ambient Cognitive Mesh Substrate active.")
        
        # Log mesh startup node in knowledge graph
        self.graph.add_node("system_event", "Ambient Mesh Active", "Cognitive Mesh background substrate started.")
        
        while self.running:
            try:
                metrics = self.sys_tool.get_system_metrics()
                # Run background graph indexing & maintenance if system resources permit
                if metrics["cpu_utilization_pct"] < 90.0:
                    self._perform_ambient_indexing()
            except Exception as e:
                logger.error(f"Mesh cycle error: {e}")
                
            await asyncio.sleep(interval_sec)

    def _perform_ambient_indexing(self):
        """Indexes active project state into the cognitive graph."""
        summary = self.graph.get_summary()
        logger.info(f"Ambient Mesh status: {summary['total_nodes']} graph nodes indexed.")

    def stop_mesh(self):
        self.running = False
