import os
import pickle
import re
import threading

import customtkinter as ctk

from GUI.new_dashboard import SystemDashboard
from GUI.user_data import userData


class CTkSpinbox(ctk.CTkFrame):
    def __init__(self, parent, variable=None, min_val=0, max_val=23, step=1, **kwargs):
        super().__init__(parent, **kwargs)

        self.variable = variable if variable else ctk.StringVar(value=str(min_val))
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        # Create spinbox elements
        self.minus_button = ctk.CTkButton(self, text="-", width=30, command=self.decrease)
        self.entry = ctk.CTkEntry(self, width=50, textvariable=self.variable)
        self.plus_button = ctk.CTkButton(self, text="+", width=30, command=self.increase)

        # Layout
        self.minus_button.grid(row=0, column=0, padx=2)
        self.entry.grid(row=0, column=1, padx=2)
        self.plus_button.grid(row=0, column=2, padx=2)

    def increase(self):
        current = int(self.variable.get())
        if current < self.max_val:
            self.variable.set(str(current + self.step))

    def decrease(self):
        current = int(self.variable.get())
        if current > self.min_val:
            self.variable.set(str(current - self.step))


class WorkingHoursApp(ctk.CTkFrame):
    def __init__(self, master, switch_callback):
        super().__init__(master)
        self.switch_callback = switch_callback
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Variables
        self.email = ctk.StringVar()
        self.start_time = ctk.StringVar(value="9")
        self.end_time = ctk.StringVar(value="17")
        self.notify_login = ctk.BooleanVar(value=True)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Work Hours Settings",
            font=("Helvetica", 24)
        )
        self.title_label.grid(row=0, column=0, pady=(20, 30))

        # Email field
        self.email_label = ctk.CTkLabel(self.main_frame, text="Email Address:")
        self.email_label.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")

        self.email_entry = ctk.CTkEntry(
            self.main_frame,
            width=300,
            textvariable=self.email,
            placeholder_text="Enter your email"
        )
        self.email_entry.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Working hours
        self.hours_label = ctk.CTkLabel(self.main_frame, text="Working Hours:")
        self.hours_label.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="w")

        # Hours container
        self.hours_frame = ctk.CTkFrame(self.main_frame)
        self.hours_frame.grid(row=4, column=0, padx=20, pady=(0, 20))

        # Start time
        self.start_label = ctk.CTkLabel(self.hours_frame, text="Start:")
        self.start_label.grid(row=0, column=0, padx=(0, 10))

        self.start_spinbox = CTkSpinbox(self.hours_frame, variable=self.start_time)
        self.start_spinbox.grid(row=0, column=1, padx=10)

        # End time
        self.end_label = ctk.CTkLabel(self.hours_frame, text="End:")
        self.end_label.grid(row=0, column=2, padx=10)

        self.end_spinbox = CTkSpinbox(self.hours_frame, variable=self.end_time)
        self.end_spinbox.grid(row=0, column=3, padx=(10, 0))

        # Notification toggle
        self.notify_switch = ctk.CTkSwitch(
            self.main_frame,
            text="Notify on system login",
            variable=self.notify_login
        )
        self.notify_switch.grid(row=5, column=0, padx=20, pady=(0, 20))

        # Save button
        self.save_button = ctk.CTkButton(
            self.main_frame,
            text="Save Settings",
            command=self.save_settings,
            width=200
        )
        self.save_button.grid(row=6, column=0, pady=20)

    def save_settings(self):
        if self.is_valid_email(self.email.get()):
            with open("user_data.pkl", "wb") as file:
                newUserData = userData(
                    notifyLogin=self.notify_login.get(),
                    email=self.email.get(),
                    startingHours=self.start_time.get(),
                    endingHours=self.end_time.get(),
                    notifySummary=False,
                )
                pickle.dump(newUserData, file)
                self.switch_callback()
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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Navigation Example")
        self.geometry("1000x800")

        self.system_dashboard = SystemDashboard(self, self.switch_to_working_hours)
        self.working_hours_app = WorkingHoursApp(self, self.switch_to_system_dashboard)

        self.current_frame = None
        if os.path.exists("user_data.pkl"):
            self.switch_to_system_dashboard()

        else:
            self.switch_to_working_hours()

    def switch_to_system_dashboard(self):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = self.system_dashboard
        self.current_frame.pack(fill="both", expand=True)

    def switch_to_working_hours(self):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = self.working_hours_app
        self.current_frame.pack(fill="both", expand=True)



