"""
Unit tests for career strategy agent service.
Tests LangChain-based career planning and multi-step agent analysis.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

from app.services.career_strategy_agent import (
    CareerStrategyAgent,
    CareerStrategyAgentError,
    JobAnalysisTool,
    SkillGapAnalysisTool,
    CareerPathPlannerTool,
)


class TestJobAnalysisTool:
    """Test suite for Job Analysis Tool."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.tool = JobAnalysisTool(self.mock_db)
        self.mock_user_id = uuid4()

        # Mock job data
        self.mock_jobs = [
            Mock(
                title="Senior Python Developer",
                description="Python, FastAPI, PostgreSQL",
            ),
            Mock(
                title="Data Scientist",
                description="Python, Machine Learning, Statistics",
            ),
            Mock(title="DevOps Engineer", description="AWS, Docker, Kubernetes"),
        ]

    @patch("app.services.career_strategy_agent.get_jobs_by_user")
    @patch("app.services.career_strategy_agent.llm_service")
    def test_job_analysis_tool_success(self, mock_llm_service, mock_get_jobs):
        """Test successful job market analysis."""
        # Setup mocks
        mock_get_jobs.return_value = self.mock_jobs
        mock_llm_service.generate_feedback.return_value = [
            """
            {
                "market_analysis": "Strong demand for Python developers",
                "demand_trends": ["Python in high demand", "Remote work increasing"],
                "salary_insights": "Senior roles: $120K-180K",
                "skill_requirements": ["Python", "FastAPI", "Cloud"]
            }
            """
        ]

        # Test tool execution
        query_input = {
            "user_id": str(self.mock_user_id),
            "target_roles": ["Senior Python Developer"],
            "location_preference": "San Francisco",
        }

        result = self.tool._run(json.dumps(query_input))
        parsed_result = json.loads(result)

        # Verify results
        assert "market_analysis" in parsed_result
        assert "demand_trends" in parsed_result
        assert "salary_insights" in parsed_result
        assert "skill_requirements" in parsed_result
        assert "Python" in parsed_result["skill_requirements"]

        # Verify service calls
        mock_get_jobs.assert_called_once_with(self.mock_db, self.mock_user_id, limit=50)
        mock_llm_service.generate_feedback.assert_called_once()

    @patch("app.services.career_strategy_agent.get_jobs_by_user")
    def test_job_analysis_no_jobs_found(self, mock_get_jobs):
        """Test job analysis when no jobs are found."""
        # Setup: no jobs found
        mock_get_jobs.return_value = []

        query_input = {
            "user_id": str(self.mock_user_id),
            "target_roles": ["Senior Developer"],
            "location_preference": "Remote",
        }

        result = self.tool._run(json.dumps(query_input))
        parsed_result = json.loads(result)

        # Verify fallback response
        assert "Limited market data available" in parsed_result["market_analysis"]
        assert "Insufficient data" in parsed_result["demand_trends"][0]
        assert "No salary data available" in parsed_result["salary_insights"]

    def test_job_analysis_invalid_input(self):
        """Test job analysis with invalid JSON input."""
        # Test with invalid JSON
        result = self.tool._run("invalid json")
        parsed_result = json.loads(result)

        # Should return error response
        assert "error" in parsed_result
        assert "Analysis failed" in parsed_result["error"]


