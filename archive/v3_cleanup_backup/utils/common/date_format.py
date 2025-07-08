"""
Date Format Utility for Core Banking System

This module provides standardized date handling across the application,
ensuring consistent formats for storing, displaying, and processing dates.
"""

import datetime
import pytz
from dateutil import parser
from typing import Optional, Union, Dict, Any

# Define standard date and time formats
DATE_FORMATS = {
    "iso": "%Y-%m-%d",  # ISO 8601 date format: 2025-05-13
    "iso_time": "%Y-%m-%dT%H:%M:%S",  # ISO 8601 datetime without timezone: 2025-05-13T14:30:45
    "iso_full": "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds and Z suffix: 2025-05-13T14:30:45.123456Z
    "display": "%d-%b-%Y",  # Human-readable date: 13-May-2025
    "display_time": "%d-%b-%Y %H:%M:%S",  # Human-readable datetime: 13-May-2025 14:30:45
    "display_short": "%d/%m/%Y",  # Short display format: 13/05/2025
    "display_time_short": "%d/%m/%Y %H:%M",  # Short datetime: 13/05/2025 14:30
    "db": "%Y-%m-%d %H:%M:%S",  # Database format: 2025-05-13 14:30:45
    "filename": "%Y%m%d_%H%M%S",  # For filenames: 20250513_143045
    "human": "%a, %d %b %Y",  # Day, DD Mon YYYY: Wed, 13 May 2025
    "human_time": "%a, %d %b %Y %H:%M:%S",  # Day, DD Mon YYYY HH:MM:SS: Wed, 13 May 2025 14:30:45
    "report": "%B %d, %Y",  # Month DD, YYYY: May 13, 2025
    "report_time": "%B %d, %Y at %H:%M:%S",  # Month DD, YYYY at HH:MM:SS: May 13, 2025 at 14:30:45
    "log": "%Y-%m-%d %H:%M:%S.%f",  # For logging with microseconds: 2025-05-13 14:30:45.123456
    "api": "%Y-%m-%dT%H:%M:%S.%fZ"  # Standard REST API format: 2025-05-13T14:30:45.123456Z
}

# Default timezone settings
DEFAULT_TIMEZONE = pytz.timezone("Asia/Kolkata")  # IST for Indian banking system
UTC = pytz.UTC

# Environment-specific format overrides (if needed)
try:
    from app.config.environment import is_production, is_development, is_test
    
    # Example: Use different date displays in different environments
    if is_development() or is_test():
        # Add environment indicator for non-production
        DATE_FORMATS["display"] = "%d-%b-%Y [DEV]" if is_development() else "%d-%b-%Y [TEST]"
except ImportError:
    # No specific overrides if environment module isn't available
    pass


def now(tz=None) -> datetime.datetime:
    """
    Get the current datetime with the specified timezone.
    
    Args:
        tz: Timezone (defaults to DEFAULT_TIMEZONE)
    
    Returns:
        Current datetime with timezone
    """
    tz = tz or DEFAULT_TIMEZONE
    return datetime.datetime.now(tz)


def utc_now() -> datetime.datetime:
    """
    Get the current UTC datetime.
    
    Returns:
        Current UTC datetime
    """
    return datetime.datetime.now(UTC)


def parse_date(date_str: str, default_tz=None) -> Optional[datetime.datetime]:
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str: String representation of a date/time
        default_tz: Timezone to apply if not specified in the string
    
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        # Parse the date string using dateutil parser
        dt = parser.parse(date_str)
        
        # Add timezone if not already present
        if dt.tzinfo is None and default_tz is not None:
            tz = default_tz if not isinstance(default_tz, str) else pytz.timezone(default_tz)
            dt = dt.replace(tzinfo=tz)
        
        return dt
    except (ValueError, TypeError) as e:
        print(f"Error parsing date '{date_str}': {str(e)}")
        return None


def format_date(dt: Union[datetime.datetime, datetime.date, str], 
                fmt: str = "display", tz=None) -> str:
    """
    Format a datetime object or string as a formatted string.
    
    Args:
        dt: Datetime object or string to format
        fmt: Format to use (key from DATE_FORMATS or strftime format string)
        tz: Timezone to convert to before formatting
    
    Returns:
        Formatted date string
    """
    # Parse the date if it's a string
    if isinstance(dt, str):
        dt = parse_date(dt)
        if dt is None:
            return ""
    
    # Get the format string
    format_str = DATE_FORMATS.get(fmt, fmt)
    
    # Convert timezone if specified and it's a datetime
    if tz is not None and hasattr(dt, 'astimezone'):
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
        dt = dt.astimezone(tz)
    
    # Format the date
    return dt.strftime(format_str)


