# event_processor.py
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging
from enum import Enum
from dataclasses import dataclass

from backend.analyzer import SessionAnalyzer, get_session_duration

# Initialize analyzer
analyzer = SessionAnalyzer()


class EventTypes(Enum):
    LOGON = 'Logon'
    LOGOFF = 'Logoff'


class EventIDs(Enum):
    SUCCESSFUL_LOGON = 4624
    LOGOFF = 4634
    FAILED_LOGON = 4625


@dataclass
class LogonType:
    code: str
    description: str


class LogonTypes:
    TYPES = {
        '2': LogonType('2', 'Interactive'),
        '3': LogonType('3', 'Network'),
        '4': LogonType('4', 'Batch'),
        '5': LogonType('5', 'Service'),
        '7': LogonType('7', 'Unlock'),
        '8': LogonType('8', 'NetworkCleartext'),
        '9': LogonType('9', 'NewCredentials'),
        '10': LogonType('10', 'RemoteInteractive'),
        '11': LogonType('11', 'CachedInteractive')
    }

    @staticmethod
    def get_description(type_code: Union[str, int]) -> str:
        """Get logon type description from code."""
        return LogonTypes.TYPES.get(str(type_code),
                                    LogonType(str(type_code), 'Unknown')).description


def create_base_entry(event: Any, timestamp: str) -> Dict[str, Any]:
    """Create base entry dictionary with default values."""
    try:
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        return {
            'timestamp': timestamp,
            'event_type': '',
            'user': '',
            'domain': '',
            'user_sid': '',
            'logon_id': '',
            'session_duration': 0,
            'status': 'success',
            'logon_type': '',
            'source_ip': '',
            'destination_ip': '',
            'is_rapid_logon': '',
            'workstation_name': '',
            'failure_reason': '',
            'process_name': '',
            'auth_package': '',
            'risk_score': 0,
            'day_of_week': dt.strftime('%A'),
            'hour_of_day': dt.hour,
            'is_business_hours': analyzer.is_business_hours(timestamp),
            'event_id': event.EventID,
            'event_task_category': event.EventCategory,
        }
    except Exception as e:
        logging.error(f"Error creating base entry: {e}")
        raise


def process_event(
        event: Any,
        data: List[str],
        timestamp: str
) -> Optional[Dict[str, Any]]:
    """
    Process individual event and extract relevant information.

    Args:
        event: Event object
        data: List of event data strings
        timestamp: Event timestamp

    Returns:
        Processed event dictionary or None if processing fails
    """
    try:
        base_entry = create_base_entry(event, timestamp)

        if event.EventID == EventIDs.SUCCESSFUL_LOGON.value:
            return process_logon(data, base_entry)
        elif event.EventID == EventIDs.LOGOFF.value:
            return process_logoff(data, base_entry)
        elif event.EventID == EventIDs.FAILED_LOGON.value:
            return process_failed_logon(data, base_entry)

    except Exception as e:
        logging.error(f"Error processing event {event.EventID}: {e}")

    return None


def process_logon(data: List[str], base_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process successful logon events."""
    if len(data) < 10:
        logging.warning("Insufficient data for logon event")
        return None

    try:
        base_entry.update({
            'event_type': EventTypes.LOGON.value,
            'user': data[5],
            'domain': data[6],
            'user_sid': data[4],
            'logon_id': data[3],
            'logon_type': LogonTypes.get_description(data[8]),
            'source_ip': data[18] if len(data) > 18 else '',
            'workstation_name': data[1],
            'elevated_token': 'Yes' in data[20] if len(data) > 20 else False
        })
        return base_entry
    except Exception as e:
        logging.error(f"Error processing logon event: {e}")
        return None


def process_logoff(data: List[str], base_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process logoff events."""
    if len(data) < 3:
        logging.warning("Insufficient data for logoff event")
        return None

    try:
        logon_id = data[3]
        logoff_time = base_entry['timestamp']
        logon_time = analyzer.get_logon_time(logon_id)

        session_duration = None
        if logon_time and logoff_time:
            session_duration = get_session_duration(logon_time, logoff_time)

        base_entry.update({
            'event_type': EventTypes.LOGOFF.value,
            'user': data[1],
            'domain': data[2],
            'logon_id': logon_id,
            'session_duration': session_duration
        })
        return base_entry
    except Exception as e:
        logging.error(f"Error processing logoff event: {e}")
        return None


def process_failed_logon(data: List[str], base_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process failed logon events."""
    if len(data) < 8:
        logging.warning("Insufficient data for failed logon event")
        return None

    try:
        base_entry.update({
            'event_type': EventTypes.LOGON.value,
            'status': 'failed',
            'user': data[5],
            'domain': data[6],
            'user_sid': data[4],
            'logon_id': data[3],
            'logon_type': LogonTypes.get_description(data[8]),
            'source_ip': data[19] if len(data) > 19 else '',
            'failure_reason': data[7] if len(data) > 7 else '',
            'auth_package': data[10] if len(data) > 10 else ''
        })
        return base_entry
    except Exception as e:
        logging.error(f"Error processing failed logon event: {e}")
        return None