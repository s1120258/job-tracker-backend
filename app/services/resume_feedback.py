# app/services/resume_feedback.py

from typing import List, Tuple
from uuid import UUID
import logging
from app.services.llm_service import llm_service, LLMServiceError
from app.crud.application import get_application

logger = logging.getLogger(__name__)


def get_general_feedback(extracted_text: str) -> List[str]:
    """
    Return general AI feedback for the given resume text.
    """
    if not extracted_text or len(extracted_text.strip()) == 0:
        return ["Resume text is empty. Please upload a valid resume."]

    try:
        feedback = llm_service.generate_feedback(
            resume_text=extracted_text, feedback_type="general"
        )
        return feedback
    except LLMServiceError as e:
        logger.error(f"Failed to generate general feedback: {str(e)}")
        return [
            "Unable to generate AI feedback at this time. Please try again later.",
            "Consider reviewing your resume for clarity and completeness.",
        ]
    except Exception as e:
        logger.error(f"Unexpected error in general feedback: {str(e)}")
        return ["An error occurred while generating feedback. Please try again."]


def get_job_specific_feedback(
    extracted_text: str, application_id: UUID
) -> Tuple[List[str], str]:
    """
    Return job-specific AI feedback for the given resume text and job (application_id).
    """
    if not extracted_text or len(extracted_text.strip()) == 0:
        return (
            ["Resume text is empty. Please upload a valid resume."],
            "No job description available.",
        )

    try:
        # Get job description from database
        from app.db.session import get_db

        db = next(get_db())
        application = get_application(db, application_id)

        if not application:
            return (
                ["Application not found. Please check the application ID."],
                "No job description available.",
            )

        job_description = application.job_description_text
        job_excerpt = f"{application.company_name} - {application.position_title}"

        feedback = llm_service.generate_feedback(
            resume_text=extracted_text,
            job_description=job_description,
            feedback_type="job_specific",
        )

        return feedback, job_excerpt

    except LLMServiceError as e:
        logger.error(f"Failed to generate job-specific feedback: {str(e)}")
        return (
            [
                "Unable to generate job-specific feedback at this time. Please try again later.",
                "Consider reviewing how your skills align with the job requirements.",
            ],
            "Error retrieving job description.",
        )
    except Exception as e:
        logger.error(f"Unexpected error in job-specific feedback: {str(e)}")
        return (
            ["An error occurred while generating feedback. Please try again."],
            "Error retrieving job description.",
        )
