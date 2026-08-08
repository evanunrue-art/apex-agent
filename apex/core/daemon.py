import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from apex.config import Config
from apex.core.orchestrator import AgentOrchestrator
from apex.tools.sysadmin import SysAdminTool

logger = logging.getLogger("apex.daemon")

class ApexAutonomousDaemon:
    """Continuous Background Autonomous Watchdog Daemon.
    Monitors codebase health, system load, runs background verification, and auto-heals failures.
    """

    def __init__(self, config: Config, workspace: Optional[Path] = None):
        self.config = config
        self.workspace = workspace or Path.cwd()
        self.orchestrator = AgentOrchestrator(config)
        self.sys_tool = SysAdminTool()
        self.running = False

    async def start(self, poll_interval_sec: float = 30.0):
        """Starts continuous background watchdog loop."""
        self.running = True
        logger.info("APEX Autonomous Watchdog Daemon started.")
        
        while self.running:
            try:
                metrics = self.sys_tool.get_system_metrics()
                # Check system load safety
                if metrics["cpu_utilization_pct"] < 85.0 and metrics["memory_percent"] < 90.0:
                    # Run quick background verification
                    await self._perform_background_watchdog()
            except Exception as e:
                logger.error(f"Daemon cycle error: {e}")
                
            await asyncio.sleep(poll_interval_sec)

    async def _perform_background_watchdog(self):
        """Executes background health checks."""
        # 1. Check for broken python unit tests in background
        test_file = self.workspace / "tests"
        if test_file.exists():
            proc = await asyncio.create_subprocess_exec(
                "python", "-m", "unittest", "discover", "-s", "tests",
                cwd=str(self.workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning("Background Watchdog detected failing tests! Triggering auto-healing...")
                # Auto-heal failure using orchestrator
                error_log = stderr.decode("utf-8", errors="ignore")
                goal = f"Fix failing unit tests detected by Watchdog:\n{error_log[:1000]}"
                async for event in self.orchestrator.run(goal):
                    pass

    def stop(self):
        self.running = False
