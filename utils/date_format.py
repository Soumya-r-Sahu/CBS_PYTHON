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
    Get the current date and time in the specified timezone
    Defaults to the system's default timezone (IST)
    
    Args:
        tz: Timezone (default: system timezone)
        
    Returns:
        Current datetime with timezone info
    """
    if tz is None:
        tz = DEFAULT_TIMEZONE
        
    return datetime.datetime.now(tz)


def utc_now() -> datetime.datetime:
    """
    Get the current UTC date and time
    
    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.datetime.now(UTC)


def parse_date(date_str: str, default_tz=None) -> Optional[datetime.datetime]:
    """
    Parse a date string in various formats
    
    Args:
        date_str: Date string to parse
        default_tz: Default timezone to use if none in string
        
    Returns:
        Parsed datetime object or None if invalid
    """
    if not date_str:
        return None
        
    try:
        dt = parser.parse(date_str)
        
        # Add timezone if not present
        if dt.tzinfo is None and default_tz is not None:
            dt = dt.replace(tzinfo=default_tz)
            
        return dt
    except (ValueError, TypeError):
        return None


def format_date(dt: Union[datetime.datetime, datetime.date, str], 
                fmt: str = "display", tz=None) -> str:
    """
    Format a date or datetime object according to the specified format
    
    Args:
        dt: Date/datetime object or string to format
        fmt: Format name from DATE_FORMATS or a format string
        tz: Target timezone for the output
        
    Returns:
        Formatted date string
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
        
    if dt is None:
        return ""
        
    # Get the format string
    format_str = DATE_FORMATS.get(fmt, fmt)
    
    # Convert to target timezone if specified
    if isinstance(dt, datetime.datetime) and tz is not None and dt.tzinfo is not None:
        dt = dt.astimezone(tz)
    
    return dt.strftime(format_str)


def to_iso_format(dt: Union[datetime.datetime, datetime.date, str], with_tz: bool = True) -> str:
    """
    Convert a date or datetime to ISO 8601 format
    
    Args:
        dt: Date/datetime object or string
        with_tz: Whether to include timezone info
        
    Returns:
        ISO 8601 formatted date string
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
        
    if dt is None:
        return ""
        
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        return dt.isoformat()
        
    if with_tz and dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
        
    return dt.isoformat()


def to_db_format(dt: Union[datetime.datetime, datetime.date, str]) -> str:
    """
    Convert a date or datetime to database format
    
    Args:
        dt: Date/datetime object or string
        
    Returns:
        Database formatted date string
    """
    return format_date(dt, fmt="db")


def to_display_format(dt: Union[datetime.datetime, datetime.date, str], 
                      include_time: bool = False) -> str:
    """
    Convert a date or datetime to human-friendly display format
    
    Args:
        dt: Date/datetime object or string
        include_time: Whether to include time in the output
        
    Returns:
        Display formatted date string
    """
    fmt = "display_time" if include_time else "display"
    return format_date(dt, fmt=fmt)


def to_api_format(dt: Union[datetime.datetime, datetime.date, str]) -> str:
    """
    Convert a date or datetime to API format (ISO with Z)
    
    Args:
        dt: Date/datetime object or string
        
    Returns:
        API formatted date string
    """
    return format_date(dt, fmt="api")


def from_timestamp(timestamp: int) -> datetime.datetime:
    """
    Convert a Unix timestamp to datetime
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Datetime object
    """
    return datetime.datetime.fromtimestamp(timestamp, tz=UTC)


def to_timestamp(dt: Union[datetime.datetime, datetime.date, str]) -> int:
    """
    Convert a datetime to Unix timestamp
    
    Args:
        dt: Date/datetime object or string
        
    Returns:
        Unix timestamp
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
        
    if dt is None:
        return 0
        
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.combine(dt, datetime.time())
        
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
        
    return int(dt.timestamp())


def date_diff_days(date1: Union[datetime.datetime, datetime.date, str],
                   date2: Union[datetime.datetime, datetime.date, str]) -> int:
    """
    Calculate the difference in days between two dates
    
    Args:
        date1: First date
        date2: Second date
        
    Returns:
        Number of days between the dates
    """
    if isinstance(date1, str):
        date1 = parse_date(date1)
        
    if isinstance(date2, str):
        date2 = parse_date(date2)
        
    if date1 is None or date2 is None:
        return 0
        
    # Get just the date part
    if isinstance(date1, datetime.datetime):
        date1 = date1.date()
        
    if isinstance(date2, datetime.datetime):
        date2 = date2.date()
        
    return (date2 - date1).days


def is_same_day(date1: Union[datetime.datetime, datetime.date, str],
                date2: Union[datetime.datetime, datetime.date, str]) -> bool:
    """
    Check if two dates are the same day
    
    Args:
        date1: First date
        date2: Second date
        
    Returns:
        True if same day, False otherwise
    """
    if isinstance(date1, str):
        date1 = parse_date(date1)
        
    if isinstance(date2, str):
        date2 = parse_date(date2)
        
    if date1 is None or date2 is None:
        return False
        
    # Get just the date part
    if isinstance(date1, datetime.datetime):
        date1 = date1.date()
        
    if isinstance(date2, datetime.datetime):
        date2 = date2.date()
        
    return date1 == date2


def get_date_dict(dt: Union[datetime.datetime, datetime.date, str]) -> Dict[str, Any]:
    """
    Get a dictionary with multiple date format representations
    Useful for API responses that need multiple formats
    
    Args:
        dt: Date/datetime object or string
        
    Returns:
        Dictionary with various date formats
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
        
    if dt is None:
        return {
            "iso": "",
            "display": "",
            "timestamp": 0,
            "human": ""
        }
        
    return {
        "iso": to_iso_format(dt),
        "display": to_display_format(dt),
        "display_with_time": to_display_format(dt, include_time=True),
        "timestamp": to_timestamp(dt),
        "human": format_date(dt, "human")
    }


# Example usage
if __name__ == "__main__":
    print(f"Current time: {to_display_format(now(), include_time=True)}")
    print(f"ISO format: {to_iso_format(now())}")
    print(f"API format: {to_api_format(now())}")
    
    # Parse a date string
    test_date = "2025-05-13T14:30:45Z"
    parsed = parse_date(test_date)
    print(f"Parsed date: {to_display_format(parsed, include_time=True)}")
    
    # Calculate days between dates
    days = date_diff_days("2025-05-01", "2025-05-13")
    print(f"Days difference: {days}")
    
    # Get multiple formats
    formats = get_date_dict(now())
    print("Multiple formats:")
    for key, value in formats.items():
        print(f"  {key}: {value}")
