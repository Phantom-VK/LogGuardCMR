import os
import PyInstaller.__main__


def build_exe():
    # Get the directory of the current script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Define paths
    main_path = os.path.join(base_dir, 'main.py')
    readme_path = os.path.join(base_dir, 'README.txt')
    enable_ev_path = os.path.join(base_dir, 'enableEV.py')
    backend_path = os.path.join(base_dir, 'backend')
    database_path = os.path.join(base_dir, 'database')
    data_clean_path = os.path.join(base_dir, 'data_clean.py')

    # Handle OS-specific path separator for --add-data
    sep = ';' if os.name == 'nt' else ':'

    # PyInstaller arguments
    args = [
        main_path,
        '--onefile',  # Create a single executable
        '--name=LogGuard',
        '--clean',  # Clean PyInstaller cache and temporary files
        '--noconsole',  # Remove this if you want to see console output
        '--log-level=INFO',  # Set logging level for PyInstaller
        '--icon=user_info/logo.ico',  # Path to the application icon (optional)
        # Add hidden imports
        '--hidden-import=win32evtlog',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32security',
        '--hidden-import=pandas',
        '--hidden-import=sqlite3',
        '--hidden-import=sklearn',  # For LabelEncoder
        # Add required files and directories
        f'--add-data={readme_path}{sep}.',
        f'--add-data={enable_ev_path}{sep}.',
        f'--add-data={data_clean_path}{sep}.',
        f'--add-data={backend_path}{sep}backend',
        f'--add-data={database_path}{sep}database',
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    build_exe()
