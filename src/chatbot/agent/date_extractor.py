from __future__ import annotations

from typing import Optional
from dateutil import parser
from datetime import datetime


def extract_datetime(text: str) -> Optional[str]:
    """Parse natural-ish date/time expressions into ISO-like string.

    This is a lightweight helper leveraging dateutil.parser. It won't
    understand very complex phrases but covers common cases like
    'tomorrow 3pm', 'next monday 10', '25 Dec 2pm', etc.
    Returns an ISO-like string or None if parsing fails.
    """
    try:
        dt = parser.parse(text, fuzzy=True)
        return dt.isoformat()
    except Exception:
        return None


def extract_date_ymd(text: str) -> Optional[str]:
    """Parse date-like text and return YYYY-MM-DD if possible."""
    try:
        dt = parser.parse(text, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


 