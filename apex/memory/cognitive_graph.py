import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

class CognitiveKnowledgeGraph:
    """Omnipresent Local Cognitive Knowledge Graph.
    Indexes terminal activities, code modifications, research notes, and developer intent.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (Path.cwd() / ".apex" / "cognitive_graph.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cognitive_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    node_type TEXT,
                    title TEXT,
                    content TEXT,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cognitive_edges (
                    source_id INTEGER,
                    target_id INTEGER,
                    relation TEXT,
                    PRIMARY KEY (source_id, target_id, relation)
                )
            """)
            conn.commit()

    def add_node(self, node_type: str, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        meta_json = json.dumps(metadata or {})
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cognitive_nodes (timestamp, node_type, title, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (time.time(), node_type, title, content, meta_json)
            )
            conn.commit()
            return cursor.lastrowid

    def add_edge(self, source_id: int, target_id: int, relation: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO cognitive_edges (source_id, target_id, relation) VALUES (?, ?, ?)",
                (source_id, target_id, relation)
            )
            conn.commit()

    def search_graph(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cognitive_nodes WHERE title LIKE ? OR content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_summary(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cognitive_nodes")
            node_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM cognitive_edges")
            edge_count = cursor.fetchone()[0]
            return {"total_nodes": node_count, "total_edges": edge_count}
