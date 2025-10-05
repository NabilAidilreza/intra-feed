import os
import json
from dotenv import load_dotenv
import asyncio
from connectors.gmail_connector import get_gmail_service, monitor_new_emails
from connectors.telegram_connector import monitor_telegram 
from display.terminal_display import *

load_dotenv()
AUTH_FOLDER = "auth"

# ------------------ Gmail Setup ------------------

async def monitor_account(account_email, cred_file, token_file, interval=60):
    service = get_gmail_service(cred_file, token_file)

    def callback(email_data):
        email_data["account"] = account_email
        display_message(email_data, service_name="GMAIL")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, monitor_new_emails, service, callback, interval)

def main_banner():
    # Title
    title = Text(f"\n📨 intra-feed \n", style="bold cyan")
    title.stylize("bold underline", 0, len(title))
    console.print(title)
    console.print("A personal feed aggregator that unifies Telegram, Gmail, and Outlook messages in a single terminal log.\n")
    # Info lines
    info1 = Text("⏱ Gmail updates every 1 minute", style="green")
    info2 = Text("💬 Telegram updates in real-time", style="magenta")
    console.print(info1)
    console.print(info2)

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
            console.print(f"[red]⚠ Credential file not found for {email}: {cred_file}[/red]")

        token_path = os.path.join(AUTH_FOLDER, token_file)
        if not os.path.exists(token_path):
            console.print(f"[red]⚠ Token file not found for {email}: {token_file}[/red]")

        # Build line to print
        line = Text()
        line.append("→ ", style="bright_green")
        line.append(email, style="bold white")
        if cred_file:
            line.append("  ", style="")
            line.append(f"[{cred_file}]", style="bright_black")
        console.print(line)

# ------------------ Main ------------------
async def main():
    console = Console()
    console.print("Checking environment variables...", style="bold #FFA500")
    # ------------------ Email Config ------------------
    raw = os.getenv("GMAIL_ACCOUNTS")
    try:
        accounts = json.loads(raw)
        log_success("✅ Valid JSON for Gmail Accounts!")
    except json.JSONDecodeError as e:
        log_error(f"❌ Invalid JSON: {e}")
        raise RuntimeError("Invalid JSON")

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

    # Add gmail task
    tasks = [
        monitor_account(account, creds["Credentials"], creds["Token"], interval=60)
        for account, creds in accounts.items()
    ]

    # Add telegram task
    tasks.append(monitor_telegram(tg_api_id, tg_api_hash, tg_chat_ids))

    main_banner()
    check_gmail_settings(accounts)

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        console.print("\n🛑 [bold red]Aggregator stopped by user.[/bold red]", justify="center")

if __name__ == "__main__":
    asyncio.run(main())


# # Get Chat IDS
# from telethon import TelegramClient
# client = TelegramClient("session_name", tg_api_id, tg_api_hash)

# async def list_chats():
#     async for dialog in client.iter_dialogs():
#         # dialog.name = chat/group name
#         # dialog.id = chat ID
#         print(f"Name: {dialog.name}, ID: {dialog.id}, Type: {'Group' if dialog.is_group else 'Private'}")



# with client:
#     client.loop.run_until_complete(list_chats())