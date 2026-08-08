import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from apex.memory.cognitive_graph import CognitiveKnowledgeGraph

class DocumentIngestionTool:
    """Parses PDF, PPTX, DOCX, and Text documents for knowledge ingestion and task synthesis."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.graph = CognitiveKnowledgeGraph(self.workspace / ".apex" / "cognitive_graph.db")

    def parse_document(self, relative_or_abs_path: str) -> str:
        """Extracts plain text content from PDF, PPTX, DOCX, or text files."""
        target = Path(relative_or_abs_path)
        if not target.is_absolute():
            target = self.workspace / relative_or_abs_path
            
        if not target.exists():
            return f"Error: File '{relative_or_abs_path}' not found."

        ext = target.suffix.lower()
        try:
            if ext == ".pdf":
                return self._parse_pdf(target)
            elif ext == ".pptx":
                return self._parse_pptx(target)
            elif ext == ".docx":
                return self._parse_docx(target)
            else:
                # Text / Markdown / CSV / JSON files
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
        except Exception as e:
            return f"Error parsing document '{relative_or_abs_path}': {str(e)}"

    def _parse_pdf(self, path: Path) -> str:
        """Parse PDF using pypdf."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            pages_text = []
            for idx, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                pages_text.append(f"--- Page {idx} ---\n{text}")
            return "\n\n".join(pages_text)
        except Exception as e:
            return f"PDF parsing error: {e}"

    def _parse_pptx(self, path: Path) -> str:
        """Parse PPTX slide text via zipfile XML extraction."""
        try:
            slide_texts = []
            with zipfile.ZipFile(path, "r") as z:
                # Find slide xml files ppt/slides/slide1.xml, slide2.xml ...
                slide_files = [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
                # Sort slide files by slide number
                slide_files.sort(key=lambda s: int("".join(filter(str.isdigit, s)) or "0"))
                
                for idx, sfile in enumerate(slide_files, 1):
                    xml_content = z.read(sfile)
                    root = ET.fromstring(xml_content)
                    texts = [elem.text for elem in root.iter() if elem.text and elem.text.strip()]
                    slide_texts.append(f"--- Slide {idx} ---\n" + " ".join(texts))
            return "\n\n".join(slide_texts)
        except Exception as e:
            return f"PPTX parsing error: {e}"

    def _parse_docx(self, path: Path) -> str:
        """Parse DOCX paragraph text."""
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception:
            # Fallback zipfile XML extraction for word/document.xml
            try:
                with zipfile.ZipFile(path, "r") as z:
                    xml_content = z.read("word/document.xml")
                    root = ET.fromstring(xml_content)
                    texts = [elem.text for elem in root.iter() if elem.text and elem.text.strip()]
                    return "\n".join(texts)
            except Exception as e:
                return f"DOCX parsing error: {e}"

    def ingest_and_index(self, file_path: str) -> str:
        """Parses a document and indexes its content into the Cognitive Knowledge Graph."""
        content = self.parse_document(file_path)
        if content.startswith("Error"):
            return content
            
        filename = Path(file_path).name
        node_id = self.graph.add_node(
            node_type="document",
            title=f"Doc: {filename}",
            content=content[:5000],  # Index snippet
            metadata={"filename": filename, "char_count": len(content)}
        )
        return f"Successfully ingested and indexed '{filename}' (Node #{node_id}, {len(content)} chars)."
