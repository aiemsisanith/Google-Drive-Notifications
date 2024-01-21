import os
from googleapiclient.discovery import build
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import time
# SendGrid API key
SENDGRID_API_KEY = 'SENDGRID API Key'

# Email configuration
SENDER_EMAIL = 'sender email'
RECIPIENT_EMAIL = 'recipient email'

def send_email(subject, body):
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAIL,
        subject=subject,
        plain_text_content=body)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code == 202:
            print("Email sent!")
        else:
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response body: {response.body}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        print("Email unsuccessful")

def get_folder_name(drive, folder_id):
    try:
        folder_info = drive.auth.service.files().get(fileId=folder_id).execute()
        return folder_info['title']
    except Exception as e:
        print(f"Error getting folder name for {folder_id}: {str(e)}")
        return None

def watch_for_new_file():
    # Authenticate and create GoogleDrive instance
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    # Set up a query to look for new files
    query = "trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()

    # Keep track of the initial file IDs, names, owners, and parent folder IDs
    initial_file_info = {
        file['id']: {
            'title': file['title'],
            'owner_email': file['owners'][0]['emailAddress'],
            'parent_folder_id': file['parents'][0]['id'] if file['parents'] else None
        }
        for file in file_list
    }

    print("Watching for new files...")

    while True:
        # Check for new files
        file_list = drive.ListFile({'q': query}).GetList()
        current_file_info = {
            file['id']: {
                'title': file['title'],
                'owner_email': file['owners'][0]['emailAddress'],
                'parent_folder_id': file['parents'][0]['id'] if file['parents'] else None
            }
            for file in file_list
        }

        # Find the new file IDs and information
        new_file_info = {file_id: current_file_info[file_id] for file_id in
                         (set(current_file_info) - set(initial_file_info))}

        # If there are new files, send an email with the updated subject and print names, owner profiles, and parent folder names
        if new_file_info:
            for file_id, file_info in new_file_info.items():
                folder_name = get_folder_name(drive, file_info['parent_folder_id']) if file_info[
                    'parent_folder_id'] else "Root"
                subject = f"{file_info['owner_email']} added a new file to folder {folder_name}"
                body = f"New file uploaded to your Google Drive:\n"
                body += f"- {file_info['title']}"

                send_email(subject, body)
                print(
                    f"New file uploaded: {file_info['title']} (Uploaded by: {file_info['owner_email']}, Folder: {folder_name})")

        # Update the initial file info
        initial_file_info = current_file_info


        #check drive every 1 second

        time.sleep(1)


# Run the watch_for_new_file function
watch_for_new_file()


