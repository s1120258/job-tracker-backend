# app/services/resume_feedback.py

from typing import List, Tuple
from uuid import UUID


def get_general_feedback(extracted_text: str) -> List[str]:
    """
    Return general AI feedback for the given resume text.
    In production, replace this with an actual LLM API call.
    """
    # --- Dummy implementation ---
    if not extracted_text or len(extracted_text.strip()) == 0:
        return ["Resume text is empty. Please upload a valid resume."]
    # Replace this with an LLM API call, etc.
    return [
        "Add more details to your experience section.",
        "Include relevant programming languages.",
    ]


def get_job_specific_feedback(
    extracted_text: str, application_id: UUID
) -> Tuple[List[str], str]:
    """
    Return job-specific AI feedback for the given resume text and job (application_id).
    In production, fetch job description from DB and call LLM API.
    """
    # --- Dummy implementation ---
    # Normally, fetch job_description from DB using application_id
    job_description_excerpt = "We are looking for a software engineer with experience in AWS and team projects."
    if not extracted_text or len(extracted_text.strip()) == 0:
        return (
            ["Resume text is empty. Please upload a valid resume."],
            job_description_excerpt,
        )
    # Replace this with an LLM API call, etc.
    return (
        [
            "Emphasize experience with cloud technologies, as required by the job description.",
            "Highlight teamwork and communication skills.",
        ],
        job_description_excerpt,
    )
