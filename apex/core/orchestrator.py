import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from apex.config import Config
from apex.providers.router import HybridRouter
from apex.tools.registry import ToolRegistry
from apex.memory.memory_manager import MemoryManager
from apex.core.lats_tree import LATSTreeSearch, LATSNode
from apex.core.context_budget import ContextBudgetManager

logger = logging.getLogger("apex.orchestrator")

SYSTEM_PROMPT = """You are APEX, an ultra-advanced autonomous generalist CLI agentic assistant running on a high-performance system.
Your mission is to perform ANY digital task across domains: software engineering, system administration, data analysis & visualization, autonomous web research & synthesis, document generation, and workflow automation.

You have access to tools:
- File & Code: view_file, write_file, replace_content, grep_search, list_files
- Execution & Shell: run_command
- Data & Math Analytics: analyze_dataset, execute_python_script
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
    """Core Cognitive Loop Orchestrator for APEX."""

    def __init__(self, config: Config):
        self.config = config
        self.router = HybridRouter(config)
        self.tools = ToolRegistry()
        self.memory = MemoryManager()
        self.lats = LATSTreeSearch(config.lats_max_depth, config.lats_max_branches, config.lats_exploration_weight)
        self.context_mgr = ContextBudgetManager(config.max_context_tokens)
        self.memory.initialize()

    async def run(self, user_goal: str, enable_tree_search: bool = True) -> AsyncGenerator[Dict[str, Any], None]:
        """Runs the main agent execution trajectory yields event objects for TUI rendering."""
        
        yield {"type": "status", "message": "Initializing APEX Cognitive Engine..."}
        
        # 1. Memory Context Retrieval
        mem_snapshot = self.memory.get_context_snapshot(user_goal)
        yield {"type": "memory", "snapshot": mem_snapshot}
        
        # 2. Setup Initial Messages
        messages = [
            {"role": "user", "content": f"User Goal: {user_goal}\nMemory Context:\n{json.dumps(mem_snapshot, indent=2)}"}
        ]
        
        # 3. Create Checkpoint if enabled
        if self.config.enable_git_checkpoints:
            self.tools.git.create_snapshot(f"Goal: {user_goal[:30]}")
            
        root = LATSNode(thought=f"Root goal: {user_goal}")
        current_node = root
        
        max_steps = 15
        step = 0
        
        while step < max_steps:
            step += 1
            yield {"type": "step", "step": step}
            
            # Compress messages if approaching context limits
            compressed_msgs = self.context_mgr.compress_messages(messages)
            
            # Request LLM generation
            response_raw = await self.router.generate(
                messages=compressed_msgs,
                system_prompt=SYSTEM_PROMPT,
                task_type="complex" if step == 1 else "code"
            )
            
            yield {"type": "thought", "text": response_raw}
            
            # Parse tool decision
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
                # Save episode to memory
                self.memory.episodic.save_episode(
                    task=user_goal,
                    plan=[thought],
                    tools_used=["run_command", "write_file"],
                    outcome=thought,
                    success=True
                )
                break
                
            yield {"type": "action", "tool": tool_name, "args": args}
            
            # Execute tool
            obs = await self.tools.execute(tool_name, args)
            yield {"type": "observation", "observation": obs}
            
            # Tree search node scoring & evaluation
            if enable_tree_search:
                score = self.lats.evaluate_observation(obs)
                child = LATSNode(thought=thought, action=tool_call, parent=current_node, depth=step)
                child.observation = obs
                child.backpropagate(score)
                current_node.add_child(child)
                current_node = child
                
            # Update trajectory messages
            messages.append({"role": "assistant", "content": json.dumps(tool_call)})
            messages.append({"role": "user", "content": f"Observation from {tool_name}:\n{obs}"})

    def _parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Parses structured JSON tool calls from markdown code blocks or plain text."""
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
