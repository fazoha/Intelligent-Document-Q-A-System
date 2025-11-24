"""
Query planner service using spaCy for multi-hop reasoning.
Analyzes queries to detect multi-hop requirements and orchestrates sequential retrieval.
"""

from typing import List, Dict, Any, Optional
import spacy
from models import ChunkMetadata
from utils import config, app_logger


class QueryPlanner:
    """
    Analyze and plan query execution for multi-hop reasoning.
    
    Uses spaCy to:
    - Detect question type and complexity
    - Identify multi-hop queries (multiple sub-questions)
    - Extract key entities and dependencies
    - Plan sequential retrieval steps
    """
    
    def __init__(self):
        self.model_name = config.SPACY_MODEL
        self.enable_multi_hop = config.ENABLE_MULTI_HOP
        self.logger = app_logger
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Load spaCy model."""
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            self.logger.warning(
                f"spaCy model '{self.model_name}' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            self.nlp = None
        except Exception as e:
            self.logger.error(f"Failed to load spaCy model: {e}")
            self.nlp = None
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query structure and extract metadata.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with query analysis:
            - is_multi_hop: Whether query requires multiple retrieval steps
            - sub_queries: List of sub-questions (for multi-hop)
            - entities: Named entities
            - question_type: Type of question (what, where, when, etc.)
            - clauses: List of clauses
        """
        if not self.nlp:
            return self._simple_analysis(query)
        
        try:
            doc = self.nlp(query)
            
            # Extract entities
            entities = [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
            ]
            
            # Detect question type
            question_type = self._detect_question_type(doc)
            
            # Extract clauses (sentences)
            clauses = [sent.text.strip() for sent in doc.sents]
            
            # Detect multi-hop queries
            is_multi_hop = self._is_multi_hop_query(doc, clauses)
            
            # Extract sub-queries for multi-hop
            sub_queries = []
            if is_multi_hop and self.enable_multi_hop:
                sub_queries = self._extract_sub_queries(doc, clauses)
            
            analysis = {
                "is_multi_hop": is_multi_hop,
                "sub_queries": sub_queries,
                "entities": entities,
                "question_type": question_type,
                "clauses": clauses,
                "original_query": query
            }
            
            self.logger.info(
                f"Query analysis: type={question_type}, "
                f"multi_hop={is_multi_hop}, "
                f"entities={len(entities)}, "
                f"sub_queries={len(sub_queries)}"
            )
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Query analysis failed: {e}")
            return self._simple_analysis(query)
    
    def _simple_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback simple analysis without spaCy."""
        # Basic heuristics
        is_multi_hop = any(connector in query.lower() for connector in [
            ' and ', ' then ', ' after ', ' also ', ' additionally ',
            '; ', '? ', 'first', 'second', 'finally'
        ])
        
        # Split on common separators for multi-hop
        clauses = [query]
        if '?' in query and query.count('?') > 1:
            clauses = [q.strip() + '?' for q in query.split('?') if q.strip()]
        
        return {
            "is_multi_hop": is_multi_hop,
            "sub_queries": clauses if is_multi_hop else [],
            "entities": [],
            "question_type": self._simple_question_type(query),
            "clauses": clauses,
            "original_query": query
        }
    
    def _detect_question_type(self, doc) -> str:
        """Detect the type of question."""
        query_lower = doc.text.lower()
        
        if query_lower.startswith('what'):
            return 'what'
        elif query_lower.startswith('when'):
            return 'when'
        elif query_lower.startswith('where'):
            return 'where'
        elif query_lower.startswith('who'):
            return 'who'
        elif query_lower.startswith('why'):
            return 'why'
        elif query_lower.startswith('how'):
            return 'how'
        elif query_lower.startswith('which'):
            return 'which'
        else:
            return 'statement'
    
    def _simple_question_type(self, query: str) -> str:
        """Simple question type detection without spaCy."""
        query_lower = query.lower().strip()
        
        for q_type in ['what', 'when', 'where', 'who', 'why', 'how', 'which']:
            if query_lower.startswith(q_type):
                return q_type
        
        return 'statement'
    
    def _is_multi_hop_query(self, doc, clauses: List[str]) -> bool:
        """
        Determine if query requires multi-hop reasoning.
        
        Heuristics:
        1. Multiple sentences/questions
        2. Conjunctions with multiple clauses (and, then, after)
        3. Coreferent pronouns (it, this, that, they)
        4. Sequential indicators (first, second, then, after)
        """
        if not self.enable_multi_hop:
            return False
        
        # Multiple questions
        if len(clauses) > 1:
            return True
        
        query_lower = doc.text.lower()
        
        # Sequential indicators
        sequential_words = ['first', 'second', 'then', 'after', 'next', 'finally', 'subsequently']
        if any(word in query_lower for word in sequential_words):
            return True
        
        # Multiple 'and' conjunctions suggesting compound questions
        and_count = query_lower.count(' and ')
        if and_count >= 2:
            return True
        
        # Coreferent pronouns (suggesting reference to previous context)
        pronouns = ['it', 'this', 'that', 'they', 'these', 'those']
        tokens = [token.text.lower() for token in doc]
        pronoun_count = sum(1 for p in pronouns if p in tokens)
        
        if pronoun_count >= 2:
            return True
        
        return False
    
    def _extract_sub_queries(self, doc, clauses: List[str]) -> List[str]:
        """
        Extract sub-queries from a multi-hop query.
        
        Strategy:
        1. Split on sentence boundaries
        2. Split on coordinating conjunctions with question words
        3. Handle sequential indicators
        """
        sub_queries = []
        
        # If multiple sentences, use them as sub-queries
        if len(clauses) > 1:
            sub_queries = clauses
        else:
            # Single sentence - try to split on conjunctions
            query = doc.text
            
            # Split on ' and ' with question context
            if ' and ' in query.lower():
                parts = query.split(' and ')
                
                # For each part after the first, check if it's a complete question
                base_part = parts[0].strip()
                sub_queries.append(base_part)
                
                for part in parts[1:]:
                    part = part.strip()
                    
                    # If part doesn't start with question word, it might be continuation
                    q_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which']
                    if not any(part.lower().startswith(qw) for qw in q_words):
                        # Inherit question type from base
                        base_q_type = self._detect_question_type(doc)
                        if base_q_type != 'statement':
                            part = f"{base_q_type.capitalize()} {part}"
                    
                    sub_queries.append(part)
            else:
                # Can't split further - use original query
                sub_queries = [query]
        
        # Clean up sub-queries
        sub_queries = [q.strip() for q in sub_queries if q.strip()]
        
        # Ensure each sub-query ends with '?' if it's a question
        sub_queries = [
            q if q.endswith('?') else f"{q}?"
            for q in sub_queries
        ]
        
        self.logger.info(f"Extracted {len(sub_queries)} sub-queries")
        
        return sub_queries
    
    def should_use_multi_hop(self, query_analysis: Dict[str, Any]) -> bool:
        """
        Determine if multi-hop retrieval should be used.
        
        Args:
            query_analysis: Result from analyze_query()
            
        Returns:
            True if multi-hop retrieval is recommended
        """
        return (
            self.enable_multi_hop and
            query_analysis.get('is_multi_hop', False) and
            len(query_analysis.get('sub_queries', [])) > 1
        )
    
    def is_available(self) -> bool:
        """Check if query planner is available."""
        return self.nlp is not None

