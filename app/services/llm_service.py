import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)


# In-memory cache for job summaries
_job_summary_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, float] = {}
CACHE_TTL = 3600  # 1 hour cache TTL
MAX_CACHE_SIZE = 256  # Maximum number of cached items


def _cleanup_cache():
    """Remove expired cache entries."""
    current_time = time.time()
    expired_keys = [
        key
        for key, timestamp in _cache_timestamps.items()
        if current_time - timestamp > CACHE_TTL
    ]

    for key in expired_keys:
        _job_summary_cache.pop(key, None)
        _cache_timestamps.pop(key, None)

    # If cache is too large, remove oldest entries
    if len(_job_summary_cache) > MAX_CACHE_SIZE:
        # Sort by timestamp and remove oldest
        sorted_keys = sorted(_cache_timestamps.items(), key=lambda x: x[1])
        keys_to_remove = [
            key for key, _ in sorted_keys[: len(_job_summary_cache) - MAX_CACHE_SIZE]
        ]

        for key in keys_to_remove:
            _job_summary_cache.pop(key, None)
            _cache_timestamps.pop(key, None)


class LLMServiceError(Exception):
    """Exception raised when LLM service operations fail."""

    pass


class LLMService:
    """Service for generating AI feedback using OpenAI GPT-4o mini."""

    def __init__(self):
        self._client = None
        self.model = "gpt-4o-mini"  # High-quality model with better reasoning

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

    def generate_intelligent_analysis(
        self,
        prompt: str,
        analysis_type: str = "market",
        max_tokens: int = 1500,
    ) -> str:
        """Generate detailed intelligent analysis with higher token limits for RAG features."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Analysis prompt cannot be empty")

        try:
            logger.info(
                f"Generating {analysis_type} analysis with max_tokens={max_tokens}"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert tech recruiter and career strategist with deep market knowledge. Provide specific, actionable, and data-driven insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content.strip()

            logger.info(
                f"Successfully generated {analysis_type} analysis of {len(content)} characters"
            )
            return content

        except openai.AuthenticationError as e:
            logger.error(
                f"OpenAI authentication error in intelligent analysis: {str(e)}"
            )
            raise LLMServiceError(f"OpenAI authentication failed: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error in intelligent analysis: {str(e)}")
            raise LLMServiceError(f"OpenAI rate limit exceeded: {str(e)}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error in intelligent analysis: {str(e)}")
            raise LLMServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in intelligent analysis: {str(e)}")
            raise LLMServiceError(f"Failed to generate intelligent analysis: {str(e)}")

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

    def analyze_skill_similarity(
        self, skill1: str, skill2: str, context: str = ""
    ) -> Dict[str, Any]:
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
            raise LLMServiceError(
                "Both skills must be provided for similarity analysis"
            )

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
                "explanation": "Unable to analyze similarity due to parsing error",
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
            prompt = self._create_enhanced_gap_analysis_prompt(
                resume_skills, job_skills, context
            )

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
            raise LLMServiceError(
                f"Invalid JSON response from enhanced analysis: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in enhanced skill gap analysis: {str(e)}")
            raise LLMServiceError(f"Failed to perform enhanced analysis: {str(e)}")

    def generate_job_summary(
        self,
        job_description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        max_length: int = 150,
    ) -> Dict[str, Any]:
        """
        Generate a concise summary of a job description.

        Args:
            job_description: Full job description (can include HTML)
            job_title: Optional job title for context
            company_name: Optional company name for context
            max_length: Maximum length of summary in words

        Returns:
            Dict containing summary and key points
        """
        if not job_description or not job_description.strip():
            raise LLMServiceError("Job description cannot be empty")

        # Generate cache key from content hash
        cache_key = self._generate_cache_key(
            job_description, job_title, company_name, max_length
        )

        # Clean up expired cache entries
        _cleanup_cache()

        # Try to get from cache first
        if cache_key in _job_summary_cache:
            cache_age = time.time() - _cache_timestamps.get(cache_key, 0)
            if cache_age < CACHE_TTL:
                logger.info(
                    f"Retrieved job summary from cache: {cache_key[:12]} (age: {cache_age:.1f}s)"
                )
                return _job_summary_cache[cache_key]
            else:
                # Remove expired entry
                _job_summary_cache.pop(cache_key, None)
                _cache_timestamps.pop(cache_key, None)

        try:
            # Clean HTML tags from job description if present
            cleaned_description = self._clean_html_content(job_description)

            # Create context string
            context = ""
            if job_title:
                context += f"Job Title: {job_title}\n"
            if company_name:
                context += f"Company: {company_name}\n"

            prompt = self._create_job_summary_prompt(
                cleaned_description, context, max_length
            )

            logger.info(f"Generating job summary with max length {max_length} words")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional job description summarizer. Create concise, informative summaries that capture the essence of job postings.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=600,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            summary_data = json.loads(response.choices[0].message.content)

            # Add metadata
            summary_data["original_length"] = len(job_description)
            summary_data["generated_at"] = datetime.now(timezone.utc)

            # Cache the result
            _job_summary_cache[cache_key] = summary_data
            _cache_timestamps[cache_key] = time.time()

            logger.info(
                f"Cached job summary: {cache_key[:12]} (cache size: {len(_job_summary_cache)})"
            )
            logger.info("Successfully generated job summary")
            return summary_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse job summary response: {str(e)}")
            # Fallback to basic summary
            cleaned_description = self._clean_html_content(job_description)
            fallback_summary = self._create_fallback_summary(
                cleaned_description, max_length
            )
            return {
                "summary": fallback_summary,
                "summary_length": len(fallback_summary.split()),
                "key_points": ["Summary generated with limited processing"],
                "original_length": len(job_description),
                "generated_at": datetime.now(timezone.utc),
            }
        except Exception as e:
            logger.error(f"Error generating job summary: {str(e)}")
            raise LLMServiceError(f"Failed to generate job summary: {str(e)}")

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

    def _create_skill_normalization_prompt(
        self, skills: List[str], context: str
    ) -> str:
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

    def _create_skill_similarity_prompt(
        self, skill1: str, skill2: str, context: str
    ) -> str:
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

    def _clean_html_content(self, content: str) -> str:
        """Clean HTML tags and excessive whitespace from content."""
        # Remove HTML tags
        cleaned = re.sub(r"<[^>]+>", " ", content)
        # Replace multiple whitespaces with single space
        cleaned = re.sub(r"\s+", " ", cleaned)
        # Remove excessive newlines
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
        return cleaned.strip()

    def _create_job_summary_prompt(
        self, job_description: str, context: str, max_length: int
    ) -> str:
        """Create prompt for job summary generation."""
        return f"""
