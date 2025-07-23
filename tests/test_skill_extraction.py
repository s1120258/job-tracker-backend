import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from app.services.skill_extraction_service import (
    SkillExtractionService,
    SkillExtractionServiceError,
)
import openai


@pytest.fixture
def skill_service():
    """Create a skill extraction service instance for testing."""
    return SkillExtractionService()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI response for testing."""
    mock_response = Mock()
    mock_choice = Mock()
    mock_choice.message.content = json.dumps(
        {
            "technical_skills": [
                {
                    "name": "Python",
                    "level": "Advanced",
                    "years_experience": 5,
                    "evidence": "5 years Python development",
                },
                {
                    "name": "FastAPI",
                    "level": "Intermediate",
                    "years_experience": 2,
                    "evidence": "Built APIs with FastAPI",
                },
            ],
            "soft_skills": ["Communication", "Problem Solving"],
            "programming_languages": ["Python", "JavaScript"],
            "frameworks": ["FastAPI", "React"],
            "tools": ["Git", "Docker"],
            "domains": ["Web Development", "API Development"],
            "education": ["Bachelor's in Computer Science"],
            "total_experience_years": 5,
        }
    )
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def mock_job_skills_response():
    """Mock job skills extraction response."""
    mock_response = Mock()
    mock_choice = Mock()
    mock_choice.message.content = json.dumps(
        {
            "required_skills": [
                {
                    "name": "Python",
                    "level": "Senior",
                    "category": "programming_language",
                    "importance": "critical",
                },
                {
                    "name": "FastAPI",
                    "level": "Intermediate",
                    "category": "framework",
                    "importance": "high",
                },
            ],
            "preferred_skills": [
                {
                    "name": "Docker",
                    "level": "Any",
                    "category": "tool",
                    "importance": "medium",
                }
            ],
            "programming_languages": ["Python"],
            "frameworks": ["FastAPI"],
            "tools": ["Docker", "Git"],
            "experience_required": "3-5 years",
            "education_required": "Bachelor's degree",
            "seniority_level": "Mid-Senior",
        }
    )
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def mock_skill_gap_response():
    """Mock skill gap analysis response."""
    mock_response = Mock()
    mock_choice = Mock()
    mock_choice.message.content = json.dumps(
        {
            "overall_match_percentage": 85,
            "match_summary": "Strong technical background with good framework experience",
            "strengths": [
                {
                    "skill": "Python",
                    "reason": "5+ years experience exceeds requirement",
                },
                {
                    "skill": "FastAPI",
                    "reason": "Good experience with required framework",
                },
            ],
            "skill_gaps": [
                {
                    "skill": "Docker",
                    "required_level": "Intermediate",
                    "current_level": "Beginner",
                    "priority": "Medium",
                    "impact": "Important for deployment",
                    "gap_severity": "Minor",
                }
            ],
            "learning_recommendations": [
                {
                    "skill": "Docker",
                    "priority": "Medium",
                    "estimated_learning_time": "2-3 months",
                    "suggested_approach": "Hands-on practice with containerization",
                    "resources": ["Docker documentation", "Online courses"],
                    "immediate_actions": ["Install Docker", "Follow tutorials"],
                }
            ],
            "experience_gap": {
                "required_years": 4,
                "candidate_years": 5,
                "gap": -1,
                "assessment": "Exceeds experience requirements",
            },
            "education_match": {
                "required": "Bachelor's degree",
                "candidate": "Bachelor's in Computer Science",
                "matches": True,
                "assessment": "Education requirements met",
            },
            "recommended_next_steps": [
                "Practice Docker containerization",
                "Apply with confidence highlighting Python expertise",
            ],
            "application_advice": "Strong candidate with excellent Python skills. Minor Docker gap easily addressable.",
        }
    )
    mock_response.choices = [mock_choice]
    return mock_response


class TestSkillExtractionService:
    """Test cases for SkillExtractionService."""

    @patch("app.services.skill_extraction_service.settings")
    def test_client_initialization_no_api_key(self, mock_settings):
        """Test that service raises error when no API key is configured."""
        mock_settings.OPENAI_API_KEY = None
        service = SkillExtractionService()

        with pytest.raises(
            SkillExtractionServiceError, match="OpenAI API key not configured"
        ):
            _ = service.client

    @patch("app.services.skill_extraction_service.settings")
    @patch("app.services.skill_extraction_service.openai.OpenAI")
    def test_client_initialization_with_api_key(
        self, mock_openai_client, mock_settings
    ):
        """Test that service initializes client when API key is provided."""
        mock_settings.OPENAI_API_KEY = "test-api-key"
        service = SkillExtractionService()

        client = service.client

        mock_openai_client.assert_called_once_with(api_key="test-api-key")
        assert client is not None

    @patch("app.services.skill_extraction_service.settings")
    def test_extract_skills_from_resume_empty_text(self, mock_settings):
        """Test that empty resume text raises appropriate error."""
        mock_settings.OPENAI_API_KEY = "test-key"
        service = SkillExtractionService()

        with pytest.raises(
            SkillExtractionServiceError, match="Resume text cannot be empty"
        ):
            service.extract_skills_from_resume("")

    @patch("app.services.skill_extraction_service.settings")
    @patch("app.services.skill_extraction_service.openai.OpenAI")
    def test_extract_skills_from_resume_success(
        self, mock_openai_client, mock_settings, mock_openai_response
    ):
        """Test successful skill extraction from resume."""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_client.return_value = mock_client

        service = SkillExtractionService()
        resume_text = "Senior Python developer with 5 years experience in FastAPI and web development."

        result = service.extract_skills_from_resume(resume_text)

        assert "technical_skills" in result
        assert len(result["technical_skills"]) == 2
        assert result["technical_skills"][0]["name"] == "Python"
        assert result["technical_skills"][0]["level"] == "Advanced"
        assert result["total_experience_years"] == 5

    @patch("app.services.skill_extraction_service.settings")
    def test_extract_skills_from_job_empty_description(self, mock_settings):
        """Test that empty job description raises appropriate error."""
        mock_settings.OPENAI_API_KEY = "test-key"
        service = SkillExtractionService()

        with pytest.raises(
            SkillExtractionServiceError, match="Job description cannot be empty"
        ):
            service.extract_skills_from_job("")

    @patch("app.services.skill_extraction_service.settings")
    @patch("app.services.skill_extraction_service.openai.OpenAI")
    def test_extract_skills_from_job_success(
        self, mock_openai_client, mock_settings, mock_job_skills_response
    ):
        """Test successful skill extraction from job description."""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_job_skills_response
        mock_openai_client.return_value = mock_client

        service = SkillExtractionService()
        job_description = (
            "Looking for a Senior Python developer with FastAPI experience."
        )

        result = service.extract_skills_from_job(
            job_description, "Senior Python Developer"
        )

        assert "required_skills" in result
        assert "preferred_skills" in result
        assert len(result["required_skills"]) == 2
        assert result["required_skills"][0]["name"] == "Python"
        assert result["required_skills"][0]["importance"] == "critical"

    @patch("app.services.skill_extraction_service.settings")
    @patch("app.services.skill_extraction_service.openai.OpenAI")
    def test_analyze_skill_gap_success(
        self, mock_openai_client, mock_settings, mock_skill_gap_response
    ):
        """Test successful skill gap analysis."""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_skill_gap_response
        mock_openai_client.return_value = mock_client

        service = SkillExtractionService()
        resume_text = "Senior Python developer with FastAPI experience."
        job_description = "Looking for Python developer with Docker knowledge."

        result = service.analyze_skill_gap(
            resume_text, job_description, "Python Developer"
        )

        assert result["overall_match_percentage"] == 85
        assert len(result["strengths"]) == 2
        assert len(result["skill_gaps"]) == 1
        assert result["skill_gaps"][0]["skill"] == "Docker"
        assert result["skill_gaps"][0]["priority"] == "Medium"

    @patch("app.services.skill_extraction_service.settings")
    def test_analyze_skill_gap_empty_inputs(self, mock_settings):
        """Test that empty inputs raise appropriate errors."""
        mock_settings.OPENAI_API_KEY = "test-key"
        service = SkillExtractionService()

        with pytest.raises(
            SkillExtractionServiceError, match="Resume text cannot be empty"
        ):
            service.analyze_skill_gap("", "job description")

        with pytest.raises(
            SkillExtractionServiceError, match="Job description cannot be empty"
        ):
            service.analyze_skill_gap("resume text", "")

    @patch("app.services.skill_extraction_service.settings")
    @patch("app.services.skill_extraction_service.openai.OpenAI")
    def test_openai_api_error_handling(self, mock_openai_client, mock_settings):
        """Test handling of various OpenAI API errors."""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_client = Mock()
        mock_openai_client.return_value = mock_client

        service = SkillExtractionService()

        # Test authentication error
        mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
            "Invalid API key"
        )
        with pytest.raises(
            SkillExtractionServiceError, match="OpenAI authentication failed"
        ):
            service.extract_skills_from_resume("test text")

        # Test rate limit error
        mock_client.chat.completions.create.side_effect = openai.RateLimitError(
            "Rate limit exceeded"
        )
        with pytest.raises(
            SkillExtractionServiceError, match="OpenAI rate limit exceeded"
        ):
            service.extract_skills_from_resume("test text")

        # Test general API error
        mock_client.chat.completions.create.side_effect = openai.APIError("API error")
        with pytest.raises(SkillExtractionServiceError, match="OpenAI API error"):
            service.extract_skills_from_resume("test text")

    @patch("app.services.skill_extraction_service.settings")
    @patch("app.services.skill_extraction_service.openai.OpenAI")
    def test_json_parsing_error_handling(self, mock_openai_client, mock_settings):
        """Test handling of invalid JSON responses from OpenAI."""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_client = Mock()
        mock_openai_client.return_value = mock_client

        # Mock invalid JSON response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Invalid JSON response"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        service = SkillExtractionService()

        with pytest.raises(
            SkillExtractionServiceError, match="Invalid JSON response from LLM"
        ):
            service.extract_skills_from_resume("test text")


class TestSkillExtractionPrompts:
    """Test the prompt generation methods."""

    def test_resume_skill_extraction_prompt(self):
        """Test resume skill extraction prompt generation."""
        service = SkillExtractionService()
        resume_text = "Python developer with 3 years experience"

        prompt = service._create_resume_skill_extraction_prompt(resume_text)

        assert "Extract skills from this resume text" in prompt
        assert resume_text in prompt
        assert "technical_skills" in prompt
        assert "programming_languages" in prompt

    def test_job_skill_extraction_prompt(self):
        """Test job skill extraction prompt generation."""
        service = SkillExtractionService()
        job_description = "Looking for Python developer"
        job_title = "Senior Developer"

        prompt = service._create_job_skill_extraction_prompt(job_description, job_title)

        assert job_title in prompt
        assert job_description in prompt
        assert "required_skills" in prompt
        assert "preferred_skills" in prompt

    def test_skill_gap_analysis_prompt(self):
        """Test skill gap analysis prompt generation."""
        service = SkillExtractionService()
        resume_text = "Python developer"
        job_description = "Looking for developer"
        job_title = "Developer"

        prompt = service._create_skill_gap_analysis_prompt(
            resume_text, job_description, job_title
        )

        assert job_title in prompt
        assert resume_text in prompt
        assert job_description in prompt
        assert "skill_gaps" in prompt
        assert "learning_recommendations" in prompt
