"""
Extractive Question Answering service using DistilBERT.

Phase 3: Provides fallback answers by extracting spans from source documents.
"""

from typing import List, Tuple, Optional, Dict, Any
from models import ChunkMetadata, Citation
from utils import app_logger, config

# Lazy loading for transformers to avoid startup delay
_model = None
_tokenizer = None


def _load_model():
    """Lazy load the DistilBERT model and tokenizer."""
    global _model, _tokenizer
    
    if _model is None:
        from transformers import AutoModelForQuestionAnswering, AutoTokenizer
        import torch
        
        model_name = config.EXTRACTIVE_MODEL
        app_logger.info(f"Loading extractive QA model: {model_name}")
        
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        
        # Set to evaluation mode
        _model.eval()
        
        # Move to GPU if available
        if torch.cuda.is_available():
            _model = _model.cuda()
            app_logger.info("Extractive QA model loaded on GPU")
        else:
            app_logger.info("Extractive QA model loaded on CPU")
    
    return _model, _tokenizer


class ExtractiveQAService:
    """
    Extractive Question Answering using DistilBERT.
    
    Extracts answer spans directly from source documents instead of
    generating text. Used as fallback when generative confidence is low.
    """
    
    def __init__(self):
        self.logger = app_logger
        self.max_seq_length = 512
        self.doc_stride = 128
    
    def extract_answer(
        self,
        question: str,
        chunks: List[ChunkMetadata],
        top_k: int = 3
    ) -> Tuple[str, float, Optional[Dict[str, Any]]]:
        """
        Extract the best answer span from the provided chunks.
        
        Args:
            question: The user's question
            chunks: Retrieved document chunks
            top_k: Number of top answers to consider
            
        Returns:
            Tuple of (answer_text, confidence_score, span_info)
        """
        if not chunks:
            return ("No context available to extract an answer.", 0.0, None)
        
        model, tokenizer = _load_model()
        
        # Combine chunks into context
        context = self._prepare_context(chunks)
        
        try:
            # Extract answer
            answer, score, span_info = self._extract_from_context(
                question=question,
                context=context,
                model=model,
                tokenizer=tokenizer
            )
            
            self.logger.info(
                f"Extracted answer (score={score:.3f}): {answer[:100]}..."
            )
            
            return answer, score, span_info
            
        except Exception as e:
            self.logger.error(f"Extractive QA failed: {e}")
            return ("Unable to extract an answer.", 0.0, None)
    
    def extract_from_single_chunk(
        self,
        question: str,
        chunk: ChunkMetadata
    ) -> Tuple[str, float, int, int]:
        """
        Extract answer from a single chunk with span positions.
        
        Args:
            question: The user's question
            chunk: Single document chunk
            
        Returns:
            Tuple of (answer_text, confidence, start_char, end_char)
        """
        model, tokenizer = _load_model()
        
        try:
            answer, score, span_info = self._extract_from_context(
                question=question,
                context=chunk.text,
                model=model,
                tokenizer=tokenizer
            )
            
            start_char = span_info.get("start_char", 0) if span_info else 0
            end_char = span_info.get("end_char", 0) if span_info else 0
            
            return answer, score, start_char, end_char
            
        except Exception as e:
            self.logger.error(f"Single chunk extraction failed: {e}")
            return ("", 0.0, 0, 0)
    
    def _prepare_context(self, chunks: List[ChunkMetadata]) -> str:
        """
        Prepare context from multiple chunks.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Combined context string
        """
        context_parts = []
        
        for chunk in chunks:
            # Include chunk metadata for context
            header = f"[{chunk.chunk_id}] (Page {chunk.page}):"
            context_parts.append(f"{header}\n{chunk.text}")
        
        return "\n\n".join(context_parts)
    
    def _extract_from_context(
        self,
        question: str,
        context: str,
        model,
        tokenizer
    ) -> Tuple[str, float, Optional[Dict[str, Any]]]:
        """
        Extract answer span from context using the model.
        
        Args:
            question: The question
            context: The context text
            model: The QA model
            tokenizer: The tokenizer
            
        Returns:
            Tuple of (answer, score, span_info)
        """
        import torch
        
        # Tokenize input
        inputs = tokenizer(
            question,
            context,
            max_length=self.max_seq_length,
            truncation="only_second",
            stride=self.doc_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding="max_length",
            return_tensors="pt"
        )
        
        # Move to same device as model
        device = next(model.parameters()).device
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)
        
        # Get model predictions
        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
        
        # Process all chunks (for long contexts)
        best_answer = ""
        best_score = 0.0
        best_span_info = None
        
        for i in range(len(inputs["input_ids"])):
            start_logits = outputs.start_logits[i]
            end_logits = outputs.end_logits[i]
            
            # Get top start and end positions
            start_idx = torch.argmax(start_logits).item()
            end_idx = torch.argmax(end_logits).item()
            
            # Ensure valid span (end >= start)
            if end_idx < start_idx:
                end_idx = start_idx
            
            # Compute confidence score (softmax of logits)
            start_probs = torch.softmax(start_logits, dim=0)
            end_probs = torch.softmax(end_logits, dim=0)
            score = (start_probs[start_idx] * end_probs[end_idx]).item()
            
            # Decode answer
            tokens = input_ids[i][start_idx:end_idx + 1]
            answer = tokenizer.decode(tokens, skip_special_tokens=True)
            
            # Get character offsets if available
            offset_mapping = inputs.get("offset_mapping")
            span_info = None
            
            if offset_mapping is not None and len(answer) > 0:
                try:
                    # Get the offset for this chunk
                    offsets = offset_mapping[i].tolist()
                    
                    # Find character positions in original context
                    if start_idx < len(offsets) and end_idx < len(offsets):
                        start_char = offsets[start_idx][0]
                        end_char = offsets[end_idx][1]
                        
                        span_info = {
                            "start_char": start_char,
                            "end_char": end_char,
                            "chunk_index": i
                        }
                except Exception as e:
                    self.logger.debug(f"Could not get character offsets: {e}")
            
            # Update best answer
            if score > best_score and len(answer.strip()) > 0:
                best_answer = answer.strip()
                best_score = score
                best_span_info = span_info
        
        # Filter out very low confidence or empty answers
        if best_score < 0.01 or not best_answer:
            return ("I could not find a specific answer in the documents.", 0.0, None)
        
        return best_answer, best_score, best_span_info
    
    def get_highlighted_context(
        self,
        context: str,
        start_char: int,
        end_char: int
    ) -> str:
        """
        Get context with highlighted answer span.
        
        Args:
            context: The full context
            start_char: Start character position
            end_char: End character position
            
        Returns:
            Context with markdown highlighting
        """
        if start_char < 0 or end_char <= start_char or end_char > len(context):
            return context
        
        before = context[:start_char]
        answer = context[start_char:end_char]
        after = context[end_char:]
        
        return f"{before}**{answer}**{after}"


