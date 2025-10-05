import os
import json
from time import sleep
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
AUTH_FOLDER = "auth"  # folder where credentials and token files are stored


def get_gmail_service(credentials_file, token_file):
    """Authenticate with Gmail API using OAuth2; saves token for future use."""
    creds = None
    token_path = os.path.join(AUTH_FOLDER, token_file)
    credentials_path = os.path.join(AUTH_FOLDER, credentials_file)

    # Load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next time
        with open(token_path, "w") as token_file_obj:
            token_file_obj.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def set_up_gmail_services(): # Use function if lose token file # For credentials must get from Google Cloud
    raw = os.getenv("GMAIL_ACCOUNTS")
    if raw is None:
        raise RuntimeError("GMAIL_ACCOUNTS not found in environment")
    accounts = json.loads(raw)
    for key,value in accounts.items():
        cred = value["Credentials"]
        token = value["Token"]
        service = get_gmail_service(cred,token)
        # Make use you have set up the OAuth client and added test users
        sleep(20)

def get_unread_emails(service, max_results=10):
    """Fetch unread emails from Gmail's Primary tab only, including timestamp, sorted newest first."""
    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread category:primary",
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return []

        emails = []
        for msg in messages:
            msg_id = msg["id"]
            msg_data = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()

            payload = msg_data.get("payload", {})
            headers = payload.get("headers", [])
            subject = sender = None
            for header in headers:
                if header.get("name") == "Subject":
                    subject = header.get("value")
                elif header.get("name") == "From":
                    sender = header.get("value")

            snippet = msg_data.get("snippet", "")
            
            # Get timestamp
            internal_ts = int(msg_data.get("internalDate", 0)) / 1000  # convert ms to s
            timestamp = datetime.fromtimestamp(internal_ts).strftime("%Y-%m-%d %H:%M:%S")

            emails.append({
                "id": msg_id,
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
                "timestamp": timestamp,
                "internal_ts": internal_ts  # keep numeric for sorting
            })

        # Sort emails by timestamp descending (newest first)
        emails.sort(key=lambda e: e["internal_ts"], reverse=True)

        # Optionally remove internal_ts if not needed
        for e in emails:
            e.pop("internal_ts")

        return emails

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    
def monitor_new_emails(service, callback, interval=60, max_results=10): # callback is print
    seen_email_ids = set()
    while True:
        unread_emails = get_unread_emails(service, max_results)
        new_emails = [email for email in unread_emails if email['id'] not in seen_email_ids]

        for email_data in new_emails:
            seen_email_ids.add(email_data['id'])
            callback(email_data)  # <--- This is where the callback is called

        sleep(interval)


