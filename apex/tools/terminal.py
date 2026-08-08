import asyncio
import subprocess
import os
import sys
from typing import Dict, Any, Tuple

class TerminalEngine:
    """Async Shell & Terminal Execution Engine supporting long-running jobs and streaming output."""

    def __init__(self, cwd: str = None):
        self.cwd = cwd or os.getcwd()

    async def run_command(self, command: str, timeout: float = 60.0) -> Tuple[int, str, str]:
        """Runs a shell command asynchronously and returns (exit_code, stdout, stderr)."""
        is_windows = sys.platform == "win32"
        shell_cmd = ["cmd.exe", "/c", command] if is_windows else ["/bin/bash", "-c", command]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *shell_cmd,
                cwd=self.cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                return proc.returncode, stdout, stderr
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return -1, "", f"Command timed out after {timeout} seconds."
        except Exception as e:
            return -1, "", f"Failed to execute command: {str(e)}"