class TestSkillGapAnalysisTool:
    """Test suite for Skill Gap Analysis Tool."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.tool = SkillGapAnalysisTool(self.mock_db)
        self.mock_user_id = uuid4()

        # Mock resume data
        self.mock_resume = Mock()
        self.mock_resume.extracted_text = "Experienced Python developer with 3 years in web development using Django and Flask"

    @patch("app.services.career_strategy_agent.get_resume_by_user")
    @patch("app.services.career_strategy_agent.llm_service")
    def test_skill_gap_analysis_success(self, mock_llm_service, mock_get_resume):
        """Test successful skill gap analysis."""
        # Setup mocks
        mock_get_resume.return_value = self.mock_resume
        mock_llm_service.generate_feedback.return_value = [
            """
            {
                "current_skills": ["Python", "Django", "Web Development"],
                "skill_gaps": ["FastAPI", "Cloud platforms", "Microservices"],
                "learning_recommendations": ["Learn FastAPI framework", "Study AWS/GCP"],
                "priority_skills": ["FastAPI", "Cloud deployment"]
            }
            """
        ]

        # Test tool execution
        query_input = {
            "user_id": str(self.mock_user_id),
            "target_roles": ["Senior Python Developer"],
            "career_goals": "Advance to senior backend developer role",
        }

        result = self.tool._run(json.dumps(query_input))
        parsed_result = json.loads(result)

        # Verify results
        assert "current_skills" in parsed_result
        assert "skill_gaps" in parsed_result
        assert "learning_recommendations" in parsed_result
        assert "priority_skills" in parsed_result
        assert "Python" in parsed_result["current_skills"]
        assert "FastAPI" in parsed_result["skill_gaps"]

        # Verify service calls
        mock_get_resume.assert_called_once_with(self.mock_db, self.mock_user_id)
        mock_llm_service.generate_feedback.assert_called_once()

    @patch("app.services.career_strategy_agent.get_resume_by_user")
    def test_skill_gap_analysis_no_resume(self, mock_get_resume):
        """Test skill gap analysis when no resume is found."""
        # Setup: no resume found
        mock_get_resume.return_value = None

        query_input = {
            "user_id": str(self.mock_user_id),
            "target_roles": ["Senior Developer"],
            "career_goals": "Career advancement",
        }

        result = self.tool._run(json.dumps(query_input))
        parsed_result = json.loads(result)

        # Verify fallback response
        assert "Unable to analyze - no resume data" in parsed_result["current_skills"]
        assert "Complete skills assessment needed" in parsed_result["skill_gaps"]
        assert "Upload resume" in parsed_result["learning_recommendations"][0]


class TestCareerPathPlannerTool:
    """Test suite for Career Path Planner Tool."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tool = CareerPathPlannerTool()

    @patch("app.services.career_strategy_agent.llm_service")
    def test_career_path_planning_success(self, mock_llm_service):
        """Test successful career path planning."""
        # Setup mock
        mock_llm_service.generate_feedback.return_value = [
            """
            {
                "career_phases": [
                    {
                        "phase": "Phase 1 (Months 1-6)",
                        "objectives": ["Skill development", "Portfolio building"],
                        "key_actions": ["Complete courses", "Build projects"],
                        "success_metrics": ["Certifications", "Portfolio"]
                    }
                ],
                "key_milestones": ["Complete certification", "Land new role"],
                "potential_challenges": ["Time management", "Skill acquisition"],
                "success_strategies": ["Consistent learning", "Networking"]
            }
            """
        ]

        # Test tool execution
        query_input = {
            "current_role": "Junior Developer",
            "target_role": "Senior Developer",
            "timeframe": "2 years",
            "constraints": ["Work full-time", "Limited budget"],
        }

        result = self.tool._run(json.dumps(query_input))
        parsed_result = json.loads(result)

        # Verify results
        assert "career_phases" in parsed_result
        assert "key_milestones" in parsed_result
        assert "potential_challenges" in parsed_result
        assert "success_strategies" in parsed_result
        assert len(parsed_result["career_phases"]) >= 1

        # Verify phase structure
        phase = parsed_result["career_phases"][0]
        assert "phase" in phase
        assert "objectives" in phase
        assert "key_actions" in phase
        assert "success_metrics" in phase

        # Verify service call
        mock_llm_service.generate_feedback.assert_called_once()

    def test_career_path_planning_fallback(self):
        """Test career path planning with fallback response."""
        # Test with minimal input that triggers fallback
        query_input = {
            "current_role": "Current Position",
            "target_role": "Target Position",
            "timeframe": "2 years",
            "constraints": [],
        }

        # Mock LLM service to return non-JSON response
        with patch("app.services.career_strategy_agent.llm_service") as mock_llm:
            mock_llm.generate_feedback.return_value = ["Non-JSON response"]

            result = self.tool._run(json.dumps(query_input))
            parsed_result = json.loads(result)

            # Verify fallback structure
            assert "career_phases" in parsed_result
            assert len(parsed_result["career_phases"]) >= 1
            assert "key_milestones" in parsed_result
            assert "potential_challenges" in parsed_result
            assert "success_strategies" in parsed_result


