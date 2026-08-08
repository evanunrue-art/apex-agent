from pathlib import Path
from typing import Optional, Dict, Any, List
from apex.memory.episodic import EpisodicMemory
from apex.memory.semantic import SemanticMemory
from apex.memory.procedural import ProceduralMemory

class MemoryManager:
    """Unified 4-Tier Cognitive Memory Coordinator for APEX."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.episodic = EpisodicMemory(self.workspace / ".apex" / "memory")
        self.semantic = SemanticMemory(self.workspace)
        self.procedural = ProceduralMemory(self.workspace / ".apex" / "skills")

    def initialize(self):
        """Index semantic code structure and load procedural skills."""
        self.semantic.index_workspace()

    def get_context_snapshot(self, query: str) -> Dict[str, Any]:
        """Produce enriched memory context to pass to the LLM orchestrator."""
        past_episodes = self.episodic.search_similar_episodes(query, top_k=2)
        symbols = self.semantic.lookup_symbol(query.strip())
        available_skills = self.procedural.list_skills()

        return {
            "past_episodes": past_episodes,
            "relevant_symbols": symbols,
            "skills": available_skills,
            "semantic_summary": self.semantic.get_summary()
        }
