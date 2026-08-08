import httpx
from typing import Optional

class BrowserTool:
    """Web fetching & visual browser interaction tool."""

    async def fetch_web_page(self, url: str) -> str:
        """Fetch and extract text content from a web URL."""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                res = await client.get(url, headers={"User-Agent": "APEX-Agent/1.0"})
                if res.status_code == 200:
                    text = res.text
                    # Basic HTML tag stripping
                    import re
                    clean = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
                    clean = re.sub(r'<style.*?</style>', '', clean, flags=re.DOTALL)
                    clean = re.sub(r'<.*?>', ' ', clean)
                    clean = re.sub(r'\s+', ' ', clean)
                    return clean[:4000]
                return f"HTTP Error {res.status_code}"
        except Exception as e:
            return f"Failed to fetch URL: {e}"

    async def run_playwright_test(self, url: str) -> str:
        """Runs a headless Playwright visual browser snapshot if available."""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=15000)
                title = await page.title()
                content = await page.content()
                await browser.close()
                return f"Page Title: {title}\nLength: {len(content)} chars"
        except Exception as e:
            return f"Playwright error or not installed: {e}"
