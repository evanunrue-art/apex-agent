from enum import Enum
from typing import Dict, Any

class UserDemographic(Enum):
    YOUTH = "YOUTH"               # Gamified, fun, clear analogies, visual
    ELDERLY = "ELDERLY"           # Patient, clear typography, zero technical jargon, step-by-step
    NON_TECHNICAL = "NON_TECHNICAL"# Plain language, clear action items, high utility
    TECHNICAL = "TECHNICAL"       # Rigorous, code snippets, benchmarks, precise AST diffs

class UniversalPersonaAdapter:
    """Adapts LLM responses to be universally accessible and high-impact across demographics."""

    @staticmethod
    def get_system_prompt_modifier(demographic: UserDemographic) -> str:
        if demographic == UserDemographic.YOUTH:
            return """
[Demographic Target: Youth / Students]
Use an engaging, friendly, and visual tone. Use fun analogies, bullet points, and encouraging language. Make learning feel like a superpower!
"""
        elif demographic == UserDemographic.ELDERLY:
            return """
[Demographic Target: Seniors / Elders]
Use ultra-clear, patient, and warm language. Avoid all technical acronyms or jargon. Provide simple 1-2-3 step instructions with zero confusion.
"""
        elif demographic == UserDemographic.NON_TECHNICAL:
            return """
[Demographic Target: General Non-Technical Users]
Be practical, clear, and direct. Focus on immediate outcome and value. Explain what was done in plain English without exposing raw code unless requested.
"""
        else:
            return """
[Demographic Target: Technical / Developers]
Be precise, concise, and rigorous. Include code diffs, CLI parameters, system metrics, and architectural rationale.
"""
