"""Domain models used by the crawler."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class JobPosting:
    """Immutable data holder for a single job posting."""

    title: str
    description: str
    location: str
    company: str
    url: str
    posted_at: Optional[_dt.date] = None  # Publication date if available
    salary: Optional[str] = None  # Raw salary text if scraped

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict representation, useful for JSON serialization."""
        return asdict(self)

    def __str__(self) -> str:  # noqa: DunderStr
        """Human-readable string representation (single line)."""
        posted = self.posted_at.isoformat() if self.posted_at else "N/A"
        return f"{self.title} @ {self.company} ({self.location}) | Posted: {posted} | {self.url}"
