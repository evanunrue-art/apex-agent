import os
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

class GitCheckpointManager:
    """Manages shadow git commits and snapshots for non-destructive, 1-click rollback & tree exploration."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path.cwd()
        self.snapshots: List[Dict[str, Any]] = []

    def is_git_repo(self) -> bool:
        return (self.workspace_dir / ".git").exists()

    def init_if_needed(self):
        if not self.is_git_repo():
            try:
                subprocess.run(["git", "init"], cwd=self.workspace_dir, check=True, capture_output=True)
                subprocess.run(["git", "config", "user.name", "APEX Agent"], cwd=self.workspace_dir, capture_output=True)
                subprocess.run(["git", "config", "user.email", "apex@local"], cwd=self.workspace_dir, capture_output=True)
            except Exception:
                pass

    def create_snapshot(self, label: str) -> Optional[str]:
        """Create a shadow git commit or stash snapshot."""
        self.init_if_needed()
        try:
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=self.workspace_dir, capture_output=True)
            # Create snapshot commit
            commit_msg = f"APEX Checkpoint [{time.strftime('%H:%M:%S')}]: {label}"
            res = subprocess.run(
                ["git", "commit", "-m", commit_msg, "--allow-empty"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            # Get current SHA
            sha_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.workspace_dir, capture_output=True, text=True)
            sha = sha_res.stdout.strip() if sha_res.returncode == 0 else ""
            
            snapshot = {
                "id": len(self.snapshots) + 1,
                "label": label,
                "sha": sha,
                "timestamp": time.time()
            }
            self.snapshots.append(snapshot)
            return sha
        except Exception:
            return None

    def rollback_to_snapshot(self, sha_or_index: Any) -> bool:
        """Rollback workspace state to a target snapshot or commit SHA."""
        if not self.is_git_repo():
            return False
        try:
            target_sha = sha_or_index
            if isinstance(sha_or_index, int) and 0 < sha_or_index <= len(self.snapshots):
                target_sha = self.snapshots[sha_or_index - 1]["sha"]
                
            res = subprocess.run(["git", "reset", "--hard", str(target_sha)], cwd=self.workspace_dir, capture_output=True)
            subprocess.run(["git", "clean", "-fd"], cwd=self.workspace_dir, capture_output=True)
            return res.returncode == 0
        except Exception:
            return False

    def list_snapshots(self) -> List[Dict[str, Any]]:
        return self.snapshots
