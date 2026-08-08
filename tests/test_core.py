import unittest
import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from apex.config import Config, detect_hardware
from apex.providers.router import HybridRouter
from apex.tools.filesystem import FileSystemTool
from apex.tools.git_checkpoint import GitCheckpointManager
from apex.tools.registry import ToolRegistry
from apex.memory.memory_manager import MemoryManager
from apex.core.lats_tree import LATSTreeSearch, LATSNode
from apex.core.context_budget import ContextBudgetManager

class TestApexSystem(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.test_dir, ignore_errors=True))

    def test_hardware_detection(self):
        specs = detect_hardware()
        self.assertGreater(specs.cpu_cores, 0)
        self.assertGreater(specs.total_ram_gb, 0)

    def test_config_management(self):
        config = Config()
        config_file = self.test_dir / "config.yaml"
        config.save(config_file)
        self.assertTrue(config_file.exists())
        
        loaded = Config.load(config_file)
        self.assertEqual(loaded.local_model, config.local_model)

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

    def test_git_checkpointing(self):
        git_mgr = GitCheckpointManager(workspace_dir=self.test_dir)
        git_mgr.init_if_needed()
        self.assertTrue(git_mgr.is_git_repo())
        
        # Create dummy file and snapshot
        (self.test_dir / "file1.txt").write_text("v1")
        sha1 = git_mgr.create_snapshot("First snapshot")
        self.assertIsNotNone(sha1)
        
        # Modify file and create second snapshot
        (self.test_dir / "file1.txt").write_text("v2")
        sha2 = git_mgr.create_snapshot("Second snapshot")
        
        # Rollback to first snapshot
        ok = git_mgr.rollback_to_snapshot(sha1)
        self.assertTrue(ok)
        self.assertEqual((self.test_dir / "file1.txt").read_text(), "v1")

    def test_memory_manager(self):
        mem = MemoryManager(workspace=self.test_dir)
        # Create a test python file for semantic indexer
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
        
        # Backpropagate score
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
