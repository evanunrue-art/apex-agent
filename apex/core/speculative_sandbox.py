import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class SpeculativeSandboxEngine:
    """Manages parallel shadow Git worktrees or temporary worktree copies for speculative branch evaluation."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.worktrees_dir = self.workspace / ".apex" / "worktrees"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, branch_name: str) -> Optional[Path]:
        """Creates an isolated git worktree or shadow sandbox directory."""
        target_dir = self.worktrees_dir / branch_name
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
            
        # Try git worktree add if git repo
        if (self.workspace / ".git").exists():
            try:
                res = subprocess.run(
                    ["git", "worktree", "add", "-d", str(target_dir)],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True
                )
                if res.returncode == 0 and target_dir.exists():
                    return target_dir
            except Exception:
                pass
            
        # Fallback shadow copy
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            for item in self.workspace.glob("*"):
                if item.name not in [".git", ".apex", "node_modules", "__pycache__", ".venv"]:
                    if item.is_file():
                        shutil.copy2(item, target_dir / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, target_dir / item.name, ignore=shutil.ignore_patterns(".git", ".apex", "node_modules", "__pycache__"))
            return target_dir
        except Exception:
            return None

    def cleanup_worktree(self, branch_name: str):
        """Removes worktree directory."""
        target_dir = self.worktrees_dir / branch_name
        try:
            subprocess.run(["git", "worktree", "remove", "--force", str(target_dir)], cwd=self.workspace, capture_output=True)
        except Exception:
            pass
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

    def merge_winning_worktree(self, winning_dir: Path) -> bool:
        """Copies changes from the winning speculative worktree back to main workspace."""
        try:
            for item in winning_dir.rglob("*"):
                if item.is_file() and not any(p in item.parts for p in [".git", ".apex", "__pycache__", "node_modules"]):
                    rel_path = item.relative_to(winning_dir)
                    dest_file = self.workspace / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_file)
            return True
        except Exception:
            return False
