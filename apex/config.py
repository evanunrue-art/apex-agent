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

class Config(BaseModel):
    # LLM Routing Settings
    primary_provider: str = Field(default="hybrid", description="hybrid, local_dgx, openai, anthropic, gemini, deepseek")
    local_dgx_endpoint: str = Field(default="http://localhost:11434", description="Ollama or vLLM endpoint")
    local_model: str = Field(default="qwen2.5-coder:latest", description="Local DGX fast model")
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
            except Exception:
                pass
        return cls()

    def save(self, config_path: Optional[Path] = None):
        target = config_path or self.apex_dir / "config.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False)

def detect_hardware() -> HardwareSpecs:
    import psutil
    specs = HardwareSpecs()
    specs.cpu_cores = psutil.cpu_count(logical=True) or 1
    specs.total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    
    # Check NVIDIA GPU via nvidia-smi
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            res = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().split("\n")
                first = lines[0].split(",")
                if len(first) >= 3:
                    specs.has_nvidia_gpu = True
                    specs.gpu_name = first[0].strip()
                    specs.gpu_memory_total_mb = float(first[1].strip())
                    specs.gpu_memory_free_mb = float(first[2].strip())
        except Exception:
            pass
            
    return specs
