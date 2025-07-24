import logging
from typing import List, Optional, Dict, Any
import json
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

            # Calculate optimal max_tokens based on input length
            input_length = len(resume_text) + (
                len(job_description) if job_description else 0
            )
            max_tokens = self._calculate_optimal_max_tokens(input_length)

            logger.info(
                f"Generating {feedback_type} feedback for resume with max_tokens={max_tokens}"
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume reviewer and career coach.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,  # Use calculated optimal value
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

    def normalize_skills(self, skills: List[str], context: str = "") -> Dict[str, Any]:
        """
        Normalize and standardize skill names using LLM intelligence.
        Avoids dictionary-based approaches for better flexibility.

        Args:
            skills: List of skill names to normalize
            context: Optional context (e.g., job domain, industry)

        Returns:
            Dict containing normalized skills with canonical names and metadata
        """
        if not skills:
            return {"normalized_skills": []}

        try:
            prompt = self._create_skill_normalization_prompt(skills, context)

            logger.info(f"Normalizing {len(skills)} skills with LLM")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill normalization expert. Standardize technology and skill names using industry conventions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.2,  # Low temperature for consistency
                response_format={"type": "json_object"},
            )

            normalized_data = json.loads(response.choices[0].message.content)
            logger.info("Successfully normalized skills using LLM")
            return normalized_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse skill normalization response: {str(e)}")
            # Fallback to original skills if JSON parsing fails
            return {
                "normalized_skills": [
                    {"original": skill, "canonical": skill, "confidence": 0.5}
                    for skill in skills
                ]
            }
        except Exception as e:
            logger.error(f"Error normalizing skills: {str(e)}")
            raise LLMServiceError(f"Failed to normalize skills: {str(e)}")

    def analyze_skill_similarity(self, skill1: str, skill2: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze semantic similarity between two skills using LLM understanding.

        Args:
            skill1: First skill name
            skill2: Second skill name
            context: Optional context for domain-specific analysis

        Returns:
            Dict containing similarity analysis and confidence
        """
        if not skill1 or not skill2:
            raise LLMServiceError("Both skills must be provided for similarity analysis")

        try:
            prompt = self._create_skill_similarity_prompt(skill1, skill2, context)

            logger.info(f"Analyzing similarity between '{skill1}' and '{skill2}'")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill analysis expert. Evaluate semantic similarity between technology skills and concepts.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            similarity_data = json.loads(response.choices[0].message.content)
            logger.info("Successfully analyzed skill similarity")
            return similarity_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse similarity analysis response: {str(e)}")
            # Fallback to basic similarity
            return {
                "similarity_score": 0.5,
                "confidence": 0.3,
                "explanation": "Unable to analyze similarity due to parsing error"
            }
        except Exception as e:
            logger.error(f"Error analyzing skill similarity: {str(e)}")
            raise LLMServiceError(f"Failed to analyze skill similarity: {str(e)}")

    def enhance_skill_gap_analysis(
        self, resume_skills: List[str], job_skills: List[str], context: str = ""
    ) -> Dict[str, Any]:
        """
        Enhanced skill gap analysis with intelligent skill matching and normalization.

        Args:
            resume_skills: Skills extracted from resume
            job_skills: Skills required by job
            context: Job context for better analysis

        Returns:
            Dict containing enhanced gap analysis with normalized skills
        """
        if not resume_skills and not job_skills:
            raise LLMServiceError("At least one skill list must be provided")

        try:
            prompt = self._create_enhanced_gap_analysis_prompt(resume_skills, job_skills, context)

            logger.info("Performing enhanced skill gap analysis")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career advisor specializing in skill gap analysis and career development.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1200,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            analysis_data = json.loads(response.choices[0].message.content)
            logger.info("Successfully completed enhanced skill gap analysis")
            return analysis_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse enhanced gap analysis response: {str(e)}")
            raise LLMServiceError(f"Invalid JSON response from enhanced analysis: {str(e)}")
        except Exception as e:
            logger.error(f"Error in enhanced skill gap analysis: {str(e)}")
            raise LLMServiceError(f"Failed to perform enhanced analysis: {str(e)}")

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

    def _create_skill_normalization_prompt(self, skills: List[str], context: str) -> str:
        """Create prompt for skill normalization."""
        skills_text = ", ".join(skills)
        context_text = f"\nContext: {context}" if context else ""

        return f"""
Normalize and standardize the following skill names to their canonical industry-standard forms.
Consider common abbreviations, alternate spellings, and variations.

Skills to normalize: {skills_text}{context_text}

Return JSON with this structure:
{{
    "normalized_skills": [
        {{
            "original": "JS",
            "canonical": "JavaScript",
            "category": "programming_language",
            "confidence": 0.95,
            "aliases": ["JS", "Javascript", "ECMAScript"],
            "related_skills": ["TypeScript", "Node.js"]
        }},
        {{
            "original": "React.js",
            "canonical": "React",
            "category": "frontend_framework",
            "confidence": 0.99,
            "aliases": ["React.js", "ReactJS"],
            "related_skills": ["Redux", "JSX", "Next.js"]
        }}
    ],
    "suggested_groupings": [
        {{
            "group_name": "JavaScript Ecosystem",
            "skills": ["JavaScript", "React", "Node.js"]
        }}
    ]
}}

Instructions:
- Use widely recognized canonical names (e.g., "JavaScript" not "JS")
- Identify skill categories (programming_language, framework, tool, etc.)
- Provide confidence scores (0.0-1.0)
- List common aliases and variations
- Suggest related skills for learning paths
- Group complementary skills together
"""

    def _create_skill_similarity_prompt(self, skill1: str, skill2: str, context: str) -> str:
        """Create prompt for skill similarity analysis."""
        context_text = f"\nContext: {context}" if context else ""

        return f"""
Analyze the semantic similarity between these two skills in terms of:
1. Technical overlap and transferable knowledge
2. Learning curve if someone knows one but not the other
3. Industry perception and job market substitutability

Skill 1: {skill1}
Skill 2: {skill2}{context_text}

Return JSON with this structure:
{{
    "similarity_score": 0.85,
    "confidence": 0.92,
    "relationship_type": "closely_related",
    "explanation": "Both are JavaScript frameworks with similar component-based architecture",
    "transferable_concepts": ["Component lifecycle", "State management", "Virtual DOM"],
    "key_differences": ["Syntax", "Ecosystem", "Performance characteristics"],
    "learning_effort": "low",
    "substitutable_in_jobs": true
}}

Instructions:
- Score similarity from 0.0 (completely different) to 1.0 (essentially same)
- Relationship types: identical, closely_related, somewhat_related, different_domains, unrelated
- Learning effort: minimal, low, moderate, high, extensive
- Consider both technical and market perspectives
"""

    def _create_enhanced_gap_analysis_prompt(
        self, resume_skills: List[str], job_skills: List[str], context: str
    ) -> str:
        """Create prompt for enhanced skill gap analysis."""
        resume_text = ", ".join(resume_skills) if resume_skills else "None specified"
        job_text = ", ".join(job_skills) if job_skills else "None specified"
        context_text = f"\nJob Context: {context}" if context else ""

        return f"""
Perform intelligent skill gap analysis considering skill relationships, transferability, and learning paths.

Candidate Skills: {resume_text}
Required Skills: {job_text}{context_text}

Return JSON with this structure:
{{
    "intelligent_matches": [
        {{
            "candidate_skill": "React",
            "required_skill": "Vue.js",
            "match_strength": 0.8,
            "reasoning": "Both are component-based frontend frameworks with transferable concepts"
        }}
    ],
    "skill_gaps": [
        {{
            "missing_skill": "Docker",
            "priority": "high",
            "learning_difficulty": "moderate",
            "estimated_time": "2-4 weeks",
            "prerequisites": ["Basic Linux commands"],
            "learning_path": ["Container concepts", "Docker basics", "Docker Compose"]
        }}
    ],
    "skill_advantages": [
        {{
            "skill": "Python",
            "advantage_type": "exceeds_requirements",
            "value": "Strong foundation for backend development and automation"
        }}
    ],
    "normalized_analysis": {{
        "total_required": 8,
        "direct_matches": 5,
        "transferable_matches": 2,
        "complete_gaps": 1,
        "match_percentage": 87.5
    }},
    "learning_strategy": {{
        "immediate_focus": ["Docker", "Kubernetes"],
        "medium_term": ["AWS certification"],
        "leverage_existing": "Use Python knowledge to learn DevOps automation",
        "estimated_ready_time": "6-8 weeks"
    }}
}}

Instructions:
- Recognize skill relationships and transferability
- Provide realistic learning timelines
- Prioritize gaps by business impact
- Suggest learning strategies that build on existing skills
- Calculate intelligent match percentages
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

    def _calculate_optimal_max_tokens(self, input_length: int) -> int:
        """Calculate optimal max_tokens based on input length"""
        if input_length < 1000:
            return 300  # Short input → short output
        elif input_length < 2000:
            return 500  # Medium input → medium output
        else:
            return 800  # Long input → long output


# Global instance
llm_service = LLMService()
