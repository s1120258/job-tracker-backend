"""
Unit tests for intelligent job matching service.
Tests RAG-powered job analysis and market intelligence features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

from app.services.intelligent_matching_service import (
    IntelligentMatchingService,
    IntelligentMatchingServiceError
)

class TestIntelligentMatchingService:
    """Test suite for RAG-powered job analysis."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = IntelligentMatchingService()
        self.mock_job_id = uuid4()
        self.mock_user_id = uuid4()
        
        # Mock job data
        self.mock_job = {
            "id": str(self.mock_job_id),
            "title": "Senior Python Developer",
            "company": "Tech Innovations Inc",
            "description": "We seek a senior Python developer with FastAPI and PostgreSQL experience",
            "location": "San Francisco, CA",
            "url": "https://example.com/job"
        }
        
        # Mock resume data
        self.mock_resume = {
            "id": str(uuid4()),
            "extracted_text": "Experienced Python developer with 5 years experience in web development using Django and FastAPI",
            "embedding": [0.1] * 1536  # Mock 1536-dimensional embedding
        }
        
        # Mock similar jobs data
        self.mock_similar_jobs = [
            {
                "id": str(uuid4()),
                "title": "Python Software Engineer",
                "company": "StartupCorp",
                "description": "Python, FastAPI, REST APIs, PostgreSQL",
                "location": "San Francisco, CA",
                "similarity_score": 0.85
            },
            {
                "id": str(uuid4()),
                "title": "Backend Developer",
                "company": "BigTech Inc",
                "description": "Python, Django, database design, API development",
                "location": "Palo Alto, CA", 
                "similarity_score": 0.78
            }
        ]
    
    @patch('app.services.intelligent_matching_service.get_job')
    @patch('app.services.intelligent_matching_service.get_resume_by_user')
    def test_get_job_and_resume_data(self, mock_get_resume, mock_get_job):
        """Test retrieval of job and resume data."""
        # Setup mocks
        mock_job_obj = Mock()
        mock_job_obj.id = self.mock_job_id
        mock_job_obj.user_id = self.mock_user_id
        mock_job_obj.title = self.mock_job["title"]
        mock_job_obj.company = self.mock_job["company"]
        mock_job_obj.description = self.mock_job["description"]
        mock_job_obj.location = self.mock_job["location"]
        mock_job_obj.url = self.mock_job["url"]
        
        mock_resume_obj = Mock()
        mock_resume_obj.id = UUID(self.mock_resume["id"])
        mock_resume_obj.extracted_text = self.mock_resume["extracted_text"]
        mock_resume_obj.embedding = self.mock_resume["embedding"]
        
        mock_get_job.return_value = mock_job_obj
        mock_get_resume.return_value = mock_resume_obj
        
        # Test job retrieval
        job_data = self.service._get_job_by_id(Mock(), self.mock_job_id, self.mock_user_id)
        assert job_data["title"] == self.mock_job["title"]
        assert job_data["company"] == self.mock_job["company"]
        
        # Test resume retrieval
        resume_data = self.service._get_user_resume(Mock(), self.mock_user_id)
        assert resume_data["extracted_text"] == self.mock_resume["extracted_text"]
        assert resume_data["embedding"] == self.mock_resume["embedding"]
    
    @patch('app.services.intelligent_matching_service.embedding_service')
    def test_retrieve_similar_jobs(self, mock_embedding_service):
        """Test similar jobs retrieval using pgVector."""
        # Setup mocks
        mock_embedding_service.generate_embedding.return_value = [0.1] * 1536
        
        # Mock database session and query results
        mock_db = Mock()
        mock_result = Mock()
        
        # Create mock rows
        mock_rows = []
        for job in self.mock_similar_jobs:
            mock_row = Mock()
            mock_row.id = UUID(job["id"])
            mock_row.title = job["title"]
            mock_row.company = job["company"]
            mock_row.description = job["description"]
            mock_row.location = job["location"]
            mock_row.similarity_score = job["similarity_score"]
            mock_rows.append(mock_row)
        
        mock_result.__iter__ = Mock(return_value=iter(mock_rows))
        mock_db.execute.return_value = mock_result
        
        # Test similar jobs retrieval
        result = self.service._retrieve_similar_jobs(
            mock_db, "Python developer position", 5, self.mock_job_id
        )
        
        assert len(result) == 2
        assert result[0]["title"] == "Python Software Engineer"
        assert result[0]["similarity_score"] == 0.85
        assert result[1]["similarity_score"] == 0.78
        
        # Verify embedding service was called
        mock_embedding_service.generate_embedding.assert_called_once_with("Python developer position")
    
    @patch('app.services.intelligent_matching_service.llm_service')
    def test_market_trends_analysis(self, mock_llm_service):
        """Test market trend extraction from similar jobs."""
        # Setup LLM mock response
        mock_llm_service.generate_feedback.return_value = [
            "Market Analysis: This is a premium position in high-demand market. "
            "Python and FastAPI skills are trending. Strong demand for backend developers."
        ]
        
        # Test market trends analysis
        result = self.service._analyze_market_trends(
            self.mock_job, self.mock_similar_jobs
        )
        
        assert result["similar_jobs_analyzed"] == 2
        assert result["average_similarity_score"] == pytest.approx(0.815)  # (0.85 + 0.78) / 2
        assert "market_positioning" in result
        assert "demand_assessment" in result
        assert "skill_trend_analysis" in result
        
        # Verify LLM service was called
        mock_llm_service.generate_feedback.assert_called_once()
    
    def test_build_market_context(self):
        """Test market context string building."""
        context = self.service._build_market_context(self.mock_similar_jobs)
        
        assert "Python Software Engineer" in context
        assert "StartupCorp" in context
        assert "similarity: 0.85" in context
        assert "Backend Developer" in context
        assert "BigTech Inc" in context
        assert "similarity: 0.78" in context
    
    def test_parse_market_analysis(self):
        """Test parsing of LLM market analysis response."""
        analysis_text = """
        Market Analysis Results:
        1. This is a premium market position with high-end requirements
        2. Strong demand for Python developers in this segment
        3. Key skills trending: Python, FastAPI, API development
        4. High demand market with competitive opportunities
        """
        
        result = self.service._parse_market_analysis(analysis_text)
        
        assert "premium" in result["market_positioning"].lower()
        assert "high" in result["demand_assessment"].lower()
        assert isinstance(result["skill_trend_analysis"], list)
    
    @patch('app.services.intelligent_matching_service.llm_service')
    def test_strategic_analysis_generation(self, mock_llm_service):
        """Test generation of strategic recommendations."""
        mock_llm_service.generate_feedback.return_value = [
            "Strategic Recommendations:\n"
            "1. Emphasize your FastAPI experience in application\n"
            "2. Highlight Python expertise and years of experience\n"
            "3. Address any gaps in PostgreSQL experience\n"
            "Competitive Advantages:\n"
            "- 5 years Python experience\n"
            "- FastAPI framework knowledge"
        ]
        
        market_intel = {
            "market_positioning": "Standard market position",
            "demand_assessment": "High market demand",
            "skill_trend_analysis": ["Python", "FastAPI", "PostgreSQL"]
        }
        
        result = self.service._generate_strategic_analysis(
            self.mock_job, self.mock_resume, market_intel
        )
        
        assert "strategic_recommendations" in result
        assert "competitive_advantages" in result
        assert "improvement_suggestions" in result
        
        # Verify LLM service was called
        mock_llm_service.generate_feedback.assert_called_once()
    
    def test_parse_strategic_recommendations(self):
        """Test parsing of strategic recommendations."""
        analysis_text = """
        Strategic Positioning:
        1. Emphasize FastAPI experience early in application
        2. Highlight full-stack capabilities
        
        Competitive Advantages:
        - 5+ years Python experience
        - FastAPI framework expertise
        
        Areas for Improvement:
        - Consider PostgreSQL certification
        - Build cloud deployment portfolio
        """
        
        result = self.service._parse_strategic_recommendations(analysis_text)
        
        assert len(result["strategic_recommendations"]) >= 1
        assert len(result["competitive_advantages"]) >= 1
        assert len(result["improvement_suggestions"]) >= 1
        
        # Check recommendation structure
        if result["strategic_recommendations"]:
            rec = result["strategic_recommendations"][0]
            assert "category" in rec
            assert "recommendation" in rec
            assert "priority" in rec
    
    @patch('app.services.intelligent_matching_service.similarity_service')
    @patch('app.services.intelligent_matching_service.embedding_service')
    def test_calculate_basic_match_score(self, mock_embedding_service, mock_similarity_service):
        """Test basic match score calculation."""
        # Setup mocks
        mock_embedding_service.generate_embedding.return_value = [0.2] * 1536
        mock_similarity_service.calculate_similarity_score.return_value = 0.76
        
        result = self.service._calculate_basic_match_score(
            self.mock_resume, self.mock_job
        )
        
        assert result == 0.76
        
        # Verify services were called
        mock_embedding_service.generate_embedding.assert_called_once()
        mock_similarity_service.calculate_similarity_score.assert_called_once()
    
    def test_compile_analysis_result(self):
        """Test compilation of comprehensive analysis result."""
        market_intel = {
            "similar_jobs_analyzed": 2,
            "average_similarity_score": 0.815,
            "market_positioning": "Standard market position"
        }
        
        strategic_analysis = {
            "strategic_recommendations": [
                {"category": "Strategic", "recommendation": "Test rec", "priority": "High"}
            ],
            "competitive_advantages": ["Test advantage"],
            "improvement_suggestions": ["Test improvement"]
        }
        
        result = self.service._compile_analysis_result(
            self.mock_job, 0.78, market_intel, strategic_analysis
        )
        
        assert result["basic_match_score"] == 0.78
        assert result["market_intelligence"] == market_intel
        assert result["job_title"] == self.mock_job["title"]
        assert result["company_name"] == self.mock_job["company"]
        assert len(result["strategic_recommendations"]) == 1
        assert len(result["competitive_advantages"]) == 1
        assert len(result["improvement_suggestions"]) == 1
    
    @patch('app.services.intelligent_matching_service.get_job')
    def test_job_not_found_error(self, mock_get_job):
        """Test error handling when job is not found."""
        mock_get_job.return_value = None
        
        with pytest.raises(IntelligentMatchingServiceError, match="Job not found"):
            self.service._get_job_by_id(Mock(), self.mock_job_id, self.mock_user_id)
    
    @patch('app.services.intelligent_matching_service.get_job')
    def test_job_access_denied_error(self, mock_get_job):
        """Test error handling when user doesn't own the job."""
        mock_job_obj = Mock()
        mock_job_obj.user_id = uuid4()  # Different user ID
        mock_get_job.return_value = mock_job_obj
        
        with pytest.raises(IntelligentMatchingServiceError, match="Job access denied"):
            self.service._get_job_by_id(Mock(), self.mock_job_id, self.mock_user_id)
    
    @patch('app.services.intelligent_matching_service.get_resume_by_user')
    def test_resume_not_found_error(self, mock_get_resume):
        """Test error handling when resume is not found."""
        mock_get_resume.return_value = None
        
        with pytest.raises(IntelligentMatchingServiceError, match="Resume not found"):
            self.service._get_user_resume(Mock(), self.mock_user_id)

