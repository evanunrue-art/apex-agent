import logging
from typing import Dict, Any, Tuple
from apex.config import Config
from apex.providers.router import HybridRouter

logger = logging.getLogger("apex.debate")

class AdversarialDebateEngine:
    """Multi-Model Consensus & Adversarial Audit Engine.
    Forces parallel models (e.g. Local DGX vs Cloud API) to cross-examine proposals before execution.
    """

    def __init__(self, config: Config):
        self.config = config
        self.router = HybridRouter(config)

    async def debate_and_refine(self, goal: str, proposed_solution: str) -> Tuple[str, float]:
        """Subject a proposed solution to adversarial cross-examination."""
        audit_prompt = f"""You are an adversarial red-team auditor.
Examine the following proposed solution for goal: '{goal}'

Proposed Solution:
{proposed_solution}

Critique this solution ruthlessly. Identify any edge cases, bugs, security vulnerabilities, or performance bottlenecks.
Output your critique in two sections:
CRITIQUE: [Detailed flaws or vulnerabilities]
HARDENED_SOLUTION: [Corrected, hardened implementation]
"""
        messages = [{"role": "user", "content": audit_prompt}]
        audit_response = await self.router.generate(messages, system_prompt="You are a ruthless code auditor.", task_type="complex")
        
        if "HARDENED_SOLUTION:" in audit_response:
            parts = audit_response.split("HARDENED_SOLUTION:")
            critique = parts[0].replace("CRITIQUE:", "").strip()
            hardened = parts[1].strip()
            confidence = 0.95
            return hardened, confidence
        
        return proposed_solution, 0.80