class TestCareerStrategyAgent:
    """Test suite for the main Career Strategy Agent."""

    def setup_method(self):
        """Setup test fixtures."""
        self.agent = CareerStrategyAgent()
        self.mock_user_id = uuid4()
        self.mock_db = Mock()

        # Mock agent executor result
        self.mock_agent_result = {
            "output": """
            Based on comprehensive analysis, here are the key findings:

            MARKET ANALYSIS:
            Strong demand for Python developers in the current market.

            SKILL RECOMMENDATIONS:
            - Focus on FastAPI and cloud technologies
            - Build portfolio of microservices projects
            - Gain experience with container orchestration

            NEXT STEPS:
            1. Complete FastAPI certification
            2. Build 3 portfolio projects
            3. Network with industry professionals
            """,
            "intermediate_steps": ["step1", "step2"],
        }

    @patch("app.services.career_strategy_agent.get_openai_callback")
    def test_create_agent_executor(self, mock_callback):
        """Test agent executor creation."""
        # Setup callback mock
        mock_cb = Mock()
        mock_cb.total_tokens = 500
        mock_cb.total_cost = 0.001
        mock_callback.return_value.__enter__ = Mock(return_value=mock_cb)
        mock_callback.return_value.__exit__ = Mock(return_value=None)

        # Test executor creation
        executor = self.agent.create_agent_executor(self.mock_db)

        # Verify executor properties
        assert executor is not None
        assert hasattr(executor, "agent")
        assert hasattr(executor, "tools")
        assert len(executor.tools) == 3  # Should have 3 tools

        # Verify tool types
        tool_names = [tool.name for tool in executor.tools]
        expected_tools = [
            "job_analysis_tool",
            "skill_gap_analysis_tool",
            "career_path_planner_tool",
        ]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @patch("app.services.career_strategy_agent.get_openai_callback")
    def test_analyze_career_strategy_success(self, mock_callback):
        """Test successful career strategy analysis."""
        # Setup callback mock
        mock_cb = Mock()
        mock_cb.total_tokens = 1200
        mock_cb.total_cost = 0.0024
        mock_callback.return_value.__enter__ = Mock(return_value=mock_cb)
        mock_callback.return_value.__exit__ = Mock(return_value=None)

        # Mock agent executor
        mock_executor = Mock()
        mock_executor.invoke.return_value = self.mock_agent_result

        with patch.object(
            self.agent, "create_agent_executor", return_value=mock_executor
        ):
            # Test career strategy analysis
            result = self.agent.analyze_career_strategy(
                user_id=self.mock_user_id,
                db=self.mock_db,
                career_goals="Become a senior Python developer",
                target_roles=["Senior Python Developer", "Tech Lead"],
                timeframe="2-3 years",
                current_role="Python Developer",
                location_preference="San Francisco",
            )

            # Verify result structure
            assert "analysis_summary" in result
            assert "market_analysis" in result
            assert "skill_analysis" in result
            assert "career_plan" in result
            assert "strategic_recommendations" in result
            assert "next_steps" in result
            assert "analysis_metadata" in result

            # Verify metadata
            metadata = result["analysis_metadata"]
            assert metadata["user_id"] == str(self.mock_user_id)
            assert metadata["tokens_used"] == 1200
            assert metadata["analysis_cost"] == 0.0024
            assert "analysis_timestamp" in metadata

            # Verify recommendations extraction
            assert len(result["strategic_recommendations"]) > 0
            assert len(result["next_steps"]) > 0

    def test_extract_recommendations(self):
        """Test recommendation extraction from agent response."""
        agent_response = """
        Based on analysis, I recommend the following:

        - Focus on FastAPI framework for modern API development
        - Build cloud-native applications using containerization
        - Develop expertise in microservices architecture
        - Create a portfolio showcasing scalable backend systems

        These recommendations will position you well for senior roles.
        """

        recommendations = self.agent._extract_recommendations(agent_response)

        # Verify extraction
        assert len(recommendations) >= 3
        assert any("FastAPI" in rec for rec in recommendations)
        assert any("cloud" in rec.lower() for rec in recommendations)
        assert any("microservices" in rec.lower() for rec in recommendations)

    def test_extract_next_steps(self):
        """Test next steps extraction from agent response."""
        agent_response = """
        Your immediate next steps should be:

        1. Enroll in FastAPI course within 2 weeks
        2. Set up development environment for containerization
        3. Identify 3 target companies for networking
        4. Begin first microservices project

        Start with step 1 as your highest priority.
        """

        next_steps = self.agent._extract_next_steps(agent_response)

        # Verify extraction
        assert len(next_steps) >= 3
        assert any("FastAPI" in step for step in next_steps)
        assert any("development environment" in step for step in next_steps)
        assert any("target companies" in step for step in next_steps)

    def test_extract_analysis_data(self):
        """Test structured data extraction from agent response."""
        agent_response = """
        Market analysis shows strong demand.

        {
            "market_analysis": "High demand for Python developers",
            "demand_trends": ["Remote work increasing", "API development growing"],
            "salary_insights": "Senior roles: $130K-200K",
            "skill_requirements": ["Python", "FastAPI", "Docker"]
        }

        Skills assessment reveals gaps in cloud technologies.

        {
            "current_skills": ["Python", "Django", "PostgreSQL"],
            "skill_gaps": ["FastAPI", "AWS", "Kubernetes"],
            "learning_recommendations": ["Complete cloud certification"],
            "priority_skills": ["FastAPI", "Docker"]
        }
        """

        analysis_data = self.agent._extract_analysis_data(agent_response)

        # Verify extraction
        assert "market_analysis" in analysis_data
        assert "skill_analysis" in analysis_data

        # Verify market data
        market_data = analysis_data["market_analysis"]
        assert "market_analysis" in market_data
        assert "demand_trends" in market_data
        assert "Python" in market_data["skill_requirements"]

        # Verify skill data
        skill_data = analysis_data["skill_analysis"]
        assert "current_skills" in skill_data
        assert "skill_gaps" in skill_data
        assert "Python" in skill_data["current_skills"]
        assert "FastAPI" in skill_data["skill_gaps"]

    @patch("app.services.career_strategy_agent.get_openai_callback")
    def test_analyze_career_strategy_error_handling(self, mock_callback):
        """Test error handling in career strategy analysis."""
        # Setup callback mock
        mock_cb = Mock()
        mock_callback.return_value.__enter__ = Mock(return_value=mock_cb)
        mock_callback.return_value.__exit__ = Mock(return_value=None)

        # Mock agent executor to raise exception
        mock_executor = Mock()
        mock_executor.invoke.side_effect = Exception("Agent execution failed")

        with patch.object(
            self.agent, "create_agent_executor", return_value=mock_executor
        ):
            # Test error handling
            with pytest.raises(
                CareerStrategyAgentError, match="Career strategy analysis failed"
            ):
                self.agent.analyze_career_strategy(
                    user_id=self.mock_user_id,
                    db=self.mock_db,
                    career_goals="Test goals",
                    target_roles=["Test Role"],
                )

    def test_fallback_recommendations(self):
        """Test fallback behavior when no recommendations are extracted."""
        # Test with response that has no clear recommendations
        agent_response = "General analysis without specific recommendations."

        recommendations = self.agent._extract_recommendations(agent_response)
        next_steps = self.agent._extract_next_steps(agent_response)

        # Should return fallback content
        assert len(recommendations) > 0
        assert len(next_steps) > 0
        assert any("skills" in rec.lower() for rec in recommendations)
        assert any("skills assessment" in step.lower() for step in next_steps)


