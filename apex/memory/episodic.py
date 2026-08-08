import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

class EpisodicMemory:
    """Stores past problem solving trajectories, solutions, and operational outcomes."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (Path.cwd() / ".apex" / "memory")
        self.storage_file = self.storage_dir / "episodic_sessions.json"
        self._load()

    def _load(self):
        self.episodes: List[Dict[str, Any]] = []
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self.episodes = json.load(f)
            except Exception:
                self.episodes = []

    def save_episode(self, task: str, plan: List[str], tools_used: List[str], outcome: str, success: bool):
        episode = {
            "timestamp": time.time(),
            "task": task,
            "plan": plan,
            "tools_used": tools_used,
            "outcome": outcome,
            "success": success
        }
        self.episodes.append(episode)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.episodes[-200:], f, indent=2)  # Keep last 200 episodes
        except Exception:
            pass

    def search_similar_episodes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Simple TF/Keyword matching to find past similar episodes."""
        query_words = set(query.lower().split())
        scored = []
        for ep in self.episodes:
            ep_text = (ep["task"] + " " + " ".join(ep.get("tools_used", []))).lower()
            score = len(query_words.intersection(set(ep_text.split())))
            if score > 0:
                scored.append((score, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]
