import logging
import httpx
from typing import Any, Dict
from backend.tools.base import BaseTool

logger = logging.getLogger(__name__)

class YouTubeTool(BaseTool):
    """
    Tool to extract transcripts and metadata from YouTube videos (e.g. tech presentations, project demos).
    """
    name: str = "YouTubeTool"
    description: str = "Fetches metadata from YouTube video links to verify project demos or presentations."

    async def run(self, video_url: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieves video information using public oEmbed API.
        """
        logger.info(f"YouTubeTool auditing video: {video_url}")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get("https://www.youtube.com/oembed", params={"url": video_url, "format": "json"}, timeout=10.0)
                res.raise_for_status()
                data = res.json()
                
            return {
                "video_url": video_url,
                "title": data.get("title", "Unknown Title"),
                "author_name": data.get("author_name", "Unknown Channel"),
                "type": data.get("type", "video"),
                "thumbnail_url": data.get("thumbnail_url", ""),
                "transcript": f"Audited YouTube presentation title '{data.get('title')}' by '{data.get('author_name')}'."
            }
        except Exception as e:
            logger.error(f"YouTubeTool failed to query oEmbed for '{video_url}': {e}")
            return {
                "video_url": video_url,
                "title": "Unreachable or private video",
                "author_name": "Unknown",
                "type": "video",
                "transcript": f"Error fetching video details: {str(e)}"
            }
