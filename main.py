import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from connectors.gmail_connector import get_gmail_service, monitor_new_emails
from connectors.telegram_connector import monitor_telegram 
from connectors.outlook_connector import monitor_new_outlook_emails, check_token_and_get_active_email
from display.terminal_display import *

load_dotenv()
ENV_FILE_PATH = Path(".env")
AUTH_FOLDER = "auth"

# ----------------- Load / Check environment ----------------
def load_environment() -> bool:
    """Load the .env file and return True if successful, False otherwise."""
    try:
        return load_dotenv(ENV_FILE_PATH)
    except Exception as e:
        log_error(f"Failed to load .env file: {e}")
        return False
    
def validate_env_variables():
    """Check if required environment variables are set."""
    # ------------------ Email Config ------------------
    raw = os.getenv("GMAIL_ACCOUNTS")
    try:
        accounts = json.loads(raw)
        log_success("✅ Valid JSON for Gmail Accounts!")
    except json.JSONDecodeError as e:
        log_error(f"❌ Invalid JSON: {e}")
        raise RuntimeError("Invalid JSON")
    
    # ------------------ Outlook Config ------------------
    outlook_cli_id = os.getenv("CLIENT_ID")
    outlook_ten_id = os.getenv("TENANT_ID")

    if outlook_cli_id:
        log_success("✅ Outlook Client ID exists!")
    else:
        log_error("❌ Outlook Client ID doesn't exist!")
        raise RuntimeError("Refer to logs.")

    if outlook_ten_id:
        log_success("✅ Outlook Tenant ID exists!")
    else:
        log_error("❌ Outlook Tenant ID doesn't exist! (But not in use ✅)")

    # ------------------ Telegram Config ------------------
    tg_api_id = os.getenv("TG_API_ID")
    tg_api_hash = os.getenv("TG_API_HASH")
    tg_chat_ids = json.loads(os.getenv("TG_CHAT_IDS"))

    if tg_api_id:
        log_success("✅ Telegram App API ID exists!")
    else:
        log_error("❌ Telegram App API ID doesn't exist!")
        raise RuntimeError("Refer to logs.")

    if tg_api_hash:
        log_success("✅ Telegram App API HASH exists!")
    else:
        log_error("❌ Telegram App API HASH doesn't exist!")
        raise RuntimeError("Refer to logs.")

    if tg_chat_ids:
        log_success("✅ Telegram Chat IDs present!")
    else:
        log_error("❌ Telegram Chat IDs not present!")
        raise RuntimeError("Refer to logs.")

    log_success("✅ Environment variables OK!")    

    return accounts,outlook_cli_id,outlook_ten_id,tg_api_id,tg_api_hash,tg_chat_ids


def load_and_check_env():
    if not ENV_FILE_PATH.is_file():
        log_error(f".env file not found at {ENV_FILE_PATH}")
        log_warning("Please create a .env file with the required configuration")
        raise Exception

    log_success(f"Found .env file")
    
    # Load environment variables
    if not load_environment():
        return
    
    return validate_env_variables()

# ------------------ Gmail / Outlook Monitor Asyncio ------------------

async def monitor_account(account_email, cred_file, token_file, interval=60):
    """
    Async wrapper to run synchronous Gmail monitor in an executor.
    """
    service = get_gmail_service(cred_file, token_file)

    def callback(email_data):
        email_data["account"] = account_email
        display_message(email_data, service_name="GMAIL")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, monitor_new_emails, service, callback, interval)

async def monitor_outlook(outlook_email,client_id, tenant_id, interval=60, max_results=10):
    """
    Async wrapper to run synchronous Outlook monitor in an executor.
    """
    def callback(email_data):
        email_data["account"] = outlook_email
        display_message(email_data, service_name="OUTLOOK")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        monitor_new_outlook_emails,
        callback,
        client_id,
        tenant_id,
        interval,
        max_results
    )

# ------------------ Gmail / Outlook Setup ------------------

def main_banner():
    # Title
    title = Text(f"\n📨 intra-feed \n", style="bold cyan")
    title.stylize("bold underline", 0, len(title))
    console.print(title)
    console.print("A personal feed aggregator that unifies Telegram, Gmail, and Outlook messages in a single terminal log.\n")
    # Info lines
    info1 = Text("⏱  Gmail updates every 1 minute", style="green")
    info2 = Text("⏱  Outlook updates every 1 minute", style="blue")
    info3 = Text("💬 Telegram updates in real-time", style="magenta")
    console.print(info1)
    console.print(info2)
    console.print(info3)

def check_gmail_settings(accounts):
    console.print("\n> Initializing Gmail monitor...", style="bold green")

    # Normalize to (email, details) pairs whether accounts is a dict or a list
    if isinstance(accounts, dict):
        pairs = accounts.items()
    else:
        pairs = accounts  # assume it's already an iterable of (email, details)

    for email, details in pairs:
        # Check if credential JSON exists
        cred_file = ""
        token_file = ""
        if isinstance(details, dict):
            cred_file = details.get("Credentials", "")
            token_file = details.get("Token", "")

        cred_path = os.path.join(AUTH_FOLDER, cred_file)
        if not os.path.exists(cred_path):
            log_error(f"⚠ Credential file not found for {email}: {cred_file}")

        token_path = os.path.join(AUTH_FOLDER, token_file)
        if not os.path.exists(token_path):
            log_error(f"⚠ Token file not found for {email}: {token_file}")

        line = Text()
        line.append("→ ", style="bright_green")
        line.append(email, style="bold white")
        if cred_file:
            line.append("  ", style="")
            line.append(f"[{cred_file}]", style="bright_black")
        console.print(line)

def check_outlook_settings():
    console.print("\n> Initializing Outlook monitor...", style="bold blue")
    outlook_email = check_token_and_get_active_email()
    # Build line to print
    line = Text()
    line.append("→ ", style="bright_green")
    line.append(outlook_email, style="bold white")
    console.print(line)
    return outlook_email


# ------------------ Main ------------------
async def main():
    console = Console()
    # Intial set up 
    console.print("Checking environment variables...", style="bold #FFA500")
    accounts,outlook_cli_id,outlook_ten_id,tg_api_id,tg_api_hash,tg_chat_ids = load_and_check_env()
    main_banner()
    check_gmail_settings(accounts)
    outlook_email = check_outlook_settings()

    # Add Gmail task
    tasks = [
        monitor_account(account, creds["Credentials"], creds["Token"], interval=60)
        for account, creds in accounts.items()
    ]

    # Outlook task
    tasks.append(monitor_outlook(outlook_email,outlook_cli_id, outlook_ten_id,interval=60))

    # Add Telegram task
    tasks.append(monitor_telegram(tg_api_id, tg_api_hash, tg_chat_ids))

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        log_error("\n🛑 Aggregator stopped by user.", justify="center")

## If token cant be read, just delete token?.json (s) and outlooktoken.json to regen
if __name__ == "__main__":
    asyncio.run(main())