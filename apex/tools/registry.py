import json
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
from apex.tools.filesystem import FileSystemTool
from apex.tools.terminal import TerminalEngine
from apex.tools.git_checkpoint import GitCheckpointManager
from apex.tools.browser import BrowserTool
from apex.tools.data_analysis import DataAnalysisTool
from apex.tools.sysadmin import SysAdminTool
from apex.tools.research_synthesis import ResearchSynthesisTool
from apex.tools.document_ingestion import DocumentIngestionTool

class ToolRegistry:
    """Universal Tool Registry for APEX with workspace propagation."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = (workspace or Path.cwd()).resolve()
        self.fs = FileSystemTool(workspace=self.workspace)
        self.term = TerminalEngine(cwd=str(self.workspace))
        self.git = GitCheckpointManager(workspace_dir=self.workspace)
        self.browser = BrowserTool()
        self.data_tool = DataAnalysisTool(workspace=self.workspace)
        self.sys_tool = SysAdminTool()
        self.research_tool = ResearchSynthesisTool()
        self.doc_tool = DocumentIngestionTool(workspace=self.workspace)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "parse_document",
                "description": "Extract text content from PDF, PPTX, DOCX, or text reference files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "ingest_document",
                "description": "Parse and index a PDF, PPTX, or DOCX reference document into the Cognitive Knowledge Graph.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "view_file",
                "description": "View contents of any text or code file with line numbers.",
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
                "description": "Create or overwrite a file with given text/code/markdown content.",
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
                "description": "Execute any shell command, CLI binary, or script.",
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
                "description": "Search text files using regex across workspace.",
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
                "description": "List files in the workspace matching a pattern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "default": "**/*"}
                    }
                }
            },
            {
                "name": "analyze_dataset",
                "description": "Load a CSV/JSON dataset and produce summary statistics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "csv_or_json_path": {"type": "string"}
                    },
                    "required": ["csv_or_json_path"]
                }
            },
            {
                "name": "execute_python_script",
                "description": "Execute inline python code for data processing, plotting, or stats.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code_snippet": {"type": "string"}
                    },
                    "required": ["code_snippet"]
                }
            },
            {
                "name": "get_system_metrics",
                "description": "Retrieve active CPU, Memory, Disk, and system hardware telemetry.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "list_running_processes",
                "description": "List top active system processes by CPU/Memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "top_n": {"type": "integer", "default": 15}
                    }
                }
            },
            {
                "name": "check_network_port",
                "description": "Check if a host and port are open.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "default": "127.0.0.1"},
                        "port": {"type": "integer", "default": 80}
                    },
                    "required": ["port"]
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
            },
            {
                "name": "search_and_synthesize",
                "description": "Run multi-angle autonomous web search synthesis on any research topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "create_checkpoint",
                "description": "Create a shadow Git checkpoint snapshot.",
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
                "description": "Rollback workspace state to a snapshot SHA or index.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"}
                    },
                    "required": ["target"]
                }
            }
        ]

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            if tool_name == "parse_document":
                return self.doc_tool.parse_document(args.get("file_path", ""))
            elif tool_name == "ingest_document":
                return self.doc_tool.ingest_and_index(args.get("file_path", ""))
            elif tool_name == "view_file":
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
            elif tool_name == "analyze_dataset":
                return self.data_tool.analyze_dataset(**args)
            elif tool_name == "execute_python_script":
                return self.data_tool.execute_python_script(**args)
            elif tool_name == "get_system_metrics":
                res = self.sys_tool.get_system_metrics()
                return json.dumps(res, indent=2)
            elif tool_name == "list_running_processes":
                res = self.sys_tool.list_running_processes(**args)
                return json.dumps(res, indent=2)
            elif tool_name == "check_network_port":
                return self.sys_tool.check_network_port(**args)
            elif tool_name == "fetch_web_page":
                return await self.browser.fetch_web_page(args.get("url", ""))
            elif tool_name == "search_and_synthesize":
                return await self.research_tool.search_and_synthesize(args.get("topic", ""))
            elif tool_name == "create_checkpoint":
                sha = self.git.create_snapshot(args.get("label", "Manual Checkpoint"))
                return f"Created checkpoint SHA: {sha}"
            elif tool_name == "rollback_checkpoint":
                ok, msg = self.git.rollback_to_snapshot(args.get("target"), confirm=True)
                return msg if ok else f"Rollback failed: {msg}"
            else:
                return f"Error: Unknown tool '{tool_name}'."
        except Exception as e:
            return f"Execution error in tool '{tool_name}': {str(e)}"
