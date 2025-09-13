"""
API tests for career strategy endpoints.
Tests LangChain agent-based career planning API functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.services.career_strategy_agent import CareerStrategyAgentError


class TestCareerStrategyAPI:
    """Test suite for career strategy API endpoints."""

    def setup_method(self):
        """Setup test fixtures for API tests."""
        self.client = TestClient(app)
        self.mock_user_id = uuid4()

        # Mock comprehensive career strategy result
        self.mock_strategy_result = {
            "analysis_summary": "Comprehensive career analysis shows strong potential for advancement to senior data scientist role...",
            "market_analysis": {
                "market_analysis": "High demand for data science professionals",
                "demand_trends": [
                    "ML roles growing 25% annually",
                    "Remote work increasing",
                ],
                "salary_insights": "Senior Data Scientists: $150K-220K",
                "skill_requirements": ["Python", "Machine Learning", "Deep Learning"],
            },
            "skill_analysis": {
                "current_skills": ["Python", "SQL", "Statistics"],
                "skill_gaps": ["Deep Learning", "MLOps", "Cloud platforms"],
                "learning_recommendations": [
                    "Complete deep learning course",
                    "Gain cloud experience",
                ],
                "priority_skills": ["Deep Learning", "MLOps"],
            },
            "career_plan": {
                "career_phases": [
                    {
                        "phase": "Phase 1 (Months 1-8)",
                        "objectives": ["Skill development", "Portfolio building"],
                        "key_actions": ["Complete ML courses", "Build projects"],
                        "success_metrics": [
                            "Certifications earned",
                            "Portfolio published",
                        ],
                    }
                ],
                "key_milestones": ["Complete ML certification", "Land senior role"],
                "potential_challenges": ["Competition", "Skill acquisition time"],
                "success_strategies": ["Consistent learning", "Strategic networking"],
            },
            "strategic_recommendations": [
                "Focus on deep learning as top priority",
                "Build strong ML portfolio",
                "Network with data science professionals",
            ],
            "next_steps": [
                "Enroll in deep learning course",
                "Identify target companies",
                "Begin first ML project",
            ],
            "analysis_metadata": {
                "user_id": str(self.mock_user_id),
                "analysis_timestamp": "2024-01-15T10:30:00Z",
                "tokens_used": 1250,
                "analysis_cost": 0.0025,
                "agent_iterations": 3,
            },
        }

        # Mock skill analysis result
        self.mock_skill_result = {
            "current_skills": ["Python", "SQL", "Data Analysis"],
            "skill_gaps": ["Machine Learning", "Deep Learning", "Cloud"],
            "learning_recommendations": ["ML course", "Cloud certification"],
            "priority_skills": ["Machine Learning", "Deep Learning"],
        }

        # Mock market insights result
        self.mock_market_result = {
            "market_analysis": "Strong demand for target roles",
            "demand_trends": ["Tech roles growing", "Remote increasing"],
            "salary_insights": "Competitive salaries in market",
            "skill_requirements": ["Python", "Cloud", "ML"],
        }

    def _setup_auth_override(self):
        """Setup authentication override for testing."""
        mock_user = Mock()
        mock_user.id = self.mock_user_id

        from app.api.routes_auth import get_current_user
        from app.db.session import get_db

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()

        return mock_user

    def _cleanup_overrides(self):
        """Clean up dependency overrides."""
        app.dependency_overrides.clear()

    @patch("app.api.routes_career_strategy.career_strategy_agent")
    def test_create_career_strategy_plan_success(self, mock_agent):
        """Test successful career strategy planning API call."""
        # Setup mocks
        mock_user = self._setup_auth_override()
        mock_agent.analyze_career_strategy.return_value = self.mock_strategy_result

        try:
            # Prepare request data
            request_data = {
                "career_goals": "Transition to senior data scientist role within 2-3 years",
                "target_roles": ["Senior Data Scientist", "ML Engineer"],
                "timeframe": "2-3 years",
                "current_role": "Data Analyst",
                "location_preference": "San Francisco Bay Area",
                "constraints": ["Work full-time", "Limited budget for courses"],
            }

            # Make API call
            response = self.client.post(
                "/api/v1/career/strategy-planning", json=request_data
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data["user_id"] == str(self.mock_user_id)
            assert "request_timestamp" in data
            assert "input_parameters" in data
            assert "analysis_summary" in data
            assert "market_analysis" in data
            assert "skill_analysis" in data
            assert "career_plan" in data
            assert "strategic_recommendations" in data
            assert "next_steps" in data
            assert "analysis_metadata" in data

            # Verify input parameters are preserved
            input_params = data["input_parameters"]
            assert input_params["career_goals"] == request_data["career_goals"]
            assert input_params["target_roles"] == request_data["target_roles"]
            assert input_params["timeframe"] == request_data["timeframe"]

            # Verify agent was called correctly
            mock_agent.analyze_career_strategy.assert_called_once_with(
                user_id=self.mock_user_id,
                db=mock_agent.analyze_career_strategy.call_args[1]["db"],
                career_goals=request_data["career_goals"],
                target_roles=request_data["target_roles"],
                timeframe=request_data["timeframe"],
                current_role=request_data["current_role"],
                location_preference=request_data["location_preference"],
                constraints=request_data["constraints"],
            )

        finally:
            self._cleanup_overrides()

    @patch("app.api.routes_career_strategy.career_strategy_agent")
    def test_create_career_strategy_plan_minimal_input(self, mock_agent):
        """Test career strategy planning with minimal input."""
        # Setup mocks
        mock_user = self._setup_auth_override()
        mock_agent.analyze_career_strategy.return_value = self.mock_strategy_result

        try:
            # Minimal request data
            request_data = {
                "career_goals": "Advance my career in technology",
                "timeframe": "2-3 years",
            }

            # Make API call
            response = self.client.post(
                "/api/v1/career/strategy-planning", json=request_data
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify agent was called with defaults
            mock_agent.analyze_career_strategy.assert_called_once()
            call_args = mock_agent.analyze_career_strategy.call_args[1]
            assert call_args["target_roles"] == []
            assert call_args["constraints"] == []
            assert call_args["current_role"] is None
            assert call_args["location_preference"] is None

        finally:
            self._cleanup_overrides()

    def test_create_career_strategy_plan_invalid_input(self):
        """Test career strategy planning with invalid input."""
        # Setup auth
        mock_user = self._setup_auth_override()

        try:
            # Test with career goals too short
            request_data = {"career_goals": "short", "timeframe": "2-3 years"}

            response = self.client.post(
                "/api/v1/career/strategy-planning", json=request_data
            )

            # Should return validation error
            assert response.status_code == 400
            assert (
                "Career goals must be at least 10 characters"
                in response.json()["detail"]
            )

        finally:
            self._cleanup_overrides()

    @patch("app.api.routes_career_strategy.career_strategy_agent")
    def test_create_career_strategy_plan_agent_error(self, mock_agent):
        """Test career strategy planning when agent raises error."""
        # Setup mocks
        mock_user = self._setup_auth_override()
        mock_agent.analyze_career_strategy.side_effect = CareerStrategyAgentError(
            "Agent analysis failed"
        )

        try:
            request_data = {
                "career_goals": "Advance to senior developer role",
                "timeframe": "2 years",
            }

            response = self.client.post(
                "/api/v1/career/strategy-planning", json=request_data
            )

            # Should return error response
            assert response.status_code == 500
            assert "Career strategy analysis failed" in response.json()["detail"]

        finally:
            self._cleanup_overrides()

    @patch("app.services.career_strategy_agent.SkillGapAnalysisTool")
    def test_analyze_skill_gaps_success(self, mock_tool_class):
        """Test successful skill gap analysis API call."""
        # Setup mocks
        mock_user = self._setup_auth_override()

        mock_tool = Mock()
        mock_tool._run.return_value = json.dumps(self.mock_skill_result)
        mock_tool_class.return_value = mock_tool

        try:
            request_data = {
                "target_roles": ["Senior Python Developer", "Tech Lead"],
                "career_goals": "Advance to senior technical role",
                "focus_areas": ["Backend Development", "System Architecture"],
            }

            response = self.client.post(
                "/api/v1/career/skill-gap-analysis", json=request_data
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data["user_id"] == str(self.mock_user_id)
            assert "analysis_timestamp" in data
            assert data["target_roles"] == request_data["target_roles"]
            assert data["career_goals"] == request_data["career_goals"]
            assert data["focus_areas"] == request_data["focus_areas"]
            assert "skill_analysis" in data

            # Verify skill analysis content
            skill_analysis = data["skill_analysis"]
            assert "current_skills" in skill_analysis
            assert "skill_gaps" in skill_analysis
            assert "learning_recommendations" in skill_analysis
            assert "priority_skills" in skill_analysis

            # Verify tool was called correctly
            mock_tool._run.assert_called_once()
            tool_input = json.loads(mock_tool._run.call_args[0][0])
            assert tool_input["user_id"] == str(self.mock_user_id)
            assert tool_input["target_roles"] == request_data["target_roles"]

        finally:
            self._cleanup_overrides()

    def test_analyze_skill_gaps_invalid_input(self):
        """Test skill gap analysis with invalid input."""
        # Setup auth
        mock_user = self._setup_auth_override()

        try:
            # Test with empty target roles
            request_data = {"target_roles": [], "career_goals": "Advance my career"}

            response = self.client.post(
                "/api/v1/career/skill-gap-analysis", json=request_data
            )

            # Should return validation error
            assert response.status_code == 400
            assert (
                "At least one target role must be specified"
                in response.json()["detail"]
            )

            # Test with career goals too short
            request_data = {"target_roles": ["Developer"], "career_goals": "grow"}

            response = self.client.post(
                "/api/v1/career/skill-gap-analysis", json=request_data
            )

            # Should return validation error
            assert response.status_code == 400
            assert (
                "Career goals must be provided for context" in response.json()["detail"]
            )

        finally:
            self._cleanup_overrides()

    @patch("app.services.career_strategy_agent.JobAnalysisTool")
    def test_get_market_insights_success(self, mock_tool_class):
        """Test successful market insights API call."""
        # Setup mocks
        mock_user = self._setup_auth_override()

        mock_tool = Mock()
        mock_tool._run.return_value = json.dumps(self.mock_market_result)
        mock_tool_class.return_value = mock_tool

        try:
            # Make API call with query parameters
            response = self.client.get(
                "/api/v1/career/market-insights",
                params={
                    "target_roles": ["Data Scientist", "ML Engineer"],
                    "location": "San Francisco",
                    "timeframe": "current",
                },
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data["user_id"] == str(self.mock_user_id)
            assert "analysis_timestamp" in data
            assert "query_parameters" in data
            assert "market_insights" in data
            assert "insights_summary" in data

            # Verify query parameters
            query_params = data["query_parameters"]
            assert "Data Scientist" in query_params["target_roles"]
            assert "ML Engineer" in query_params["target_roles"]
            assert query_params["location"] == "San Francisco"
            assert query_params["timeframe"] == "current"

            # Verify market insights content
            market_insights = data["market_insights"]
            assert "market_analysis" in market_insights
            assert "demand_trends" in market_insights
            assert "salary_insights" in market_insights
            assert "skill_requirements" in market_insights

            # Verify tool was called correctly
            mock_tool._run.assert_called_once()
            tool_input = json.loads(mock_tool._run.call_args[0][0])
            assert tool_input["user_id"] == str(self.mock_user_id)
            assert tool_input["location_preference"] == "San Francisco"

        finally:
            self._cleanup_overrides()

    def test_get_market_insights_invalid_input(self):
        """Test market insights with invalid input."""
        # Setup auth
        mock_user = self._setup_auth_override()

        try:
            # Test with no target roles
            response = self.client.get("/api/v1/career/market-insights")

            # Should return validation error
            assert response.status_code == 422  # FastAPI validation error

        finally:
            self._cleanup_overrides()

    @patch("app.api.routes_career_strategy.career_strategy_agent")
    def test_get_agent_status_success(self, mock_agent):
        """Test successful agent status check."""
        # Mock agent properties
        mock_agent.llm.model_name = "gpt-3.5-turbo"

        response = self.client.get("/api/v1/career/agent-status")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["service"] == "career_strategy_agent"
        assert data["status"] in ["operational", "degraded", "unavailable"]
        assert "timestamp" in data
        assert "agent_capabilities" in data
        assert "tool_status" in data
        assert "llm_status" in data
        assert "model_info" in data
        assert "features" in data

        # Verify capabilities
        capabilities = data["agent_capabilities"]
        expected_capabilities = [
            "job_market_analysis",
            "skill_gap_assessment",
            "career_path_planning",
            "strategic_recommendations",
            "multi_step_reasoning",
        ]
        for capability in expected_capabilities:
            assert capability in capabilities
            assert isinstance(capabilities[capability], bool)

        # Verify tool status
        tool_status = data["tool_status"]
        expected_tools = [
            "job_analysis_tool",
            "skill_gap_analysis_tool",
            "career_path_planner_tool",
        ]
        for tool in expected_tools:
            assert tool in tool_status

        # Verify model info
        model_info = data["model_info"]
        assert "model" in model_info
        assert "temperature" in model_info
        assert "max_tokens" in model_info

    def test_get_agent_status_error(self):
        """Test agent status check when error occurs."""
        # Mock datetime to raise exception in the status data creation
        with patch("app.api.routes_career_strategy.datetime") as mock_datetime:
            mock_datetime.now.side_effect = Exception("Datetime access failed")

            response = self.client.get("/api/v1/career/agent-status")

            # Should return service unavailable
            assert response.status_code == 503
            assert (
                "Career strategy agent status check failed" in response.json()["detail"]
            )


class TestCareerStrategyAuthenticationAndPermissions:
    """Test authentication and permissions for career strategy endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_strategy_planning_requires_authentication(self):
        """Test that career strategy planning requires authentication."""
        request_data = {
            "career_goals": "Advance to senior developer role",
            "timeframe": "2 years",
        }

        response = self.client.post(
            "/api/v1/career/strategy-planning", json=request_data
        )

        # Should require authentication
        assert response.status_code == 401

    def test_skill_gap_analysis_requires_authentication(self):
        """Test that skill gap analysis requires authentication."""
        request_data = {
            "target_roles": ["Senior Developer"],
            "career_goals": "Career advancement",
        }

        response = self.client.post(
            "/api/v1/career/skill-gap-analysis", json=request_data
        )

        # Should require authentication
        assert response.status_code == 401

    def test_market_insights_requires_authentication(self):
        """Test that market insights requires authentication."""
        response = self.client.get(
            "/api/v1/career/market-insights", params={"target_roles": ["Developer"]}
        )

        # Should require authentication
        assert response.status_code == 401

    def test_agent_status_no_authentication_required(self):
        """Test that agent status check doesn't require authentication."""
        response = self.client.get("/api/v1/career/agent-status")

        # Should work without authentication
        assert response.status_code == 200