Analyze the following job description and create a concise, informative summary.

{context}

Job Description:
{job_description[:4000]}  # Limit text length to avoid token limits

Requirements:
- Create a summary of maximum {max_length} words
- Extract 3-5 key points that job seekers should know
- Focus on role responsibilities, required skills, and key benefits
- Make it engaging and informative for potential candidates
- Remove any HTML formatting or excessive technical jargon

Return JSON with this structure:
{{
    "summary": "A {max_length}-word concise summary of the job position highlighting key responsibilities and requirements",
    "summary_length": 145,
    "key_points": [
        "Primary responsibility or main role focus",
        "Key technical skills or qualifications required",
        "Notable benefits or company highlights",
        "Experience level or career stage targeted",
        "Work arrangement (remote, hybrid, etc.) if mentioned"
    ]
}}

Instructions:
- Keep summary clear and professional
- Avoid repetitive information
- Highlight what makes this opportunity unique
- Ensure key_points are specific and actionable
- Count words accurately for summary_length
"""

    def _create_fallback_summary(
        self, cleaned_description: str, max_length: int
    ) -> str:
        """Create a basic fallback summary when LLM processing fails."""
        words = cleaned_description.split()

        # Take first portion of the description as fallback
        if len(words) <= max_length:
            return cleaned_description

        # Extract first max_length words and ensure it ends with complete sentence
        summary_words = words[:max_length]
        summary = " ".join(summary_words)

        # Try to end at a sentence boundary
        if "." in summary:
            sentences = summary.split(".")
            if len(sentences) > 1:
                # Keep all complete sentences
                complete_sentences = sentences[:-1]
                summary = ". ".join(complete_sentences) + "."

        return summary

    def _generate_cache_key(
        self,
        job_description: str,
        job_title: Optional[str],
        company_name: Optional[str],
        max_length: int,
    ) -> str:
        """Generate a hash-based cache key for job summary."""
        # Combine all inputs that affect the output
        content = (
            f"{job_description}|{job_title or ''}|{company_name or ''}|{max_length}"
        )

        # Create SHA256 hash for consistent, collision-resistant key
        hash_object = hashlib.sha256(content.encode("utf-8"))
        cache_key = f"job_summary_{hash_object.hexdigest()}"

        return cache_key

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        _cleanup_cache()
        current_time = time.time()

        # Calculate cache ages
        ages = [current_time - timestamp for timestamp in _cache_timestamps.values()]
        avg_age = sum(ages) / len(ages) if ages else 0

        return {
            "cache_size": len(_job_summary_cache),
            "max_size": MAX_CACHE_SIZE,
            "ttl_seconds": CACHE_TTL,
            "average_age_seconds": avg_age,
            "oldest_entry_seconds": max(ages) if ages else 0,
        }


# Global instance
llm_service = LLMService()
