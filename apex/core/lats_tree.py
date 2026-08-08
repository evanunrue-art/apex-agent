import math
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("apex.lats")

class LATSNode:
    """Node in the Language Agent Tree Search tree."""

    def __init__(self, thought: str, action: Optional[Dict[str, Any]] = None, parent: Optional["LATSNode"] = None, depth: int = 0):
        self.thought = thought
        self.action = action
        self.parent = parent
        self.children: List["LATSNode"] = []
        self.depth = depth
        self.visits = 0
        self.value = 0.0
        self.observation = ""
        self.is_terminal = False
        self.checkpoint_sha: Optional[str] = None

    def uct_score(self, exploration_weight: float = 1.414) -> float:
        if self.visits == 0:
            return float("inf")
        parent_visits = self.parent.visits if self.parent else 1
        exploitation = self.value / self.visits
        exploration = exploration_weight * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration

    def add_child(self, child: "LATSNode"):
        self.children.append(child)

    def backpropagate(self, score: float):
        self.visits += 1
        self.value += score
        if self.parent:
            self.parent.backpropagate(score)


class LATSTreeSearch:
    """Language Agent Tree Search (LATS) engine for parallel hypothesis exploration."""

    def __init__(self, max_depth: int = 5, max_branches: int = 3, exploration_weight: float = 1.414):
        self.max_depth = max_depth
        self.max_branches = max_branches
        self.exploration_weight = exploration_weight

    def select_best_node(self, root: LATSNode) -> LATSNode:
        """Selects the node with highest UCT score."""
        current = root
        while current.children:
            unvisited = [c for c in current.children if c.visits == 0]
            if unvisited:
                return unvisited[0]
            current = max(current.children, key=lambda c: c.uct_score(self.exploration_weight))
        return current

    def evaluate_observation(self, observation: str, exit_code: Optional[int] = None) -> float:
        """Heuristic scorer for tool observations."""
        score = 0.5
        if exit_code is not None:
            if exit_code == 0:
                score += 0.4
            else:
                score -= 0.3
        
        obs_lower = observation.lower()
        if "error" in obs_lower or "failed" in obs_lower or "exception" in obs_lower:
            score -= 0.2
        if "success" in obs_lower or "passed" in obs_lower or "successfully" in obs_lower:
            score += 0.3
            
        return max(0.0, min(1.0, score))
