"""
LangChain-based career strategy agent service.
Provides multi-step autonomous career planning and analysis using agent patterns.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool, tool
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks.manager import get_openai_callback

from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.similarity_service import similarity_service
from app.crud.job import get_jobs
from app.crud.resume import get_resume_by_user
from app.core.config import settings

logger = logging.getLogger(__name__)


class CareerStrategyAgentError(Exception):
    """Exception raised when career strategy agent operations fail."""

    pass


class JobAnalysisTool(BaseTool):
    """Tool for analyzing job market trends and opportunities."""

    name: str = "job_analysis_tool"
    description: str = """
    Analyze job market trends and opportunities for career planning.
    Input should be a JSON string with keys: user_id, target_roles, location_preference.
    Returns market analysis including demand trends, salary insights, and skill requirements.
    """
    db: Union[Session, Any]

    def __init__(self, db: Session):
        super().__init__(db=db)

    def _run(self, query: str) -> str:
        """Execute job market analysis."""
        try:
            # Parse input
            query_data = json.loads(query)
            user_id = query_data.get("user_id")
            target_roles = query_data.get("target_roles", [])
            location_preference = query_data.get("location_preference", "")

            # Get user's job postings for market context
            user_jobs = get_jobs(self.db, UUID(user_id))[:50]

            if not user_jobs:
                return json.dumps(
                    {
                        "market_analysis": "Limited market data available - no job postings found",
                        "demand_trends": ["Insufficient data for trend analysis"],
                        "salary_insights": "No salary data available",
                        "skill_requirements": ["General industry skills recommended"],
                    }
                )

            # Analyze job market trends from user's posted jobs
            job_titles = [job.title for job in user_jobs if job.title]
            job_descriptions = [job.description for job in user_jobs if job.description]

            # Create market analysis prompt
            market_prompt = f"""
            Analyze the job market based on the following job data:

            TARGET ROLES: {', '.join(target_roles) if target_roles else 'General analysis'}
            LOCATION PREFERENCE: {location_preference or 'Not specified'}

            AVAILABLE JOB DATA:
            Job Titles: {job_titles[:10]}  # Limit to first 10 for prompt size

            Provide analysis in JSON format:
            {{
                "market_analysis": "Overall market condition assessment",
                "demand_trends": ["trend1", "trend2", "trend3"],
                "salary_insights": "Salary range and progression insights",
                "skill_requirements": ["skill1", "skill2", "skill3"]
            }}
            """

            # Use existing LLM service for analysis
            analysis_result = llm_service.generate_feedback(
                resume_text=market_prompt, feedback_type="general"
            )

            if analysis_result and analysis_result[0]:
                try:
                    # Try to extract JSON from the response
                    response_text = analysis_result[0]
                    if "{" in response_text and "}" in response_text:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_str = response_text[json_start:json_end]
                        parsed_result = json.loads(json_str)
                        return json.dumps(parsed_result)
                except json.JSONDecodeError:
                    pass

            # Fallback response if JSON parsing fails
            return json.dumps(
                {
                    "market_analysis": f"Market analysis for {len(user_jobs)} job opportunities",
                    "demand_trends": [
                        "Technology roles in high demand",
                        "Remote work opportunities increasing",
                    ],
                    "salary_insights": "Competitive salary ranges observed across postings",
                    "skill_requirements": [
                        "Technical skills",
                        "Communication abilities",
                        "Problem-solving",
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error in job analysis tool: {str(e)}")
            return json.dumps(
                {
                    "error": f"Analysis failed: {str(e)}",
                    "market_analysis": "Unable to complete market analysis",
                    "demand_trends": ["Analysis unavailable"],
                    "salary_insights": "No salary insights available",
                    "skill_requirements": ["General skills recommended"],
                }
            )


class SkillGapAnalysisTool(BaseTool):
    """Tool for analyzing skill gaps and learning recommendations."""

    name: str = "skill_gap_analysis_tool"
    description: str = """
    Analyze skill gaps between current profile and target career goals.
    Input should be a JSON string with keys: user_id, target_roles, career_goals.
    Returns skill gap analysis and learning recommendations.
    """
    db: Union[Session, Any]

    def __init__(self, db: Session):
        super().__init__(db=db)

    def _run(self, query: str) -> str:
        """Execute skill gap analysis."""
        try:
            # Parse input
            query_data = json.loads(query)
            user_id = query_data.get("user_id")
            target_roles = query_data.get("target_roles", [])
            career_goals = query_data.get("career_goals", "")

            # Get user's resume for current skills
            user_resume = get_resume_by_user(self.db, UUID(user_id))

            if not user_resume or not user_resume.extracted_text:
                return json.dumps(
                    {
                        "current_skills": ["Unable to analyze - no resume data"],
                        "skill_gaps": ["Complete skills assessment needed"],
                        "learning_recommendations": [
                            "Upload resume for personalized recommendations"
                        ],
                        "priority_skills": ["Basic professional skills"],
                    }
                )

            # Create skill gap analysis prompt
            skill_prompt = f"""
            Analyze skill gaps for career transition:

            CURRENT PROFILE:
            {user_resume.extracted_text[:1000]}...

            TARGET ROLES: {', '.join(target_roles) if target_roles else 'General career growth'}
            CAREER GOALS: {career_goals or 'Professional development'}

            Provide detailed skill gap analysis in JSON format:
            {{
                "current_skills": ["skill1", "skill2", "skill3"],
                "skill_gaps": ["gap1", "gap2", "gap3"],
                "learning_recommendations": ["Learn X for Y role", "Develop Z skills"],
                "priority_skills": ["high_priority_skill1", "high_priority_skill2"]
            }}
            """

            # Use existing LLM service for analysis
            analysis_result = llm_service.generate_feedback(
                resume_text=skill_prompt, feedback_type="skills"
            )

            if analysis_result and analysis_result[0]:
                try:
                    # Try to extract JSON from the response
                    response_text = analysis_result[0]
                    if "{" in response_text and "}" in response_text:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_str = response_text[json_start:json_end]
                        parsed_result = json.loads(json_str)
                        return json.dumps(parsed_result)
                except json.JSONDecodeError:
                    pass

            # Fallback response
            return json.dumps(
                {
                    "current_skills": [
                        "Professional experience demonstrated",
                        "Communication skills",
                        "Technical abilities",
                    ],
                    "skill_gaps": [
                        "Specific technical skills for target role",
                        "Industry-specific knowledge",
                    ],
                    "learning_recommendations": [
                        "Focus on target role requirements",
                        "Build portfolio projects",
                    ],
                    "priority_skills": [
                        "Role-specific technical skills",
                        "Industry best practices",
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error in skill gap analysis tool: {str(e)}")
            return json.dumps(
                {
                    "error": f"Analysis failed: {str(e)}",
                    "current_skills": ["Unable to analyze"],
                    "skill_gaps": ["Analysis unavailable"],
                    "learning_recommendations": ["Retry analysis with valid data"],
                    "priority_skills": ["General professional development"],
                }
            )


class CareerPathPlannerTool(BaseTool):
    """Tool for creating structured career progression plans."""

    name: str = "career_path_planner_tool"
    description: str = """
    Create structured career progression plans with timelines and milestones.
    Input should be a JSON string with keys: current_role, target_role, timeframe, constraints.
    Returns detailed career progression plan with actionable steps.
    """

    def _run(self, query: str) -> str:
        """Execute career path planning."""
        try:
            # Parse input
            query_data = json.loads(query)
            current_role = query_data.get("current_role", "Current Position")
            target_role = query_data.get("target_role", "Target Position")
            timeframe = query_data.get("timeframe", "2-3 years")
            constraints = query_data.get("constraints", [])

            # Create career planning prompt
            planning_prompt = f"""
            Create a detailed career progression plan:

            FROM: {current_role}
            TO: {target_role}
            TIMEFRAME: {timeframe}
            CONSTRAINTS: {', '.join(constraints) if constraints else 'None specified'}

            Provide a structured career plan in JSON format:
            {{
                "career_phases": [
                    {{
                        "phase": "Phase 1 (Months 1-6)",
                        "objectives": ["objective1", "objective2"],
                        "key_actions": ["action1", "action2"],
                        "success_metrics": ["metric1", "metric2"]
                    }}
                ],
                "key_milestones": ["milestone1", "milestone2"],
                "potential_challenges": ["challenge1", "challenge2"],
                "success_strategies": ["strategy1", "strategy2"]
            }}
            """

            # Use existing LLM service for planning
            planning_result = llm_service.generate_feedback(
                resume_text=planning_prompt, feedback_type="general"
            )

            if planning_result and planning_result[0]:
                try:
                    # Try to extract JSON from the response
                    response_text = planning_result[0]
                    if "{" in response_text and "}" in response_text:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_str = response_text[json_start:json_end]
                        parsed_result = json.loads(json_str)
                        return json.dumps(parsed_result)
                except json.JSONDecodeError:
                    pass

            # Fallback structured plan
            return json.dumps(
                {
                    "career_phases": [
                        {
                            "phase": "Phase 1 (Short-term: 6 months)",
                            "objectives": ["Skill development", "Network building"],
                            "key_actions": [
                                "Complete relevant training",
                                "Join professional groups",
                            ],
                            "success_metrics": [
                                "Certifications earned",
                                "Connections made",
                            ],
                        },
                        {
                            "phase": "Phase 2 (Medium-term: 1-2 years)",
                            "objectives": ["Gain experience", "Build portfolio"],
                            "key_actions": [
                                "Take on stretch projects",
                                "Document achievements",
                            ],
                            "success_metrics": [
                                "Project success",
                                "Skill demonstration",
                            ],
                        },
                    ],
                    "key_milestones": [
                        f"Transition from {current_role} to {target_role}",
                        "Skill mastery achievement",
                    ],
                    "potential_challenges": [
                        "Market competition",
                        "Skill acquisition time",
                    ],
                    "success_strategies": [
                        "Consistent learning",
                        "Strategic networking",
                        "Performance excellence",
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error in career path planner tool: {str(e)}")
            return json.dumps(
                {
                    "error": f"Planning failed: {str(e)}",
                    "career_phases": [],
                    "key_milestones": ["Plan creation failed"],
                    "potential_challenges": ["Analysis error"],
                    "success_strategies": ["Retry with valid input"],
                }
            )


class CareerStrategyAgent:
    """
    LangChain-based career strategy agent for autonomous multi-step career planning.
    Provides comprehensive career analysis and strategic planning capabilities.
    """

    def __init__(self):
        """Initialize the career strategy agent."""
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )

        # Agent system prompt
        self.system_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="""
            You are a Career Strategy Agent, an expert career advisor with deep knowledge of job markets,
            skill development, and career progression strategies. Your role is to provide comprehensive,
            actionable career guidance through multi-step analysis.

            Your capabilities include:
            1. Job market analysis and trend identification
            2. Skill gap analysis and learning recommendations
            3. Career path planning with structured timelines
            4. Strategic advice for career transitions

            Always provide:
            - Data-driven insights when possible
            - Actionable recommendations with clear next steps
            - Realistic timelines and expectations
            - Multiple perspectives and options

            Use the available tools to gather information and provide comprehensive analysis.
            Structure your responses clearly and include specific recommendations.
            """
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessage(content="{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def create_agent_executor(self, db: Session) -> AgentExecutor:
        """Create and configure the agent executor with tools."""

        # Initialize tools with database session
        tools = [
            JobAnalysisTool(db),
            SkillGapAnalysisTool(db),
            CareerPathPlannerTool(),
        ]

        # Create the agent
        agent = create_openai_functions_agent(
            llm=self.llm, tools=tools, prompt=self.system_prompt
        )

        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate",
        )

        return agent_executor

    def analyze_career_strategy(
        self,
        user_id: UUID,
        db: Union[Session, Any],
        career_goals: str,
        target_roles: List[str] = None,
        timeframe: str = "2-3 years",
        current_role: str = None,
        location_preference: str = None,
        constraints: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive career strategy analysis using agent approach.

        Args:
            user_id: User ID for personalized analysis
            db: Database session
            career_goals: User's career goals and aspirations
            target_roles: List of target job roles
            timeframe: Desired timeframe for career progression
            current_role: Current job role/position
            location_preference: Preferred work location
            constraints: Any constraints or limitations

        Returns:
            Comprehensive career strategy analysis
        """
        try:
            logger.info(f"Starting career strategy analysis for user {user_id}")

            # Create agent executor
            agent_executor = self.create_agent_executor(db)

            # Prepare analysis input
            target_roles = target_roles or []
            constraints = constraints or []

            analysis_input = f"""
            Please provide a comprehensive career strategy analysis for the following profile:

            CAREER GOALS: {career_goals}
            TARGET ROLES: {', '.join(target_roles) if target_roles else 'Not specified'}
            CURRENT ROLE: {current_role or 'Not specified'}
            TIMEFRAME: {timeframe}
            LOCATION PREFERENCE: {location_preference or 'Not specified'}
            CONSTRAINTS: {', '.join(constraints) if constraints else 'None'}
            USER_ID: {str(user_id)}

            Please use your tools to:
            1. Analyze the job market for the target roles and location
            2. Assess skill gaps based on the user's profile
            3. Create a structured career progression plan

            Provide comprehensive analysis with actionable recommendations.
            """

            # Execute agent analysis with cost tracking
            with get_openai_callback() as cb:
                result = agent_executor.invoke(
                    {"input": analysis_input, "chat_history": []}
                )

            # Log token usage
            logger.info(
                f"Agent analysis completed - Tokens: {cb.total_tokens}, Cost: ${cb.total_cost:.4f}"
            )

            # Extract and structure the result
            agent_response = result.get("output", "")

            # Parse any structured data from tool responses
            analysis_data = self._extract_analysis_data(agent_response)

            # Compile comprehensive result
            return {
                "analysis_summary": agent_response,
                "market_analysis": analysis_data.get("market_analysis", {}),
                "skill_analysis": analysis_data.get("skill_analysis", {}),
                "career_plan": analysis_data.get("career_plan", {}),
                "strategic_recommendations": self._extract_recommendations(
                    agent_response
                ),
                "next_steps": self._extract_next_steps(agent_response),
                "analysis_metadata": {
                    "user_id": str(user_id),
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "tokens_used": cb.total_tokens,
                    "analysis_cost": cb.total_cost,
                    "agent_iterations": len(result.get("intermediate_steps", [])),
                },
            }

        except Exception as e:
            logger.error(f"Error in career strategy analysis: {str(e)}", exc_info=True)
            raise CareerStrategyAgentError(f"Career strategy analysis failed: {str(e)}")

    def _extract_analysis_data(self, agent_response: str) -> Dict[str, Any]:
        """Extract structured analysis data from agent response."""
        analysis_data = {"market_analysis": {}, "skill_analysis": {}, "career_plan": {}}

        try:
            # Look for JSON blocks in the response
            lines = agent_response.split("\n")
            json_buffer = []
            in_json = False

            for line in lines:
                if "{" in line and not in_json:
                    in_json = True
                    json_buffer = [line]
                elif in_json:
                    json_buffer.append(line)
                    if "}" in line and line.count("}") >= line.count("{"):
                        # Try to parse the JSON block
                        try:
                            json_str = "\n".join(json_buffer)
                            if "{" in json_str and "}" in json_str:
                                json_start = json_str.find("{")
                                json_end = json_str.rfind("}") + 1
                                clean_json = json_str[json_start:json_end]
                                parsed_data = json.loads(clean_json)

                                # Categorize the data based on content
                                if any(
                                    key in parsed_data
                                    for key in ["market_analysis", "demand_trends"]
                                ):
                                    analysis_data["market_analysis"] = parsed_data
                                elif any(
                                    key in parsed_data
                                    for key in ["current_skills", "skill_gaps"]
                                ):
                                    analysis_data["skill_analysis"] = parsed_data
                                elif any(
                                    key in parsed_data
                                    for key in ["career_phases", "key_milestones"]
                                ):
                                    analysis_data["career_plan"] = parsed_data

                        except json.JSONDecodeError:
                            pass

                        json_buffer = []
                        in_json = False

        except Exception as e:
            logger.warning(f"Error extracting analysis data: {str(e)}")

        return analysis_data

    def _extract_recommendations(self, agent_response: str) -> List[str]:
        """Extract strategic recommendations from agent response."""
        recommendations = []

        try:
            lines = agent_response.split("\n")
            in_recommendations = False

            for line in lines:
                line = line.strip()

                # Look for recommendation sections
                if any(
                    keyword in line.lower()
                    for keyword in ["recommend", "suggest", "advice", "should"]
                ):
                    in_recommendations = True

                # Extract bulleted or numbered recommendations
                if in_recommendations and (
                    line.startswith(("-", "•", "*"))
                    or any(char.isdigit() and "." in line for char in line[:3])
                ):
                    clean_line = line.lstrip("-•*0123456789. ").strip()
                    if len(clean_line) > 10:  # Meaningful content
                        recommendations.append(clean_line)

                # Stop at next major section
                if in_recommendations and line.isupper() and len(line) > 5:
                    break

        except Exception as e:
            logger.warning(f"Error extracting recommendations: {str(e)}")

        # Fallback recommendations if none found
        if not recommendations:
            recommendations = [
                "Focus on developing skills relevant to your target roles",
                "Build a strong professional network in your industry",
                "Create a portfolio showcasing your capabilities",
                "Stay updated with industry trends and best practices",
            ]

        return recommendations[:5]  # Limit to top 5

    def _extract_next_steps(self, agent_response: str) -> List[str]:
        """Extract actionable next steps from agent response."""
        next_steps = []

        try:
            lines = agent_response.split("\n")
            in_next_steps = False

            for line in lines:
                line = line.strip()

                # Look for next steps sections
                if any(
                    keyword in line.lower()
                    for keyword in ["next step", "action", "immediate", "start"]
                ):
                    in_next_steps = True

                # Extract bulleted or numbered items
                if in_next_steps and (
                    line.startswith(("-", "•", "*"))
                    or any(char.isdigit() and "." in line for char in line[:3])
                ):
                    clean_line = line.lstrip("-•*0123456789. ").strip()
                    if len(clean_line) > 5:  # Meaningful content
                        next_steps.append(clean_line)

                # Stop at next major section
                if in_next_steps and line.isupper() and len(line) > 5:
                    break

        except Exception as e:
            logger.warning(f"Error extracting next steps: {str(e)}")

        # Fallback next steps if none found
        if not next_steps:
            next_steps = [
                "Complete a comprehensive skills assessment",
                "Research target companies and roles in detail",
                "Update resume and LinkedIn profile",
                "Begin networking with professionals in target field",
            ]

        return next_steps[:4]  # Limit to top 4


# Global instance
career_strategy_agent = CareerStrategyAgent()