def to_iso_format(dt: Union[datetime.datetime, datetime.date, str], with_tz: bool = True) -> str:
    """
    Convert a datetime to ISO 8601 format.
    
    Args:
        dt: Datetime object or string to format
        with_tz: Whether to include timezone info
    
    Returns:
        Formatted ISO date string
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
        if dt is None:
            return ""
    
    if with_tz and hasattr(dt, 'astimezone'):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEFAULT_TIMEZONE)
        return dt.isoformat()
    
    if hasattr(dt, 'strftime'):
        return dt.strftime(DATE_FORMATS["iso_time"])
    
    return ""


def to_db_format(dt: Union[datetime.datetime, datetime.date, str]) -> str:
    """
    Format a datetime for database storage.
    
    Args:
        dt: Datetime object or string to format
    
    Returns:
        Database-formatted date string
    """
    return format_date(dt, fmt="db")


def to_display_format(dt: Union[datetime.datetime, datetime.date, str], 
                      include_time: bool = False) -> str:
    """
    Format a datetime for user display.
    
    Args:
        dt: Datetime object or string to format
        include_time: Whether to include time information
    
    Returns:
        Display-formatted date string
    """
    fmt = "display_time" if include_time else "display"
    return format_date(dt, fmt=fmt)


def to_api_format(dt: Union[datetime.datetime, datetime.date, str]) -> str:
    """
    Format a datetime for API response.
    
    Args:
        dt: Datetime object or string to format
    
    Returns:
        API-formatted date string (ISO with Z)
    """
    return format_date(dt, fmt="api")


def from_timestamp(timestamp: int) -> datetime.datetime:
    """
    Convert a UNIX timestamp to a datetime object.
    
    Args:
        timestamp: UNIX timestamp (seconds since epoch)
    
    Returns:
        Datetime object
    """
    return datetime.datetime.fromtimestamp(timestamp, tz=UTC)


def to_timestamp(dt: Union[datetime.datetime, datetime.date, str]) -> int:
    """
    Convert a datetime to a UNIX timestamp.
    
    Args:
        dt: Datetime object or string
    
    Returns:
        UNIX timestamp (seconds since epoch)
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
        if dt is None:
            return 0
    
    if not hasattr(dt, 'timestamp'):
        # Convert date to datetime
        dt = datetime.datetime.combine(dt, datetime.time.min)
    
    # Ensure timezone is set
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    
    return int(dt.timestamp())


def date_diff_days(date1: Union[datetime.datetime, datetime.date, str],
                   date2: Union[datetime.datetime, datetime.date, str]) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        date1: First date
        date2: Second date
    
    Returns:
        Number of days between dates (absolute value)
    """
    # Parse dates if they're strings
    if isinstance(date1, str):
        date1 = parse_date(date1)
    if isinstance(date2, str):
        date2 = parse_date(date2)
    
    # Return 0 if either date is None
    if date1 is None or date2 is None:
        return 0
    
    # Convert to date objects if they're datetimes
    if hasattr(date1, 'date'):
        date1 = date1.date()
    if hasattr(date2, 'date'):
        date2 = date2.date()
    
    # Calculate absolute difference
    return abs((date2 - date1).days)


def is_same_day(date1: Union[datetime.datetime, datetime.date, str],
                date2: Union[datetime.datetime, datetime.date, str]) -> bool:
    """
    Check if two dates are on the same day.
    
    Args:
        date1: First date
        date2: Second date
    
    Returns:
        True if dates are on the same day
    """
    # Parse dates if they're strings
    if isinstance(date1, str):
        date1 = parse_date(date1)
    if isinstance(date2, str):
        date2 = parse_date(date2)
    
    # Return False if either date is None
    if date1 is None or date2 is None:
        return False
    
    # Convert to date objects if they're datetimes
    if hasattr(date1, 'date'):
        date1 = date1.date()
    if hasattr(date2, 'date'):
        date2 = date2.date()
    
    # Compare dates
    return date1 == date2


def get_month_start_end(year: int, month: int) -> tuple:
    """
    Get the start and end dates for a specific month.
    
    Args:
        year: Year
        month: Month (1-12)
    
    Returns:
        Tuple of (start_date, end_date)
    """
    # Validate input
    if not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12")
    
    # Get first day of month
    start_date = datetime.date(year, month, 1)
    
    # Get first day of next month, then subtract one day
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    return (start_date, end_date)
