# app/services/embedding_service.py

import logging
from typing import List, Optional
import openai
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Exception raised when embedding service operations fail."""

    pass


class EmbeddingService:
    """Service for generating and managing vector embeddings."""

    def __init__(self):
        self._client = None
        self.model = "text-embedding-ada-002"  # OpenAI's embedding model

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured")
                raise EmbeddingServiceError("OpenAI API key not configured")
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using OpenAI API."""
        if not text or not text.strip():
            raise EmbeddingServiceError("Text cannot be empty")

        try:
            logger.info(f"Generating embedding for text of length {len(text)}")
            response = self.client.embeddings.create(model=self.model, input=text)
            embedding = response.data[0].embedding
            logger.info(
                f"Successfully generated embedding of dimension {len(embedding)}"
            )
            return embedding
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise EmbeddingServiceError(f"OpenAI authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            raise EmbeddingServiceError(f"OpenAI rate limit exceeded: {str(e)}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise EmbeddingServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {str(e)}")


# Global instance
embedding_service = EmbeddingService()
