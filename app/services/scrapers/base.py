"""Base classes and contracts for job board scrapers."""

from __future__ import annotations

import abc
from typing import List

from .models import JobPosting


class JobBoardScraper(abc.ABC):
    """Abstract base class for all job board scrapers."""

    name: str = "unknown"

    @abc.abstractmethod
    def search(
        self,
        keyword: str,
        location: str = "",
        *,
        limit: int = 20,
    ) -> List[JobPosting]:
        """Return up to *limit* job postings matching *keyword* and *location*."""

    def __repr__(self) -> str:  # noqa: D401
        return f"<{self.__class__.__name__} name={self.name!r}>"
