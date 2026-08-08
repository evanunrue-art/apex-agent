from typing import Dict, Any
from apex.agents.base import BaseAgent

class ArchitectAgent(BaseAgent):
    """Specialized Sub-Agent for System Design, File Structuring, and Plan Generation."""

    def __init__(self, config):
        super().__init__("Architect", "Designs overall architecture, file blueprints, and execution plans.", config)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        goal = input_data.get("goal", "")
        system_prompt = f"You are {self.name}. {self.role_description}\nDecompose the goal into concrete file modules and execution steps."
        messages = [{"role": "user", "content": f"Architect Goal: {goal}"}]
        
        plan = await self.router.generate(messages, system_prompt=system_prompt, task_type="complex")
        return {"agent": self.name, "plan": plan}


class CoderAgent(BaseAgent):
    """Specialized Sub-Agent for Surgical Code Implementation and Diff Patch Generation."""

    def __init__(self, config):
        super().__init__("Coder", "Generates production code and surgical edits.", config)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        file_path = input_data.get("file_path", "")
        instruction = input_data.get("instruction", "")
        existing_code = input_data.get("existing_code", "")
        
        system_prompt = f"You are {self.name}. {self.role_description}\nProduce high quality, bug-free implementation for {file_path}."
        prompt = f"Instruction: {instruction}\n\nExisting Code:\n{existing_code}"
        messages = [{"role": "user", "content": prompt}]
        
        code = await self.router.generate(messages, system_prompt=system_prompt, task_type="code")
        return {"agent": self.name, "file_path": file_path, "code": code}


class AuditorAgent(BaseAgent):
    """Specialized Sub-Agent for Code Review, Linting, and Security Auditing."""

    def __init__(self, config):
        super().__init__("Auditor", "Audits code for bugs, syntax errors, and security issues.", config)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        code = input_data.get("code", "")
        system_prompt = f"You are {self.name}. {self.role_description}\nAudit the given code snippet. List any potential vulnerabilities or bugs."
        messages = [{"role": "user", "content": f"Code to audit:\n{code}"}]
        
        audit_res = await self.router.generate(messages, system_prompt=system_prompt, task_type="fast")
        return {"agent": self.name, "audit": audit_res}


class DebuggerAgent(BaseAgent):
    """Specialized Sub-Agent for Error Log Tracing and Root-Cause Diagnosis."""

    def __init__(self, config):
        super().__init__("Debugger", "Parses stack traces and generates targeted bug fixes.", config)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        error_log = input_data.get("error_log", "")
        code_context = input_data.get("code_context", "")
        system_prompt = f"You are {self.name}. {self.role_description}\nAnalyze the error log and trace back to the exact root cause."
        messages = [{"role": "user", "content": f"Error Log:\n{error_log}\n\nCode Context:\n{code_context}"}]
        
        fix = await self.router.generate(messages, system_prompt=system_prompt, task_type="code")
        return {"agent": self.name, "fix_proposal": fix}
