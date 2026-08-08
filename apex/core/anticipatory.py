import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.tools.sysadmin import SysAdminTool
from apex.tools.filesystem import FileSystemTool

class AnticipatoryEngine:
    """Proactive Anticipatory Intelligence Engine.
    Analyzes workspace state, recent commits, system load, and graph nodes to generate pre-emptive recommendations.
    """

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.graph = CognitiveKnowledgeGraph(self.workspace / ".apex" / "cognitive_graph.db")
        self.sys_tool = SysAdminTool()
        self.fs_tool = FileSystemTool(self.workspace)

    def generate_proactive_suggestions(self) -> List[Dict[str, Any]]:
        suggestions = []

        
        # 1. Inspect workspace files for untracked or failing test indicators
        files = self.fs_tool.list_files()
        if "tests" in [Path(f).parts[0] for f in files if Path(f).parts]:
            suggestions.append({
                "type": "test_verification",
                "title": "Automated Test Suite Detected",
                "description": "APEX detected a unit test suite. Run background watchdog verification?",
                "action": "apex daemon"
            })
            
        # 2. Inspect system load telemetry
        metrics = self.sys_tool.get_system_metrics()
        if metrics["memory_percent"] > 80.0:
            suggestions.append({
                "type": "system_optimization",
                "title": "High RAM Utilization",
                "description": f"RAM usage at {metrics['memory_percent']}%. Inspect top memory-consuming processes?",
                "action": "apex sysadmin"
            })
            
        # 3. Check graph nodes for recent research
        graph_summary = self.graph.get_summary()
        suggestions.append({
            "type": "knowledge_indexing",
            "title": "Cognitive Graph Active",
            "description": f"{graph_summary['total_nodes']} knowledge nodes indexed across workspace.",
            "action": "apex graph 'recent'"
        })
        
        return suggestions
