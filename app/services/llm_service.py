import logging
from typing import List, Optional
import openai
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Exception raised when LLM service operations fail."""

    pass


class LLMService:
    """Service for generating AI feedback using OpenAI GPT-3.5-turbo."""

    def __init__(self):
        self._client = None
        self.model = "gpt-3.5-turbo"  # Cheaper model for cost optimization

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured")
                raise LLMServiceError("OpenAI API key not configured")
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def generate_feedback(
        self,
        resume_text: str,
        job_description: Optional[str] = None,
        feedback_type: str = "general",
    ) -> List[str]:
        """Generate AI feedback for resume."""
        if not resume_text or not resume_text.strip():
            raise LLMServiceError("Resume text cannot be empty")

        try:
            if feedback_type == "general":
                prompt = self._create_general_feedback_prompt(resume_text)
            elif feedback_type == "job_specific":
                if not job_description:
                    raise LLMServiceError(
                        "Job description required for job-specific feedback"
                    )
                prompt = self._create_job_specific_feedback_prompt(
                    resume_text, job_description
                )
            else:
                raise LLMServiceError(f"Unknown feedback type: {feedback_type}")

            logger.info(f"Generating {feedback_type} feedback for resume")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume reviewer and career coach.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            feedback_text = response.choices[0].message.content.strip()
            # Parse feedback into list format
            feedback_list = self._parse_feedback_response(feedback_text)

            logger.info(f"Successfully generated {len(feedback_list)} feedback items")
            return feedback_list

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise LLMServiceError(f"OpenAI authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            raise LLMServiceError(f"OpenAI rate limit exceeded: {str(e)}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating feedback: {str(e)}")
            raise LLMServiceError(f"Failed to generate feedback: {str(e)}")

    def _create_general_feedback_prompt(self, resume_text: str) -> str:
        """Create prompt for general resume feedback."""
        return f"""
Please analyze the following resume and provide constructive feedback to improve it.
Focus on the following areas:
1. Content completeness and relevance
2. Skills and experience presentation
3. Formatting and structure
4. Action verbs and achievements
5. Overall impact and professionalism

Resume text:
{resume_text[:3000]}  # Limit text length to avoid token limits

Please provide 3-5 specific, actionable feedback points. Format your response as a numbered list.
Each point should be concise but helpful.
"""

    def _create_job_specific_feedback_prompt(
        self, resume_text: str, job_description: str
    ) -> str:
        """Create prompt for job-specific resume feedback."""
        return f"""
Please analyze how well the resume matches the specific job description and provide targeted feedback.
Focus on:
1. Skills alignment with job requirements
2. Experience relevance to the position
3. Missing qualifications or experiences
4. How to better highlight relevant achievements
5. Specific improvements for this role

Job Description:
{job_description[:2000]}

Resume text:
{resume_text[:2000]}

Please provide 3-5 specific, actionable feedback points that address the job requirements.
Format your response as a numbered list. Each point should be concise but helpful.
"""

    def _parse_feedback_response(self, feedback_text: str) -> List[str]:
        """Parse LLM response into structured feedback list."""
        lines = feedback_text.strip().split("\n")
        feedback_list = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove numbering (1., 2., etc.) and bullet points
            if line[0].isdigit() and ". " in line:
                line = line.split(". ", 1)[1]
            elif line.startswith("- ") or line.startswith("• "):
                line = line[2:]
            elif line.startswith("* "):
                line = line[2:]

            if line and len(line) > 10:  # Only include substantial feedback
                feedback_list.append(line)

        return (
            feedback_list
            if feedback_list
            else ["Unable to generate specific feedback at this time."]
        )


# Global instance
llm_service = LLMService()
