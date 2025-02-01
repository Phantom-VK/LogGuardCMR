import pickle
import smtplib
from email.mime.text import MIMEText
import os.path
from user_data import userData

# File path for user data pickle
file_path = "user_data.pkl"

# Email subject and body
subject = 'This is the subject of email'
body = 'This is the body of the email'

# Sender email and app password
app_password = 'lrjj pvxn gtsn nbka'
sender = 'adnankhan17371@gmail.com'
userData1=userData()

# Check if the file exists and load user data
if (os.path.exists("user_data.pkl")):
    with open("user_data.pkl", 'rb') as file:
        userData1 = pickle.load(file)
        print("Receiver "+userData1.email)
else:
    userData1 = userData1()
    print("User data file not found!")
  # Fallback email if file is not found

print(f"Sender: {sender}")  # Print recipient to check

recipient=userData1.email
# Function to send email
def send_email(subject, body, sender, recipient):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient  # Directly pass the email as a string

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, app_password)
            smtp_server.sendmail(sender, recipient, msg.as_string())
        print('Message sent successfully.')
    except Exception as e:
        print(f"Failed to send email: {e}")


# Send the email
send_email(subject, body, sender, recipient)