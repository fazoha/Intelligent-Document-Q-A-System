"""
Chunk builder service for creating layout-aware document chunks.
"""

import tiktoken
from typing import List, Dict, Any
from models import ChunkMetadata
from utils import config, app_logger


class ChunkBuilder:
    """Build layout-aware chunks from parsed document elements."""
    
    def __init__(self, max_tokens: int = None):
        self.max_tokens = max_tokens or config.MAX_CHUNK_TOKENS
        self.tokenizer = self._resolve_tokenizer()
        self.logger = app_logger
    
    def build_chunks(
        self,
        elements: List[Dict[str, Any]],
        doc_id: str,
        doc_name: str,
        parser
    ) -> List[ChunkMetadata]:
        """
        Build chunks from parsed elements with layout metadata.
        
        Args:
            elements: List of parsed elements from Unstructured.io
            doc_id: Document ID
            doc_name: Original filename
            parser: UnstructuredParser instance for helper methods
            
        Returns:
            List of ChunkMetadata objects
        """
        chunks = []
        current_chunk_texts = []
        current_chunk_tokens = 0
        current_page = 1
        current_bbox = []
        current_block_type = "paragraph"
        current_section_heading = None
        
        for idx, element in enumerate(elements):
            text = parser.extract_text(element)
            if not text or not text.strip():
                continue
            
            element_type = parser.extract_type(element)
            block_type = parser.map_type_to_block_type(element_type)
            page = parser.extract_page(element)
            bbox = parser.extract_bbox(element)
            
            # Track section headings
            if block_type == "heading":
                current_section_heading = text.strip()
            
            # Count tokens in this element
            token_count = len(self.tokenizer.encode(text))
            
            # Check if we need to start a new chunk
            should_split = (
                current_chunk_tokens + token_count > self.max_tokens and
                current_chunk_texts  # Don't split if this is the first element
            )
            
            if should_split:
                # Save current chunk
                chunk = self._create_chunk(
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=len(chunks),
                    texts=current_chunk_texts,
                    page=current_page,
                    bbox=current_bbox,
                    block_type=current_block_type,
                    section_heading=current_section_heading,
                    token_count=current_chunk_tokens
                )
                chunks.append(chunk)
                
                # Reset for new chunk
                current_chunk_texts = [text]
                current_chunk_tokens = token_count
                current_page = page
                current_bbox = bbox
                current_block_type = block_type
            else:
                # Add to current chunk
                current_chunk_texts.append(text)
                current_chunk_tokens += token_count
                
                # Update chunk metadata (use first element's page/bbox if not set)
                if not current_bbox and bbox:
                    current_bbox = bbox
                if page:
                    current_page = page
                current_block_type = block_type  # Use latest block type
        
        # Don't forget the last chunk
        if current_chunk_texts:
            chunk = self._create_chunk(
                doc_id=doc_id,
                doc_name=doc_name,
                chunk_index=len(chunks),
                texts=current_chunk_texts,
                page=current_page,
                bbox=current_bbox,
                block_type=current_block_type,
                section_heading=current_section_heading,
                token_count=current_chunk_tokens
            )
            chunks.append(chunk)
        
        self.logger.info(
            f"Built {len(chunks)} chunks from {len(elements)} elements "
            f"for document {doc_name}"
        )
        
        return chunks
    
    @staticmethod
    def _resolve_tokenizer():
        """
        GPT-5-mini shares the cl100k_base tokenizer; fall back gracefully if the
        named encoding is unavailable in the current tiktoken build.
        """
        try:
            return tiktoken.encoding_for_model("gpt-5-mini")
        except Exception:
            return tiktoken.get_encoding("cl100k_base")
    
    def _create_chunk(
        self,
        doc_id: str,
        doc_name: str,
        chunk_index: int,
        texts: List[str],
        page: int,
        bbox: List[float],
        block_type: str,
        section_heading: str,
        token_count: int
    ) -> ChunkMetadata:
        """Create a ChunkMetadata object from accumulated data."""
        chunk_text = "\n\n".join(texts)
        
        return ChunkMetadata(
            doc_id=doc_id,
            chunk_id=f"chunk_{chunk_index}",
            text=chunk_text,
            page=page,
            bbox=bbox or [],
            block_type=block_type,
            section_heading=section_heading,
            doc_name=doc_name,
            token_count=token_count
        )

