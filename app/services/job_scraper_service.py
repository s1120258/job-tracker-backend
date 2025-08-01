"""Job scraper service for managing different job board scrapers."""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from .scrapers.base import JobBoardScraper
from .scrapers.models import JobPosting
from .scrapers.remoteok import RemoteOKScraper

logger = logging.getLogger(__name__)


class JobBoardType(str, Enum):
    """Available job board types."""

    REMOTEOK = "remoteok"
    # Add more job boards here as they are implemented
    # INDEED = "indeed"
    # LINKEDIN = "linkedin"


class JobScraperService:
    """Service for coordinating job searches across multiple job boards."""

    def __init__(self):
        """Initialize the scraper service with available scrapers."""
        self._scrapers: Dict[JobBoardType, JobBoardScraper] = {
            JobBoardType.REMOTEOK: RemoteOKScraper(),
        }

    def get_available_sources(self) -> List[str]:
        """Get list of available job board sources."""
        return [source.value for source in JobBoardType]

    def search_jobs(
        self,
        keyword: str,
        location: str = "",
        source: Optional[str] = None,
        limit: int = 20,
        fetch_full_description: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs across specified or all available job boards.

        Args:
            keyword: Search keyword
            location: Job location (may be ignored by some sources like RemoteOK)
            source: Specific job board to search (if None, searches all available)
            limit: Maximum number of jobs to return per source
            fetch_full_description: Whether to fetch full job descriptions

        Returns:
            List of job postings as dictionaries
        """
        all_jobs: List[Dict[str, Any]] = []

        # Determine which scrapers to use
        if source:
            try:
                source_enum = JobBoardType(source.lower())
                scrapers_to_use = {source_enum: self._scrapers[source_enum]}
            except (ValueError, KeyError):
                logger.warning("Unknown job board source: %s", source)
                return []
        else:
            scrapers_to_use = self._scrapers

        # Search each selected job board
        for board_type, scraper in scrapers_to_use.items():
            try:
                logger.info("Searching %s for keyword: %s", scraper.name, keyword)

                # Handle RemoteOK specific parameters
                if isinstance(scraper, RemoteOKScraper):
                    jobs = scraper.search(
                        keyword=keyword,
                        location=location,
                        limit=limit,
                        fetch_full_description=fetch_full_description,
                    )
                else:
                    # For other scrapers that don't support fetch_full_description
                    jobs = scraper.search(
                        keyword=keyword,
                        location=location,
                        limit=limit,
                    )

                # Convert JobPosting objects to dictionaries with source info
                for job in jobs:
                    job_dict = job.to_dict()
                    job_dict["source"] = scraper.name
                    job_dict["board_type"] = board_type.value
                    all_jobs.append(job_dict)

                logger.info("Found %d jobs from %s", len(jobs), scraper.name)

            except Exception as e:
                logger.error("Error searching %s: %s", scraper.name, e)
                # Continue with other scrapers even if one fails
                continue

        # Sort by posting date if available, newest first
        all_jobs.sort(key=lambda x: x.get("posted_at") or "", reverse=True)

        # Apply overall limit if searching multiple sources
        if not source and len(all_jobs) > limit:
            all_jobs = all_jobs[:limit]

        logger.info("Total jobs found across all sources: %d", len(all_jobs))
        return all_jobs

    def search_single_source(
        self,
        source: str,
        keyword: str,
        location: str = "",
        limit: int = 20,
    ) -> List[JobPosting]:
        """
        Search a specific job board and return JobPosting objects.

        Args:
            source: Job board source name
            keyword: Search keyword
            location: Job location
            limit: Maximum number of jobs to return

        Returns:
            List of JobPosting objects

        Raises:
            ValueError: If source is not available
        """
        try:
            source_enum = JobBoardType(source.lower())
            scraper = self._scrapers[source_enum]
        except (ValueError, KeyError):
            raise ValueError(f"Unknown job board source: {source}")

        return scraper.search(keyword=keyword, location=location, limit=limit)


# Singleton instance
job_scraper_service = JobScraperService()
