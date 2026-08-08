import json
from enum import Enum
from typing import Dict, Any, Tuple, Set, Optional

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GovernancePolicyEngine:
    """Policy-Bound Safety & Risk Governance Engine with Granular Action Fingerprinting."""

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

    def compute_action_fingerprint(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Computes a unique granular fingerprint for an exact action invocation."""
        serialized_args = json.dumps(args or {}, sort_keys=True)
        return f"{tool_name}:{serialized_args}"

    def evaluate_action_risk(self, tool_name: str, args: Dict[str, Any]) -> Tuple[RiskLevel, bool, str]:
        """Evaluates risk level, approval requirement, and policy reason."""
        level = self.risk_rules.get(tool_name, RiskLevel.MEDIUM)
        requires_approval = level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        if tool_name in ["run_command", "execute_python_script"]:
            requires_approval = True
            cmd = str(args.get("command", "") or args.get("code_snippet", "")).lower()
            if any(danger in cmd for danger in ["rm -rf", "drop database", "format ", "mkfs", "del /f /s /q"]):
                level = RiskLevel.CRITICAL
                return level, True, f"Critical destructive command detected: '{cmd}'"
            if "deploy" in cmd or "sudo" in cmd or "chmod 777" in cmd:
                return RiskLevel.HIGH, True, f"High privilege action detected: '{cmd}'"
                
        return level, requires_approval, f"Tool '{tool_name}' classified as {level.value} risk."

    def validate_execution_allowed(
        self,
        tool_name: str,
        args: Dict[str, Any],
        is_interactive: bool = False,
        approved_fingerprints: Optional[Set[str]] = None
    ) -> Tuple[bool, str]:
        """Strictly enforces governance before tool execution.
        Unattended modes default-deny actions requiring approval.
        Interactive mode requires explicit confirmation for the exact action fingerprint.
        """
        level, requires_approval, reason = self.evaluate_action_risk(tool_name, args)
        fingerprint = self.compute_action_fingerprint(tool_name, args)
        approved_set = approved_fingerprints or set()
        
        if not is_interactive:
            if requires_approval or level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return False, f"Governance Denial (Unattended Mode): Action '{tool_name}' ({level.value} risk) requires explicit user approval."
            return True, f"Autonomous execution permitted for {tool_name} ({level.value} risk)."
            
        if requires_approval:
            if fingerprint not in approved_set:
                return False, f"Governance Confirmation Required: Action '{tool_name}' ({level.value} risk) requires explicit user approval for fingerprint '{fingerprint}'. Reason: {reason}"
            
        return True, f"Execution approved for fingerprint '{fingerprint}'."
