import sqlite3

Export_fields = [
    'timestamp',
    'event_type',
    'user',
    'domain',
    'user_sid',
    'logon_type',
    'status',
    'failure_reason',
    'logon_id',
    'session_duration',
    'source_ip',
    'workstation_name',
    'is_business_hours',
    'is_rapid_logon',
    'day_of_week',
    'hour_of_day',
    'risk_score',
    'event_id',
    'event_task_category',
]


def ensure_columns_exist(cursor, table_name, columns):
    """Ensure all required columns exist in the table schema."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {col[1] for col in cursor.fetchall()}
    for col in columns:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")


def save_to_database(logs, db_name):
    """Save logs to an SQLite database, ensuring no duplicate rows are inserted."""
    if not logs:
        print("No logs to save.")
        return

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create the session_logs table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS session_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                user TEXT,
                domain TEXT,
                user_sid TEXT,
                logon_type TEXT,
                status TEXT,
                failure_reason TEXT,
                logon_id TEXT,
                session_duration REAL,
                source_ip TEXT,
                workstation_name TEXT,
                is_business_hours BOOLEAN,
                is_rapid_login BOOLEAN,
                day_of_week TEXT,
                hour_of_day INTEGER,
                risk_score REAL,
                event_id INTEGER,
                event_task_category TEXT
            )
        """)

        # Ensure all required columns exist
        ensure_columns_exist(cursor, "session_logs", Export_fields)

        # Prepare logs for insertion
        formatted_logs = []
        for log in logs:
            formatted_log = {field: log.get(field, '') for field in Export_fields}
            formatted_logs.append(formatted_log)

        # Insert logs into the table
        fields_str, placeholders = ', '.join(Export_fields), ', '.join([f":{field}" for field in Export_fields])
        query = f"INSERT OR IGNORE INTO session_logs ({fields_str}) VALUES ({placeholders})"
        cursor.executemany(query, formatted_logs)

        # Commit changes and close the connection
        conn.commit()
        conn.close()

        print(f"Logs successfully saved to database: {db_name}")
    except Exception as e:
        print(f"Error saving logs to database: {e}")


def query_database(db_name, table_name='session_logs'):
    """Query selected columns from the database."""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Define columns to fetch
        selected_columns = [
            'timestamp',
            'user',
            'status',
            'is_rapid_login',
            'is_business_hours',
            'risk_score',
            'logon_type',
            'source_ip'
        ]
        ensure_columns_exist(cursor, table_name, selected_columns)

        # Query the database
        fields_str = ', '.join(selected_columns)
        query = f"SELECT {fields_str} FROM {table_name}"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert rows into dictionaries
        data = [dict(zip(selected_columns, row)) for row in rows]
        conn.close()
        return data
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error querying database: {e}")
        return []
