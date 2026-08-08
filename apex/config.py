import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import yaml

class HardwareSpecs(BaseModel):
    has_nvidia_gpu: bool = False
    gpu_name: str = "Unknown"
    gpu_memory_total_mb: float = 0.0
    gpu_memory_free_mb: float = 0.0
    cpu_cores: int = 1
    total_ram_gb: float = 0.0
    is_unified_memory: bool = False

class Config(BaseModel):
    # LLM Routing Settings
    primary_provider: str = Field(default="hybrid", description="hybrid, local_dgx, ollama, vllm, nim, openai, anthropic, gemini, deepseek")
    local_dgx_endpoint: str = Field(default="http://localhost:11434", description="Ollama, vLLM, or NIM endpoint")
    local_model: str = Field(default="qwen2.5-coder:latest", description="Local fast model")
    cloud_model: str = Field(default="gpt-4o", description="Frontier reasoning model")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    deepseek_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"))
    
    # Search & Tree Search Parameters
    lats_max_depth: int = 5
    lats_max_branches: int = 3
    lats_exploration_weight: float = 1.414
    max_context_tokens: int = 128000
    
    # Features
    enable_git_checkpoints: bool = True
    enable_skill_synthesis: bool = True
    enable_tui: bool = True
    strict_governance: bool = True
    
    # Paths
    apex_dir: Path = Field(default_factory=lambda: Path.cwd() / ".apex")
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        target = config_path or Path.cwd() / ".apex" / "config.yaml"
        if target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return cls(**data)
            except Exception as e:
                raise ValueError(f"Invalid configuration file at '{target}': {str(e)}")
        return cls()

    def save(self, config_path: Optional[Path] = None):
        target = config_path or self.apex_dir / "config.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False)

def validate_workspace_path(workspace: Path) -> Path:
    """Refuses execution if workspace is home directory."""
    resolved = workspace.resolve()
    home_dir = Path.home().resolve()
    if resolved == home_dir:
        raise ValueError(f"Autonomous execution is prohibited in user home directory '{home_dir}'. Specify a dedicated workspace directory via --workspace or 'apex init'.")
    return resolved

def detect_hardware() -> HardwareSpecs:
    import psutil
    specs = HardwareSpecs()
    specs.cpu_cores = psutil.cpu_count(logical=True) or 1
    specs.total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            res = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().split("\n")
                first = [item.strip() for item in lines[0].split(",")]
                if len(first) >= 1 and first[0]:
                    specs.has_nvidia_gpu = True
                    specs.gpu_name = first[0]
                    
                    # Safe parsing of numeric memory fields for unified memory (DGX Spark)
                    try:
                        specs.gpu_memory_total_mb = float(first[1])
                    except (ValueError, IndexError):
                        specs.gpu_memory_total_mb = specs.total_ram_gb * 1024
                        specs.is_unified_memory = True
                        
                    try:
                        specs.gpu_memory_free_mb = float(first[2])
                    except (ValueError, IndexError):
                        specs.gpu_memory_free_mb = (psutil.virtual_memory().available / (1024 ** 2))
                        specs.is_unified_memory = True
        except Exception:
            pass
            
    return specs
