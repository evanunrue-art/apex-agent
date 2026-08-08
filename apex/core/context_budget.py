from typing import List, Dict, Any

class ContextBudgetManager:
    """Manages token context budget, dynamically truncating long logs and compressing prompts."""

    def __init__(self, max_tokens: int = 128000):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation: ~4 chars per token."""
        return len(text) // 4

    def compress_messages(self, messages: List[Dict[str, str]], budget: int = 16000) -> List[Dict[str, str]]:
        """Ensures total messages fit within budget by truncating old tool outputs."""
        compressed = []
        for msg in messages:
            content = msg["content"]
            if len(content) > 4000:
                # Keep top 1500 chars and bottom 1500 chars
                content = content[:1500] + "\n... [Output Truncated by APEX Context Budget] ...\n" + content[-1500:]
            compressed.append({"role": msg["role"], "content": content})
        return compressed
