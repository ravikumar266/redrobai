import os
import logging
from typing import Any, Dict
from backend.tools.base import BaseTool

logger = logging.getLogger(__name__)

class PDFTool(BaseTool):
    """
    Tool to extract text content, metadata, and structural layout from PDF files.
    """
    name: str = "PDFTool"
    description: str = "Extracts structured metadata and raw text from PDF resume and portfolio uploads."

    async def run(self, file_path: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses a PDF file locally and extracts plain text.
        """
        logger.info(f"PDFTool parsing PDF file: {file_path}")
        
        if not os.path.exists(file_path):
            return {
                "file_path": file_path,
                "error": "File not found.",
                "extracted_text": "",
                "page_count": 0
            }
            
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
            
            text_parts = []
            extracted_urls = set()
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text_parts.append(f"--- Page {i+1} ---\n{text}")
                
                # Extract hidden URL annotations
                if "/Annots" in page:
                    try:
                        for annot in page["/Annots"]:
                            obj = annot.get_object()
                            if obj.get("/Subtype") == "/Link" and "/A" in obj and "/URI" in obj["/A"]:
                                extracted_urls.add(str(obj["/A"]["/URI"]))
                    except Exception as e:
                        logger.warning(f"Error extracting annotations on page {i+1}: {e}")
                
            extracted_text = "\n\n".join(text_parts) if page_count > 0 else ""
            
            if extracted_urls:
                extracted_text += "\n\n[Extracted Links]\n" + "\n".join(f"- {url}" for url in extracted_urls)
            
            metadata = {}
            if reader.metadata:
                metadata = {
                    "author": reader.metadata.get("/Author", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                    "producer": reader.metadata.get("/Producer", ""),
                    "title": reader.metadata.get("/Title", "")
                }
                
            return {
                "file_path": file_path,
                "page_count": page_count,
                "extracted_text": extracted_text,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"PDFTool failed to parse PDF '{file_path}': {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "extracted_text": "Failed to parse PDF.",
                "page_count": 0
            }
