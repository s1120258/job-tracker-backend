import logging
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.resume import Resume
from app.models.match_score import MatchScore

from app.crud.resume import get_resume_by_user
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class SimilarityServiceError(Exception):
    """Exception raised when similarity calculation operations fail."""

    pass


class SimilarityService:
    """Service for calculating similarity scores between resumes and job descriptions."""

    def calculate_similarity_score(
        self, resume_embedding: list[float], job_embedding: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            resume_embedding: Resume vector embedding
            job_embedding: Job description vector embedding

        Returns:
            float: Similarity score between 0 and 1
        """
        # Handle NumPy arrays properly
        if resume_embedding is None or (
            hasattr(resume_embedding, "size") and resume_embedding.size == 0
        ):
            raise SimilarityServiceError("Resume embedding must be provided")

        if job_embedding is None or (
            hasattr(job_embedding, "size") and job_embedding.size == 0
        ):
            raise SimilarityServiceError("Job embedding must be provided")

        # Convert to list if they are NumPy arrays
        if hasattr(resume_embedding, "tolist"):
            resume_embedding = resume_embedding.tolist()
        if hasattr(job_embedding, "tolist"):
            job_embedding = job_embedding.tolist()

        if len(resume_embedding) != len(job_embedding):
            raise SimilarityServiceError("Embeddings must have the same dimensions")

        try:
            # Calculate cosine similarity using dot product and magnitudes
            dot_product = sum(a * b for a, b in zip(resume_embedding, job_embedding))

            resume_magnitude = sum(a * a for a in resume_embedding) ** 0.5
            job_magnitude = sum(b * b for b in job_embedding) ** 0.5

            if resume_magnitude == 0 or job_magnitude == 0:
                return 0.0

            similarity = dot_product / (resume_magnitude * job_magnitude)

            # Ensure the result is between 0 and 1
            final_similarity = max(0.0, min(1.0, similarity))

            return final_similarity

        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}", exc_info=True)
            raise SimilarityServiceError(f"Failed to calculate similarity: {str(e)}")



    def _store_match_score(
        self,
        db: Session,
        application_id: UUID,
        resume_id: UUID,
        similarity_score: float,
    ) -> MatchScore:
        """
        Store or update match score in the database.

        Args:
            db: Database session
            application_id: ID of the job application
            resume_id: ID of the resume
            similarity_score: Calculated similarity score

        Returns:
            MatchScore: The created or updated match score record
        """
        try:
            # Check if match score already exists
            existing_match = (
                db.query(MatchScore)
                .filter(MatchScore.application_id == application_id)
                .first()
            )

            if existing_match:
                # Update existing record
                existing_match.similarity_score = similarity_score
                existing_match.resume_id = resume_id
                db.commit()
                db.refresh(existing_match)
                logger.info(f"Updated match score for application {application_id}")
                return existing_match
            else:
                # Create new record
                match_score = MatchScore(
                    application_id=application_id,
                    resume_id=resume_id,
                    similarity_score=similarity_score,
                )
                db.add(match_score)
                db.commit()
                db.refresh(match_score)
                logger.info(f"Created new match score for application {application_id}")
                return match_score

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing match score: {str(e)}")
            raise SimilarityServiceError(f"Failed to store match score: {str(e)}")






# Global instance
similarity_service = SimilarityService()
