import os
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

class GitCheckpointManager:
    """Manages persistent shadow Git checkpoints without implicit git init or untracked file deletion."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()
        self.apex_dir = self.workspace_dir / ".apex"
        self.metadata_file = self.apex_dir / "checkpoints.json"

    def is_git_repo(self) -> bool:
        return (self.workspace_dir / ".git").exists()

    def load_snapshots(self) -> List[Dict[str, Any]]:
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_snapshots(self, snapshots: List[Dict[str, Any]]):
        self.apex_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(snapshots, f, indent=2)
        except Exception:
            pass

    def create_snapshot(self, label: str) -> Optional[str]:
        """Create a shadow git commit snapshot IF the workspace is already a git repository."""
        if not self.is_git_repo():
            return None
            
        try:
            # Stage files respecting .gitignore
            subprocess.run(["git", "add", "."], cwd=self.workspace_dir, capture_output=True)

            commit_msg = f"APEX Checkpoint [{time.strftime('%H:%M:%S')}]: {label}"
            res = subprocess.run(
                ["git", "commit", "-m", commit_msg, "--allow-empty"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            sha_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.workspace_dir, capture_output=True, text=True)
            sha = sha_res.stdout.strip() if sha_res.returncode == 0 else ""
            
            snapshots = self.load_snapshots()
            snapshot = {
                "id": len(snapshots) + 1,
                "label": label,
                "sha": sha,
                "timestamp": time.time()
            }
            snapshots.append(snapshot)
            self._save_snapshots(snapshots)
            return sha
        except Exception:
            return None

    def get_rollback_affected_files(self, target_sha_or_index: Any) -> List[str]:
        """Returns list of files that will be affected by a rollback."""
        if not self.is_git_repo():
            return []
        try:
            target_sha = self._resolve_target_sha(target_sha_or_index)
            if not target_sha:
                return []
            res = subprocess.run(
                ["git", "diff", "--name-status", target_sha, "HEAD"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip().split("\n")
        except Exception:
            pass
        return []

    def rollback_to_snapshot(self, target_sha_or_index: Any, confirm: bool = False) -> Tuple[bool, str]:
        """Rollback workspace state to a target snapshot SHA without running implicit git clean -fd."""
        if not self.is_git_repo():
            return False, "Workspace is not a Git repository."
            
        target_sha = self._resolve_target_sha(target_sha_or_index)
        if not target_sha:
            return False, f"Invalid checkpoint target: '{target_sha_or_index}'."
            
        affected = self.get_rollback_affected_files(target_sha)
        if not confirm:
            affected_summary = "\n".join(affected[:10])
            return False, f"Rollback requires explicit confirmation. Affected files ({len(affected)}):\n{affected_summary}\nRe-run with confirm=True or --force."

        try:
            # Perform git reset --hard to target sha without running git clean -fd (preserves untracked files)
            res = subprocess.run(["git", "reset", "--hard", str(target_sha)], cwd=self.workspace_dir, capture_output=True, text=True)
            if res.returncode == 0:
                return True, f"Successfully rolled back to snapshot {target_sha[:8]}."
            return False, f"Git reset failed: {res.stderr}"
        except Exception as e:
            return False, f"Rollback error: {str(e)}"

    def _resolve_target_sha(self, target: Any) -> Optional[str]:
        snapshots = self.load_snapshots()
        if isinstance(target, int) and 0 < target <= len(snapshots):
            return snapshots[target - 1]["sha"]
        target_str = str(target).strip()
        for sn in snapshots:
            if sn["sha"].startswith(target_str) or str(sn["id"]) == target_str:
                return sn["sha"]
        if len(target_str) >= 4:
            return target_str
        return None

    def list_snapshots(self) -> List[Dict[str, Any]]:
        return self.load_snapshots()
