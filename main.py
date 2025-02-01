import os
import sys
import winreg as reg
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from GUI.userSettings import App
from backend.event_logger import get_session_logs
from backend.export_utils import save_to_json, save_json_file_to_csv, analyze_last_logs
from data_clean import clean_csv
from database.db_utils import save_to_database
from GUI.email_script import send_email
from enableEV import enable_failed_login_auditing
from ML.model import start_model

APP_NAME = "LogGuard"
EXE_NAME = "LogGuard.exe"


def get_base_path():
    """Get base path dynamically, handling frozen EXE cases."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)  # PyInstaller EXE folder
    return Path.cwd()


def get_export_path(filename):
    """Get the path for exported files."""
    return str(get_base_path() / 'Exports' / filename)


def add_to_startup():
    """Adds the EXE to Windows startup using the registry."""
    try:
        exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else "dist/" + EXE_NAME)

        if not os.path.exists(exe_path):
            print(f"❌ EXE not found: {exe_path}")
            return

        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE) as reg_key:
            reg.SetValueEx(reg_key, APP_NAME, 0, reg.REG_SZ, exe_path)

        print(f"✅ {APP_NAME} added to Windows startup successfully!")

    except Exception as e:
        logging.error(f"❌ Error adding to startup: {e}")


class LogAnalyzer:
    def __init__(self):
        self.database_dir = None
        self.logons = []
        self.logoffs = []
        base_dir = get_base_path()
        self.export_dir = base_dir / 'Exports'
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def collect_logs(self, minutes_back: Optional[int] = None, days_back: Optional[int] = None) -> None:
        """Collect system logon logs."""
        enable_failed_login_auditing()
        self.logons, self.logoffs = get_session_logs(days_back=days_back) if days_back else get_session_logs(
            minutes_back=minutes_back)

    def analyze_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Analyze the time range of logs."""
        if not self.logons:
            return None
        first_log = datetime.strptime(self.logons[0]['timestamp'], '%Y-%m-%d %H:%M:%S')
        last_log = datetime.strptime(self.logons[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')
        return first_log, last_log

    def analyze_risk_distribution(self) -> Dict[int, int]:
        """Analyze risk scores in logs."""
        risk_groups = defaultdict(list)
        for log in self.logons:
            risk_groups[log.get('risk_score', 0)].append(log)
        return {score: len(events) for score, events in risk_groups.items()}

    def export_data(self):
        """Export logs to JSON, CSV, and database."""
        try:
            logons_json_path = get_export_path('session_logons.json')
            logoffs_json_path = get_export_path('session_logoffs.json')

            save_to_database(self.logons, get_export_path('session_logons.db'))
            save_to_database(self.logoffs, get_export_path('session_logoffs.db'))
            save_to_json(self.logons, logons_json_path)
            save_to_json(self.logoffs, logoffs_json_path)

            logons_csv_path = get_export_path('exported_logons.csv')
            csv_path = save_json_file_to_csv(logons_json_path, logons_csv_path)

            if not csv_path or not os.path.exists(csv_path):
                raise FileNotFoundError(f"Failed to create CSV file: {csv_path}")

            cleaned_csv_path = get_export_path('cleaned_logons.csv')
            clean_csv(logons_csv_path, cleaned_csv_path)

        except Exception as e:
            logging.error(f"❌ Error exporting data: {e}")


def main():
    """Main function to analyze logs and detect anomalies."""
    output = None
    try:
        analyzer = LogAnalyzer()
        analyzer.collect_logs(minutes_back=40)
        analyzer.analyze_time_range()
        analyzer.analyze_risk_distribution()
        analyzer.export_data()

        latest_log = analyze_last_logs(get_export_path('cleaned_logons.csv'))
        output = start_model(latest_log)

        if getattr(sys, 'frozen', False):
            input("\nPress Enter to exit...")  # Keeps window open in EXE mode

    except Exception as e:
        logging.error(f"❌ Fatal error in main(): {e}")
        if getattr(sys, 'frozen', False):
            input(f"\nError: {e}\nPress Enter to exit...")  # Shows error in EXE
        sys.exit(1)

    return output


if __name__ == '__main__':
    add_to_startup()

    # Add the app to Windows startup at first run

    if main():
        send_email(
                subject="Anomalous System Login Notification",
                body="Your system has successfully logged in. Seems Rapid Login.",
                recipient="vikramadityakhupse@gmail.com",
                sender='adnankhan17371@gmail.com'
            )
    else:

        send_email(
                subject="System Login Notification",
                body="Your system has successfully logged in. No anomalous behavior detected.",
                recipient="vikramadityakhupse@gmail.com",
                sender='adnankhan17371@gmail.com'
            )

    app = App()
    app.mainloop()