class TestCareerStrategyResponseValidation:
    """Test response validation for career strategy endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
        self.mock_user_id = uuid4()

    def _setup_auth_override(self):
        """Setup authentication override for testing."""
        mock_user = Mock()
        mock_user.id = self.mock_user_id

        from app.api.routes_auth import get_current_user
        from app.db.session import get_db

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()

        return mock_user

    def _cleanup_overrides(self):
        """Clean up dependency overrides."""
        app.dependency_overrides.clear()

    @patch("app.api.routes_career_strategy.career_strategy_agent")
    def test_career_strategy_response_validation(self, mock_agent):
        """Test that career strategy response matches schema."""
        # Setup mocks
        mock_user = self._setup_auth_override()

        # Mock response that should validate against schema
        mock_result = {
            "analysis_summary": "Test analysis",
            "market_analysis": None,
            "skill_analysis": None,
            "career_plan": None,
            "strategic_recommendations": ["Test recommendation"],
            "next_steps": ["Test step"],
            "analysis_metadata": {
                "user_id": str(self.mock_user_id),
                "analysis_timestamp": "2024-01-15T10:30:00Z",
                "tokens_used": 100,
                "analysis_cost": 0.001,
                "agent_iterations": 1,
            },
        }

        mock_agent.analyze_career_strategy.return_value = mock_result

        try:
            request_data = {
                "career_goals": "Test career goals for validation",
                "timeframe": "2 years",
            }

            response = self.client.post(
                "/api/v1/career/strategy-planning", json=request_data
            )

            # Should succeed with valid response structure
            assert response.status_code == 200
            data = response.json()

            # Verify required fields are present
            required_fields = [
                "user_id",
                "request_timestamp",
                "input_parameters",
                "analysis_summary",
                "strategic_recommendations",
                "next_steps",
            ]
            for field in required_fields:
                assert field in data

        finally:
            self._cleanup_overrides()
