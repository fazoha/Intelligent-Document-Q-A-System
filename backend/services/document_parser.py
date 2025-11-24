"""
Document parsing service using Unstructured.io API.
"""

import requests
from typing import List, Dict, Any
from pypdf import PdfReader
from utils import config, app_logger


class UnstructuredParser:
    """Parse documents using Unstructured.io API to extract text and layout."""
    
    def __init__(self):
        self.api_key = config.UNSTRUCTURED_API_KEY
        self.api_url = config.UNSTRUCTURED_API_URL
        self.logger = app_logger
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a document file and extract elements with layout metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of elements, each containing:
                - type: Element type (Title, NarrativeText, Table, etc.)
                - text: Text content
                - metadata: Contains page_number, coordinates (bbox), etc.
        
        Raises:
            Exception: If API call fails
        """
        try:
            with open(file_path, "rb") as f:
                files = {"files": f}
                headers = {"unstructured-api-key": self.api_key}
                
                data = {
                    "strategy": "hi_res",  # High-resolution parsing
                    "coordinates": "true",  # Include bounding boxes
                    "pdf_infer_table_structure": "true",  # Detect table structure
                }
                
                self.logger.info(f"Parsing document: {file_path}")
                
                response = requests.post(
                    self.api_url,
                    files=files,
                    headers=headers,
                    data=data,
                    timeout=60  # 60 second timeout
                )
                
                response.raise_for_status()
                elements = response.json()
                
                self.logger.info(
                    f"Successfully parsed document. "
                    f"Found {len(elements)} elements"
                )
                
                return elements
        
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout parsing document: {file_path}")
            raise Exception("Document parsing timed out after 60 seconds")
        
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                "Unstructured API unavailable (%s). Falling back to lightweight parser.",
                e,
            )
            return self._fallback_parse(file_path)
        
        except Exception as e:
            self.logger.warning(
                "Unexpected error parsing document (%s). Falling back to lightweight parser.",
                e,
            )
            return self._fallback_parse(file_path)
    
    @staticmethod
    def extract_text(element: Dict[str, Any]) -> str:
        """Extract text from an element."""
        return element.get("text", "")
    
    @staticmethod
    def extract_type(element: Dict[str, Any]) -> str:
        """Extract element type."""
        return element.get("type", "NarrativeText")
    
    @staticmethod
    def extract_page(element: Dict[str, Any]) -> int:
        """Extract page number from element metadata."""
        metadata = element.get("metadata", {})
        return metadata.get("page_number", 1)
    
    @staticmethod
    def extract_bbox(element: Dict[str, Any]) -> List[float]:
        """Extract bounding box coordinates from element metadata."""
        metadata = element.get("metadata", {})
        coordinates = metadata.get("coordinates", {})
        
        # coordinates may have 'points' or direct bbox
        if "points" in coordinates:
            points = coordinates["points"]
            if len(points) >= 4:
                # Extract min/max x,y from points
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                return [min(xs), min(ys), max(xs), max(ys)]
        
        # Fallback to empty bbox
        return []
    
    @staticmethod
    def map_type_to_block_type(element_type: str) -> str:
        """Map Unstructured.io element type to our block type."""
        type_mapping = {
            "Title": "heading",
            "Header": "heading",
            "Footer": "footer",
            "NarrativeText": "paragraph",
            "ListItem": "paragraph",
            "Table": "table",
            "FigureCaption": "caption",
            "Image": "image",
        }
        return type_mapping.get(element_type, "paragraph")

    def _fallback_parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Minimal parser used when Unstructured API isn't reachable.
        Currently only supports PDF files using pypdf.
        """
        # Check file extension
        file_lower = file_path.lower()
        if not file_lower.endswith('.pdf'):
            self.logger.error(
                f"Fallback parser only supports PDF files. Got: {file_path}"
            )
            raise Exception(
                f"Unstructured API is unavailable and fallback parser only supports PDF files. "
                f"Cannot parse {file_path}. Please ensure Unstructured API is accessible or upload a PDF file."
            )
        
        elements: List[Dict[str, Any]] = []
        try:
            reader = PdfReader(file_path)
            for page_index, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
                if not paragraphs:
                    paragraphs = [raw_text.strip()] if raw_text.strip() else []

                for paragraph in paragraphs:
                    elements.append(
                        {
                            "type": "NarrativeText",
                            "text": paragraph,
                            "metadata": {
                                "page_number": page_index + 1,
                                "coordinates": {},
                            },
                        }
                    )
            self.logger.info(
                "Fallback parser extracted %s chunks across %s pages",
                len(elements),
                len(reader.pages),
            )
            return elements
        except Exception as e:
            self.logger.error(f"Fallback PDF parsing failed: {e}")
            raise Exception(
                "Failed to parse document via Unstructured API or local fallback."
            )

