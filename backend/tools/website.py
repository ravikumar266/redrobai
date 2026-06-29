import logging
import httpx
import re
from typing import Any, Dict
from backend.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WebsiteTool(BaseTool):
    """
    Tool to fetch and scrape text content from candidate websites, blogs, or personal pages.
    """
    name: str = "WebsiteTool"
    description: str = "Scrapes text and retrieves headers/metadata from candidate personal websites and blogs."

    async def run(self, url: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Crawls the target URL and returns raw/cleaned content.
        """
        logger.info(f"WebsiteTool crawling URL: {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
                status_code = res.status_code
                html = res.text
                
            # Extract title using regex
            title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "No Title Found"
            
            # Clean HTML to get plain text summary
            text = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            summary = text[:500] + "..." if len(text) > 500 else text
            
            return {
                "url": url,
                "status_code": status_code,
                "title": title,
                "broken_links_found": [],
                "raw_text": summary
            }
        except Exception as e:
            logger.error(f"WebsiteTool failed to fetch '{url}': {e}")
            return {
                "url": url,
                "status_code": 0,
                "title": "Unreachable website",
                "broken_links_found": [],
                "raw_text": f"Error loading page: {str(e)}"
            }
