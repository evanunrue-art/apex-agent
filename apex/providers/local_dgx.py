import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator

class LocalDGXProvider:
    """Interface for local GPU acceleration on DGX Spark via Ollama or vLLM / NIM."""
    
    def __init__(self, endpoint: str = "http://localhost:11434", default_model: str = "qwen2.5-coder:latest"):
        self.endpoint = endpoint.rstrip("/")
        self.default_model = default_model
        
    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Try Ollama endpoint first
                res = await client.get(f"{self.endpoint}/api/tags")
                if res.status_code == 200:
                    return True
                # Try vLLM / OpenAI compatible endpoint
                res = await client.get(f"{self.endpoint}/v1/models")
                if res.status_code == 200:
                    return True
        except Exception:
            return False
        return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        target_model = model or self.default_model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Try OpenAI compatible endpoint (vLLM / NIM / Ollama v1)
            try:
                res = await client.post(
                    f"{self.endpoint}/v1/chat/completions",
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
            except Exception:
                pass
                
            # Fallback to Ollama native API
            res = await client.post(
                f"{self.endpoint}/api/chat",
                json={
                    "model": target_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
            )
            res.raise_for_status()
            return res.json().get("message", {}).get("content", "")
