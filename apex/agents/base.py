from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from apex.config import Config
from apex.providers.router import HybridRouter

class BaseAgent(ABC):
    """Abstract base class for specialized agents within the APEX swarm."""

    def __init__(self, name: str, role_description: str, config: Config):
        self.name = name
        self.role_description = role_description
        self.config = config
        self.router = HybridRouter(config)

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
