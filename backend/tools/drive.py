import logging
import httpx
import re
from typing import Any, Dict
from backend.tools.base import BaseTool

logger = logging.getLogger(__name__)

class DriveTool(BaseTool):
    """
    Tool to connect to Google Drive to download candidate resumes or portfolios.
    """
    name: str = "DriveTool"
    description: str = "Downloads files (Resumes, portfolios, transcripts) hosted on Google Drive using file IDs or sharing links."

    async def run(self, file_url: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Connects to Google Drive to retrieve file headers or metadata.
        """
        logger.info(f"DriveTool downloading file from: {file_url}")
        
        try:
            file_id = None
            id_match_1 = re.search(r"/file/d/([a-zA-Z0-9-_]+)", file_url)
            id_match_2 = re.search(r"[?&]id=([a-zA-Z0-9-_]+)", file_url)
            
            if id_match_1:
                file_id = id_match_1.group(1)
            elif id_match_2:
                file_id = id_match_2.group(1)
                
            if not file_id:
                raise ValueError("Could not extract Google Drive file ID from URL.")
                
            download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient() as client:
                res = await client.head(download_url, headers=headers, timeout=10.0, follow_redirects=True)
                
                if res.status_code >= 400:
                    headers["Range"] = "bytes=0-1024"
                    res = await client.get(download_url, headers=headers, timeout=10.0, follow_redirects=True)
                    
                res.raise_for_status()
                
                content_type = res.headers.get("Content-Type", "application/octet-stream")
                content_length = int(res.headers.get("Content-Length", "1048576"))
                content_disposition = res.headers.get("Content-Disposition", "")
                
                filename = "downloaded_file"
                filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
                    
            return {
                "file_url": file_url,
                "file_id": file_id,
                "filename": filename,
                "file_size_bytes": content_length,
                "mime_type": content_type,
                "download_success": True
            }
        except Exception as e:
            logger.error(f"DriveTool failed for file '{file_url}': {e}")
            return {
                "file_url": file_url,
                "filename": "failed_download.bin",
                "file_size_bytes": 0,
                "mime_type": "unknown",
                "download_success": False,
                "error": str(e)
            }
