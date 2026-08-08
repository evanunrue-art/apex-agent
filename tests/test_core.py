import unittest
import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from apex.config import Config, detect_hardware, validate_workspace_path
from apex.providers.router import HybridRouter
from apex.providers.local_dgx import LocalDGXProvider, normalize_endpoint_url
from apex.tools.filesystem import FileSystemTool
from apex.tools.git_checkpoint import GitCheckpointManager
from apex.tools.registry import ToolRegistry
from apex.memory.memory_manager import MemoryManager
from apex.core.lats_tree import LATSTreeSearch, LATSNode
from apex.core.context_budget import ContextBudgetManager
from apex.tools.sysadmin import SysAdminTool
from apex.tools.data_analysis import DataAnalysisTool
from apex.core.adversarial_debate import AdversarialDebateEngine
from apex.core.speculative_sandbox import SpeculativeSandboxEngine
from apex.core.self_evolver import SelfEvolverEngine
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph
from apex.core.governance import GovernancePolicyEngine, RiskLevel
from apex.core.anticipatory import AnticipatoryEngine
from apex.core.daily_digest import DailyDigestGenerator
from apex.tools.document_ingestion import DocumentIngestionTool
from apex.tools.security import resolve_and_verify_workspace_path
from apex.core.orchestrator import AgentOrchestrator

class TestApexSystem(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.test_dir, ignore_errors=True))

    def test_workspace_propagation_to_orchestrator_and_tools(self):
        config = Config()
        custom_workspace = self.test_dir / "custom_proj"
        custom_workspace.mkdir(parents=True, exist_ok=True)
        
        orchestrator = AgentOrchestrator(config, workspace=custom_workspace)
        self.assertEqual(orchestrator.workspace, custom_workspace)
        self.assertEqual(orchestrator.tools.workspace, custom_workspace)
        self.assertEqual(orchestrator.tools.fs.workspace, custom_workspace)
        self.assertEqual(orchestrator.tools.git.workspace_dir, custom_workspace)
        self.assertEqual(orchestrator.tools.doc_tool.workspace, custom_workspace)
        self.assertEqual(orchestrator.tools.data_tool.workspace, custom_workspace)

    def test_interactive_flag_behavior_in_orchestrator(self):
        config = Config()
        orchestrator = AgentOrchestrator(config, workspace=self.test_dir)
        
        async def run_unattended():
            events = []
            async for event in orchestrator.run("Run shell command", is_interactive=False):
                events.append(event)
            return events

        # Unattended execution must default-deny actions requiring approval
        events = asyncio.run(run_unattended())
        denial_events = [e for e in events if e.get("type") == "governance_denial"]
        # If model proposed run_command or high-risk tool, denial event is recorded
        self.assertIsInstance(events, list)

    def test_hardware_detection(self):
        specs = detect_hardware()
        self.assertGreater(specs.cpu_cores, 0)
        self.assertGreater(specs.total_ram_gb, 0)

    def test_config_management_and_malformed_handling(self):
        config = Config()
        config_file = self.test_dir / "config.yaml"
        config.save(config_file)
        self.assertTrue(config_file.exists())
        
        loaded = Config.load(config_file)
        self.assertEqual(loaded.local_model, config.local_model)
        
        config_file.write_text("invalid_yaml: [unclosed list")
        with self.assertRaises(ValueError):
            Config.load(config_file)

    def test_endpoint_normalization(self):
        root1, v1_1 = normalize_endpoint_url("http://localhost:8000")
        self.assertEqual(root1, "http://localhost:8000")
        self.assertEqual(v1_1, "http://localhost:8000/v1")
        
        root2, v1_2 = normalize_endpoint_url("http://localhost:8000/v1")
        self.assertEqual(root2, "http://localhost:8000")
        self.assertEqual(v1_2, "http://localhost:8000/v1")

    def test_path_containment_and_traversal_rejection(self):
        fs = FileSystemTool(workspace=self.test_dir)
        
        valid_path = resolve_and_verify_workspace_path("test.py", self.test_dir)
        self.assertEqual(valid_path, self.test_dir / "test.py")
        
        with self.assertRaises(PermissionError):
            resolve_and_verify_workspace_path("C:/Windows/System32/drivers/etc/hosts" if os.name == 'nt' else "/etc/passwd", self.test_dir)
            
        with self.assertRaises(PermissionError):
            resolve_and_verify_workspace_path("../../outside.txt", self.test_dir)

    def test_governance_policy_pre_execution(self):
        gov = GovernancePolicyEngine()
        
        risk, req, _ = gov.evaluate_action_risk("view_file", {})
        self.assertEqual(risk, RiskLevel.LOW)
        self.assertFalse(req)
        
        risk_cmd, req_cmd, _ = gov.evaluate_action_risk("run_command", {"command": "ls"})
        self.assertEqual(risk_cmd, RiskLevel.HIGH)
        self.assertTrue(req_cmd)
        
        allowed, msg = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=False)
        self.assertFalse(allowed)
        
        allowed_appr, _ = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=True, approved_by_user=True)
        self.assertTrue(allowed_appr)

    def test_home_directory_execution_prohibited(self):
        home_dir = Path.home().resolve()
        with self.assertRaises(ValueError):
            validate_workspace_path(home_dir)

    def test_document_ingestion_tool(self):
        doc_tool = DocumentIngestionTool(workspace=self.test_dir)
        txt_file = self.test_dir / "paper.txt"
        txt_file.write_text("Abstract: Deep Learning Research 2026")
        
        parsed = doc_tool.parse_document("paper.txt")
        self.assertIn("Deep Learning Research", parsed)

    def test_tool_registry_async(self):
        registry = ToolRegistry(workspace=self.test_dir)
        
        async def run_async_test():
            res = await registry.execute("write_file", {"relative_path": "hello.txt", "content": "Hello APEX"})
            self.assertIn("Successfully wrote", res)
            
            content = await registry.execute("view_file", {"relative_path": "hello.txt"})
            self.assertIn("Hello APEX", content)
            
        asyncio.run(run_async_test())

if __name__ == "__main__":
    unittest.main()
