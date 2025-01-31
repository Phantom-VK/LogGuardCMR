import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from backend.event_logger import get_session_logs
from backend.export_utils import save_to_json, save_json_file_to_csv
from data_clean import clean_csv
from enableEV import enable_failed_login_auditing


# Configure logging
def setup_logging(log_dir: Path):
    """Setup logging with proper path handling"""
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"logguard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_base_path():
    """Get base path for the application, handling both development and executable environments"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        return Path(sys._MEIPASS)
    else:
        # If the application is run from a Python interpreter
        return Path(os.path.dirname(os.path.abspath(__file__)))


class LogAnalyzer:
    def __init__(self):
        self.database_dir = None
        self.logons = []
        self.logoffs = []

        # Set up base directory for the application
        if getattr(sys, 'frozen', False):
            base_dir = Path(os.environ.get('APPDATA')) / "LogGuard"
        else:
            base_dir = Path.cwd()

        # Centralized export folder
        self.export_dir = base_dir / 'Exports'

        # Create the export folder if it doesn't exist
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        log_file = self.export_dir / "logguard.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def get_export_path(self, filename):
        """Helper to get the full path for a file in the export directory."""
        return str(self.export_dir / filename)

    def setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        try:
            self.export_dir.mkdir(exist_ok=True)
            self.database_dir.mkdir(exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create directories: {e}")
            raise

    def collect_logs(self, days_back: int = 100) -> None:
        """Collect logs for the specified time period."""
        try:
            logging.info(f"Collecting logs for past {days_back} days...")
            enable_failed_login_auditing()
            self.logons, self.logoffs = get_session_logs(days_back=days_back)
            logging.info(f"Found {len(self.logons)} human user sessions")
        except Exception as e:
            logging.error(f"Error collecting logs: {e}")
            raise

    def analyze_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Analyze the time range of collected logs."""
        if not self.logons:
            logging.warning("No logs found to analyze time range")
            return None

        try:
            first_log = datetime.strptime(self.logons[0]['timestamp'], '%Y-%m-%d %H:%M:%S')
            last_log = datetime.strptime(self.logons[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')
            logging.info(f"Log time range: {first_log} to {last_log}")
            return first_log, last_log
        except Exception as e:
            logging.error(f"Error analyzing time range: {e}")
            return None

    def analyze_risk_distribution(self) -> Dict[int, int]:
        """Analyze risk score distribution in logs."""
        try:
            risk_groups = defaultdict(list)
            for log in self.logons:
                risk_groups[log.get('risk_score', 0)].append(log)

            distribution = {score: len(events) for score, events in risk_groups.items()}

            logging.info("Risk Score Distribution:")
            for score in sorted(distribution.keys()):
                logging.info(f"Risk Score {score}: {distribution[score]} events")

            return distribution
        except Exception as e:
            logging.error(f"Error analyzing risk distribution: {e}")
            return {}

    def export_data(self):
        """Export logs to JSON, CSV, and cleaned CSV files."""
        try:
            # Export JSON files
            logons_json_path = self.get_export_path('session_logons.json')
            logoffs_json_path = self.get_export_path('session_logoffs.json')
            save_to_json(self.logons, logons_json_path)
            save_to_json(self.logoffs, logoffs_json_path)

            # Export CSV files
            logons_csv_path = self.get_export_path('exported_logons.csv')
            csv_path = save_json_file_to_csv(logons_json_path, logons_csv_path)
            if not csv_path or not os.path.exists(csv_path):
                raise FileNotFoundError(f"Failed to create CSV file: {csv_path}")
            # Clean CSV file
            cleaned_csv_path = self.get_export_path('cleaned_logons.csv')
            clean_csv(logons_csv_path, cleaned_csv_path)

            logging.info("Export process completed successfully.")
        except Exception as e:
            logging.error(f"Error during export: {e}")
            raise


def main():
    try:
        # Create analyzer instance
        analyzer = LogAnalyzer()

        # Log start of execution
        logging.info("Starting LogGuard application...")
        start_time = time.time()

        # Collect and analyze logs
        analyzer.collect_logs(days_back=30)
        analyzer.analyze_time_range()
        analyzer.analyze_risk_distribution()

        # Export data
        analyzer.export_data()

        # Log execution time
        execution_time = time.time() - start_time
        logging.info(f"Total execution time: {execution_time:.2f} seconds")

        # Pause for user input (only for executables)
        if getattr(sys, 'frozen', False):
            os.system("pause")  # Use pause for Windows
    except Exception as e:
        logging.critical(f"Application failed: {e}")
        if getattr(sys, 'frozen', False):
            # Gracefully exit without input() for executables
            logging.error("Exiting due to error.")
        sys.exit(1)


if __name__ == '__main__':
    main()
