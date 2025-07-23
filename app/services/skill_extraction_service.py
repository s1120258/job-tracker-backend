import logging
from typing import Dict, List, Optional, Any
import json
import openai
from app.core.config import settings

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

    def extract_skills_from_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract skills from resume text.

        Args:
            resume_text: The extracted text from user's resume

        Returns:
            Dict containing categorized skills extracted from resume
        """
        if not resume_text or not resume_text.strip():
            raise SkillExtractionServiceError("Resume text cannot be empty")

        try:
            prompt = self._create_resume_skill_extraction_prompt(resume_text)

            logger.info("Extracting skills from resume text")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional skill extraction expert. Extract skills from text and return structured JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            skills_data = json.loads(response.choices[0].message.content)
            logger.info("Successfully extracted skills from resume")
            return skills_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise SkillExtractionServiceError(f"Invalid JSON response from LLM: {str(e)}")
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
            logger.error(f"Unexpected error extracting resume skills: {str(e)}")
            raise SkillExtractionServiceError(f"Failed to extract skills: {str(e)}")

    def extract_skills_from_job(self, job_description: str, job_title: str = "") -> Dict[str, Any]:
        """
        Extract required and preferred skills from job description.

        Args:
            job_description: The job description text
            job_title: Optional job title for context

        Returns:
            Dict containing required and preferred skills from job posting
        """
        if not job_description or not job_description.strip():
            raise SkillExtractionServiceError("Job description cannot be empty")

        try:
            prompt = self._create_job_skill_extraction_prompt(job_description, job_title)

            logger.info("Extracting skills from job description")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional skill extraction expert. Extract skills from job descriptions and return structured JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            skills_data = json.loads(response.choices[0].message.content)
            logger.info("Successfully extracted skills from job description")
            return skills_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise SkillExtractionServiceError(f"Invalid JSON response from LLM: {str(e)}")
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
            logger.error(f"Unexpected error extracting job skills: {str(e)}")
            raise SkillExtractionServiceError(f"Failed to extract skills: {str(e)}")

    def analyze_skill_gap(self, resume_text: str, job_description: str, job_title: str = "") -> Dict[str, Any]:
        """
        Perform comprehensive skill gap analysis between resume and job requirements.

        Args:
            resume_text: The extracted text from user's resume
            job_description: The job description text
            job_title: Optional job title for context

        Returns:
            Dict containing detailed skill gap analysis
        """
        if not resume_text or not resume_text.strip():
            raise SkillExtractionServiceError("Resume text cannot be empty")
        if not job_description or not job_description.strip():
            raise SkillExtractionServiceError("Job description cannot be empty")

        try:
            prompt = self._create_skill_gap_analysis_prompt(resume_text, job_description, job_title)

            logger.info("Performing skill gap analysis")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional career advisor and skill analysis expert. Analyze skill gaps between resumes and job requirements, providing actionable insights."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis_data = json.loads(response.choices[0].message.content)
            logger.info("Successfully completed skill gap analysis")
            return analysis_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise SkillExtractionServiceError(f"Invalid JSON response from LLM: {str(e)}")
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
            logger.error(f"Unexpected error in skill gap analysis: {str(e)}")
            raise SkillExtractionServiceError(f"Failed to analyze skill gap: {str(e)}")

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

    def _create_job_skill_extraction_prompt(self, job_description: str, job_title: str) -> str:
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

    def _create_skill_gap_analysis_prompt(self, resume_text: str, job_description: str, job_title: str) -> str:
        """Create prompt for skill gap analysis."""
        context = f"Job Title: {job_title}\n\n" if job_title else ""

        return f"""
Perform a comprehensive skill gap analysis between this resume and job requirements. Provide actionable insights.

{context}Job Description:
{job_description[:2000]}

Resume:
{resume_text[:2000]}

Return JSON with this exact structure:
{{
    "overall_match_percentage": 75,
    "match_summary": "Strong technical background with some gaps in cloud technologies",
    "strengths": [
        {{"skill": "Python", "reason": "5+ years experience matches senior requirement"}},
        {{"skill": "Problem Solving", "reason": "Demonstrated through complex project implementations"}}
    ],
    "skill_gaps": [
        {{
            "skill": "AWS",
            "required_level": "Intermediate",
            "current_level": "None",
            "priority": "High",
            "impact": "Critical for cloud deployment responsibilities",
            "gap_severity": "Major"
        }},
        {{
            "skill": "Kubernetes",
            "required_level": "Intermediate",
            "current_level": "Beginner",
            "priority": "Medium",
            "impact": "Important for container orchestration",
            "gap_severity": "Minor"
        }}
    ],
    "learning_recommendations": [
        {{
            "skill": "AWS",
            "priority": "High",
            "estimated_learning_time": "3-6 months",
            "suggested_approach": "Start with AWS Certified Cloud Practitioner, practice with hands-on projects",
            "resources": ["AWS Training", "Cloud Academy", "A Cloud Guru"],
            "immediate_actions": ["Sign up for AWS free tier", "Complete AWS fundamentals course"]
        }}
    ],
    "experience_gap": {{
        "required_years": 5,
        "candidate_years": 3,
        "gap": 2,
        "assessment": "Candidate has strong foundation but needs more senior-level experience"
    }},
    "education_match": {{
        "required": "Bachelor's in Computer Science",
        "candidate": "Bachelor's in Computer Science",
        "matches": true,
        "assessment": "Education requirements fully met"
    }},
    "recommended_next_steps": [
        "Focus on AWS certification and hands-on cloud projects",
        "Gain experience with Kubernetes through personal projects",
        "Highlight problem-solving skills more prominently in applications"
    ],
    "application_advice": "Strong candidate with core skills. Address cloud technology gaps through learning plan. Emphasize Python expertise and project experience."
}}

Instructions:
- Calculate realistic match percentage based on critical vs. nice-to-have skills
- Identify both technical and soft skill gaps
- Prioritize gaps by business impact (High, Medium, Low)
- Classify gap severity (Major, Minor, None)
- Provide specific, actionable learning recommendations
- Suggest realistic timelines for skill development
- Give practical application advice
"""


# Global instance
skill_extraction_service = SkillExtractionService()