# event_logger.py
from typing import List, Dict, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import win32evtlog
from contextlib import contextmanager

from backend.analyzer import SessionAnalyzer
from backend.event_processor import process_event
from backend.timeUtils import parse_timestamp


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('event_logs.log'),
        logging.StreamHandler()
    ]
)

# Initialize the session analyzer
analyzer = SessionAnalyzer()


@contextmanager
def event_log_handle(server: str, log_type: str):
    """Context manager for handling event log connections."""
    handle = None
    try:
        handle = win32evtlog.OpenEventLog(server, log_type)
        yield handle
    finally:
        if handle:
            win32evtlog.CloseEventLog(handle)


def get_session_logs(
        minutes_back: Optional[int] = None,
        days_back: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Fetches and analyzes user session logs focusing on human interactions.

    Args:
        minutes_back: Number of minutes to look back
        days_back: Number of days to look back

    Returns:
        Tuple containing two lists: session logons and logoffs
    """
    session_logons: List[Dict[str, Any]] = []
    session_logoffs: List[Dict[str, Any]] = []

    try:
        # Calculate cutoff time
        cutoff_time = calculate_cutoff_time(minutes_back, days_back)

        with event_log_handle("localhost", "Security") as handle:
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            while True:
                try:
                    events = win32evtlog.ReadEventLog(handle, flags, 0)
                    if not events:
                        break

                    for event in events:
                        process_single_event(event, cutoff_time, session_logons, session_logoffs)

                except win32evtlog.error as e:
                    logging.error(f"Error reading event log: {e}")
                    break

    except Exception as e:
        logging.error(f"Error in get_session_logs: {e}")

    return session_logons, session_logoffs


def calculate_cutoff_time(
        minutes_back: Optional[int] = None,
        days_back: Optional[int] = None
) -> datetime:
    """Calculate the cutoff time based on input parameters."""
    if minutes_back is not None:
        return datetime.now() - timedelta(minutes=minutes_back)
    elif days_back is not None:
        return datetime.now() - timedelta(days=days_back)
    return datetime.now() - timedelta(days=7)  # Default to 7 days


def process_single_event(
        event: Any,
        cutoff_time: datetime,
        session_logons: List[Dict[str, Any]],
        session_logoffs: List[Dict[str, Any]]
) -> None:
    """Process a single event and update the session lists."""
    try:
        event_time = parse_timestamp(event.TimeGenerated)
        event_dt = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')

        if event_dt < cutoff_time:
            return

        if event.EventID in [4624, 4634, 4625]:  # Successful, Logoff, Failed
            data = event.StringInserts or []
            log_entry = process_event(event, data, event_time)

            if not log_entry:
                return

            if log_entry['event_type'] == 'Logoff':
                session_logoffs.append(log_entry)
            elif analyzer.is_human_session(log_entry) or log_entry['status'] == 'failed':
                log_entry = assess_risk(log_entry)
                session_logons.append(log_entry)
                analyzer.session_history[log_entry['user']].append(log_entry)

    except Exception as e:
        logging.error(f"Error processing event: {e}")


def assess_risk(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess risk and prepare features for ML model.
    """
    try:
        # Calculate is_rapid_login
        is_rapid_login = analyzer.is_rapid_login(log_entry)

        # Check business hours
        is_business_hours = analyzer.is_business_hours(log_entry['timestamp'])

        # Calculate risk score
        risk_score = 0
        if not is_business_hours:
            risk_score += 1
        if is_rapid_login:
            risk_score += 3
        if log_entry.get('status') == 'failed':
            risk_score += 2

        # Update log entry with ML features
        log_entry.update({
            'is_rapid_login': is_rapid_login,  # Ensure this is always calculated
            'is_business_hours': is_business_hours,
            'risk_score': risk_score,
            'status': log_entry.get('status', 'success')
        })

        return log_entry
    except Exception as e:
        logging.error(f"Error in assess_risk: {e}")
        return log_entry
