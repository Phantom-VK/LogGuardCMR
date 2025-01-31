import os

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def clean_csv(input_csv_path, output_csv_path):
    """
    Clean the input CSV file and save it to the output path.

    Args:
        input_csv_path (str): Path to the input CSV file.
        output_csv_path (str): Path to save the cleaned CSV file.
    """
    try:
        # Check if the input CSV file exists
        if not os.path.exists(input_csv_path):
            raise FileNotFoundError(f"Input CSV file not found: {input_csv_path}")

        # Load the dataset
        df = pd.read_csv(input_csv_path)

        # Convert 'timestamp' to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Apply Label Encoding to specific columns
        label_columns = ['status', 'is_rapid_login', 'is_business_hours']
        for column in label_columns:
            if column in df.columns:
                df[column] = LabelEncoder().fit_transform(df[column])

        # Save the cleaned DataFrame
        df['weekday'] = df['day_of_week'].apply(check_result)
        df['result'] = df['risk_score'].apply(check_result)
        df.to_csv(output_csv_path, index=False)
        print(f"Cleaned CSV saved to: {output_csv_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error while cleaning CSV: {e}")


def check_result(inpt):
    dic = {"Sunday": 6, "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5}
    if type(inpt) == str:
        return dic[inpt]
    if inpt <= 2:
        return 0
    elif 2 <= inpt <= 6:
        return 1
    else:
        return 2
# Example usage
# cleaned_df = clean_csv('exported_logs.csv')
