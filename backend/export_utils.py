# export_utils.py
import json
import logging
import msvcrt  # Windows-specific file locking
import os
from contextlib import contextmanager

import pandas as pd

from data_clean import check_result


@contextmanager
def windows_file_lock(file_handle):
    """Windows-compatible file locking context manager."""

    try:
        # Lock the file
        msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        yield
    finally:
        # Release the lock
        try:
            # Unlock the file
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
        except:
            pass


def save_to_json(logs, filepath):
    """
    Save logs to JSON format.

    Args:
        logs: List of log dictionaries.
        filepath: Full path to the JSON file.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)
        logging.info(f"JSON file saved: {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Failed to save JSON file: {e}")
        raise


def save_to_csv(data, filename='exported_logs.csv'):
    """
    Save ML-relevant features to CSV.
    """
    if not data:
        # print("No data to save to CSV.")
        logging.error("No data to save to CSV.")
        return

    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)

        # Debug: Check if 'is_rapid_login' exists and is populated
        if 'is_rapid_login' not in df.columns:
            # print("is_rapid_login column is missing from the data.")
            logging.error("is_rapid_login column is missing from the data.")
        else:
            # print(f"is_rapid_login values:\n{df['is_rapid_login'].value_counts()}")
            logging.error(f"is_rapid_login values:\n{df['is_rapid_login'].value_counts()}")

        # Select ML-relevant columns
        ml_columns = [
            'timestamp',
            'user',
            'status',
            'is_rapid_login',
            'is_business_hours',
            'risk_score',
            'logon_type',
            'source_ip'
        ]

        # Filter columns and handle missing columns
        available_columns = [col for col in ml_columns if col in df.columns]
        df_ml = df[available_columns]

        # Remove duplicates
        df_unique = df_ml.drop_duplicates(keep='first')

        # Save to CSV
        if not os.path.exists(filename):
            df_unique.to_csv(filename, index=False)
            logging.debug(f"Created new file: {filename}")
        else:
            # Append to existing file
            df_existing = pd.read_csv(filename)
            combined_df = pd.concat([df_existing, df_unique]).drop_duplicates(keep='first')
            combined_df.to_csv(filename, index=False)
            logging.debug(f"Updated existing file: {filename}")
            logging.debug(f"Total records in file: {len(combined_df)}")

    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")


def save_json_file_to_csv(json_file_path, csv_file_path='exported_logs.csv'):
    """
    Load JSON data from a file, filter ML-relevant columns, and save to a CSV file.

    Args:
        json_file_path (str): Path to the JSON file containing log entries.
        csv_file_path (str): Path to the CSV file to save filtered data.
    Returns:
        str: Path to the created CSV file if successful, None otherwise.
    """
    # Define ML-relevant columns to save
    ml_columns = [
        'timestamp',
        'status',
        'day_of_week',
        'is_rapid_login',
        'is_business_hours',
        'risk_score',
        'logon_type'
    ]

    try:
        # Check if the JSON file exists
        if not os.path.exists(json_file_path):
            logging.error(f"JSON file not found: {json_file_path}")
            return None

        # Load JSON data from the file
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)

        # Convert JSON data to DataFrame
        df = pd.DataFrame(json_data)

        # Ensure the JSON data is not empty
        if df.empty:
            logging.warning(f"The JSON file {json_file_path} is empty.")
            return None

        # Filter only the required ML columns
        available_columns = [col for col in ml_columns if col in df.columns]
        if not available_columns:
            logging.warning("No ML-relevant columns found in the JSON file.")
            return None

        df_filtered = df[available_columns]

        # Ensure 'is_rapid_login' column is mapped to 1 and 0
        if 'is_rapid_login' in df_filtered.columns:
            df_filtered.loc[:, 'is_rapid_login'] = df_filtered['is_rapid_login'].astype(bool).map({True: 1, False: 0})

        # Remove duplicates
        df_filtered = df_filtered.drop_duplicates(keep='first')

        # Ensure there is data to save
        if df_filtered.empty:
            logging.info("No data to save after filtering.")
            return None

        # Save to CSV
        df_filtered['weekday'] = df_filtered['day_of_week'].apply(check_result)
        df_filtered['result'] = df_filtered['risk_score'].apply(check_result)
        df_filtered.to_csv(csv_file_path, index=False)
        logging.info(f"Data successfully saved to {csv_file_path}")
        return csv_file_path

    except FileNotFoundError as e:
        logging.error(f"File not found: {json_file_path}. Error: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from file: {json_file_path}. Error: {e}")
    except Exception as e:
        logging.error(f"Error saving JSON to CSV: {e}")

    return None
