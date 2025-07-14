import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from app.main import app
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.models.match_score import MatchScore
from app.api.routes_auth import get_current_user
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture
def fake_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="hashed")


@pytest.fixture(autouse=True)
def override_get_current_user(fake_user):
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    app.dependency_overrides.clear()


def auth_headers():
    """Helper function to create auth headers for testing."""
    return {"Authorization": "Bearer test-token"}


class TestStatusSummary:
    """Tests for GET /analytics/status-summary"""

    def test_get_status_summary_success(self, fake_user):
        mock_db = MagicMock()

        # ---- dependency override ----
        def _override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db
        # --------------------------------

        # Mock query chain - now returns job statuses
        mock_results = [
            (JobStatus.applied, 5),
            (JobStatus.matched, 2),
            (JobStatus.saved, 1),
            (JobStatus.rejected, 3),
        ]
        (
            mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value
        ) = mock_results

        resp = client.get("/api/v1/analytics/status-summary", headers=auth_headers())
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["total_jobs"] == 11

        # Clear override
        app.dependency_overrides.clear()

    def test_get_status_summary_no_applications(self, fake_user):
        mock_db = MagicMock()

        def _override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db

        (
            mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value
        ) = []

        resp = client.get("/api/v1/analytics/status-summary", headers=auth_headers())
        assert resp.status_code == 200
        assert resp.json()["total_jobs"] == 0
        app.dependency_overrides.clear()


class TestApplicationsOverTime:
    """Test cases for GET /analytics/applications-over-time endpoint."""

    def test_get_applications_over_time_weekly(self, fake_user):
        """Test successful retrieval of weekly applications over time"""
        with patch("app.api.routes_analytics.get_db") as mock_get_db:
            mock_db = MagicMock()

            def _get_db():
                yield mock_db

            mock_get_db.side_effect = _get_db

            # Mock query results
            mock_results = [
                (2024, 1, 3),
                (2024, 2, 5),
                (2024, 3, 2),
            ]

            # Set up the mock chain properly
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_group_by = MagicMock()
            mock_order_by = MagicMock()
            mock_all = MagicMock()

            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_filter
            mock_filter.group_by.return_value = mock_group_by
            mock_group_by.order_by.return_value = mock_order_by
            mock_order_by.all.return_value = mock_results

            response = client.get(
                "/api/v1/analytics/applications-over-time?period=weekly",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period"] == "weekly"
            assert "applications_over_time" in data

    def test_get_applications_over_time_monthly(self, fake_user):
        """Test successful retrieval of monthly applications over time"""
        with patch("app.api.routes_analytics.get_db") as mock_get_db:
            mock_db = MagicMock()

            def _get_db():
                yield mock_db

            mock_get_db.side_effect = _get_db

            # Mock query results
            mock_results = [
                (2024, 1, 10),
                (2024, 2, 15),
                (2024, 3, 8),
            ]

            # Set up the mock chain properly
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_group_by = MagicMock()
            mock_order_by = MagicMock()
            mock_all = MagicMock()

            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_filter
            mock_filter.group_by.return_value = mock_group_by
            mock_group_by.order_by.return_value = mock_order_by
            mock_order_by.all.return_value = mock_results

            response = client.get(
                "/api/v1/analytics/applications-over-time?period=monthly",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period"] == "monthly"
            assert "applications_over_time" in data

    def test_get_applications_over_time_invalid_period(self, fake_user):
        """Test with invalid period parameter"""
        response = client.get(
            "/api/v1/analytics/applications-over-time?period=invalid",
            headers=auth_headers(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Period must be either 'weekly' or 'monthly'" in data["detail"]


class TestMatchScoreSummary:
    """Tests for GET /analytics/match-score-summary"""

    def test_get_match_score_summary_success(self, fake_user):
        mock_db = MagicMock()

        def _override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db

        stats = MagicMock(
            average_score=0.75, min_score=0.45, max_score=0.95, total_scores=10
        )
        distribution = [("excellent", 3), ("good", 4), ("fair", 2), ("poor", 1)]

        call_no = {"n": 0}

        def _query_side_effect(*args, **kwargs):
            call_no["n"] += 1
            base = MagicMock()
            joined = base.join.return_value
            filtered = joined.filter.return_value
            if call_no["n"] == 1:
                filtered.first.return_value = stats
            else:
                filtered.group_by.return_value.all.return_value = distribution
            return base

        mock_db.query.side_effect = _query_side_effect

        resp = client.get(
            "/api/v1/analytics/match-score-summary", headers=auth_headers()
        )
        data = resp.json()
        assert resp.status_code == 200
        assert data["average_score"] == 0.75
        assert data["total_scores"] == 10
        app.dependency_overrides.clear()

    def test_get_match_score_summary_no_scores(self, fake_user):
        mock_db = MagicMock()

        def _override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = _override_get_db

        empty_stats = MagicMock(
            average_score=None, min_score=None, max_score=None, total_scores=0
        )

        def _query_side_effect(*args, **kwargs):
            base = MagicMock()
            joined = base.join.return_value
            filtered = joined.filter.return_value
            if not hasattr(_query_side_effect, "called"):
                _query_side_effect.called = True
                filtered.first.return_value = empty_stats
            else:
                filtered.group_by.return_value.all.return_value = []
            return base

        mock_db.query.side_effect = _query_side_effect

        resp = client.get(
            "/api/v1/analytics/match-score-summary", headers=auth_headers()
        )
        data = resp.json()
        assert resp.status_code == 200
        assert data["average_score"] == 0.0
        assert data["total_scores"] == 0
        app.dependency_overrides.clear()


class TestAuthentication:
    """Test authentication requirements."""

    def test_status_summary_no_auth(self):
        """Test that status summary endpoint requires authentication"""
        # Clear dependency overrides for this test
        app.dependency_overrides.clear()

        response = client.get("/api/v1/analytics/status-summary")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_applications_over_time_no_auth(self):
        """Test that applications over time endpoint requires authentication"""
        # Clear dependency overrides for this test
        app.dependency_overrides.clear()

        response = client.get("/api/v1/analytics/applications-over-time")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_match_score_summary_no_auth(self):
        """Test that match score summary endpoint requires authentication"""
        # Clear dependency overrides for this test
        app.dependency_overrides.clear()

        response = client.get("/api/v1/analytics/match-score-summary")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
