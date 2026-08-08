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
        
        # Malformed config test
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

    def test_invalid_model_id_error(self):
        provider = LocalDGXProvider("http://localhost:11434", default_model="non_existent_model_999")
        
        async def run_val():
            # Mock get_available_models returning ['model_a', 'model_b']
            provider.get_available_models = lambda: asyncio.sleep(0.001, result=["model_a", "model_b"])
            with self.assertRaises(ValueError) as cm:
                await provider.validate_or_select_model("non_existent_model_999")
            self.assertIn("Available model IDs: model_a, model_b", str(cm.exception))
            
        asyncio.run(run_val())

    def test_path_containment_and_traversal_rejection(self):
        fs = FileSystemTool(workspace=self.test_dir)
        
        # Normal path inside workspace
        valid_path = resolve_and_verify_workspace_path("test.py", self.test_dir)
        self.assertEqual(valid_path, self.test_dir / "test.py")
        
        # Absolute path outside workspace
        with self.assertRaises(PermissionError):
            resolve_and_verify_workspace_path("C:/Windows/System32/drivers/etc/hosts" if os.name == 'nt' else "/etc/passwd", self.test_dir)
            
        # Traversal escape
        with self.assertRaises(PermissionError):
            resolve_and_verify_workspace_path("../../outside.txt", self.test_dir)
            
        # Verify FileSystemTool returns Error message
        res_abs = fs.view_file("C:/Windows/System32/drivers/etc/hosts" if os.name == 'nt' else "/etc/passwd")
        self.assertIn("Access denied", res_abs)

    def test_governance_policy_pre_execution(self):
        gov = GovernancePolicyEngine()
        
        # LOW risk actions
        risk, req, _ = gov.evaluate_action_risk("view_file", {})
        self.assertEqual(risk, RiskLevel.LOW)
        self.assertFalse(req)
        
        # HIGH risk actions (run_command, execute_python_script) require approval
        risk_cmd, req_cmd, _ = gov.evaluate_action_risk("run_command", {"command": "ls"})
        self.assertEqual(risk_cmd, RiskLevel.HIGH)
        self.assertTrue(req_cmd)
        
        # Unattended execution (headless/daemon/mesh/web) MUST default-deny HIGH & CRITICAL
        allowed, msg = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=False)
        self.assertFalse(allowed)
        self.assertIn("Governance Denial (Unattended Mode)", msg)
        
        # Interactive execution requires explicit user approval
        allowed_int, msg_int = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=True, approved_by_user=False)
        self.assertFalse(allowed_int)
        self.assertIn("Governance Approval Required", msg_int)
        
        allowed_appr, _ = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=True, approved_by_user=True)
        self.assertTrue(allowed_appr)

    def test_home_directory_execution_prohibited(self):
        home_dir = Path.home().resolve()
        with self.assertRaises(ValueError) as cm:
            validate_workspace_path(home_dir)
        self.assertIn("prohibited in user home directory", str(cm.exception))
        
        # Git checkpointing returns None if not git repo and does not initialize git in home
        git_mgr = GitCheckpointManager(workspace_dir=home_dir)
        snapshot = git_mgr.create_snapshot("Test")
        self.assertIsNone(snapshot)

    def test_rollback_does_not_implicitly_clean_untracked_files(self):
        # Create a git repo inside test_dir
        import subprocess
        subprocess.run(["git", "init"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@local"], cwd=self.test_dir, capture_output=True)
        
        (self.test_dir / "tracked.txt").write_text("v1")
        git_mgr = GitCheckpointManager(workspace_dir=self.test_dir)
        sha1 = git_mgr.create_snapshot("Commit 1")
        
        (self.test_dir / "tracked.txt").write_text("v2")
        sha2 = git_mgr.create_snapshot("Commit 2")
        
        # Add an untracked file
        untracked_file = self.test_dir / "untracked_important.txt"
        untracked_file.write_text("Do not delete me")
        
        # Perform rollback without confirm -> requires confirmation
        ok_no_conf, msg = git_mgr.rollback_to_snapshot(sha1, confirm=False)
        self.assertFalse(ok_no_conf)
        self.assertIn("requires explicit confirmation", msg)
        
        # Perform rollback with confirm=True
        ok_conf, _ = git_mgr.rollback_to_snapshot(sha1, confirm=True)
        self.assertTrue(ok_conf)
        self.assertEqual((self.test_dir / "tracked.txt").read_text(), "v1")
        # Untracked file MUST NOT be deleted (no implicit git clean -fd)
        self.assertTrue(untracked_file.exists())
        self.assertEqual(untracked_file.read_text(), "Do not delete me")

    def test_document_ingestion_tool(self):
        doc_tool = DocumentIngestionTool(workspace=self.test_dir)
        txt_file = self.test_dir / "paper.txt"
        txt_file.write_text("Abstract: Deep Learning Research 2026")
        
        parsed = doc_tool.parse_document("paper.txt")
        self.assertIn("Deep Learning Research", parsed)
        
        res = doc_tool.ingest_and_index("paper.txt")
        self.assertIn("Successfully ingested", res)

    def test_sysadmin_and_data_tools(self):
        data_tool = DataAnalysisTool(workspace=self.test_dir)
        csv_file = self.test_dir / "data.csv"
        csv_file.write_text("id,val\n1,100\n2,200\n")
        
        res = data_tool.analyze_dataset("data.csv")
        self.assertIn("shape", res)
        
        sys_tool = SysAdminTool()
        metrics = sys_tool.get_system_metrics()
        self.assertIn("cpu_utilization_pct", metrics)

    def test_speculative_sandbox(self):
        sandbox = SpeculativeSandboxEngine(workspace=self.test_dir)
        worktree_path = sandbox.create_worktree("branch_test")
        self.assertIsNotNone(worktree_path)
        sandbox.cleanup_worktree("branch_test")

    def test_cognitive_knowledge_graph(self):
        db_path = self.test_dir / "cognitive_graph.db"
        graph = CognitiveKnowledgeGraph(db_path=db_path)
        node_id = graph.add_node("intent", "Test Goal", "Content description")
        self.assertGreater(node_id, 0)
        
        results = graph.search_graph("Test")
        self.assertEqual(len(results), 1)

    def test_tool_registry_async(self):
        registry = ToolRegistry()
        registry.fs = FileSystemTool(workspace=self.test_dir)
        
        async def run_async_test():
            res = await registry.execute("write_file", {"relative_path": "hello.txt", "content": "Hello APEX"})
            self.assertIn("Successfully wrote", res)
            
            content = await registry.execute("view_file", {"relative_path": "hello.txt"})
            self.assertIn("Hello APEX", content)
            
        asyncio.run(run_async_test())

if __name__ == "__main__":
    unittest.main()
