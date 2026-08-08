import unittest
import asyncio
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from apex.config import Config, detect_hardware
from apex.providers.router import HybridRouter
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

class TestApexSystem(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.test_dir, ignore_errors=True))

    def test_hardware_detection(self):
        specs = detect_hardware()
        self.assertGreater(specs.cpu_cores, 0)
        self.assertGreater(specs.total_ram_gb, 0)

    def test_document_ingestion_tool(self):
        doc_tool = DocumentIngestionTool(workspace=self.test_dir)
        txt_file = self.test_dir / "paper.txt"
        txt_file.write_text("Abstract: Deep Learning Research 2026")
        
        parsed = doc_tool.parse_document("paper.txt")
        self.assertIn("Deep Learning Research", parsed)
        
        res = doc_tool.ingest_and_index("paper.txt")
        self.assertIn("Successfully ingested", res)

    def test_config_management(self):
        config = Config()
        config_file = self.test_dir / "config.yaml"
        config.save(config_file)
        self.assertTrue(config_file.exists())
        
        loaded = Config.load(config_file)
        self.assertEqual(loaded.local_model, config.local_model)

    def test_anticipatory_engine(self):
        engine = AnticipatoryEngine(workspace=self.test_dir)
        suggestions = engine.generate_proactive_suggestions()
        self.assertIsInstance(suggestions, list)

    def test_daily_digest_generator(self):
        generator = DailyDigestGenerator(workspace=self.test_dir)
        digest = generator.generate_digest()
        self.assertIn("date", digest)
        self.assertIn("total_intents_executed", digest)

    def test_cognitive_knowledge_graph(self):
        db_path = self.test_dir / "cognitive_graph.db"
        graph = CognitiveKnowledgeGraph(db_path=db_path)
        node_id = graph.add_node("intent", "Test Goal", "Content description")
        self.assertGreater(node_id, 0)
        
        results = graph.search_graph("Test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Goal")

    def test_governance_policy_engine(self):
        gov = GovernancePolicyEngine()
        risk, _ = gov.evaluate_action_risk("view_file", {})
        self.assertEqual(risk, RiskLevel.LOW)
        
        risk_crit, _ = gov.evaluate_action_risk("run_command", {"command": "rm -rf /"})
        self.assertEqual(risk_crit, RiskLevel.CRITICAL)

    def test_filesystem_tools(self):
        fs = FileSystemTool(workspace=self.test_dir)
        write_res = fs.write_file("test.py", "def foo():\n    return 'bar'\n")
        self.assertIn("Successfully wrote", write_res)
        
        view_res = fs.view_file("test.py")
        self.assertIn("def foo():", view_res)
        
        replace_res = fs.replace_content("test.py", "return 'bar'", "return 'baz'")
        self.assertIn("Successfully replaced", replace_res)
        
        grep_res = fs.grep_search("foo")
        self.assertEqual(len(grep_res), 1)

    def test_sysadmin_tools(self):
        sys_tool = SysAdminTool()
        metrics = sys_tool.get_system_metrics()
        self.assertIn("cpu_utilization_pct", metrics)
        self.assertIn("memory_total_gb", metrics)
        
        procs = sys_tool.list_running_processes(top_n=5)
        self.assertGreater(len(procs), 0)

    def test_data_analysis_tools(self):
        data_tool = DataAnalysisTool(workspace=self.test_dir)
        csv_file = self.test_dir / "data.csv"
        csv_file.write_text("id,val\n1,100\n2,200\n")
        
        res = data_tool.analyze_dataset("data.csv")
        self.assertIn("shape", res)
        self.assertIn("columns", res)

    def test_speculative_sandbox(self):
        sandbox = SpeculativeSandboxEngine(workspace=self.test_dir)
        worktree_path = sandbox.create_worktree("branch_test")
        self.assertIsNotNone(worktree_path)
        sandbox.cleanup_worktree("branch_test")

    def test_self_evolver(self):
        evolver = SelfEvolverEngine(storage_dir=self.test_dir)
        evolver.record_failure_mode("test task", "run_command", "Syntax error", "Always validate syntax before execution.")
        self.assertGreater(len(evolver.insights), 0)

    def test_git_checkpointing(self):
        git_mgr = GitCheckpointManager(workspace_dir=self.test_dir)
        git_mgr.init_if_needed()
        self.assertTrue(git_mgr.is_git_repo())
        
        (self.test_dir / "file1.txt").write_text("v1")
        sha1 = git_mgr.create_snapshot("First snapshot")
        self.assertIsNotNone(sha1)
        
        (self.test_dir / "file1.txt").write_text("v2")
        sha2 = git_mgr.create_snapshot("Second snapshot")
        
        ok = git_mgr.rollback_to_snapshot(sha1)
        self.assertTrue(ok)
        self.assertEqual((self.test_dir / "file1.txt").read_text(), "v1")

    def test_memory_manager(self):
        mem = MemoryManager(workspace=self.test_dir)
        (self.test_dir / "app.py").write_text("class MyService:\n    def process(self):\n        pass\n")
        mem.initialize()
        
        snapshot = mem.get_context_snapshot("MyService")
        self.assertGreater(len(snapshot["relevant_symbols"]), 0)
        self.assertEqual(snapshot["relevant_symbols"][0]["kind"], "class")

    def test_lats_tree_search(self):
        lats = LATSTreeSearch()
        root = LATSNode(thought="Root node")
        child1 = LATSNode(thought="Child 1", parent=root)
        child2 = LATSNode(thought="Child 2", parent=root)
        root.add_child(child1)
        root.add_child(child2)
        
        selected = lats.select_best_node(root)
        self.assertIn(selected, [child1, child2])
        
        child1.backpropagate(0.9)
        self.assertEqual(child1.visits, 1)
        self.assertEqual(root.visits, 1)

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
