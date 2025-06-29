import logging
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.application import Application
from app.models.resume import Resume
from app.models.match_score import MatchScore
from app.crud.application import get_application
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

    def calculate_and_store_match_score(
        self, db: Session, application_id: UUID, user_id: UUID
    ) -> MatchScore:
        """
        Calculate similarity score between user's resume and a job application,
        then store the result in the database.

        Args:
            db: Database session
            application_id: ID of the job application
            user_id: ID of the user

        Returns:
            MatchScore: The created or updated match score record
        """
        try:
            # Get the application and resume
            application = get_application(db, application_id)
            if not application:
                raise SimilarityServiceError(f"Application {application_id} not found")

            if application.user_id != user_id:
                raise SimilarityServiceError("Application does not belong to user")

            resume = get_resume_by_user(db, user_id)
            if not resume:
                raise SimilarityServiceError("User has no resume uploaded")

            # Check if embeddings exist
            if not resume.embedding:
                raise SimilarityServiceError("Resume embedding not available")

            if not application.job_embedding:
                raise SimilarityServiceError("Job description embedding not available")

            # Calculate similarity score
            similarity_score = self.calculate_similarity_score(
                resume.embedding, application.job_embedding
            )

            logger.info(
                f"Calculated similarity score: {similarity_score:.3f} for application {application_id}"
            )

            # Store or update the match score
            return self._store_match_score(
                db, application_id, resume.id, similarity_score
            )

        except Exception as e:
            logger.error(f"Error in calculate_and_store_match_score: {str(e)}")
            raise SimilarityServiceError(
                f"Failed to calculate and store match score: {str(e)}"
            )

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

    def get_match_score(
        self, db: Session, application_id: UUID, user_id: UUID
    ) -> Optional[MatchScore]:
        """
        Get existing match score for an application.

        Args:
            db: Database session
            application_id: ID of the job application
            user_id: ID of the user

        Returns:
            Optional[MatchScore]: The match score record if it exists
        """
        try:
            # Verify the application belongs to the user
            application = get_application(db, application_id)
            if not application or application.user_id != user_id:
                return None

            # Get the match score
            match_score = (
                db.query(MatchScore)
                .filter(MatchScore.application_id == application_id)
                .first()
            )

            return match_score

        except Exception as e:
            logger.error(f"Error getting match score: {str(e)}")
            return None

    def get_average_match_score(self, db: Session, user_id: UUID) -> Optional[float]:
        """
        Calculate average match score across all user's applications.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            Optional[float]: Average similarity score or None if no scores exist
        """
        try:
            result = (
                db.query(func.avg(MatchScore.similarity_score))
                .join(Application, MatchScore.application_id == Application.id)
                .filter(Application.user_id == user_id)
                .scalar()
            )

            return float(result) if result is not None else None

        except Exception as e:
            logger.error(f"Error calculating average match score: {str(e)}")
            return None

    def get_match_score_distribution(self, db: Session, user_id: UUID) -> dict:
        """
        Get distribution of match scores for analytics.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            dict: Distribution of match scores by ranges
        """
        try:
            # Get all match scores for the user
            scores = (
                db.query(MatchScore.similarity_score)
                .join(Application, MatchScore.application_id == Application.id)
                .filter(Application.user_id == user_id)
                .all()
            )

            if not scores:
                return {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "total": 0}

            # Categorize scores
            distribution = {
                "excellent": 0,  # 0.8-1.0
                "good": 0,  # 0.6-0.79
                "fair": 0,  # 0.4-0.59
                "poor": 0,  # 0.0-0.39
                "total": len(scores),
            }

            for (score,) in scores:
                if score >= 0.8:
                    distribution["excellent"] += 1
                elif score >= 0.6:
                    distribution["good"] += 1
                elif score >= 0.4:
                    distribution["fair"] += 1
                else:
                    distribution["poor"] += 1

            return distribution

        except Exception as e:
            logger.error(f"Error getting match score distribution: {str(e)}")
            return {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "total": 0}


# Global instance
similarity_service = SimilarityService()
