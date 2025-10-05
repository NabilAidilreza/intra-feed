import os
import requests
import json
from msal import PublicClientApplication, SerializableTokenCache
from time import sleep
from display.terminal_display import console  

# ===== CONFIG =====
SCOPES = ["Mail.Read"]

# ===== TOKEN PATH (always relative to project root) =====
AUTH_FOLDER = os.path.join(os.getcwd(), "auth")
TOKEN_CACHE_FILE = os.path.join(AUTH_FOLDER, "outlooktoken.json")


# ===== TOKEN CACHE =====
def load_cache():
    cache = SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache

def check_token_and_get_active_email():
    if not os.path.exists(TOKEN_CACHE_FILE):
        return None

    with open(TOKEN_CACHE_FILE, "r") as f:
        data = f.read()

    try:
        cache_json = json.loads(data)
    except json.JSONDecodeError:
        return None

    # MSAL cache stores accounts under "Account" key
    accounts = cache_json.get("Account", {})
    if not accounts:
        return None

    # Get the first username in the accounts
    first_account_obj = next(iter(accounts.values()))
    username = first_account_obj.get("username")
    return username

def save_cache(cache):
    os.makedirs(AUTH_FOLDER, exist_ok=True)
    with open(TOKEN_CACHE_FILE, "w") as f:
        f.write(cache.serialize())


# ===== MAIN LOGIN FUNCTION =====
def acquire_token(client_id, tenant_id=None):
    """
    Acquire Outlook token using MSAL with given client_id.
    Uses /common authority so any Microsoft account can login.
    tenant_id is optional for future flexibility.
    """
    authority = "https://login.microsoftonline.com/common"
    cache = load_cache()
    app = PublicClientApplication(client_id, authority=authority, token_cache=cache)

    # Try silent login if token exists
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            # console.print("🔄 Using cached token", style="green")
            return result

    # Device code flow
    console.print("🔐 No cached token found. Starting device code login...", style="yellow")
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError("Failed to create device flow. Check your app registration.")

    console.print(flow["message"], style="cyan")
    result = app.acquire_token_by_device_flow(flow)

    # Save cache after login
    save_cache(cache)

    if "access_token" in result:
        return result
    else:
        console.print("❌ Failed to acquire token: " + str(result.get("error_description")), style="bold red")
        return None


# ===== FETCH UNREAD EMAILS =====
def fetch_unread_emails_structured(access_token, max_results=10):
    """
    Fetch unread emails from Outlook and return a list of dicts.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = (
        "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
        f"?$filter=isRead eq false&$top={max_results}"
    )

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        console.print(f"❌ Outlook API Error: {e}", style="red")
        return []

    mails = res.json().get("value", [])
    formatted = []
    for mail in mails:
        sender = mail.get("from", {}).get("emailAddress", {}).get("address", "(unknown)")
        formatted.append({
            "sender": sender,
            "subject": mail.get("subject", "(no subject)"),
            "received": mail.get("receivedDateTime")
        })
    return formatted


# ===== SYNCHRONOUS MONITOR (for callback + executor in main.py) =====
def monitor_new_outlook_emails(callback, client_id, tenant_id=None, interval=60, max_results=10):
    """
    Polls Outlook for unread emails in a loop and calls the callback for each new email.
    Designed to be run in a ThreadPoolExecutor for async usage.
    """
    seen_email_ids = set()
    sleep(3)
    while True:
        token = acquire_token(client_id, tenant_id)
        if token and "access_token" in token:
            access_token = token["access_token"]
            emails = fetch_unread_emails_structured(access_token, max_results=max_results)

            for email in emails:
                email_id = f"{email['sender']}-{email['received']}"
                if email_id not in seen_email_ids:
                    seen_email_ids.add(email_id)
                    callback(email)
        else:
            console.print("❌ Failed to acquire Outlook token.", style="bold red")

        sleep(interval)
