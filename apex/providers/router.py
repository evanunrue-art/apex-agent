import logging
from typing import List, Dict, Any, Optional
from apex.config import Config
from apex.providers.local_dgx import LocalDGXProvider
from apex.providers.cloud_llm import CloudLLMProvider

logger = logging.getLogger("apex.router")

class HybridRouter:
    """Intelligent Model Router that balances Local DGX GPU compute with Cloud API models."""

    def __init__(self, config: Config):
        self.config = config
        self.local_dgx = LocalDGXProvider(config.local_dgx_endpoint, config.local_model)
        self.cloud_llm = CloudLLMProvider(config)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        task_type: str = "general",  # "fast", "complex", "code", "search"
        temperature: float = 0.2
    ) -> str:
        """Route request dynamically based on task_type, provider preference, and hardware availability."""
        
        mode = self.config.primary_provider.lower()
        
        # Fast tasks (search, AST parsing, linter log analysis) default to Local DGX if available
        if task_type in ["fast", "search", "parse"] or mode == "local_dgx":
            if await self.local_dgx.is_available():
                try:
                    full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                    return await self.local_dgx.generate(
                        prompt=full_prompt,
                        system_prompt=system_prompt,
                        temperature=temperature
                    )
                except Exception as e:
                    logger.warning(f"Local DGX generation failed: {e}. Falling back to cloud...")
        
        # Try cloud models if API keys are available
        if self.config.openai_api_key:
            try:
                formatted_msgs = []
                if system_prompt:
                    formatted_msgs.append({"role": "system", "content": system_prompt})
                formatted_msgs.extend(messages)
                return await self.cloud_llm.generate_openai(
                    formatted_msgs, model=self.config.cloud_model, temperature=temperature
                )
            except Exception as e:
                logger.warning(f"OpenAI call failed: {e}")
                
        if self.config.anthropic_api_key:
            try:
                return await self.cloud_llm.generate_anthropic(
                    messages, system_prompt=system_prompt, temperature=temperature
                )
            except Exception as e:
                logger.warning(f"Anthropic call failed: {e}")

        if self.config.deepseek_api_key:
            try:
                formatted_msgs = []
                if system_prompt:
                    formatted_msgs.append({"role": "system", "content": system_prompt})
                formatted_msgs.extend(messages)
                return await self.cloud_llm.generate_deepseek(formatted_msgs, temperature=temperature)
            except Exception as e:
                logger.warning(f"DeepSeek call failed: {e}")

        # Ultimate fallback: attempt Local DGX even for complex tasks
        if await self.local_dgx.is_available():
            full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            return await self.local_dgx.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )

        # Mock fallback mode for testing / offline demo if no API keys or local servers are running
        return self._mock_fallback(messages, system_prompt, task_type)

    def _mock_fallback(self, messages: List[Dict[str, str]], system_prompt: str, task_type: str) -> str:
        """Returns structured JSON response when running in offline standalone mode."""
        user_msg = messages[-1]["content"] if messages else ""
        return f"[APEX Engine Local Response]\nTask: {task_type}\nProcessed input: {user_msg[:100]}..."
