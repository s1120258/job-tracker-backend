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

    def analyze_skill_gap(
        self,
        resume_text: str,
        job_description: str,
        job_title: str = "",
        normalize: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive skill gap analysis between resume and job requirements.

        Args:
            resume_text: The extracted text from user's resume
            job_description: The job description text
            job_title: Optional job title for context
            normalize: Whether to apply LLM-based skill normalization

        Returns:
            Dict containing comprehensive skill gap analysis
        """
        if not resume_text or not resume_text.strip():
            raise SkillExtractionServiceError("Resume text cannot be empty")

        if not job_description or not job_description.strip():
            raise SkillExtractionServiceError("Job description cannot be empty")

        try:
            # First try enhanced analysis using structured skill data
            try:
                # Extract structured skills data with levels and experience
                resume_skills_data = self.extract_skills_from_resume(
                    resume_text, normalize=normalize
                )
                job_skills_data = self.extract_skills_from_job(
                    job_description, job_title, normalize=normalize
                )

                # Perform intelligent skill matching using structured data
                converted_analysis = self._perform_intelligent_skill_matching(
                    resume_skills_data, job_skills_data, job_title
                )

                logger.info("Successfully completed intelligent skill gap analysis")
                return converted_analysis

            except LLMServiceError as e:
                logger.warning(
                    f"Enhanced analysis failed, falling back to basic analysis: {str(e)}"
                )
                # Fallback to basic analysis
                return self._basic_skill_gap_analysis(
                    resume_text, job_description, job_title, normalize
                )

        except SkillExtractionServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in skill gap analysis: {str(e)}")
            raise SkillExtractionServiceError(f"Failed to analyze skill gap: {str(e)}")

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

    def _apply_skill_normalization_to_analysis(
        self, analysis_data: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """
        Apply skill normalization to skill gap analysis results.

        Args:
            analysis_data: Skill gap analysis results
            context: Context for normalization

        Returns:
            Analysis data with normalized skill names
        """
        try:
            # Extract all skill names from the analysis
            all_skills = []

            # From strengths
            if "strengths" in analysis_data:
                for strength in analysis_data["strengths"]:
                    if isinstance(strength, dict) and "skill" in strength:
                        all_skills.append(strength["skill"])

            # From skill gaps
            if "skill_gaps" in analysis_data:
                for gap in analysis_data["skill_gaps"]:
                    if isinstance(gap, dict) and "skill" in gap:
                        all_skills.append(gap["skill"])

            # From learning recommendations
            if "learning_recommendations" in analysis_data:
                for rec in analysis_data["learning_recommendations"]:
                    if isinstance(rec, dict) and "skill" in rec:
                        all_skills.append(rec["skill"])

            if all_skills:
                # Normalize the skills
                normalized = self._normalize_skill_list(all_skills, context)
                normalized_skills = normalized.get("normalized_skills", [])

                # Create a mapping from original to canonical names
                skill_mapping = {}
                for norm_skill in normalized_skills:
                    if isinstance(norm_skill, dict):
                        original = norm_skill.get("original", "")
                        canonical = norm_skill.get("canonical", original)
                        if original:
                            skill_mapping[original] = canonical

                # Apply the mapping to the analysis data
                if "strengths" in analysis_data:
                    for strength in analysis_data["strengths"]:
                        if isinstance(strength, dict) and "skill" in strength:
                            original_skill = strength["skill"]
                            strength["skill"] = skill_mapping.get(
                                original_skill, original_skill
                            )

                if "skill_gaps" in analysis_data:
                    for gap in analysis_data["skill_gaps"]:
                        if isinstance(gap, dict) and "skill" in gap:
                            original_skill = gap["skill"]
                            gap["skill"] = skill_mapping.get(
                                original_skill, original_skill
                            )

                if "learning_recommendations" in analysis_data:
                    for rec in analysis_data["learning_recommendations"]:
                        if isinstance(rec, dict) and "skill" in rec:
                            original_skill = rec["skill"]
                            rec["skill"] = skill_mapping.get(
                                original_skill, original_skill
                            )

                # Add normalization metadata
                analysis_data["skill_normalization_applied"] = True
                analysis_data["normalized_skill_mappings"] = skill_mapping

            return analysis_data

        except Exception as e:
            logger.warning(
                f"Skill normalization in analysis failed, returning original data: {str(e)}"
            )
            return analysis_data

    def _perform_intelligent_skill_matching(
        self,
        resume_skills_data: Dict[str, Any],
        job_skills_data: Dict[str, Any],
        job_title: str,
    ) -> Dict[str, Any]:
        """
        Perform intelligent skill matching using structured skill data.

        Args:
            resume_skills_data: Structured resume skills with levels and experience
            job_skills_data: Structured job requirements with levels and priorities
            job_title: Job title for context

        Returns:
            Dict in standard SkillGapAnalysisResponse format
        """
        try:
            # Create skill maps from the input data
            resume_skill_map = self._create_resume_skill_map(resume_skills_data)
            job_requirement_map = self._create_job_requirement_map(job_skills_data)

            # Perform core skill matching analysis
            analysis_results = self._analyze_skill_matches(
                resume_skill_map, job_requirement_map, job_title
            )

            # Generate learning recommendations from gaps
            learning_recommendations = self._generate_learning_recommendations(
                analysis_results["skill_gaps"]
            )

            # Generate application advice and next steps
            advice_data = self._generate_application_advice(
                analysis_results["overall_match_percentage"],
                analysis_results["skill_gaps"],
                job_title,
            )

            # Assemble final result
            return self._assemble_analysis_result(
                analysis_results, learning_recommendations, advice_data
            )

        except Exception as e:
            logger.error(f"Error in intelligent skill matching: {str(e)}")
            # Fallback to basic analysis
            return {
                "overall_match_percentage": 50.0,
                "match_summary": "Analysis completed with limitations due to processing error",
                "strengths": [],
                "skill_gaps": [],
                "learning_recommendations": [],
                "recommended_next_steps": [
                    "Review job requirements manually and identify skills to develop"
                ],
                "application_advice": "Consider your experience and skills against the job requirements",
            }

    def _create_resume_skill_map(
        self, resume_skills_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create a comprehensive map of resume skills with levels and experience.

        Args:
            resume_skills_data: Raw resume skills data

        Returns:
            Dict mapping skill names to skill details (level, years, evidence)
        """
        resume_skill_map = {}

        # Extract resume skills with levels
        resume_technical_skills = resume_skills_data.get("technical_skills", [])

        # Add technical skills with levels
        for skill in resume_technical_skills:
            if isinstance(skill, dict):
                name = skill.get("name", "").lower()
                level = skill.get("level", "Entry")
                years = skill.get("years_experience", 0)
                resume_skill_map[name] = {
                    "level": level,
                    "years_experience": years,
                    "evidence": skill.get("evidence", ""),
                }

        # Add other skill categories as lists
        skill_categories = ["programming_languages", "frameworks", "tools", "domains"]

        for category in skill_categories:
            skills_list = resume_skills_data.get(category, [])
            for skill in skills_list:
                skill_name = str(skill).lower()
                if skill_name not in resume_skill_map:
                    resume_skill_map[skill_name] = {
                        "level": "Intermediate",  # Default level for non-detailed skills
                        "years_experience": 1,
                        "evidence": f"Listed in resume",
                    }

        return resume_skill_map

    def _create_job_requirement_map(
        self, job_skills_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create a comprehensive map of job requirements with importance and levels.

        Args:
            job_skills_data: Raw job skills data

        Returns:
            Dict mapping skill names to requirement details (level, importance, required)
        """
        job_requirement_map = {}

        # Add required skills with importance
        required_skills = job_skills_data.get("required_skills", [])
        for skill in required_skills:
            if isinstance(skill, dict):
                name = skill.get("name", "").lower()
                level = skill.get("level", "Intermediate")
                importance = skill.get("importance", "medium")
                job_requirement_map[name] = {
                    "level": level,
                    "importance": importance,
                    "required": True,
                }

        # Add preferred skills
        preferred_skills = job_skills_data.get("preferred_skills", [])
        for skill in preferred_skills:
            if isinstance(skill, dict):
                name = skill.get("name", "").lower()
                level = skill.get("level", "Intermediate")
                importance = skill.get("importance", "low")
                if name not in job_requirement_map:
                    job_requirement_map[name] = {
                        "level": level,
                        "importance": importance,
                        "required": False,
                    }

        # Add other job skill categories
        skill_categories = [
            "programming_languages",
            "frameworks",
            "tools",
            "cloud_platforms",
            "databases",
        ]

        for category in skill_categories:
            skills_list = job_skills_data.get(category, [])
            for skill in skills_list:
                skill_name = str(skill).lower()
                # Skip if already exists (avoid duplicates)
                if skill_name not in job_requirement_map:
                    # Extract base skill for compound skills (e.g., "aws sagemaker" -> "aws")
                    base_skill = self._extract_base_skill(skill_name)

                    job_requirement_map[skill_name] = {
                        "level": "Intermediate",
                        "importance": "medium",
                        "required": True,
                    }

                    # Also add base skill if different (for matching purposes)
                    if (
                        base_skill != skill_name
                        and base_skill not in job_requirement_map
                    ):
                        job_requirement_map[base_skill] = {
                            "level": "Intermediate",
                            "importance": "medium",
                            "required": True,
                        }

        return job_requirement_map

    def _analyze_skill_matches(
        self,
        resume_skill_map: Dict[str, Dict[str, Any]],
        job_requirement_map: Dict[str, Dict[str, Any]],
        job_title: str,
    ) -> Dict[str, Any]:
        """
        Perform core skill matching analysis between resume and job requirements.

        Args:
            resume_skill_map: Map of resume skills
            job_requirement_map: Map of job requirements
            job_title: Job title for context

        Returns:
            Dict with strengths, skill_gaps, matched_skills, and overall_match_percentage
        """
        strengths = []
        skill_gaps = []
        matched_skills = 0
        total_required_skills = sum(
            1 for req in job_requirement_map.values() if req["required"]
        )

        for job_skill, job_req in job_requirement_map.items():
            # Use improved matching to find resume skill
            matching_resume_skill_key = self._find_matching_resume_skill(
                job_skill, resume_skill_map
            )
            resume_skill = (
                resume_skill_map.get(matching_resume_skill_key)
                if matching_resume_skill_key
                else None
            )

            if resume_skill:
                # Skill is present in resume
                resume_level = resume_skill["level"]
                required_level = job_req["level"]
                years_exp = resume_skill["years_experience"]

                # Check if skill level meets requirements
                if self._compare_skill_levels(resume_level, required_level):
                    # Skill meets requirements - add to strengths
                    strengths.append(
                        {
                            "skill": job_skill.title(),
                            "reason": f"{resume_level} level with {years_exp} years experience meets {required_level} requirement",
                        }
                    )
                    if job_req["required"]:
                        matched_skills += 1
                else:
                    # Skill present but insufficient level
                    priority = self._map_importance_to_priority(job_req["importance"])
                    skill_gaps.append(
                        {
                            "skill": job_skill.title(),
                            "required_level": required_level,
                            "current_level": resume_level,
                            "priority": priority,
                            "impact": f"Current {resume_level} level needs improvement to {required_level} for {job_title}",
                            "gap_severity": "Minor",  # Has skill but needs improvement
                        }
                    )

            else:
                # Skill is completely missing
                if job_req["required"]:
                    priority = self._map_importance_to_priority(job_req["importance"])
                    skill_gaps.append(
                        {
                            "skill": job_skill.title(),
                            "required_level": job_req["level"],
                            "current_level": "None",
                            "priority": priority,
                            "impact": f"Required skill for {job_title} position",
                            "gap_severity": "Major",
                        }
                    )

        # Calculate match percentage
        overall_match_percentage = (
            matched_skills / max(total_required_skills, 1)
        ) * 100

        # Generate match summary
        match_summary = f"Matched {matched_skills} of {total_required_skills} required skills. Overall compatibility: {overall_match_percentage:.1f}%"

        return {
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "matched_skills": matched_skills,
            "total_required_skills": total_required_skills,
            "overall_match_percentage": overall_match_percentage,
            "match_summary": match_summary,
        }

    def _generate_learning_recommendations(
        self, skill_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate learning recommendations from skill gaps.

        Args:
            skill_gaps: List of skill gaps with details

        Returns:
            List of learning recommendations
        """
        learning_recommendations = []

        for gap in skill_gaps:
            skill_name = gap["skill"]
            priority = gap["priority"]
            gap_severity = gap["gap_severity"]

            # Estimate learning time based on gap severity and skill type
            if gap_severity == "Major":
                estimated_time = (
                    "6-12 weeks"
                    if any(
                        term in skill_name.lower()
                        for term in ["aws", "cloud", "ai", "machine learning"]
                    )
                    else "4-8 weeks"
                )
            else:
                estimated_time = "2-4 weeks"

            learning_recommendations.append(
                {
                    "skill": skill_name,
                    "priority": priority,
                    "estimated_learning_time": estimated_time,
                    "suggested_approach": f"Focus on {skill_name} fundamentals and practical application",
                    "resources": [
                        "Online courses",
                        "Official documentation",
                        "Hands-on projects",
                    ],
                    "immediate_actions": [
                        f"Start with {skill_name} basics and practice"
                    ],
                }
            )

        return learning_recommendations

    def _generate_application_advice(
        self,
        overall_match_percentage: float,
        skill_gaps: List[Dict[str, Any]],
        job_title: str,
    ) -> Dict[str, Any]:
        """
        Generate application advice and recommended next steps.

        Args:
            overall_match_percentage: Overall skill match percentage
            skill_gaps: List of skill gaps
            job_title: Job title for context

        Returns:
            Dict with recommended_next_steps and application_advice
        """
        # Generate recommendations and advice
        recommended_next_steps = []
        high_priority_gaps = [
            gap["skill"] for gap in skill_gaps if gap["priority"] == "High"
        ]
        if high_priority_gaps:
            recommended_next_steps.append(
                f"Priority learning: {', '.join(high_priority_gaps)}"
            )

        medium_priority_gaps = [
            gap["skill"] for gap in skill_gaps if gap["priority"] == "Medium"
        ]
        if medium_priority_gaps:
            recommended_next_steps.append(
                f"Secondary focus: {', '.join(medium_priority_gaps)}"
            )

        # Generate application advice
        if overall_match_percentage >= 80:
            application_advice = f"Excellent {overall_match_percentage:.0f}% match! You're well-qualified for this {job_title} position. Highlight your relevant experience and address any minor skill gaps."
        elif overall_match_percentage >= 60:
            application_advice = f"Good {overall_match_percentage:.0f}% match for this {job_title} position. Emphasize your transferable skills and create a development plan for missing competencies."
        elif overall_match_percentage >= 40:
            application_advice = f"Moderate {overall_match_percentage:.0f}% match. Consider developing key missing skills before applying, but you have a solid foundation to build upon."
        else:
            application_advice = f"Limited {overall_match_percentage:.0f}% match. Focus on building fundamental skills required for this {job_title} role before applying."

        return {
            "recommended_next_steps": recommended_next_steps,
            "application_advice": application_advice,
        }

    def _assemble_analysis_result(
        self,
        analysis_results: Dict[str, Any],
        learning_recommendations: List[Dict[str, Any]],
        advice_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Assemble the final skill gap analysis result.

        Args:
            analysis_results: Core analysis results from skill matching
            learning_recommendations: Generated learning recommendations
            advice_data: Application advice and next steps

        Returns:
            Complete skill gap analysis response
        """
        return {
            "overall_match_percentage": float(
                analysis_results["overall_match_percentage"]
            ),
            "match_summary": analysis_results["match_summary"],
            "strengths": analysis_results["strengths"],
            "skill_gaps": analysis_results["skill_gaps"],
            "learning_recommendations": learning_recommendations,
            "recommended_next_steps": advice_data["recommended_next_steps"],
            "application_advice": advice_data["application_advice"],
        }

    def _compare_skill_levels(self, resume_level: str, required_level: str) -> bool:
        """
        Compare skill levels to determine if resume level meets job requirement.

        Args:
            resume_level: Candidate's skill level (Entry, Intermediate, Advanced, Senior)
            required_level: Required skill level

        Returns:
            True if resume level meets or exceeds requirement
        """
        level_hierarchy = {
            "entry": 1,
            "beginner": 1,
            "basic": 1,
            "intermediate": 2,
            "advanced": 3,
            "senior": 4,
            "expert": 4,
        }

        resume_score = level_hierarchy.get(resume_level.lower(), 1)
        required_score = level_hierarchy.get(required_level.lower(), 2)

        return resume_score >= required_score

    def _map_importance_to_priority(self, importance: str) -> str:
        """Map job skill importance to gap priority."""
        importance_lower = importance.lower()
        if importance_lower in ["critical", "high"]:
            return "High"
        elif importance_lower in ["medium", "moderate"]:
            return "Medium"
        else:
            return "Low"

    def _extract_base_skill(self, skill_name: str) -> str:
        """
        Extract base skill from compound skill names.

        Args:
            skill_name: The skill name (e.g., "aws sagemaker", "node.js")

        Returns:
            Base skill name (e.g., "aws", "nodejs")
        """
        skill_lower = skill_name.lower().strip()

        # Common skill mappings
        base_skill_mappings = {
            "aws sagemaker": "aws",
            "aws bedrock": "aws",
            "aws lambda": "aws",
            "aws ec2": "aws",
            "aws s3": "aws",
            "aws rds": "aws",
            "node.js": "nodejs",
            "react.js": "react",
            "vue.js": "vue",
            "angular.js": "angular",
        }

        # Check for direct mappings
        if skill_lower in base_skill_mappings:
            return base_skill_mappings[skill_lower]

        # Extract first word for compound skills
        words = skill_lower.split()
        if len(words) > 1:
            first_word = words[0]
            # Common cloud/tech platforms where first word is the base skill
            if first_word in ["aws", "azure", "google", "microsoft", "oracle"]:
                return first_word

        return skill_lower

    def _find_matching_resume_skill(
        self, job_skill: str, resume_skill_map: Dict[str, Any]
    ) -> str:
        """
        Find matching resume skill for a job requirement.

        Args:
            job_skill: Required job skill name
            resume_skill_map: Map of resume skills

        Returns:
            Matching resume skill key, or None if not found
        """
        job_skill_lower = job_skill.lower()

        # Direct match
        if job_skill_lower in resume_skill_map:
            return job_skill_lower

        # Check base skill
        base_skill = self._extract_base_skill(job_skill_lower)
        if base_skill in resume_skill_map:
            return base_skill

        # Check for partial matches (e.g., "aws" matches "aws ec2")
        for resume_skill in resume_skill_map.keys():
            if base_skill in resume_skill or resume_skill in base_skill:
                return resume_skill

        return None

    def _basic_skill_gap_analysis(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        normalize: bool = True,
    ) -> Dict[str, Any]:
        """
        Fallback basic skill gap analysis when enhanced analysis fails.

        Args:
            resume_text: Resume text
            job_description: Job description text
            job_title: Job title
            normalize: Whether to apply normalization to extracted skills

        Returns:
            Basic skill gap analysis results
        """
        try:
            prompt = self._create_skill_gap_analysis_prompt(
                resume_text, job_description, job_title
            )

            response = self._make_llm_request(
                prompt=prompt,
                system_content="You are a career advisor. Analyze skill gaps and provide recommendations.",
                max_tokens=1200,
            )

            analysis_data = self._parse_json_response(
                response, "basic skill gap analysis"
            )

            # Apply normalization if requested
            if normalize:
                analysis_data = self._apply_skill_normalization_to_analysis(
                    analysis_data, f"job {job_title}"
                )

            return analysis_data

        except Exception as e:
            logger.error(f"Basic skill gap analysis failed: {str(e)}")
            # Return minimal fallback structure
            return {
                "overall_match_percentage": 50,
                "match_summary": "Unable to complete detailed analysis due to technical issues",
                "strengths": [],
                "skill_gaps": [],
                "learning_recommendations": [],
                "recommended_next_steps": [
                    "Review job requirements manually",
                    "Consider skill development in key areas",
                ],
                "application_advice": "Focus on highlighting relevant experience and skills",
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

    def _create_skill_gap_analysis_prompt(
        self, resume_text: str, job_description: str, job_title: str
    ) -> str:
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