class TestIntelligentMatchingAPI:
    """Test suite for intelligent matching API endpoints."""
    
    def setup_method(self):
        """Setup test fixtures for API tests."""
        self.mock_job_id = uuid4()
        self.mock_user_id = uuid4()
        
        # Mock analysis result
        self.mock_analysis_result = {
            "basic_match_score": 0.78,
            "market_intelligence": {
                "similar_jobs_analyzed": 3,
                "average_similarity_score": 0.75,
                "market_positioning": "Standard market position",
                "salary_range_insight": "Competitive salary range",
                "skill_trend_analysis": ["Python", "FastAPI"],
                "demand_assessment": "High market demand"
            },
            "strategic_recommendations": [
                {
                    "category": "Strategic",
                    "recommendation": "Emphasize FastAPI experience",
                    "priority": "High"
                }
            ],
            "competitive_advantages": ["5+ years Python experience"],
            "improvement_suggestions": ["Consider cloud certification"],
            "job_title": "Senior Python Developer",
            "company_name": "Tech Corp",
            "analysis_summary": "Analyzed 3 similar positions"
        }
    
    @patch('app.api.routes_intelligent_matching.intelligent_matching_service')
    @patch('app.api.routes_intelligent_matching.get_current_user')
    def test_get_intelligent_job_analysis_success(self, mock_get_user, mock_service):
        """Test successful intelligent job analysis API call."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Setup mocks
        mock_user = Mock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        mock_service.analyze_job_with_market_context.return_value = self.mock_analysis_result
        
        # Create test client with dependency overrides
        client = TestClient(app)
        
        # Override auth dependency
        from app.api.routes_auth import get_current_user
        from app.db.session import get_db
        
        def override_get_current_user():
            return mock_user
        
        def override_get_db():
            return Mock()
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # Make API call
            response = client.get(
                f"/jobs/{self.mock_job_id}/intelligent-analysis?include_market_context=true&context_depth=5"
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["job_id"] == str(self.mock_job_id)
            assert data["basic_match_score"] == 0.78
            assert data["market_intelligence"]["similar_jobs_analyzed"] == 3
            assert len(data["strategic_recommendations"]) == 1
            assert data["job_title"] == "Senior Python Developer"
            
            # Verify service was called correctly
            mock_service.analyze_job_with_market_context.assert_called_once_with(
                job_id=self.mock_job_id,
                user_id=self.mock_user_id,
                db=mock_service.analyze_job_with_market_context.call_args[1]['db'],
                context_depth=5
            )
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
    
    @patch('app.api.routes_intelligent_matching.intelligent_matching_service')
    @patch('app.api.routes_intelligent_matching.get_current_user')
    def test_get_market_intelligence_only_success(self, mock_get_user, mock_service):
        """Test market intelligence only endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Setup mocks
        mock_user = Mock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        mock_service.analyze_job_with_market_context.return_value = self.mock_analysis_result
        
        client = TestClient(app)
        
        # Override dependencies
        from app.api.routes_auth import get_current_user
        from app.db.session import get_db
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()
        
        try:
            # Make API call
            response = client.get(f"/jobs/{self.mock_job_id}/market-intelligence?context_depth=3")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["job_id"] == str(self.mock_job_id)
            assert data["context_depth"] == 3
            assert "market_intelligence" in data
            assert data["market_intelligence"]["similar_jobs_analyzed"] == 3
            
        finally:
            app.dependency_overrides.clear()
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        response = client.get("/health/intelligent-matching")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "intelligent_matching"
        assert data["status"] == "healthy"
        assert "features" in data
        assert data["features"]["rag_analysis"] is True
    
    @patch('app.api.routes_intelligent_matching.intelligent_matching_service')
    @patch('app.api.routes_intelligent_matching.get_current_user')
    def test_job_not_found_error(self, mock_get_user, mock_service):
        """Test API error handling when job is not found."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.services.intelligent_matching_service import IntelligentMatchingServiceError
        
        # Setup mocks
        mock_user = Mock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        mock_service.analyze_job_with_market_context.side_effect = IntelligentMatchingServiceError("Job not found")
        
        client = TestClient(app)
        
        # Override dependencies
        from app.api.routes_auth import get_current_user
        from app.db.session import get_db
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()
        
        try:
            # Make API call
            response = client.get(f"/jobs/{self.mock_job_id}/intelligent-analysis")
            
            # Verify error response
            assert response.status_code == 404
            assert "Job not found" in response.json()["detail"]
            
        finally:
            app.dependency_overrides.clear()
    
    def test_invalid_context_depth_parameter(self):
        """Test validation of context_depth parameter."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Override auth to avoid authentication issues
        from app.api.routes_auth import get_current_user
        from app.db.session import get_db
        
        mock_user = Mock()
        mock_user.id = self.mock_user_id
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()
        
        try:
            # Test invalid context_depth (too high)
            response = client.get(f"/jobs/{self.mock_job_id}/intelligent-analysis?context_depth=15")
            
            assert response.status_code == 422  # Validation error
            
            # Test invalid context_depth (too low)
            response = client.get(f"/jobs/{self.mock_job_id}/intelligent-analysis?context_depth=0")
            
            assert response.status_code == 422  # Validation error
            
        finally:
            app.dependency_overrides.clear()
