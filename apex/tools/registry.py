import json
from typing import Dict, Any, Callable, List, Optional
from apex.tools.filesystem import FileSystemTool
from apex.tools.terminal import TerminalEngine
from apex.tools.git_checkpoint import GitCheckpointManager
from apex.tools.browser import BrowserTool

class ToolRegistry:
    """Central registration & dispatcher for all APEX tools."""

    def __init__(self):
        self.fs = FileSystemTool()
        self.term = TerminalEngine()
        self.git = GitCheckpointManager()
        self.browser = BrowserTool()
        self._custom_skills: Dict[str, Any] = {}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "view_file",
                "description": "View contents of a file with line numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relative_path": {"type": "string"},
                        "start_line": {"type": "integer", "default": 1},
                        "end_line": {"type": "integer", "default": 400}
                    },
                    "required": ["relative_path"]
                }
            },
            {
                "name": "write_file",
                "description": "Create or overwrite a file with given content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relative_path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["relative_path", "content"]
                }
            },
            {
                "name": "replace_content",
                "description": "Surgically replace target string in a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relative_path": {"type": "string"},
                        "target_string": {"type": "string"},
                        "replacement_string": {"type": "string"}
                    },
                    "required": ["relative_path", "target_string", "replacement_string"]
                }
            },
            {
                "name": "run_command",
                "description": "Execute a shell command in the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "timeout": {"type": "number", "default": 60.0}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "grep_search",
                "description": "Search code using regex pattern across files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "file_pattern": {"type": "string", "default": "*"}
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "list_files",
                "description": "List files in the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "default": "**/*"}
                    }
                }
            },
            {
                "name": "create_checkpoint",
                "description": "Create an instant shadow Git checkpoint before high-risk changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"}
                    },
                    "required": ["label"]
                }
            },
            {
                "name": "rollback_checkpoint",
                "description": "Rollback workspace to a previous checkpoint SHA or index.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"}
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "fetch_web_page",
                "description": "Fetch text content from a web URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"}
                    },
                    "required": ["url"]
                }
            }
        ]

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            if tool_name == "view_file":
                return self.fs.view_file(**args)
            elif tool_name == "write_file":
                return self.fs.write_file(**args)
            elif tool_name == "replace_content":
                return self.fs.replace_content(**args)
            elif tool_name == "run_command":
                code, out, err = await self.term.run_command(**args)
                return f"[Exit Code {code}]\nSTDOUT:\n{out}\nSTDERR:\n{err}"
            elif tool_name == "grep_search":
                res = self.fs.grep_search(**args)
                return json.dumps(res, indent=2)
            elif tool_name == "list_files":
                res = self.fs.list_files(**args)
                return json.dumps(res, indent=2)
            elif tool_name == "create_checkpoint":
                sha = self.git.create_snapshot(args.get("label", "Manual Checkpoint"))
                return f"Created checkpoint SHA: {sha}"
            elif tool_name == "rollback_checkpoint":
                ok = self.git.rollback_to_snapshot(args.get("target"))
                return "Successfully rolled back workspace." if ok else "Failed to rollback workspace."
            elif tool_name == "fetch_web_page":
                return await self.browser.fetch_web_page(args.get("url", ""))
            else:
                return f"Error: Unknown tool '{tool_name}'."
        except Exception as e:
            return f"Execution error in tool '{tool_name}': {str(e)}"
