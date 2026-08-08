import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional

class FileSystemTool:
    """High-performance file system & code inspection utilities."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()

    def view_file(self, relative_path: str, start_line: int = 1, end_line: int = 400) -> str:
        target = self.workspace / relative_path
        if not target.exists() or not target.is_file():
            return f"Error: File '{relative_path}' not found."
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            sliced = lines[max(0, start_line - 1):end_line]
            formatted = [f"{i + max(1, start_line):4d} | {line}" for i, line in enumerate(sliced)]
            return "".join(formatted)
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, relative_path: str, content: str) -> str:
        target = self.workspace / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {relative_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def replace_content(self, relative_path: str, target_string: str, replacement_string: str) -> str:
        target = self.workspace / relative_path
        if not target.exists():
            return f"Error: File '{relative_path}' does not exist."
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            if target_string not in content:
                return f"Error: Target string not found in {relative_path}"
            new_content = content.replace(target_string, replacement_string, 1)
            target.write_text(new_content, encoding="utf-8")
            return f"Successfully replaced target string in {relative_path}"
        except Exception as e:
            return f"Error updating file: {e}"

    def grep_search(self, pattern: str, file_pattern: str = "*") -> List[Dict[str, Any]]:
        results = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for path in self.workspace.rglob(file_pattern):
                if path.is_file() and not any(p in path.parts for p in [".git", ".apex", "__pycache__", "node_modules", ".venv"]):
                    try:
                        with open(path, "r", encoding="utf-8", errors="replace") as f:
                            for idx, line in enumerate(f, 1):
                                if regex.search(line):
                                    results.append({
                                        "file": str(path.relative_to(self.workspace)),
                                        "line": idx,
                                        "content": line.strip()
                                    })
                                    if len(results) >= 100:
                                        break
                    except Exception:
                        pass
        except Exception:
            pass
        return results

    def list_files(self, pattern: str = "**/*") -> List[str]:
        files = []
        for path in self.workspace.glob(pattern):
            if path.is_file() and not any(p in path.parts for p in [".git", ".apex", "__pycache__", "node_modules", ".venv"]):
                files.append(str(path.relative_to(self.workspace)))
        return files[:200]
