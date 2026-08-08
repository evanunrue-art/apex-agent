import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

class SelfEvolverEngine:
    """Self-Improving Reflexive Engine.
    Tracks failure modes, analyzes execution traces, and mutates meta-instructions.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (Path.cwd() / ".apex" / "meta")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.reflections_file = self.storage_dir / "reflexive_insights.json"
        self._load()

    def _load(self):
        self.insights: List[Dict[str, Any]] = []
        if self.reflections_file.exists():
            try:
                with open(self.reflections_file, "r", encoding="utf-8") as f:
                    self.insights = json.load(f)
            except Exception:
                self.insights = []

    def record_failure_mode(self, task: str, failed_tool: str, error_msg: str, lesson_learned: str):
        """Record a failure pattern and the distilled heuristic lesson."""
        insight = {
            "timestamp": time.time(),
            "task": task,
            "failed_tool": failed_tool,
            "error": error_msg[:500],
            "lesson": lesson_learned
        }
        self.insights.append(insight)
        try:
            with open(self.reflections_file, "w", encoding="utf-8") as f:
                json.dump(self.insights[-100:], f, indent=2)
        except Exception:
            pass

    def get_meta_instructions(self) -> str:
        """Returns dynamic system prompt injections derived from past self-reflections."""
        return "\n".join([f"- Reflexive Rule: {ins['lesson']}" for ins in self.insights[-5:]])

