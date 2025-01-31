import logging
from datetime import datetime, timezone
from typing import Union

from dateutil import parser


def parse_timestamp(
        time_str: Union[str, datetime, None]
) -> str:
    """
    Parse timestamp with timezone handling.

    Args:
        time_str: Input timestamp
    Returns:
        Standardized datetime string
    Raises:
        ValueError: If timestamp is invalid
    """
    if time_str is None:
        raise ValueError("Timestamp cannot be None")

    try:
        if isinstance(time_str, datetime):
            dt = time_str
        else:
            dt = parser.parse(str(time_str))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logging.error(f"Error parsing timestamp {time_str}: {e}")
        raise ValueError(f"Invalid timestamp format: {time_str}")