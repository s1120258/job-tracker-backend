"""Scraper implementation for RemoteOK API.

RemoteOK provides a free public API for remote job listings.
No authentication required.
API Documentation: https://remoteok.io/api
"""

from __future__ import annotations

import logging
import time
from typing import List

import requests
from bs4 import BeautifulSoup

from .models import JobPosting
from .base import JobBoardScraper

logger = logging.getLogger(__name__)


class RemoteOKScraper(JobBoardScraper):
    """Fetch remote job postings from RemoteOK API."""

    name: str = "RemoteOK"
    API_ENDPOINT: str = "https://remoteok.io/api"

    def __init__(self) -> None:
        self._session = requests.Session()
        # RemoteOK requires a User-Agent header
        self._session.headers.update(
            {
                "User-Agent": "res-match-crawler/1.0 (https://github.com/example/res-match-crawler)"
            }
        )

    def _fetch_full_description(self, job_url: str) -> str:
        """Fetch the full job description from the job detail page."""
        try:
            time.sleep(1)  # Be respectful to the server
            response = self._session.get(job_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for the job description in various possible selectors
            desc_selectors = [
                ".markdown",
                ".job-description",
                ".description",
                "[data-description]",
                ".content",
            ]

            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    # Clean up the text
                    description = desc_elem.get_text(separator="\n", strip=True)
                    if len(description) > 100:  # Make sure it's substantial
                        return description

            # Fallback: try to find any substantial text content
            main_content = soup.select_one("main") or soup.select_one("body")
            if main_content:
                # Remove navigation, header, footer elements
                for elem in main_content.select(
                    "nav, header, footer, .nav, .header, .footer"
                ):
                    elem.decompose()

                text = main_content.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text.split("\n") if line.strip()]

                # Find substantial content (likely the job description)
                substantial_lines = [line for line in lines if len(line) > 50]
                if substantial_lines:
                    return "\n".join(
                        substantial_lines[:20]
                    )  # Limit to first 20 substantial lines

            logger.warning("Could not extract full description from %s", job_url)
            return ""

        except Exception as e:
            logger.debug("Failed to fetch full description from %s: %s", job_url, e)
            return ""

    def search(
        self,
        keyword: str,
        location: str = "",
        *,
        limit: int = 20,
        fetch_full_description: bool = True,
    ) -> List[JobPosting]:
        """Search RemoteOK for remote jobs.

        Note: RemoteOK API returns all jobs, so we filter by keyword locally.
        The location parameter is ignored since all jobs are remote.

        Args:
            keyword: Search keyword
            location: Ignored (all jobs are remote)
            limit: Maximum number of jobs to return
            fetch_full_description: If True, fetch full descriptions from job pages
        """
        logger.info("RemoteOK API search for keyword: %s", keyword)

        try:
            # Add a small delay to be respectful to the API
            time.sleep(0.5)

            response = self._session.get(self.API_ENDPOINT, timeout=30)
            response.raise_for_status()
            data = response.json()

            # RemoteOK API returns a list where the first item is metadata
            # and the rest are job postings
            if not data or len(data) < 2:
                logger.warning("No jobs found in RemoteOK API response")
                return []

            # Skip the first item (metadata) and process job listings
            jobs_data = data[1:]  # Skip metadata
            logger.debug("Found %d total jobs from RemoteOK", len(jobs_data))

            postings: list[JobPosting] = []
            keyword_lower = keyword.lower()

            for job in jobs_data:
                if len(postings) >= limit:
                    break

                # Filter by keyword in title, description, or tags
                title = job.get("position", "")
                description = job.get("description", "")
                tags = " ".join(job.get("tags", []))

                # Check if keyword matches
                search_text = f"{title} {description} {tags}".lower()
                if keyword_lower not in search_text:
                    continue

                # Extract job information
                company = job.get("company", "")
                url = job.get("url", "")
                if url and not url.startswith("http"):
                    url = f"https://remoteok.io/remote-jobs/{job.get('id', '')}"

                # RemoteOK jobs are all remote by definition
                location_text = "Remote"
                if job.get("location"):
                    location_text = f"Remote ({job.get('location')})"

                # Fetch full description if requested
                full_description = description
                if fetch_full_description and url:
                    logger.info("Fetching full description for: %s", title)
                    full_desc = self._fetch_full_description(url)
                    if full_desc:
                        full_description = full_desc

                postings.append(
                    JobPosting(
                        title=title,
                        description=full_description,
                        location=location_text,
                        company=company,
                        url=url,
                    )
                )

            logger.info("Successfully filtered %d matching job postings", len(postings))
            return postings

        except requests.exceptions.RequestException as e:
            logger.error("RemoteOK API request failed: %s", e)
            raise
        except Exception as e:
            logger.error("Failed to parse RemoteOK API response: %s", e)
            raise
