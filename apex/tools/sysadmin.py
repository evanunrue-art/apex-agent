import os
import sys
import psutil
import socket
import shutil
import subprocess
from typing import Dict, Any, List

class SysAdminTool:
    """System administration, process monitoring, and network/environment diagnostic tool."""

    def get_system_metrics(self) -> Dict[str, Any]:
        """Returns active CPU, Memory, Disk, and Network stats."""
        cpu_pct = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(os.getcwd())
        
        return {
            "cpu_utilization_pct": cpu_pct,
            "memory_total_gb": round(mem.total / (1024 ** 3), 2),
            "memory_used_gb": round(mem.used / (1024 ** 3), 2),
            "memory_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "disk_percent": disk.percent
        }

    def list_running_processes(self, top_n: int = 15) -> List[Dict[str, Any]]:
        """Lists top processes by CPU/Memory usage."""
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda p: p.get('cpu_percent') or 0, reverse=True)
        return procs[:top_n]

    def check_network_port(self, host: str = "127.0.0.1", port: int = 80) -> str:
        """Checks connectivity to a host and port."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        try:
            res = s.connect_ex((host, port))
            s.close()
            if res == 0:
                return f"Port {port} on {host} is OPEN."
            return f"Port {port} on {host} is CLOSED (Code {res})."
        except Exception as e:
            return f"Failed to check port {port} on {host}: {e}"
