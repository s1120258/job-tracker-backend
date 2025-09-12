"""
RAG-powered intelligent job matching service.
Enhances existing pgVector search with market context analysis.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.similarity_service import similarity_service
from app.crud.job import get_job
from app.crud.resume import get_resume_by_user
from app.core.config import settings

logger = logging.getLogger(__name__)

class IntelligentMatchingServiceError(Exception):
    """Exception raised when intelligent matching operations fail."""
    pass

class IntelligentMatchingService:
    """
    RAG-powered intelligent job matching service.
    Extends existing pgVector search with market context analysis.
    """

    def __init__(self):
        # Reuse existing services - hybrid approach
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.similarity_service = similarity_service

    def analyze_job_with_market_context(
        self,
        job_id: UUID,
        user_id: UUID,
        db: Session,
        context_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Perform intelligent job analysis using RAG approach.

        Args:
            job_id: Target job ID
            user_id: User ID for resume retrieval
            db: Database session
            context_depth: Number of similar jobs to analyze

        Returns:
            Enhanced analysis with market intelligence
        """
        try:
            # Step 1: Get target job and user resume
            target_job = self._get_job_by_id(db, job_id, user_id)
            user_resume = self._get_user_resume(db, user_id)

            # Step 2: Find similar jobs using existing pgVector
            similar_jobs = self._retrieve_similar_jobs(
                db, target_job["description"], context_depth, job_id
            )

            # Step 3: Extract market trends using LLM
            market_intelligence = self._analyze_market_trends(
                target_job, similar_jobs
            )

            # Step 4: Generate strategic recommendations
            strategic_analysis = self._generate_strategic_analysis(
                target_job, user_resume, market_intelligence
            )

            # Step 5: Calculate basic match score using existing service
            basic_match_score = self._calculate_basic_match_score(
                user_resume, target_job
            )

            # Step 6: Compile comprehensive result
            return self._compile_analysis_result(
                target_job, basic_match_score, market_intelligence, strategic_analysis
            )

        except Exception as e:
            logger.error(f"Error in intelligent job analysis for job {job_id}: {str(e)}")
            raise IntelligentMatchingServiceError(f"Analysis failed: {str(e)}")

    def _get_job_by_id(self, db: Session, job_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Retrieve job by ID with ownership validation."""
        job = get_job(db, job_id)
        if not job:
            raise IntelligentMatchingServiceError("Job not found")

        if job.user_id != user_id:
            raise IntelligentMatchingServiceError("Job access denied")

        return {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "location": job.location,
            "url": job.url
        }

    def _get_user_resume(self, db: Session, user_id: UUID) -> Dict[str, Any]:
        """Retrieve user's resume."""
        resume = get_resume_by_user(db, user_id)
        if not resume:
            raise IntelligentMatchingServiceError("Resume not found")

        if not resume.extracted_text:
            raise IntelligentMatchingServiceError("Resume text not available")

        return {
            "id": str(resume.id),
            "extracted_text": resume.extracted_text,
            "embedding": resume.embedding
        }

    def _retrieve_similar_jobs(
        self,
        db: Session,
        job_description: str,
        limit: int = 5,
        exclude_job_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar jobs using existing pgVector infrastructure.

        Args:
            db: Database session
            job_description: Job description to find similar jobs for
            limit: Number of similar jobs to retrieve
            exclude_job_id: Job ID to exclude from results

        Returns:
            List of similar jobs with similarity scores
        """
        try:
            # Generate embedding using existing service
            query_embedding = self.embedding_service.generate_embedding(job_description)

            # Use existing pgVector setup for similarity search
            query = text("""
                SELECT
                    id, title, company, description, location,
                    1 - (job_embedding <=> :query_embedding) as similarity_score
                FROM jobs
                WHERE job_embedding IS NOT NULL
                  AND (:exclude_job_id IS NULL OR id != :exclude_job_id)
                ORDER BY job_embedding <=> :query_embedding
                LIMIT :limit
            """)

            result = db.execute(query, {
                "query_embedding": query_embedding,
                "limit": limit,
                "exclude_job_id": exclude_job_id
            })

            similar_jobs = []
            for row in result:
                similar_jobs.append({
                    "id": str(row.id),
                    "title": row.title,
                    "company": row.company,
                    "description": row.description,
                    "location": row.location,
                    "similarity_score": float(row.similarity_score)
                })

            logger.info(f"Retrieved {len(similar_jobs)} similar jobs for market analysis")
            return similar_jobs

        except Exception as e:
            logger.error(f"Error retrieving similar jobs: {str(e)}")
            raise IntelligentMatchingServiceError(f"Failed to retrieve similar jobs: {str(e)}")

    def _analyze_market_trends(
        self,
        target_job: Dict[str, Any],
        similar_jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract market trends and insights using LLM analysis.

        Args:
            target_job: Target job information
            similar_jobs: List of similar jobs for context

        Returns:
            Market intelligence data
        """
        try:
            if not similar_jobs:
                return {
                    "similar_jobs_analyzed": 0,
                    "average_similarity_score": 0.0,
                    "market_positioning": "Insufficient market data",
                    "salary_range_insight": None,
                    "skill_trend_analysis": ["Limited market data available"],
                    "demand_assessment": "Cannot assess market demand"
                }

            # Build context from similar jobs
            context = self._build_market_context(similar_jobs)
            avg_similarity = sum(job["similarity_score"] for job in similar_jobs) / len(similar_jobs)

            # Create market analysis prompt
            market_prompt = f"""
            Analyze the job market context for this position:

            TARGET POSITION:
            Title: {target_job.get('title', 'N/A')}
            Company: {target_job.get('company', 'N/A')}
            Location: {target_job.get('location', 'N/A')}
            Description: {target_job.get('description', '')[:500]}...

            MARKET CONTEXT (Similar Positions):
            {context}

            Based on the {len(similar_jobs)} similar positions analyzed, provide:
            1. Market positioning (premium/standard/entry-level) based on requirements
            2. Estimated salary range compared to similar roles
            3. Top 3 skill trends in this market segment
            4. Market demand assessment (high/medium/low)

            Provide specific, data-driven insights based on the similar positions.
            """

            # Use existing LLM service for analysis
            analysis_result = self.llm_service.generate_feedback(
                resume_text=market_prompt,
                feedback_type="general"
            )

            # Parse and structure the analysis
            parsed_analysis = self._parse_market_analysis(analysis_result[0] if analysis_result else "")

            # Add quantitative data
            parsed_analysis.update({
                "similar_jobs_analyzed": len(similar_jobs),
                "average_similarity_score": avg_similarity
            })

            return parsed_analysis

        except Exception as e:
            logger.error(f"Error analyzing market trends: {str(e)}")
            return {
                "similar_jobs_analyzed": len(similar_jobs) if similar_jobs else 0,
                "average_similarity_score": 0.0,
                "market_positioning": f"Analysis error: {str(e)}",
                "salary_range_insight": None,
                "skill_trend_analysis": ["Analysis unavailable due to error"],
                "demand_assessment": "Unable to assess"
            }

    def _build_market_context(self, similar_jobs: List[Dict[str, Any]]) -> str:
        """Build market context string from similar jobs."""
        if not similar_jobs:
            return "No similar jobs found for market analysis."

        context_parts = []
        for i, job in enumerate(similar_jobs, 1):
            context_parts.append(
                f"{i}. {job['title']} at {job['company']} "
                f"(similarity: {job['similarity_score']:.2f})\n"
                f"   Location: {job.get('location', 'N/A')}\n"
                f"   Requirements: {job['description'][:200]}..."
            )

        return "\n\n".join(context_parts)

    def _parse_market_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse LLM market analysis into structured data."""
        # Simple parsing - in production, might use more sophisticated NLP
        default_result = {
            "market_positioning": "Standard market position",
            "salary_range_insight": "Competitive salary range expected",
            "skill_trend_analysis": ["Technology skills in demand", "Communication skills valued"],
            "demand_assessment": "Moderate market demand"
        }

        if not analysis_text:
            return default_result

        try:
            # Extract key insights from analysis text
            lines = analysis_text.split('\n')

            for line in lines:
                line = line.strip().lower()
                if 'premium' in line or 'high-end' in line:
                    default_result["market_positioning"] = "Premium market position"
                elif 'entry' in line or 'junior' in line:
                    default_result["market_positioning"] = "Entry-level market position"

                if 'high demand' in line or 'strong demand' in line:
                    default_result["demand_assessment"] = "High market demand"
                elif 'low demand' in line or 'limited demand' in line:
                    default_result["demand_assessment"] = "Low market demand"

            # Extract skill trends - look for bullet points or numbered items
            skill_trends = []
            for line in lines:
                if any(indicator in line.lower() for indicator in ['skill', 'technology', 'framework', 'language']):
                    if len(line.strip()) > 10 and len(line.strip()) < 100:
                        skill_trends.append(line.strip())

            if skill_trends:
                default_result["skill_trend_analysis"] = skill_trends[:3]  # Top 3

            return default_result

        except Exception as e:
            logger.warning(f"Error parsing market analysis: {str(e)}")
            return default_result

    def _generate_strategic_analysis(
        self,
        target_job: Dict[str, Any],
        user_resume: Dict[str, Any],
        market_intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate strategic recommendations based on job and market analysis.

        Args:
            target_job: Target job information
            user_resume: User's resume data
            market_intelligence: Market analysis results

        Returns:
            Strategic analysis with recommendations
        """
        try:
            strategic_prompt = f"""
            Provide strategic job application analysis:

            JOB POSITION:
            {target_job.get('title', 'N/A')} at {target_job.get('company', 'N/A')}
            Location: {target_job.get('location', 'N/A')}

            CANDIDATE PROFILE:
            {user_resume.get('extracted_text', '')[:500]}...

            MARKET INTELLIGENCE:
            - Market Position: {market_intelligence.get('market_positioning', 'Standard')}
            - Demand Level: {market_intelligence.get('demand_assessment', 'Moderate')}
            - Key Skills: {', '.join(market_intelligence.get('skill_trend_analysis', [])[:3])}

            Provide specific recommendations for:
            1. How to position candidacy for maximum impact
            2. Key selling points to emphasize in application
            3. Potential concerns to address proactively
            4. Competitive advantages to highlight
            5. Areas for improvement before applying

            Be specific and actionable based on the market context.
            """

            strategic_analysis = self.llm_service.generate_feedback(
                resume_text=strategic_prompt,
                feedback_type="general"
            )

            return self._parse_strategic_recommendations(
                strategic_analysis[0] if strategic_analysis else ""
            )

        except Exception as e:
            logger.error(f"Error generating strategic analysis: {str(e)}")
            return {
                "strategic_recommendations": [
                    {"category": "General", "recommendation": "Review job requirements carefully", "priority": "Medium"}
                ],
                "competitive_advantages": ["Review your unique strengths"],
                "improvement_suggestions": ["Continue professional development"]
            }

    def _parse_strategic_recommendations(self, analysis_text: str) -> Dict[str, Any]:
        """Parse strategic analysis into structured recommendations."""
        default_result = {
            "strategic_recommendations": [],
            "competitive_advantages": [],
            "improvement_suggestions": []
        }

        if not analysis_text:
            return default_result

        try:
            lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]

            current_section = None
            for line in lines:
                # Identify sections
                if any(keyword in line.lower() for keyword in ['position', 'selling', 'advantage']):
                    current_section = "recommendations"
                elif any(keyword in line.lower() for keyword in ['competitive', 'strength']):
                    current_section = "advantages"
                elif any(keyword in line.lower() for keyword in ['improvement', 'develop', 'concern']):
                    current_section = "improvements"

                # Extract actionable items
                if line.startswith(('-', '•', '*')) or any(char.isdigit() and '.' in line for char in line[:3]):
                    clean_line = line.lstrip('-•*0123456789. ').strip()
                    if len(clean_line) > 10:  # Meaningful content
                        if current_section == "recommendations":
                            default_result["strategic_recommendations"].append({
                                "category": "Strategic",
                                "recommendation": clean_line,
                                "priority": "High"
                            })
                        elif current_section == "advantages":
                            default_result["competitive_advantages"].append(clean_line)
                        elif current_section == "improvements":
                            default_result["improvement_suggestions"].append(clean_line)
                        else:
                            # General recommendation
                            default_result["strategic_recommendations"].append({
                                "category": "General",
                                "recommendation": clean_line,
                                "priority": "Medium"
                            })

            # Ensure we have at least some content
            if not default_result["strategic_recommendations"]:
                default_result["strategic_recommendations"].append({
                    "category": "General",
                    "recommendation": "Tailor your application to highlight relevant experience",
                    "priority": "High"
                })

            return default_result

        except Exception as e:
            logger.warning(f"Error parsing strategic recommendations: {str(e)}")
            return default_result

    def _calculate_basic_match_score(
        self,
        user_resume: Dict[str, Any],
        target_job: Dict[str, Any]
    ) -> Optional[float]:
        """Calculate basic match score using existing similarity service."""
        try:
            resume_embedding = user_resume.get("embedding")
            if not resume_embedding:
                logger.warning("Resume embedding not available for match score calculation")
                return None

            # Generate job embedding
            job_embedding = self.embedding_service.generate_embedding(
                target_job.get("description", "")
            )

            # Calculate similarity using existing service
            similarity_score = self.similarity_service.calculate_similarity_score(
                resume_embedding, job_embedding
            )

            return float(similarity_score)

        except Exception as e:
            logger.warning(f"Error calculating basic match score: {str(e)}")
            return None

    def _compile_analysis_result(
        self,
        target_job: Dict[str, Any],
        basic_match_score: Optional[float],
        market_intelligence: Dict[str, Any],
        strategic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile comprehensive analysis result."""
        return {
            "basic_match_score": basic_match_score,
            "market_intelligence": market_intelligence,
            "strategic_recommendations": strategic_analysis.get("strategic_recommendations", []),
            "competitive_advantages": strategic_analysis.get("competitive_advantages", []),
            "improvement_suggestions": strategic_analysis.get("improvement_suggestions", []),
            "job_title": target_job.get("title"),
            "company_name": target_job.get("company"),
            "analysis_summary": f"Analyzed {market_intelligence.get('similar_jobs_analyzed', 0)} similar positions"
        }

# Global instance
intelligent_matching_service = IntelligentMatchingService()
