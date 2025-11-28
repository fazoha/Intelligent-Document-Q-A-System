"""
Answer generation service using OpenAI GPT-5-mini.

Phase 3 enhancements:
- Confidence scoring using ROUGE-L
- Extractive fallback for low-confidence answers
"""

import re
from typing import List, Tuple, Optional, Literal, Dict, Any
from dataclasses import dataclass
from openai import OpenAI
from models import ChunkMetadata, Citation
from utils import config, app_logger

ReasoningEffort = Literal["none", "low", "medium", "high"]
VerbosityLevel = Literal["low", "medium", "high"]
AnswerType = Literal["generative", "extractive"]


@dataclass
class GenerationResult:
    """Result of answer generation with confidence scoring."""
    answer: str
    citations: List[Citation]
    confidence_score: float
    confidence_level: str
    answer_type: AnswerType
    extractive_span: Optional[Dict[str, Any]] = None


class GPTAnswerGenerator:
    """
    Generate answers using GPT-5-mini with retrieved context.
    
    Phase 3: Includes confidence scoring and extractive fallback.
    """
    
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
        
        # Phase 3: Initialize confidence scorer (lazy load extractive QA)
        from services.confidence_service import ConfidenceScorer
        self.confidence_scorer = ConfidenceScorer()
        self._extractive_qa = None
    
    @property
    def extractive_qa(self):
        """Lazy load extractive QA service."""
        if self._extractive_qa is None and config.ENABLE_EXTRACTIVE_FALLBACK:
            from services.extractive_qa_service import ExtractiveQAService
            self._extractive_qa = ExtractiveQAService()
        return self._extractive_qa
    
    def generate_with_confidence(
        self,
        query: str,
        chunks: List[ChunkMetadata],
        reasoning_effort: Optional[ReasoningEffort] = None,
        text_verbosity: Optional[VerbosityLevel] = None
    ) -> GenerationResult:
        """
        Generate an answer with confidence scoring and optional extractive fallback.
        
        Phase 3 Workflow:
        1. Generate answer with GPT-5-mini
        2. Compute confidence score using ROUGE-L
        3. If confidence < threshold, try extractive fallback
        4. Return best answer with confidence info
        
        Args:
            query: User's question
            chunks: Retrieved context chunks
            reasoning_effort: Override reasoning effort level
            text_verbosity: Override verbosity level
            
        Returns:
            GenerationResult with answer, citations, and confidence info
        """
        if not chunks:
            return GenerationResult(
                answer="I don't have any documents indexed to answer this question. Please upload a document first.",
                citations=[],
                confidence_score=0.0,
                confidence_level="low",
                answer_type="generative"
            )
        
        # Step 1: Generate answer with GPT-5-mini
        answer, citations = self.generate(
            query=query,
            chunks=chunks,
            reasoning_effort=reasoning_effort,
            text_verbosity=text_verbosity
        )
        
        # Step 2: Compute confidence score
        confidence_score = self.confidence_scorer.compute_confidence_score(
            answer=answer,
            citations=citations
        )
        confidence_level = self.confidence_scorer.get_confidence_level(confidence_score)
        
        self.logger.info(
            f"Generative answer confidence: {confidence_score:.3f} ({confidence_level})"
        )
        
        # Step 3: Check if extractive fallback is needed
        if (
            confidence_score < config.CONFIDENCE_THRESHOLD
            and config.ENABLE_EXTRACTIVE_FALLBACK
            and self.extractive_qa is not None
        ):
            self.logger.info(
                f"Confidence {confidence_score:.3f} < threshold {config.CONFIDENCE_THRESHOLD}, "
                "trying extractive fallback..."
            )
            
            # Try extractive QA
            extractive_result = self._try_extractive_fallback(query, chunks)
            
            if extractive_result is not None:
                ext_answer, ext_score, ext_span = extractive_result
                
                # Use extractive if it has better confidence
                if ext_score > confidence_score:
                    self.logger.info(
                        f"Using extractive answer (score={ext_score:.3f} > {confidence_score:.3f})"
                    )
                    
                    # Create citation from the source chunk
                    ext_citations = self._create_extractive_citations(chunks, ext_span)
                    
                    return GenerationResult(
                        answer=ext_answer,
                        citations=ext_citations,
                        confidence_score=ext_score,
                        confidence_level=self.confidence_scorer.get_confidence_level(ext_score),
                        answer_type="extractive",
                        extractive_span=ext_span
                    )
                else:
                    self.logger.info(
                        f"Keeping generative answer (extractive score {ext_score:.3f} <= {confidence_score:.3f})"
                    )
        
        # Return generative result
        return GenerationResult(
            answer=answer,
            citations=citations,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            answer_type="generative"
        )
    
    def _try_extractive_fallback(
        self,
        query: str,
        chunks: List[ChunkMetadata]
    ) -> Optional[Tuple[str, float, Optional[Dict[str, Any]]]]:
        """
        Try extractive QA as fallback.
        
        Args:
            query: User's question
            chunks: Retrieved context chunks
            
        Returns:
            Tuple of (answer, confidence, span_info) or None if failed
        """
        try:
            answer, score, span_info = self.extractive_qa.extract_answer(
                question=query,
                chunks=chunks
            )
            
            # Validate the extractive answer
            if answer and len(answer.strip()) > 0 and score > 0.01:
                return (answer, score, span_info)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Extractive fallback failed: {e}")
            return None
    
    def _create_extractive_citations(
        self,
        chunks: List[ChunkMetadata],
        span_info: Optional[Dict[str, Any]]
    ) -> List[Citation]:
        """
        Create citations for extractive answer.
        
        Args:
            chunks: Source chunks
            span_info: Span information from extraction
            
        Returns:
            List of Citation objects
        """
        # Use the first chunk as the citation source (most relevant)
        if not chunks:
            return []
        
        chunk = chunks[0]
        
        citation = Citation(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            page=chunk.page,
            bbox=chunk.bbox,
            doc_name=chunk.doc_name,
            block_type=chunk.block_type
        )
        
        return [citation]
    
    def generate(
        self,
        query: str,
        chunks: List[ChunkMetadata],
        reasoning_effort: Optional[ReasoningEffort] = None,
        text_verbosity: Optional[VerbosityLevel] = None
    ) -> Tuple[str, List[Citation]]:
        """
        Generate an answer with citations (original method for backward compatibility).
        
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
