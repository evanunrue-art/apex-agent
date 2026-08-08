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

SYSTEM_PROMPT = """You are APEX, an ultra-advanced autonomous CLI agentic assistant running on a high-performance system.
Your mission is to solve coding tasks, debug codebases, build complete features, and execute CLI commands with surgical precision.

You have access to tools:
- view_file(relative_path, start_line, end_line)
- write_file(relative_path, content)
- replace_content(relative_path, target_string, replacement_string)
- run_command(command, timeout)
- grep_search(pattern, file_pattern)
- list_files(pattern)
- create_checkpoint(label)
- rollback_checkpoint(target)
- fetch_web_page(url)

When responding, output standard JSON tool calls in the format:
```json
{
  "thought": "Step-by-step reasoning...",
  "tool": "tool_name",
  "args": { ... }
}
```
If your task is completely finished, set "tool" to "final_answer" and put your response in "thought".
Always verify your edits by running appropriate commands or test suites.
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
