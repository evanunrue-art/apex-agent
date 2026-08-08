import json
import httpx
from typing import List, Dict, Any, Optional

class ResearchSynthesisTool:
    """Autonomous deep research synthesis tool that queries web endpoints, extracts context, and indexes sources."""

    def __init__(self):
        self.sources: List[Dict[str, str]] = []

    async def search_and_synthesize(self, topic: str, subqueries: Optional[List[str]] = None) -> str:
        """Executes multi-angle search synthesis on a given topic."""
        queries = subqueries or [topic, f"{topic} latest research 2026", f"{topic} best practices and documentation"]
        results = []

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for q in queries:
                try:
                    # Search query via DuckDuckGo API or HTTP web endpoint
                    res = await client.get(
                        "https://html.duckduckgo.com/html/",
                        params={"q": q},
                        headers={"User-Agent": "APEX-ResearchAgent/1.0"}
                    )
                    if res.status_code == 200:
                        import re
                        links = re.findall(r'href="(/l/\?kh=-1&amp;uddg=[^"]+)"', res.text)
                        clean_text = re.sub(r'<.*?>', ' ', res.text)
                        clean_text = re.sub(r'\s+', ' ', clean_text)
                        results.append({
                            "query": q,
                            "snippet": clean_text[:1200]
                        })
                except Exception as e:
                    results.append({"query": q, "error": str(e)})

        synthesis_doc = f"# Research Synthesis: {topic}\n\n"
        for item in results:
            synthesis_doc += f"## Query: {item['query']}\n"
            synthesis_doc += f"{item.get('snippet', item.get('error', ''))}\n\n"

        return synthesis_doc
