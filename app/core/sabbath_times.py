"""Core functionality for Sabbath time calculations and management."""

import datetime
from zoneinfo import ZoneInfo
from typing import Tuple

def get_sabbath_times(timezone_str: str = 'UTC') -> Tuple[datetime.datetime, datetime.datetime]:
    """Calculate Sabbath times based on SDA understanding (Friday sunset to Saturday sunset).
    
    Args:
        timezone_str: Timezone string (e.g., 'UTC', 'America/New_York')
        
    Returns:
        Tuple containing sabbath start and end times
    """
    now = datetime.datetime.now(ZoneInfo(timezone_str))
    
    # Find the next Friday
    days_until_friday = (4 - now.weekday()) % 7
    next_friday = now + datetime.timedelta(days=days_until_friday)
    
    # Set to sunset time (approximate as 18:00 for now)
    sabbath_start = next_friday.replace(hour=18, minute=0, second=0, microsecond=0)
    sabbath_end = sabbath_start + datetime.timedelta(days=1)
    
    return sabbath_start, sabbath_end

def format_time_until(target_time: datetime.datetime, current_time: datetime.datetime = None) -> str:
    """Format the time remaining until a target time.
    
    Args:
        target_time: The target datetime
        current_time: Current datetime (defaults to now if not provided)
        
    Returns:
        Formatted string describing time remaining
    """
    if current_time is None:
        current_time = datetime.datetime.now(target_time.tzinfo)
    
    time_diff = target_time - current_time
    
    if time_diff.total_seconds() < 0:
        return "Time has passed"
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    return ", ".join(parts) if parts else "Less than a minute"

def get_sabbath_status(timezone_str: str = 'UTC') -> dict:
    """Get current Sabbath status and timing information.
    
    Args:
        timezone_str: Timezone string
        
    Returns:
        Dictionary containing Sabbath status information
    """
    now = datetime.datetime.now(ZoneInfo(timezone_str))
    start_time, end_time = get_sabbath_times(timezone_str)
    
    is_sabbath = start_time <= now <= end_time
    next_start = start_time if now < start_time else get_sabbath_times(timezone_str, now + datetime.timedelta(days=7))[0]
    
    return {
        'is_sabbath': is_sabbath,
        'start_time': start_time,
        'end_time': end_time,
        'next_start': next_start,
        'time_until_start': format_time_until(next_start, now) if not is_sabbath else None,
        'time_until_end': format_time_until(end_time, now) if is_sabbath else None
    }
