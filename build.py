import os
import PyInstaller.__main__

# Project Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")
ICON_PATH = os.path.join(BASE_DIR, "user_info", "logo.ico")  # Ensure the logo exists

# PyInstaller Arguments
args = [
    MAIN_SCRIPT,
    "--onefile",  # Bundle everything into a single EXE
    "--noconsole",  # Hide the terminal window
    "--name=LogGuard",  # Name of the output EXE
    f"--icon={ICON_PATH}",  # Set application icon
    "--clean",  # Clean previous builds
    "--log-level=INFO",  # Detailed logs
    "--add-data=backend;backend",  # Include backend folder
    "--add-data=database;database",  # Include database folder
    "--add-data=GUI;GUI",  # Include GUI folder
    "--add-data=ML;ML",  # Include ML folder
    "--add-data=user_info;user_info",  # Include user data folder
    "--hidden-import=win32evtlog",
    "--hidden-import=win32api",
    "--hidden-import=win32con",
    "--hidden-import=sqlite3",
    "--hidden-import=pandas",
]

# Run PyInstaller
if __name__ == "__main__":
    PyInstaller.__main__.run(args)
    print("\n✅ Build completed! Check the 'dist' folder for LogGuard.exe.")
