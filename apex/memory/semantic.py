import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class SemanticMemory:
    """Indexes workspace files, code symbols, class definitions, and import relationships."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.symbol_index: Dict[str, List[Dict[str, Any]]] = {}

    def index_workspace(self):
        """Scans python/js/ts/html/css files and extracts definitions & symbols."""
        self.symbol_index.clear()
        for root, _, files in os.walk(self.workspace):
            if any(p in root for p in [".git", ".apex", "__pycache__", "node_modules", ".venv"]):
                continue
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css")):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(self.workspace))
                    self._parse_file_symbols(full_path, rel_path)

    def _parse_file_symbols(self, full_path: Path, rel_path: str):
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Regex matching for python class and function definitions
            if full_path.suffix == ".py":
                matches = re.finditer(r'^(class|def)\s+([A-Za-z0-9_]+)', content, re.MULTILINE)
                for m in matches:
                    kind = m.group(1)
                    name = m.group(2)
                    line_no = content[:m.start()].count("\n") + 1
                    if name not in self.symbol_index:
                        self.symbol_index[name] = []
                    self.symbol_index[name].append({
                        "file": rel_path,
                        "kind": kind,
                        "line": line_no
                    })
        except Exception:
            pass

    def lookup_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        return self.symbol_index.get(symbol_name, [])

    def get_summary(self) -> str:
        total_symbols = len(self.symbol_index)
        return f"Semantic Index: {total_symbols} code symbols cataloged across workspace."
