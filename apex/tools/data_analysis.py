import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from apex.tools.security import resolve_and_verify_workspace_path

class DataAnalysisTool:
    """Executes inline Python data analysis scripts using pandas with workspace path containment."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = (workspace or Path.cwd()).resolve()

    def analyze_dataset(self, csv_or_json_path: str) -> str:
        """Loads a dataset (CSV/JSON/Parquet) and returns summary statistics."""
        try:
            target = resolve_and_verify_workspace_path(csv_or_json_path, self.workspace)
        except PermissionError as pe:
            return f"Error: {pe}"
            
        if not target.exists():
            return f"Error: Dataset '{csv_or_json_path}' not found."
            
        script = f"""
import pandas as pd
import json

path = r"{target}"
if path.endswith('.csv'):
    df = pd.read_csv(path)
elif path.endswith('.json'):
    df = pd.read_json(path)
elif path.endswith('.parquet'):
    df = pd.read_parquet(path)
else:
    df = pd.read_csv(path)

info = {{
    "shape": df.shape,
    "columns": list(df.columns),
    "dtypes": {{col: str(dtype) for col, dtype in df.dtypes.items()}},
    "missing_values": df.isnull().sum().to_dict(),
    "head": df.head(5).to_dict(orient="records"),
    "describe": df.describe(include="all").to_dict()
}}
print(json.dumps(info, default=str, indent=2))
"""
        try:
            res = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                return res.stdout
            return f"Error running data analysis: {res.stderr}"
        except Exception as e:
            return f"Data analysis execution failed: {e}"

    def execute_python_script(self, code_snippet: str) -> str:
        """Executes an inline script in the workspace directory."""
        try:
            res = subprocess.run([sys.executable, "-c", code_snippet], cwd=self.workspace, capture_output=True, text=True, timeout=45)
            output = f"[Exit Code {res.returncode}]\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            return output
        except Exception as e:
            return f"Script execution error: {e}"
