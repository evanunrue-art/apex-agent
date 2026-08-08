import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class ProceduralMemory:
    """Voyager Skill Synthesizer: Dynamically generates, catalogs, and reuses operational Python/Bash tools."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or (Path.cwd() / ".apex" / "skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.load_skills()

    def load_skills(self):
        index_file = self.skills_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    self.skills = json.load(f)
            except Exception:
                self.skills = {}

    def register_skill(self, name: str, description: str, code: str, language: str = "python"):
        skill_filename = f"{name}.py" if language == "python" else f"{name}.sh"
        file_path = self.skills_dir / skill_filename
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            self.skills[name] = {
                "name": name,
                "description": description,
                "file": skill_filename,
                "language": language,
                "created_at": time.time()
            }
            
            with open(self.skills_dir / "index.json", "w", encoding="utf-8") as f:
                json.dump(self.skills, f, indent=2)
            return True
        except Exception:
            return False

    def list_skills(self) -> List[Dict[str, Any]]:
        return list(self.skills.values())
