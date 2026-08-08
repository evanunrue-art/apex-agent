import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from apex.config import Config, validate_workspace_path
from apex.providers.router import HybridRouter
from apex.tools.registry import ToolRegistry
from apex.memory.memory_manager import MemoryManager
from apex.core.lats_tree import LATSTreeSearch, LATSNode
from apex.core.context_budget import ContextBudgetManager
from apex.core.governance import GovernancePolicyEngine

logger = logging.getLogger("apex.orchestrator")

SYSTEM_PROMPT = """You are APEX, an autonomous generalist CLI agentic assistant.
Your mission is to perform tasks across coding, system administration, data analysis, web research, document synthesis, and workflow automation.

You have access to tools:
- Document Ingestion: parse_document, ingest_document
- File & Code: view_file, write_file, replace_content, grep_search, list_files
- Execution & Shell: run_command (requires approval)
- Data & Math Analytics: analyze_dataset, execute_python_script (requires approval)
- System Admin & Telemetry: get_system_metrics, list_running_processes, check_network_port
- Web & Autonomous Research: fetch_web_page, search_and_synthesize
- Checkpoints & Undo: create_checkpoint, rollback_checkpoint

When responding, output standard JSON tool calls in the format:
```json
{
  "thought": "Step-by-step reasoning...",
  "tool": "tool_name",
  "args": { ... }
}
```
If your task is completely finished, set "tool" to "final_answer" and put your response in "thought".
"""

class AgentOrchestrator:
    """Core Cognitive Loop Orchestrator for APEX with strict governance enforcement."""

    def __init__(self, config: Config):
        self.config = config
        self.router = HybridRouter(config)
        self.tools = ToolRegistry()
        self.memory = MemoryManager()
        self.governance = GovernancePolicyEngine()
        self.lats = LATSTreeSearch(config.lats_max_depth, config.lats_max_branches, config.lats_exploration_weight)
        self.context_mgr = ContextBudgetManager(config.max_context_tokens)
        self.memory.initialize()

    async def run(
        self,
        user_goal: str,
        enable_tree_search: bool = True,
        is_interactive: bool = False,
        approved_actions: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Runs the main agent execution trajectory with strict pre-execution governance."""
        
        # Enforce workspace boundary check
        validate_workspace_path(self.tools.fs.workspace)
        
        yield {"type": "status", "message": "Initializing APEX Cognitive Engine..."}
        
        mem_snapshot = self.memory.get_context_snapshot(user_goal)
        yield {"type": "memory", "snapshot": mem_snapshot}
        
        messages = [
            {"role": "user", "content": f"User Goal: {user_goal}\nMemory Context:\n{json.dumps(mem_snapshot, indent=2)}"}
        ]
        
        if self.config.enable_git_checkpoints and (self.tools.fs.workspace / ".git").exists():
            self.tools.git.create_snapshot(f"Goal: {user_goal[:30]}")
            
        root = LATSNode(thought=f"Root goal: {user_goal}")
        current_node = root
        
        max_steps = 15
        step = 0
        approved_set = set(approved_actions or [])
        
        while step < max_steps:
            step += 1
            yield {"type": "step", "step": step}
            
            compressed_msgs = self.context_mgr.compress_messages(messages)
            
            response_raw = await self.router.generate(
                messages=compressed_msgs,
                system_prompt=SYSTEM_PROMPT,
                task_type="complex" if step == 1 else "code"
            )
            
            yield {"type": "thought", "text": response_raw}
            
            tool_call = self._parse_tool_call(response_raw)
            if not tool_call:
                messages.append({"role": "assistant", "content": response_raw})
                messages.append({"role": "user", "content": "Please output a valid JSON response with 'thought', 'tool', and 'args'."})
                continue
                
            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})
            thought = tool_call.get("thought", "")
            
            if tool_name == "final_answer":
                yield {"type": "final", "content": thought}
                self.memory.episodic.save_episode(
                    task=user_goal,
                    plan=[thought],
                    tools_used=["run_command", "write_file"],
                    outcome=thought,
                    success=True
                )
                break
                
            # Pre-execution Governance Evaluation
            user_approved = tool_name in approved_set
            allowed, reason = self.governance.validate_execution_allowed(
                tool_name, args, is_interactive=is_interactive, approved_by_user=user_approved
            )
            
            yield {"type": "action", "tool": tool_name, "args": args, "governance_allowed": allowed, "governance_reason": reason}
            
            if not allowed:
                obs = f"Action Denied by Governance Policy: {reason}"
                yield {"type": "governance_denial", "tool": tool_name, "reason": reason}
            else:
                obs = await self.tools.execute(tool_name, args)
                yield {"type": "observation", "observation": obs}
            
            if enable_tree_search:
                score = self.lats.evaluate_observation(obs)
                child = LATSNode(thought=thought, action=tool_call, parent=current_node, depth=step)
                child.observation = obs
                child.backpropagate(score)
                current_node.add_child(child)
                current_node = child
                
            messages.append({"role": "assistant", "content": json.dumps(tool_call)})
            messages.append({"role": "user", "content": f"Observation from {tool_name}:\n{obs}"})

    def _parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            if "```json" in text:
                block = text.split("```json")[1].split("```")[0].strip()
                return json.loads(block)
            elif "```" in text:
                block = text.split("```")[1].split("```")[0].strip()
                return json.loads(block)
            elif "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                return json.loads(text[start:end])
        except Exception:
            pass
        return None
