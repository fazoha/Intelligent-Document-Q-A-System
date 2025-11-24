"""
Embedding service using OpenAI API.
"""

import time
from typing import List
from openai import OpenAI
from utils import config, app_logger


class OpenAIEmbedder:
    """Generate embeddings using OpenAI's text-embedding-3-large model."""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        # Upstash index configured for 1536 dimensions, so use text-embedding-3-small.
        self.model = "text-embedding-3-small"
        self.logger = app_logger
    
    def embed(self, text: str, retry_count: int = 3) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Text to embed
            retry_count: Number of retries on failure
            
        Returns:
            1536-dimensional embedding vector
            
        Raises:
            Exception: If embedding generation fails after retries
        """
        for attempt in range(retry_count):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                
                embedding = response.data[0].embedding
                
                self.logger.debug(
                    f"Generated embedding (dim={len(embedding)}) for text "
                    f"(length={len(text)} chars)"
                )
                
                return embedding
            
            except Exception as e:
                self.logger.warning(
                    f"Embedding attempt {attempt + 1}/{retry_count} failed: {e}"
                )
                
                if attempt < retry_count - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Failed to generate embedding after {retry_count} attempts")
                    raise Exception(f"Embedding generation failed: {str(e)}")
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                self.logger.info(
                    f"Generated embeddings for batch {i // batch_size + 1} "
                    f"({len(batch)} texts)"
                )
            
            except Exception as e:
                self.logger.error(f"Batch embedding failed for batch starting at {i}: {e}")
                # Fall back to individual embedding for this batch
                for text in batch:
                    embedding = self.embed(text)
                    embeddings.append(embedding)
        
        return embeddings

