import unittest
import asyncio
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

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
from apex.ui.web_server import verify_token, start_web_server
from typer.testing import CliRunner
from apex.main import app

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
            provider.get_available_models = lambda: asyncio.sleep(0.001, result=["model_a", "model_b"])
            with self.assertRaises(ValueError) as cm:
                await provider.validate_or_select_model("non_existent_model_999")
            self.assertIn("Available model IDs: model_a, model_b", str(cm.exception))
            
        asyncio.run(run_val())

    def test_local_dgx_provider_generation_mock(self):
        provider = LocalDGXProvider(
            "http://localhost:8000",
            default_model="spark-model",
        )

        async def run_test():
            provider.validate_or_select_model = AsyncMock(
                return_value="spark-model"
            )

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "choices": [
                    {"message": {"content": "Hello from mock vLLM"}}
                ]
            }

            client = AsyncMock()
            client.post.return_value = response

            context_manager = MagicMock()
            context_manager.__aenter__ = AsyncMock(return_value=client)
            context_manager.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "apex.providers.local_dgx.httpx.AsyncClient",
                return_value=context_manager,
            ) as constructor:
                result = await provider.generate("Test prompt")

            self.assertEqual(result, "Hello from mock vLLM")
            constructor.assert_called_once_with(
                timeout=90.0,
                trust_env=False,
            )
            client.post.assert_awaited_once()

        asyncio.run(run_test())

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
        
        # Unattended execution default-denies HIGH risk
        allowed, msg = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=False)
        self.assertFalse(allowed)
        
        # Interactive execution requires exact fingerprint approval
        fingerprint = gov.compute_action_fingerprint("run_command", {"command": "echo test"})
        allowed_appr, _ = gov.validate_execution_allowed("run_command", {"command": "echo test"}, is_interactive=True, approved_fingerprints={fingerprint})
        self.assertTrue(allowed_appr)

    def test_home_directory_execution_prohibited(self):
        home_dir = Path.home().resolve()
        with self.assertRaises(ValueError):
            validate_workspace_path(home_dir)

    def test_rollback_does_not_implicitly_clean_untracked_files(self):
        subprocess.run(["git", "init"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@local"], cwd=self.test_dir, capture_output=True)
        
        (self.test_dir / "tracked.txt").write_text("v1")
        git_mgr = GitCheckpointManager(workspace_dir=self.test_dir)
        sha1 = git_mgr.create_snapshot("Commit 1")
        
        (self.test_dir / "tracked.txt").write_text("v2")
        sha2 = git_mgr.create_snapshot("Commit 2")
        
        untracked_file = self.test_dir / "untracked_important.txt"
        untracked_file.write_text("Do not delete me")
        
        ok_no_conf, msg = git_mgr.rollback_to_snapshot(sha1, confirm=False)
        self.assertFalse(ok_no_conf)
        
        ok_conf, _ = git_mgr.rollback_to_snapshot(sha1, confirm=True)
        self.assertTrue(ok_conf)
        self.assertEqual((self.test_dir / "tracked.txt").read_text(), "v1")
        self.assertTrue(untracked_file.exists())

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

    def test_self_evolver(self):
        evolver = SelfEvolverEngine(storage_dir=self.test_dir)
        evolver.record_failure_mode("test task", "run_command", "Syntax error", "Always validate syntax before execution.")
        self.assertGreater(len(evolver.insights), 0)

    def test_cognitive_knowledge_graph(self):
        db_path = self.test_dir / "cognitive_graph.db"
        graph = CognitiveKnowledgeGraph(db_path=db_path)
        node_id = graph.add_node("intent", "Test Goal", "Content description")
        self.assertGreater(node_id, 0)
        
        results = graph.search_graph("Test")
        self.assertEqual(len(results), 1)

    def test_tool_registry_async(self):
        registry = ToolRegistry(workspace=self.test_dir)
        
        async def run_async_test():
            res = await registry.execute("write_file", {"relative_path": "hello.txt", "content": "Hello APEX"})
            self.assertIn("Successfully wrote", res)
            
            content = await registry.execute("view_file", {"relative_path": "hello.txt"})
            self.assertIn("Hello APEX", content)
            
        asyncio.run(run_async_test())

    def test_workspace_propagation_to_orchestrator_and_tools(self):
        config = Config()
        custom_workspace = self.test_dir / "custom_proj"
        custom_workspace.mkdir(parents=True, exist_ok=True)
        
        orchestrator = AgentOrchestrator(config, workspace=custom_workspace)
        self.assertEqual(orchestrator.workspace, custom_workspace)
        self.assertEqual(orchestrator.tools.workspace, custom_workspace)

    def test_web_server_auth_verification(self):
        mock_req = MagicMock()
        mock_req.headers = {"Authorization": "Bearer secret123"}
        mock_req.query_params = {}
        
        import apex.ui.web_server as ws
        ws.GLOBAL_AUTH_TOKEN = "secret123"
        self.assertTrue(verify_token(mock_req))
        
        mock_req_bad = MagicMock()
        mock_req_bad.headers = {"Authorization": "Bearer wrong_token"}
        mock_req_bad.query_params = {}
        self.assertFalse(verify_token(mock_req_bad))
        
        ws.GLOBAL_AUTH_TOKEN = None

    def test_cli_smoke_tests(self):
        runner = CliRunner()
        
        # Test help command
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("APEX CLI", result.stdout)
        
        # Test policy command
        result = runner.invoke(app, ["policy"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Risk Classification", result.stdout)
        
        # Test dgx command
        result = runner.invoke(app, ["dgx"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Hardware & Local Engine Diagnostic", result.stdout)

    def test_cli_debate_smoke(self):
        runner = CliRunner()

        with patch(
            "apex.core.adversarial_debate.AdversarialDebateEngine.debate_and_refine",
            new=AsyncMock(return_value=("Hardened solution", 0.95)),
        ):
            result = runner.invoke(
                app,
                ["debate", "Test goal", "Initial proposal"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Audit Confidence: 0.95", result.stdout)
        self.assertIn("Hardened solution", result.stdout)

if __name__ == "__main__":
    unittest.main()
