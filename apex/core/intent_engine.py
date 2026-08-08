import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from apex.config import Config
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.core.governance import GovernancePolicyEngine, RiskLevel
from apex.core.orchestrator import AgentOrchestrator

class EphemeralIntentEngine:
    """Translates high-level human intent into dynamic execution plans and UI workspaces."""

    def __init__(self, config: Config):
        self.config = config
        self.graph = CognitiveKnowledgeGraph()
        self.governance = GovernancePolicyEngine()
        self.orchestrator = AgentOrchestrator(config)

    async def execute_intent(self, intent_prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "message": f"Processing Human Intent: '{intent_prompt}'..."}
        
        # 1. Query Cognitive Graph for historical context
        related_nodes = self.graph.search_graph(intent_prompt)
        yield {"type": "cognitive_graph", "related_nodes": related_nodes}
        
        # 2. Record Intent Node in Knowledge Graph
        node_id = self.graph.add_node("intent", intent_prompt, f"User intent initiated: {intent_prompt}")
        
        # 3. Delegate execution to cognitive orchestrator loop
        async for event in self.orchestrator.run(intent_prompt):
            if event.get("type") == "action":
                tool = event.get("tool")
                args = event.get("args", {})
                risk_level, reason = self.governance.evaluate_action_risk(tool, args)
                event["risk_level"] = risk_level.value
                event["governance_reason"] = reason
            yield event

        # 4. Record completion node in graph
        completion_id = self.graph.add_node("completion", f"Completed: {intent_prompt[:30]}", f"Intent '{intent_prompt}' completed.")
        self.graph.add_edge(node_id, completion_id, "RESOLVED_BY")
