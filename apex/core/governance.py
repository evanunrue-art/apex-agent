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
            "parse_document": RiskLevel.LOW,
            "ingest_document": RiskLevel.LOW,
            "write_file": RiskLevel.MEDIUM,
            "replace_content": RiskLevel.MEDIUM,
            "analyze_dataset": RiskLevel.LOW,
            "execute_python_script": RiskLevel.HIGH,
            "run_command": RiskLevel.HIGH,
            "create_checkpoint": RiskLevel.LOW,
            "rollback_checkpoint": RiskLevel.HIGH,
        }

    def evaluate_action_risk(self, tool_name: str, args: Dict[str, Any]) -> Tuple[RiskLevel, bool, str]:
        """Evaluates risk level, approval requirement, and policy reason."""
        level = self.risk_rules.get(tool_name, RiskLevel.MEDIUM)
        requires_approval = level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Check high-risk or critical shell/python executions
        if tool_name in ["run_command", "execute_python_script"]:
            requires_approval = True
            cmd = str(args.get("command", "") or args.get("code_snippet", "")).lower()
            if any(danger in cmd for danger in ["rm -rf", "drop database", "format ", "mkfs", "del /f /s /q"]):
                level = RiskLevel.CRITICAL
                return level, True, f"Critical destructive command detected: '{cmd}'"
            if "deploy" in cmd or "sudo" in cmd or "chmod 777" in cmd:
                level = RiskLevel.HIGH,
                return RiskLevel.HIGH, True, f"High privilege action detected: '{cmd}'"
                
        return level, requires_approval, f"Tool '{tool_name}' classified as {level.value} risk."

    def validate_execution_allowed(self, tool_name: str, args: Dict[str, Any], is_interactive: bool = False, approved_by_user: bool = False) -> Tuple[bool, str]:
        """Strictly enforces governance before tool execution.
        Unattended modes (daemon, mesh, web API, headless) default-deny actions requiring approval.
        """
        level, requires_approval, reason = self.evaluate_action_risk(tool_name, args)
        
        if not is_interactive:
            if requires_approval or level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return False, f"Governance Denial (Unattended Mode): Action '{tool_name}' ({level.value} risk) requires explicit user approval."
            return True, f"Autonomous execution permitted for {tool_name} ({level.value} risk)."
            
        if requires_approval and not approved_by_user:
            return False, f"Governance Approval Required: Action '{tool_name}' ({level.value} risk) requires explicit confirmation. Reason: {reason}"
            
        return True, f"Interactive execution approved for {tool_name}."
