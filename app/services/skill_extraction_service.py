import logging
from typing import Dict, List, Optional, Any
import json
import openai
from app.core.config import settings
from app.services.llm_service import llm_service, LLMServiceError

logger = logging.getLogger(__name__)


class SkillExtractionServiceError(Exception):
    """Exception raised when skill extraction operations fail."""

    pass


class SkillExtractionService:
    """Service for extracting skills from resume and job description texts using LLM."""

    def __init__(self):
        self._client = None
        self.model = "gpt-3.5-turbo"

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured")
                raise SkillExtractionServiceError("OpenAI API key not configured")
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def extract_skills_from_resume(
        self, resume_text: str, normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Extract skills from resume text with optional normalization.

        Args:
            resume_text: The extracted text from user's resume
            normalize: Whether to apply LLM-based skill normalization

        Returns:
            Dict containing categorized skills extracted from resume
        """
        return self._extract_skills_common(
            text=resume_text,
            context="resume",
            prompt_generator=self._create_resume_skill_extraction_prompt,
            system_content="You are a professional skill extraction expert. Extract skills from text and return structured JSON.",
            normalize=normalize,
        )

    def extract_skills_from_job(
        self, job_description: str, job_title: str = "", normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Extract required and preferred skills from job description with normalization.

        Args:
            job_description: The job description text
            job_title: Optional job title for context
            normalize: Whether to apply LLM-based skill normalization

        Returns:
            Dict containing required and preferred skills from job posting
        """

        def job_prompt_generator(text):
            return self._create_job_skill_extraction_prompt(text, job_title)

        context = f"job {job_title}" if job_title else "job"

        return self._extract_skills_common(
            text=job_description,
            context=context,
            prompt_generator=job_prompt_generator,
            system_content="You are a job requirements analysis expert. Extract required and preferred skills from job descriptions.",
            normalize=normalize,
        )

    def _extract_skills_common(
        self,
        text: str,
        context: str,
        prompt_generator: callable,
        system_content: str,
        normalize: bool = True,
    ) -> Dict[str, Any]:
        """
        Common skill extraction logic for both resume and job descriptions.

        Args:
            text: The text to extract skills from
            context: Context description for logging and error messages
            prompt_generator: Function to generate the appropriate prompt
            system_content: System message content for the LLM
            normalize: Whether to apply LLM-based skill normalization

        Returns:
            Dict containing categorized skills extracted from text
        """
        if not text or not text.strip():
            raise SkillExtractionServiceError(
                f"{context.capitalize()} text cannot be empty"
            )

        try:
            prompt = prompt_generator(text)

            logger.info(f"Extracting skills from {context}")
            response = self._make_llm_request(
                prompt=prompt,
                system_content=system_content,
                max_tokens=1000,
            )

            skills_data = self._parse_json_response(
                response, f"{context} skill extraction"
            )

            # Apply normalization if requested
            if normalize and (
                skills_data.get("technical_skills")
                or skills_data.get("required_skills")
            ):
                skills_data = self._apply_skill_normalization(skills_data, context)

            logger.info(f"Successfully extracted skills from {context}")
            return skills_data

        except SkillExtractionServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting {context} skills: {str(e)}")
            raise SkillExtractionServiceError(f"Failed to extract skills: {str(e)}")

    def _make_llm_request(
        self, prompt: str, system_content: str, max_tokens: int = 1000
    ) -> str:
        """
        Make LLM request with comprehensive error handling.

        Args:
            prompt: The user prompt
            system_content: System message content
            max_tokens: Maximum tokens for response

        Returns:
            Response content string

        Raises:
            SkillExtractionServiceError: For various API failures
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            return response.choices[0].message.content.strip()

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise SkillExtractionServiceError(f"OpenAI authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            raise SkillExtractionServiceError(f"OpenAI rate limit exceeded: {str(e)}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise SkillExtractionServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in LLM request: {str(e)}")
            raise SkillExtractionServiceError(f"LLM request failed: {str(e)}")

    def _parse_json_response(
        self, response_content: str, operation: str
    ) -> Dict[str, Any]:
        """
        Parse JSON response with error handling and fallbacks.

        Args:
            response_content: The LLM response content
            operation: Description of the operation for error messages

        Returns:
            Parsed JSON data

        Raises:
            SkillExtractionServiceError: If JSON parsing fails critically
        """
        if not response_content:
            raise SkillExtractionServiceError(
                f"Empty response from LLM for {operation}"
            )

        try:
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse LLM response as JSON for {operation}: {str(e)}"
            )
            logger.debug(f"Response content: {response_content}")

            # Try to extract partial JSON or provide meaningful fallback
            try:
                # Attempt to find JSON-like content
                start_idx = response_content.find("{")
                end_idx = response_content.rfind("}")

                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    partial_json = response_content[start_idx : end_idx + 1]
                    return json.loads(partial_json)

            except json.JSONDecodeError:
                pass

            # Return structured fallback based on operation type
            if "resume" in operation:
                return {
                    "technical_skills": [],
                    "soft_skills": [],
                    "experience_level": "Unknown",
                    "domains": [],
                }
            elif "job" in operation:
                return {
                    "required_skills": [],
                    "preferred_skills": [],
                    "experience_required": "Not specified",
                }
            else:
                return {"error": f"Failed to parse response for {operation}"}

    def _apply_skill_normalization(
        self, skills_data: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """
        Apply skill normalization to extracted skills data.

        Args:
            skills_data: Original skills data
            context: Context for normalization

        Returns:
            Skills data with normalized skill names
        """
        try:
            # Extract skill names from various fields
            all_skills = []

            # From technical skills
            if "technical_skills" in skills_data:
                for skill in skills_data["technical_skills"]:
                    if isinstance(skill, dict):
                        all_skills.append(skill.get("name", ""))
                    else:
                        all_skills.append(str(skill))

            # From other skill lists
            for field in [
                "programming_languages",
                "frameworks",
                "tools",
                "cloud_platforms",
                "databases",
            ]:
                if field in skills_data:
                    all_skills.extend([str(s) for s in skills_data[field]])

            # From required/preferred skills (for job data)
            for field in ["required_skills", "preferred_skills"]:
                if field in skills_data:
                    for skill in skills_data[field]:
                        if isinstance(skill, dict):
                            all_skills.append(skill.get("name", ""))
                        else:
                            all_skills.append(str(skill))

            if all_skills:
                normalized = self._normalize_skill_list(all_skills, context)
                skills_data["normalized_skills"] = normalized.get(
                    "normalized_skills", []
                )
                skills_data["skill_groupings"] = normalized.get(
                    "suggested_groupings", []
                )

            return skills_data

        except Exception as e:
            logger.warning(
                f"Skill normalization failed, returning original data: {str(e)}"
            )
            return skills_data

    def _normalize_skill_list(
        self, skills: List[str], context: str = ""
    ) -> Dict[str, Any]:
        """
        Normalize a list of skills using LLM intelligence.

        Args:
            skills: List of skill names to normalize
            context: Optional context for better normalization

        Returns:
            Dict containing normalized skills with metadata
        """
        if not skills:
            return {"normalized_skills": []}

        try:
            return llm_service.normalize_skills(skills, context)
        except LLMServiceError as e:
            logger.error(f"Skill normalization failed: {str(e)}")
            # Return original skills as fallback
            return {
                "normalized_skills": [
                    {"original": skill, "canonical": skill, "confidence": 0.5}
                    for skill in skills
                ]
            }

    def _create_resume_skill_extraction_prompt(self, resume_text: str) -> str:
        """Create prompt for extracting skills from resume."""
        return f"""
Extract skills from this resume text and categorize them. Be comprehensive but accurate.

Resume text:
{resume_text[:3000]}

Return JSON with this exact structure:
{{
    "technical_skills": [
        {{"name": "Python", "level": "Advanced", "years_experience": 5, "evidence": "5 years as Python developer"}},
        {{"name": "Docker", "level": "Intermediate", "years_experience": 2, "evidence": "Used Docker for containerization"}}
    ],
    "soft_skills": ["Communication", "Leadership", "Problem Solving", "Teamwork"],
    "certifications": ["AWS Certified Solutions Architect", "PMP"],
    "programming_languages": ["Python", "JavaScript", "Java"],
    "frameworks": ["FastAPI", "React", "Django", "Spring"],
    "tools": ["Git", "Docker", "Jenkins", "Kubernetes"],
    "domains": ["Machine Learning", "Web Development", "DevOps", "Data Science"],
    "education": ["Bachelor's in Computer Science", "Master's in Data Science"],
    "total_experience_years": 5
}}

Instructions:
- Extract only skills explicitly mentioned or clearly implied
- Estimate experience level based on context (Entry: 0-2 years, Intermediate: 2-5 years, Advanced: 5+ years)
- Provide evidence from the resume text for technical skills
- Be conservative with experience estimates
"""

    def _create_job_skill_extraction_prompt(
        self, job_description: str, job_title: str
    ) -> str:
        """Create prompt for extracting skills from job description."""
        context = f"Job Title: {job_title}\n\n" if job_title else ""

        return f"""
Extract required and preferred skills from this job posting. Distinguish between must-have and nice-to-have skills.

{context}Job Description:
{job_description[:3000]}

Return JSON with this exact structure:
{{
    "required_skills": [
        {{"name": "Python", "level": "Senior", "category": "programming_language", "importance": "critical"}},
        {{"name": "AWS", "level": "Intermediate", "category": "cloud_platform", "importance": "high"}}
    ],
    "preferred_skills": [
        {{"name": "Machine Learning", "level": "Any", "category": "domain", "importance": "medium"}},
        {{"name": "Leadership", "level": "Any", "category": "soft_skill", "importance": "low"}}
    ],
    "programming_languages": ["Python", "JavaScript"],
    "frameworks": ["FastAPI", "React"],
    "tools": ["Docker", "Kubernetes", "Git"],
    "cloud_platforms": ["AWS", "Azure"],
    "databases": ["PostgreSQL", "MongoDB"],
    "soft_skills": ["Communication", "Leadership", "Problem Solving"],
    "certifications": ["AWS Certified", "Kubernetes Certified"],
    "experience_required": "3-5 years",
    "education_required": "Bachelor's degree in Computer Science or related field",
    "seniority_level": "Mid-level"
}}

Instructions:
- Classify skills by category (programming_language, framework, tool, cloud_platform, database, soft_skill, domain, certification)
- Determine skill level requirements (Entry, Intermediate, Senior, Any)
- Set importance level (critical, high, medium, low)
- Extract both explicit requirements and implied skills
- Be precise about experience and education requirements
"""


# Global instance
skill_extraction_service = SkillExtractionService()
