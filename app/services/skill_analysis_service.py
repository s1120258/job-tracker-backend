import json
import logging
from typing import Any, Dict, List, Optional

import openai

from app.core.config import settings
from app.services.llm_service import LLMServiceError, llm_service

logger = logging.getLogger(__name__)


class SkillAnalysisServiceError(Exception):
    """Exception raised when skill analysis operations fail."""

    pass


class SkillAnalysisService:
    """Service for analyzing skill gaps and providing career recommendations."""

    def __init__(self):
        self._client = None
        self.model = "gpt-3.5-turbo"

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured")
                raise SkillAnalysisServiceError("OpenAI API key not configured")
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def analyze_skill_gap(
        self,
        resume_skills_data: Dict[str, Any],
        job_skills_data: Dict[str, Any],
        job_title: str = "",
        normalize: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive skill gap analysis between resume and job requirements.

        Args:
            resume_skills_data: Structured resume skills data
            job_skills_data: Structured job skills data
            job_title: Optional job title for context
            normalize: Whether to apply LLM-based skill normalization

        Returns:
            Dict containing comprehensive skill gap analysis
        """
        if not resume_skills_data:
            raise SkillAnalysisServiceError("Resume skills data cannot be empty")

        if not job_skills_data:
            raise SkillAnalysisServiceError("Job skills data cannot be empty")

        try:
            # Perform intelligent skill matching using structured data
            converted_analysis = self._perform_intelligent_skill_matching(
                resume_skills_data, job_skills_data, job_title
            )

            logger.info("Successfully completed intelligent skill gap analysis")
            return converted_analysis

        except Exception as e:
            logger.error(f"Unexpected error in skill gap analysis: {str(e)}")
            raise SkillAnalysisServiceError(f"Failed to analyze skill gap: {str(e)}")

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


# Global instance
skill_analysis_service = SkillAnalysisService()
