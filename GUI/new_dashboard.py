import os.path
import pickle
import random
import re
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

from GUI.email_script import send_email
from GUI.user_data import userData
from ai_with_gui import LogSummaryGenerator


class SystemDashboard(ctk.CTkFrame):
    def __init__(self, master, switch_callback):
        super().__init__(master)

        if (os.path.exists("user_data.pkl")):
            with open("user_data.pkl", 'rb') as file:
                self.userData = pickle.load(file)
        else:
            self.userData = userData()
        # Configure grid layout
        self.notify_loginVar = tk.BooleanVar(value=self.userData.notifyLogin)
        self.notify_summaryVar = tk.BooleanVar()
        self.email = ctk.StringVar(value=self.userData.email)
        self.start_time = ctk.StringVar(value=self.userData.startingHours)
        self.end_time = ctk.StringVar(value=self.userData.endingHours)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self.create_sidebar()

        # Create main content area
        self.create_main_content()

        # Initially show overview
        self.show_overview()

    def create_sidebar(self):
        # Sidebar frame
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="LogGuard",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation buttons
        self.nav_btn_1 = ctk.CTkButton(
            self.sidebar,
            text="Overview",
            command=self.show_overview
        )
        self.nav_btn_1.grid(row=1, column=0, padx=20, pady=10)

        self.nav_btn_2 = ctk.CTkButton(
            self.sidebar,
            text="Login History",
            command=self.show_login_history
        )
        self.nav_btn_2.grid(row=2, column=0, padx=20, pady=10)

        self.nav_btn_3 = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=self.show_settings
        )
        self.nav_btn_3.grid(row=3, column=0, padx=20, pady=10)

        # Appearance mode
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar,
            text="Appearance Mode:",
            anchor="w"
        )
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(10, 20))

    def create_main_content(self):
        # Main content frame
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)

    def show_overview(self):
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Title
        title = ctk.CTkLabel(
            self.main_content,
            text="System Overview",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Stats container
        stats_frame = ctk.CTkFrame(self.main_content)
        stats_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Stat boxes
        self.create_stat_box(
            stats_frame,
            "Total Logins Today",
            "15",
            row=0, column=0
        )
        self.create_stat_box(
            stats_frame,
            "Outside Hours Logins",
            "3",
            row=0, column=1
        )
        self.create_stat_box(
            stats_frame,
            "Alert Status",
            "Normal",
            row=0, column=2
        )

        # Summary controls frame
        summary_controls_frame = ctk.CTkFrame(self.main_content)
        summary_controls_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Label for summary frequency
        frequency_label = ctk.CTkLabel(
            summary_controls_frame,
            text="Summary Frequency:",
            font=ctk.CTkFont(size=12)
        )
        frequency_label.pack(side="left", padx=(10, 5))

        # Dropdown menu for summary frequency
        frequency_options = ["1 day", "7 days", "30 days"]
        frequency_var = ctk.StringVar(value=frequency_options[0])  # Default value

        frequency_dropdown = ctk.CTkComboBox(
            summary_controls_frame,
            values=frequency_options,
            variable=frequency_var,
            width=100
        )
        frequency_dropdown.pack(side="left", padx=(0, 10))

        # Generate Summary Button (smaller size)
        generate_summary_button = ctk.CTkButton(
            summary_controls_frame,
            text="Generate Summary",
            command=self.generate_summary,
            width=120  # Set a smaller width
        )
        generate_summary_button.pack(side="left", padx=(0, 10))

        # Recent activity
        activity_frame = ctk.CTkFrame(self.main_content)
        activity_frame.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")

        activity_label = ctk.CTkLabel(
            activity_frame,
            text="Recent Activity",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        activity_label.pack(padx=10, pady=10, anchor="w")

        # Create Treeview for recent activity
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

        tree = ttk.Treeview(
            activity_frame,
            columns=("Time", "Event", "Status"),
            show="headings",
            height=6
        )

        tree.heading("Time", text="Time")
        tree.heading("Event", text="Event")
        tree.heading("Status", text="Status")

        # Add sample data
        recent_activities = [
            (datetime.now().strftime("%H:%M:%S"), "System Login", "Success"),
            (datetime.now().strftime("%H:%M:%S"), "File Access", "Warning"),
            (datetime.now().strftime("%H:%M:%S"), "System Login", "Success"),
        ]

        for activity in recent_activities:
            tree.insert("", "end", values=activity)

        tree.pack(padx=10, pady=10, fill="both", expand=True)

    def generate_summary(self, sample_log=None):
        """
        Function to handle the "Generate Summary" button click.
        """
        # generator = LogSummaryGenerator()

        print("Generating summary...")  # Replace with your logic
        send_email(
            subject="Today's Summary",
            body = "Hey there, this is your today's summary",
            recipient="vikramadityakhupse@gmail.com",
            sender='adnankhan17371@gmail.com'
        )
        # Example: Show a toast or update the UI with the summary
        self.show_toast("Summary generated successfully!")

    def show_login_history(self):
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Title
        title = ctk.CTkLabel(
            self.main_content,
            text="Login History",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Create Treeview frame
        tree_frame = ctk.CTkFrame(self.main_content)
        tree_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # Create Treeview
        columns = ("Date", "Time", "Status", "Location", "Device")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Add sample data
        for i in range(20):
            date = datetime.now().strftime("%Y-%m-%d")
            time = datetime.now().strftime("%H:%M:%S")
            status = random.choice(["Success", "Warning", "Failed"])
            location = random.choice(["Home", "Office", "Remote"])
            device = random.choice(["Windows PC", "MacBook", "Linux Server"])

            tree.insert("", "end", values=(date, time, status, location, device))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_settings(self):
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Title
        title = ctk.CTkLabel(
            self.main_content,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Settings container
        settings_frame = ctk.CTkFrame(self.main_content)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.email_label = ctk.CTkLabel(settings_frame, text="Email Address:").pack()
        self.email_entry = ctk.CTkEntry(
            settings_frame,
            width=300,
            textvariable=self.email,
            placeholder_text="Enter your email"
        ).pack()
        # Email settings
        email_label = ctk.CTkLabel(
            settings_frame,
            text="Email Notifications",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        email_label.pack(padx=20, pady=(20, 10), anchor="w")

        notify_login = ctk.CTkSwitch(
            settings_frame,
            text="Send email on suspicious login",
            variable=self.notify_summaryVar
        )
        notify_login.pack(padx=20, pady=5, anchor="w")

        notify_summary = ctk.CTkSwitch(
            settings_frame,
            text="Send daily summary",
            variable=self.notify_loginVar
        )
        notify_summary.pack(padx=20, pady=5, anchor="w")

        # Working hours
        hours_label = ctk.CTkLabel(
            settings_frame,
            text="Working Hours",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        hours_label.pack(padx=20, pady=(20, 10), anchor="w")

        hours_frame = ctk.CTkFrame(settings_frame)
        hours_frame.pack(padx=20, pady=5, anchor="w")

        # Start time
        start_label = ctk.CTkLabel(hours_frame, text="Start:")
        start_label.grid(row=0, column=0, padx=5, pady=5)

        def increase_start():
            current_value = int(self.start_time.get())
            if current_value < 23:
                self.start_time.set(current_value + 1)

        def decrease_start():
            current_value = int(self.start_time.get())
            if current_value > 0:
                self.start_time.set(current_value - 1)

        start_decrease_button = ctk.CTkButton(hours_frame, text="-", width=20, command=decrease_start)
        start_decrease_button.grid(row=0, column=1, padx=5, pady=5)

        start_entry = ctk.CTkEntry(hours_frame, textvariable=self.start_time, width=60)
        start_entry.grid(row=0, column=2, padx=5, pady=5)

        start_increase_button = ctk.CTkButton(hours_frame, text="+", width=20, command=increase_start)
        start_increase_button.grid(row=0, column=3, padx=5, pady=5)

        # End time
        end_label = ctk.CTkLabel(hours_frame, text="End:")
        end_label.grid(row=1, column=0, padx=5, pady=5)

        def increase_end():
            current_value = int(self.end_time.get())
            if current_value < 23:
                self.end_time.set(current_value + 1)

        def decrease_end():
            current_value = int(self.end_time.get())
            if current_value > 0:
                self.end_time.set(current_value - 1)

        end_decrease_button = ctk.CTkButton(hours_frame, text="-", width=20, command=decrease_end)
        end_decrease_button.grid(row=1, column=1, padx=5, pady=5)

        end_entry = ctk.CTkEntry(hours_frame, textvariable=self.end_time, width=60)
        end_entry.grid(row=1, column=2, padx=5, pady=5)

        end_increase_button = ctk.CTkButton(hours_frame, text="+", width=20, command=increase_end)
        end_increase_button.grid(row=1, column=3, padx=5, pady=5)

        # Save button
        save_button = ctk.CTkButton(
            settings_frame,
            text="Save Changes",
            command=self.submit_changes
        )
        save_button.pack(pady=30)

    def submit_changes(self):
        if self.is_valid_email(self.email.get()):
            with open("user_data.pkl", "wb") as file:
                newUserData = userData(
                    notifyLogin=self.notify_loginVar.get(),
                    email=self.email.get(),
                    startingHours=self.start_time.get(),
                    endingHours=self.end_time.get(),
                    notifySummary=self.notify_summaryVar.get(),
                )
                pickle.dump(newUserData, file)
        else:
            self.show_toast("Invalid email")

    def is_valid_email(self, email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    def show_toast(self, message):
        """
        Show a toast notification at the bottom of the screen.
        """
        toast = ctk.CTkToplevel(self.master.current_frame)
        toast.geometry("300x50+500+700")  # Position the toast at the bottom
        toast.overrideredirect(True)  # Remove window decorations
        toast.attributes("-alpha", 0.9)  # Set transparency

        # Add a label to display the message
        label = ctk.CTkLabel(toast, text=message, fg_color="gray", text_color="white", corner_radius=10)
        label.pack(padx=10, pady=10, fill="both", expand=True)

        # Close the toast after 3 seconds
        threading.Timer(3, toast.destroy).start()

    def create_stat_box(self, parent, title, value, row, column):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(padx=20, pady=(20, 10))

        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(padx=20, pady=(0, 20))

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = SystemDashboard()
    app.mainloop()
