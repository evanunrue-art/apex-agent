import os
import httpx
from typing import List, Dict, Any, Optional

class CloudLLMProvider:
    """Unified provider client for OpenAI, Anthropic, Gemini, and DeepSeek endpoints."""
    
    def __init__(self, config: Any):
        self.config = config
        
    async def generate_openai(self, messages: List[Dict[str, str]], model: str = "gpt-4o", temperature: float = 0.2) -> str:
        api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key missing")
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

    async def generate_anthropic(self, messages: List[Dict[str, str]], system_prompt: str = "", model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.2) -> str:
        api_key = self.config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key missing")
        async with httpx.AsyncClient(timeout=90.0) as client:
            payload = {
                "model": model,
                "max_tokens": 4096,
                "messages": messages,
                "temperature": temperature
            }
            if system_prompt:
                payload["system"] = system_prompt
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json=payload
            )
            res.raise_for_status()
            data = res.json()
            return data["content"][0]["text"]

    async def generate_deepseek(self, messages: List[Dict[str, str]], model: str = "deepseek-coder", temperature: float = 0.2) -> str:
        api_key = self.config.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API key missing")
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
