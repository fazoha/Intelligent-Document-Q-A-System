"""
Answer generation service using OpenAI GPT-5-mini.
"""

import re
from typing import List, Tuple, Optional, Literal
from openai import OpenAI
from models import ChunkMetadata, Citation
from utils import config, app_logger

ReasoningEffort = Literal["none", "low", "medium", "high"]
VerbosityLevel = Literal["low", "medium", "high"]


class GPTAnswerGenerator:
    """Generate answers using GPT-5-mini with retrieved context."""
    
    def __init__(
        self,
        default_reasoning_effort: ReasoningEffort = "low",
        default_text_verbosity: VerbosityLevel = "low"
    ):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-5-mini"
        self.default_reasoning_effort = default_reasoning_effort
        self.default_text_verbosity = default_text_verbosity
        self.logger = app_logger
    
    def generate(
        self,
        query: str,
        chunks: List[ChunkMetadata],
        reasoning_effort: Optional[ReasoningEffort] = None,
        text_verbosity: Optional[VerbosityLevel] = None
    ) -> Tuple[str, List[Citation]]:
        """
        Generate an answer with citations.
        
        Args:
            query: User's question
            chunks: Retrieved context chunks
            reasoning_effort: Override reasoning effort level if needed
            text_verbosity: Override verbosity level if needed
            
        Returns:
            Tuple of (answer_text, list_of_citations)
        """
        if not chunks:
            return (
                "I don't have any documents indexed to answer this question. "
                "Please upload a document first.",
                []
            )
        
        # Build prompt
        prompt = self._build_prompt(query, chunks)
        target_reasoning_effort = reasoning_effort or self.default_reasoning_effort
        target_text_verbosity = text_verbosity or self.default_text_verbosity
        
        try:
            # Call GPT-5-mini Responses API
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                instructions="You are a helpful assistant answering questions about uploaded documents.",
                reasoning={"effort": target_reasoning_effort},
                text={"verbosity": target_text_verbosity},
            )
            
            answer = self._extract_response_text(response)
            if not answer:
                raise ValueError("Empty response from gpt-5-mini")
            
            self.logger.info(f"Generated answer (length={len(answer)} chars)")
            
            # Extract citations from answer
            citations = self._extract_citations(answer, chunks)
            
            return answer, citations
        
        except Exception as e:
            self.logger.error(f"Answer generation failed: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    def _build_prompt(self, query: str, chunks: List[ChunkMetadata]) -> str:
        """Build the GPT prompt with context and instructions."""
        context_blocks = []
        
        for chunk in chunks:
            context_block = (
                f"[{chunk.chunk_id}] "
                f"(Document: {chunk.doc_name}, Page {chunk.page}, Type: {chunk.block_type})\n"
                f"{chunk.text}\n"
            )
            context_blocks.append(context_block)
        
        context = "\n".join(context_blocks)
        
        prompt = f"""You are a helpful assistant answering questions about uploaded documents.

Context from documents:
{context}

User Question:
{query}

Instructions:
1. Answer the question using ONLY the information provided in the context above.
2. Cite your sources by including [chunk_id] inline in your answer wherever you reference information.
3. Place citations immediately after the sentence or fact they support, not on a new line. Example: "The revenue grew by 5% [chunk_12]."
4. If the context does not contain enough information to answer the question, respond with: "I don't have enough information in the provided documents to answer this question."
5. Be concise, accurate, and professional.
6. Do not make up information or cite chunks that were not provided.

Answer:"""
        
        return prompt
    
    def _extract_citations(
        self,
        answer: str,
        chunks: List[ChunkMetadata]
    ) -> List[Citation]:
        """
        Extract citation tags from answer and build Citation objects.
        
        Args:
            answer: Generated answer text
            chunks: Available chunks for citations
            
        Returns:
            List of Citation objects
        """
        # Find all [chunk_XX] patterns in the answer
        citation_pattern = r'\[chunk_(\d+)\]'
        matches = re.findall(citation_pattern, answer)
        
        # Create a mapping of chunk_id to chunk
        chunk_map = {chunk.chunk_id: chunk for chunk in chunks}
        
        # Build Citation objects for referenced chunks
        citations = []
        seen_chunk_ids = set()
        
        for match in matches:
            chunk_id = f"chunk_{match}"
            
            # Avoid duplicate citations
            if chunk_id in seen_chunk_ids:
                continue
            
            seen_chunk_ids.add(chunk_id)
            
            # Find the corresponding chunk
            chunk = chunk_map.get(chunk_id)
            if chunk:
                citation = Citation(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    page=chunk.page,
                    bbox=chunk.bbox,
                    doc_name=chunk.doc_name,
                    block_type=chunk.block_type
                )
                citations.append(citation)
            else:
                self.logger.warning(
                    f"GPT cited {chunk_id} but it's not in retrieved chunks"
                )
        
        self.logger.info(f"Extracted {len(citations)} citations from answer")
        
        return citations
    
    @staticmethod
    def _extract_response_text(response) -> str:
        """Coalesce text output from the Responses API payload."""
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()
        
        content_blocks = []
        for output_item in getattr(response, "output", []) or []:
            for content in getattr(output_item, "content", []) or []:
                if getattr(content, "type", None) == "output_text":
                    content_blocks.append(getattr(content, "text", "") or "")
                elif hasattr(content, "text"):
                    text_obj = getattr(content, "text")
                    if hasattr(text_obj, "value"):
                        content_blocks.append(text_obj.value)
                    elif isinstance(text_obj, str):
                        content_blocks.append(text_obj)
        return "\n".join(block.strip() for block in content_blocks if block).strip()
