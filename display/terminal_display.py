from rich.console import Console
from rich.text import Text
import time
import re

console = Console()

# ------------------ Helper Functions ------------------
def log_success(message: str):
    console.print(Text(message, style="bold light_green"))

def log_error(message: str):
    console.print(Text(message, style="bold red"))


# ------------------------------------------------------

# Service-specific color mapping
SERVICE_COLORS = {
    "GMAIL": "green",
    "TELEGRAM": "bright_cyan",
    "OUTLOOK": "blue",  # softer than bright red, still distinct
}

# Content colors for contrast (first, second, third fields)
CONTENT_COLORS = {
    "GMAIL": {"field1": "bright_cyan", "field2": "yellow", "field3": "bright_magenta"},
    "TELEGRAM": {"field1": "bright_green", "field2": "bright_yellow", "field3": "bright_cyan"},
    "OUTLOOK": {
        "field1": "yellow",  
        "field2": "bright_blue",     
        "field3": "bright_white"     
    },
}
def display_message(message_data, service_name="SERVICE", pause=1):
    """
    Generalized display for multiple services.
    Assumes message_data has 3 fields:
      - field1: sender / username
      - field2: email / chat_id
      - field3: subject / text
    Only prints `account` if service is an email type (GMAIL or OUTLOOK).
    """
    # Extract fields
    fields0_raw = message_data.get("account", "NIL")
    field1_raw = message_data.get("sender", "Unknown")
    field2_raw = message_data.get("email") or str(message_data.get("chat_id", "N/A"))
    field3_raw = message_data.get("subject") or message_data.get("text") or "(No Content)"
    field4_raw = message_data.get("timestamp", "NIL")

    # Determine colors
    service_color = SERVICE_COLORS.get(service_name.upper(), "green")
    content_colors = CONTENT_COLORS.get(service_name.upper(), CONTENT_COLORS["GMAIL"])

    # Attempt to parse email if applicable
    sender_name = field1_raw
    sender_email = field2_raw
    m = re.match(r'^(?P<name>.*?)\s*<(?P<email>[^>]+)>$', field1_raw.strip())
    if m:
        sender_name = m.group("name").strip() or "Unknown"
        sender_email = m.group("email").strip()

    MAX_MSG_WIDTH = 120  # width of main message before timestamp

    # Build Rich text
    line = Text()
    line.append(f"[{service_name}] ", style=f"bold {service_color}")

    # Add Email Account line if it's email service
    if service_name.upper() in ["GMAIL", "OUTLOOK"]:
        if field4_raw != "NIL":
            line.append(f"Email Acct: {fields0_raw} [", style="bold bright_magenta")
            line.append(f"{field4_raw}", style="bold white")
            line.append("]\n", style="bold bright_magenta")
        else:
            line.append(f"Email Acct: {fields0_raw}\n", style="bold bright_magenta")


    # Build main message part
    main_msg = Text()
    main_msg.append(sender_name, style=content_colors["field1"])
    if sender_email:
        main_msg.append(f" <{sender_email}>", style=content_colors["field2"])
    main_msg.append("  >>  ")
    main_msg.append(field3_raw, style=content_colors["field3"])

    # Calculate padding to align timestamp
    msg_len = len(main_msg.plain)
    if msg_len < MAX_MSG_WIDTH:
        padding = MAX_MSG_WIDTH - msg_len
        main_msg.append(" " * padding)



    line.append(main_msg)

    # Print line + separator
    console.print(line)
    console.print(Text("-" * 120, style="dim green"))

    time.sleep(pause)
