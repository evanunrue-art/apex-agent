from enum import Enum
from typing import Dict, Any, Tuple

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GovernancePolicyEngine:
    """Policy-Bound Safety & Risk Governance Engine for Autonomous Execution."""

    def __init__(self):
        self.risk_rules = {
            "view_file": RiskLevel.LOW,
            "grep_search": RiskLevel.LOW,
            "list_files": RiskLevel.LOW,
            "fetch_web_page": RiskLevel.LOW,
            "search_and_synthesize": RiskLevel.LOW,
            "get_system_metrics": RiskLevel.LOW,
            "write_file": RiskLevel.MEDIUM,
            "replace_content": RiskLevel.MEDIUM,
            "analyze_dataset": RiskLevel.LOW,
            "execute_python_script": RiskLevel.MEDIUM,
            "run_command": RiskLevel.MEDIUM,
            "create_checkpoint": RiskLevel.LOW,
            "rollback_checkpoint": RiskLevel.HIGH,
        }

    def evaluate_action_risk(self, tool_name: str, args: Dict[str, Any]) -> Tuple[RiskLevel, str]:
        """Evaluates risk level and safety policy reason for a proposed tool action."""
        level = self.risk_rules.get(tool_name, RiskLevel.MEDIUM)
        
        # Check high-risk command patterns inside shell executions
        if tool_name == "run_command":
            cmd = str(args.get("command", "")).lower()
            if any(danger in cmd for danger in ["rm -rf", "drop database", "format ", "mkfs", "del /f /s /q"]):
                return RiskLevel.CRITICAL, f"Critical destructive command detected: '{cmd}'"
            if "deploy" in cmd or "sudo" in cmd or "chmod 777" in cmd:
                return RiskLevel.HIGH, f"High privilege action detected: '{cmd}'"
                
        return level, f"Tool '{tool_name}' classified as {level.value} risk."

    def is_autonomous_allowed(self, level: RiskLevel) -> bool:
        """Determines if action can proceed autonomously without user prompt."""
        return level in [RiskLevel.LOW, RiskLevel.MEDIUM]
