from collections import defaultdict
from datetime import datetime
import logging
from enum import Enum
from typing import Dict, List, Any, Tuple, Optional


class RiskFactors(Enum):
    OUTSIDE_BUSINESS_HOURS = 'outside_business_hours'
    RAPID_LOGIN_ATTEMPTS = 'rapid_login_attempts'


def get_session_duration(logon_time, logoff_time):
    """Calculate the duration of a session."""
    try:
        logon_dt = datetime.strptime(logon_time, '%Y-%m-%d %H:%M:%S')
        logoff_dt = datetime.strptime(logoff_time, '%Y-%m-%d %H:%M:%S')
        return (logoff_dt - logon_dt).total_seconds()
    except ValueError as e:
        logging.error(f"Error parsing timestamps: {e}")
        return None


class SessionAnalyzer:
    def __init__(self, business_hours: Tuple[int, int] = (9, 18)):
        """
        Initialize the SessionAnalyzer.
        Args:
            business_hours: Tuple defining start and end of business hours (24-hour format)
        Raises:
            ValueError: If business hours are invalid
        """
        self.RISK_WEIGHTS = None
        if not (0 <= business_hours[0] < 24 and 0 <= business_hours[1] < 24):
            raise ValueError("Business hours must be between 0 and 23")
        if business_hours[0] >= business_hours[1]:
            raise ValueError("Start time must be before end time")

        self.session_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.logon_sessions: Dict[str, str] = {}
        self.business_hours = business_hours

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_logon_time(self, logon_id: str) -> Optional[str]:
        """Retrieve the logon time for a given logon_id."""
        return self.logon_sessions.get(logon_id)

    def record_logon_event(self, logon_id: str, logon_time: str) -> None:
        """Record a logon event for tracking."""
        if not isinstance(logon_id, str) or not isinstance(logon_time, str):
            raise ValueError("Invalid input types")
        self.logon_sessions[logon_id] = logon_time

    @staticmethod
    def is_human_session(log_entry):
        """
        Determine if a log entry represents a human session.
        :param log_entry: Dictionary containing log details.
        :return: True if the session is human, False otherwise.
        """
        system_accounts = {'SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE', 'ANONYMOUS LOGON'}
        system_prefixes = ('$', 'NT ', 'UMFD-', 'DWM-', 'WINDOW MANAGER')
        user = log_entry.get('user', '').upper()
        logon_type = log_entry.get('logon_type', '')
        return (
                user
                and user not in system_accounts
                and not user.startswith(system_prefixes)
                and logon_type in {'Interactive', 'RemoteInteractive', 'CachedInteractive', 'Unlock'}
        )

    def is_business_hours(self, timestamp):
        """
        Check if the given timestamp falls within business hours.
        :param timestamp: String representation of the timestamp.
        :return: True if within business hours, False otherwise.
        """
        try:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return (
                    dt.weekday() < 5  # Monday-Friday
                    and self.business_hours[0] <= dt.hour < self.business_hours[1]
            )
        except ValueError:
            logging.warning(f"Invalid timestamp format: {timestamp}")
            return False

    def is_rapid_login(self, log_entry):
        """
        Check for rapid login attempts within 1 minute.
        Returns True if 3 or more login attempts are detected within 60 seconds.
        """
        if log_entry['event_type'] != 'Logon':
            return False

        user = log_entry['user']
        current_time = datetime.strptime(log_entry['timestamp'], '%Y-%m-%d %H:%M:%S')

        # Get all login attempts for this user in the last minute
        recent_attempts = [
            entry for entry in self.session_history[user]
            if (
                    entry['event_type'] == 'Logon' and
                    abs((datetime.strptime(entry['timestamp'],
                                           '%Y-%m-%d %H:%M:%S') - current_time).total_seconds()) <= 60
            )
        ]

        return len(recent_attempts) >= 3

    def enrich_log_entry(self, log_entry):
        """
        Analyze and enrich a log entry with risk factors and a risk score.
        :param log_entry: Dictionary containing log details.
        """
        # Validate input
        if not isinstance(log_entry, dict) or 'timestamp' not in log_entry:
            raise ValueError("Invalid log entry format")

        user = log_entry.get('user')
        timestamp = log_entry.get('timestamp')

        risk_factors = []

        # Analyze risk factors

        if not self.is_business_hours(timestamp):
            risk_factors.append('outside_business_hours')

        if user in self.session_history:
            if self.is_rapid_login(log_entry):
                risk_factors.append('rapid_login_attempts')

        # Calculate risk score
        log_entry['risk_factors'] = risk_factors
        log_entry['risk_score'] = sum(self.RISK_WEIGHTS[risk] for risk in risk_factors)
