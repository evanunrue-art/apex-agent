import logging
from typing import List, Dict, Any, Optional
from apex.config import Config
from apex.providers.local_dgx import LocalDGXProvider
from apex.providers.cloud_llm import CloudLLMProvider

logger = logging.getLogger("apex.router")

class HybridRouter:
    """Intelligent Model Router balancing Local DGX GPU compute with Cloud APIs."""

    def __init__(self, config: Config):
        self.config = config
        self.local_dgx = LocalDGXProvider(config.local_dgx_endpoint, config.local_model, config.primary_provider)
        self.cloud_llm = CloudLLMProvider(config)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        task_type: str = "general",
        temperature: float = 0.2
    ) -> str:
        provider = self.config.primary_provider.lower()
        
        # Explicit local provider execution
        if provider in ["local_dgx", "ollama", "vllm", "nim"]:
            full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            return await self.local_dgx.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
        # Explicit cloud provider execution
        if provider == "openai":
            formatted_msgs = []
            if system_prompt:
                formatted_msgs.append({"role": "system", "content": system_prompt})
            formatted_msgs.extend(messages)
            return await self.cloud_llm.generate_openai(formatted_msgs, model=self.config.cloud_model, temperature=temperature)
            
        if provider == "anthropic":
            return await self.cloud_llm.generate_anthropic(messages, system_prompt=system_prompt, temperature=temperature)

        if provider == "deepseek":
            formatted_msgs = []
            if system_prompt:
                formatted_msgs.append({"role": "system", "content": system_prompt})
            formatted_msgs.extend(messages)
            return await self.cloud_llm.generate_deepseek(formatted_msgs, temperature=temperature)

        # Hybrid Mode: Try Local DGX first for fast/search/parse tasks
        if task_type in ["fast", "search", "parse"]:
            if await self.local_dgx.is_available():
                try:
                    full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                    return await self.local_dgx.generate(
                        prompt=full_prompt,
                        system_prompt=system_prompt,
                        temperature=temperature
                    )
                except Exception as e:
                    logger.warning(f"Hybrid local DGX attempt failed: {e}")

        # Cloud Fallback in Hybrid Mode
        if self.config.openai_api_key:
            try:
                formatted_msgs = []
                if system_prompt:
                    formatted_msgs.append({"role": "system", "content": system_prompt})
                formatted_msgs.extend(messages)
                return await self.cloud_llm.generate_openai(formatted_msgs, model=self.config.cloud_model, temperature=temperature)
            except Exception as e:
                logger.warning(f"OpenAI call failed: {e}")

        if self.config.anthropic_api_key:
            try:
                return await self.cloud_llm.generate_anthropic(messages, system_prompt=system_prompt, temperature=temperature)
            except Exception as e:
                logger.warning(f"Anthropic call failed: {e}")

        if await self.local_dgx.is_available():
            try:
                full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                return await self.local_dgx.generate(
                    prompt=full_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature
                )
            except Exception as e:
                logger.warning(f"Local DGX generation failed: {e}")

        # Standalone mock fallback for offline demo/test suites
        return self._mock_fallback(messages, system_prompt, task_type)

    def _mock_fallback(self, messages: List[Dict[str, str]], system_prompt: str, task_type: str) -> str:
        user_msg = messages[-1]["content"] if messages else ""
        return f"[APEX Engine Response]\nTask: {task_type}\nProcessed input: {user_msg[:100]}..."
