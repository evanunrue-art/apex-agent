import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.memory.memory_manager import MemoryManager

class DailyDigestGenerator:
    """Generates 2-minute daily productivity summaries and task digests."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.graph = CognitiveKnowledgeGraph(self.workspace / ".apex" / "cognitive_graph.db")
        self.memory = MemoryManager(self.workspace)

    def generate_digest(self) -> Dict[str, Any]:
        """Synthesizes task history, knowledge nodes, and skill state for the daily digest."""
        self.memory.initialize()
        recent_nodes = self.graph.search_graph("", limit=10)
        skills = self.memory.procedural.list_skills()
        episodes = self.memory.episodic.episodes
        
        return {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_intents_executed": len(recent_nodes),
            "episodes_recorded": len(episodes),
            "skills_available": len(skills),
            "recent_activities": [r.get("title") for r in recent_nodes[:5]]
        }

    def format_markdown_digest(self) -> str:
        data = self.generate_digest()
        doc = f"# 📋 APEX Daily Productivity Digest [{data['date']}]\n\n"
        doc += f"- **Intents Executed**: {data['total_intents_executed']}\n"
        doc += f"- **Session Episodes Recorded**: {data['episodes_recorded']}\n"
        doc += f"- **Synthesized Skills Available**: {data['skills_available']}\n\n"
        doc += "## Recent Activity Highlights\n"
        for act in data["recent_activities"]:
            doc += f"- {act}\n"
        return doc