class TestCareerStrategyIntegration:
    """Integration tests for career strategy components."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.mock_user_id = uuid4()
        self.mock_db = Mock()

    @patch("app.services.career_strategy_agent.get_jobs_by_user")
    @patch("app.services.career_strategy_agent.get_resume_by_user")
    @patch("app.services.career_strategy_agent.llm_service")
    def test_tool_integration(self, mock_llm_service, mock_get_resume, mock_get_jobs):
        """Test integration between different agent tools."""
        # Setup mocks for all tools
        mock_jobs = [Mock(title="Python Developer", description="Python, FastAPI")]
        mock_resume = Mock(extracted_text="Python developer with 2 years experience")

        mock_get_jobs.return_value = mock_jobs
        mock_get_resume.return_value = mock_resume

        # Mock LLM responses for different tools
        def mock_llm_response(resume_text, feedback_type):
            if "market" in resume_text.lower():
                return [
                    '{"market_analysis": "Strong demand", "demand_trends": ["Python growing"]}'
                ]
            elif "skill" in resume_text.lower():
                return ['{"current_skills": ["Python"], "skill_gaps": ["FastAPI"]}']
            else:
                return [
                    '{"career_phases": [{"phase": "Phase 1", "objectives": ["Learn"]}]}'
                ]

        mock_llm_service.generate_feedback.side_effect = mock_llm_response

        # Test each tool independently
        job_tool = JobAnalysisTool(self.mock_db)
        skill_tool = SkillGapAnalysisTool(self.mock_db)
        career_tool = CareerPathPlannerTool()

        # Test job analysis tool
        job_input = {
            "user_id": str(self.mock_user_id),
            "target_roles": ["Python Developer"],
        }
        job_result = job_tool._run(json.dumps(job_input))
        job_data = json.loads(job_result)
        assert "market_analysis" in job_data

        # Test skill analysis tool
        skill_input = {
            "user_id": str(self.mock_user_id),
            "target_roles": ["Python Developer"],
            "career_goals": "Advance",
        }
        skill_result = skill_tool._run(json.dumps(skill_input))
        skill_data = json.loads(skill_result)
        assert "current_skills" in skill_data

        # Test career planning tool
        career_input = {
            "current_role": "Junior",
            "target_role": "Senior",
            "timeframe": "2 years",
        }
        career_result = career_tool._run(json.dumps(career_input))
        career_data = json.loads(career_result)
        assert "career_phases" in career_data

        # Verify all tools can work with the same data
        assert mock_get_jobs.called
        assert mock_get_resume.called
        assert mock_llm_service.generate_feedback.called
