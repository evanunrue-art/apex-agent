import httpx
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("apex.local_dgx")

def normalize_endpoint_url(base_url: str) -> Tuple[str, str]:
    """Normalizes base endpoint URL to avoid /v1/v1 duplicate paths.
    Returns (root_url, v1_url).
    """
    clean = base_url.rstrip("/")
    if clean.endswith("/v1"):
        root_url = clean[:-3]
        v1_url = clean
    else:
        root_url = clean
        v1_url = f"{clean}/v1"
    return root_url, v1_url


class LocalDGXProvider:
    """Interface for local GPU endpoints (Ollama, vLLM, NIM) with endpoint normalization and model discovery validation."""
    
    def __init__(self, endpoint: str = "http://localhost:11434", default_model: str = "qwen2.5-coder:latest", provider_type: str = "hybrid"):
        self.root_url, self.v1_url = normalize_endpoint_url(endpoint)
        self.default_model = default_model
        self.provider_type = provider_type.lower()
        
    async def get_available_models(self) -> List[str]:
        """Queries /v1/models or /api/tags to list available local model IDs."""
        models = []
        async with httpx.AsyncClient(timeout=3.0) as client:
            # 1. Try vLLM / NIM / OpenAI endpoint
            try:
                res = await client.get(f"{self.v1_url}/models")
                if res.status_code == 200:
                    data = res.json()
                    for m in data.get("data", []):
                        if isinstance(m, dict) and "id" in m:
                            models.append(m["id"])
            except Exception:
                pass
                
            # 2. Try Ollama endpoint
            if not models:
                try:
                    res = await client.get(f"{self.root_url}/api/tags")
                    if res.status_code == 200:
                        data = res.json()
                        for m in data.get("models", []):
                            if isinstance(m, dict) and "name" in m:
                                models.append(m["name"])
                except Exception:
                    pass
                    
        return models

    async def is_available(self) -> bool:
        models = await self.get_available_models()
        return len(models) > 0

    async def validate_or_select_model(self, requested_model: Optional[str] = None) -> str:
        """Validates requested model against available model IDs or auto-selects if exactly 1 exists."""
        available = await self.get_available_models()
        target = requested_model or self.default_model
        
        if not available:
            raise RuntimeError(f"No local models detected at endpoint '{self.root_url}'. Ensure Ollama, vLLM, or NIM is running.")
            
        if target in available:
            return target
            
        # Check partial match (e.g. qwen vs qwen:latest)
        for m in available:
            if m.startswith(target) or target.startswith(m):
                return m
                
        if len(available) == 1:
            logger.info(f"Auto-selected sole available model '{available[0]}' at '{self.root_url}'.")
            return available[0]
            
        raise ValueError(
            f"Configured model '{target}' not found at local endpoint '{self.root_url}'. Available model IDs: {', '.join(available)}"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        target_model = await self.validate_or_select_model(model)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=90.0) as client:
            # Prefer vLLM / NIM OpenAI endpoint if provider_type is vllm or nim
            if self.provider_type in ["vllm", "nim", "hybrid"]:
                try:
                    res = await client.post(
                        f"{self.v1_url}/chat/completions",
                        json={
                            "model": target_model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        }
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                except Exception as e:
                    if self.provider_type in ["vllm", "nim"]:
                        raise RuntimeError(f"Local {self.provider_type.upper()} endpoint '{self.v1_url}' error: {e}")
                        
            # Ollama API
            res = await client.post(
                f"{self.root_url}/api/chat",
                json={
                    "model": target_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
            )
            res.raise_for_status()
            return res.json().get("message", {}).get("content", "")
