import os
import json
from pathlib import Path
from display.terminal_display import Console, log_success, log_error, log_warning
from dotenv import load_dotenv

from telethon import TelegramClient
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

# Constants
ENV_FILE_PATH = Path(".env")

def load_environment() -> bool:
    """Load the .env file and return True if successful, False otherwise."""
    try:
        return load_dotenv(ENV_FILE_PATH)
    except Exception as e:
        log_error(f"Failed to load .env file: {e}")
        return False

def validate_env_variables(required_vars: list[str]) -> None:
    """Check if required environment variables are set."""
    has_error = False
    for var in required_vars:
        if not os.getenv(var):
            log_warning(f"Environment variable '{var}' is not set in .env file")
            has_error = True
    if has_error:
        log_error("Please set the correct .env variables accordingly!")
    else:
        log_success("Environment variables present.")


def replace_env_value(file_path, key, new_value):
    # Read the .env file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Replace the line with the new value
    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith(f'{key}='):
                # Safely format the list as a JSON string
                formatted_value = json.dumps(new_value)
                file.write(f'{key}={formatted_value}\n')
            else:
                file.write(line)


def check_config() -> None:
    """Check for .env file, load it, and validate environment variables."""
    
    # Check if .env file exists
    if not ENV_FILE_PATH.is_file():
        log_error(f".env file not found at {ENV_FILE_PATH}")
        log_warning("Please create a .env file with the required configuration")
        return

    log_success(f"Found .env file at {ENV_FILE_PATH}")
    
    # Load environment variables
    if not load_environment():
        return

    # Validate specific environment variables (modify as needed)
    required_vars = ["GMAIL_ACCOUNTS", "CLIENT_ID","TENANT_ID","TG_API_ID","TG_API_HASH","TG_CHAT_IDS"] 
    validate_env_variables(required_vars)


def edit_config():
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    client = TelegramClient("session_name", api_id, api_hash)

    # Define custom style for the prompt
    custom_style = Style.from_dict({
        "prompt": "fg:#00fff7 bold",         # bright cyan (electric blue) for prompt message
        "": "fg:#39ff14 bold",               # neon green for general text (answers)
        "pointer": "fg:#ff0080 bold",        # hot pink / magenta for pointer
        "selected": "fg:#ff0080 bold",       # hot pink / magenta for highlighted/selected choice
    })

    async def multi_prompt(options, msg, current=-1):
        # Add "Finish" option to the list
        display_options = options + ["Finish"]
        
        # Highlight current selection if provided
        if current != -1 and 0 <= current < len(display_options):
            display_options[current] = f"<selected>🔥 {display_options[current]}</selected>"
        
        # Create a PromptSession with fuzzy completion
        session = PromptSession(
            HTML(f"<prompt>{msg}: </prompt>"),
            completer=FuzzyWordCompleter(options),  # Use original options for completion
            complete_while_typing=True,
            style=custom_style,
            key_bindings=KeyBindings()
        )
        
        # Get user selection
        choice = await session.prompt_async()
        # Remove the "🔥 " prefix if present
        choice = choice.replace("🔥 ", "")
        return choice

    async def list_and_select_chats():
        # Store all chats in a list
        chat_list = []
        async for dialog in client.iter_dialogs():
            chat_list.append({
                'name': dialog.name,
                'id': dialog.id,
                'type': 'Group' if dialog.is_group else 'Private'
            })
        
        # Prepare chat options for the prompt
        chat_options = [f"{chat['name']} (ID: {chat['id']}, {chat['type']})" for chat in chat_list]
        selected_chats = []
        
        current_idx = -1  # Track current selection for highlighting
        while chat_options:
            try:
                # Prompt user to select a chat or finish
                choice = await multi_prompt(chat_options, "Select a chat or type Finish", current_idx)
                
                if choice == "Finish":
                    break
                    
                # Find and process the selected chat
                for idx, option in enumerate(chat_options):
                    if choice == option:
                        selected_chats.append(chat_list[idx])
                        print(f"Added: {chat_list[idx]['name']} (ID: {chat_list[idx]['id']}, {chat_list[idx]['type']})")
                        # Remove the selected chat from options
                        chat_options.pop(idx)
                        chat_list.pop(idx)
                        current_idx = min(current_idx, len(chat_options) - 1)  # Adjust current index
                        break
                else:
                    print("Invalid selection. Please choose a chat from the list or 'Finish'.")
                    
            except KeyboardInterrupt:
                print("\nSelection interrupted. Finishing...")
                break
        
        console = Console()
        # Print selected chats
        if selected_chats:
            console.print("\nSelected Chats:",style="bold yellow")
            console.rule("[bold green]-[/bold green]")
            for chat in selected_chats:
                console.print(f"Name: [bold cyan]{chat['name']}[/bold cyan], ID: {chat['id']}, Type: [bold bright_magenta]{chat['type']}[/bold bright_magenta]")
            console.rule("[bold green]-[/bold green]")

        return selected_chats

    with client:
        selected = client.loop.run_until_complete(list_and_select_chats())
        if selected:
            ids = [select["id"] for select in selected]
            Console().print("[bold yellow]Update selected chats to .env variable? (y/n): [bold yellow]", end="")
            user_input = input()
            if user_input.upper() == "Y":
                replace_env_value('.env', 'TG_CHAT_IDS', ids)
                log_success("Updated .env with selected chats.")
            elif user_input.upper() == "N":
                log_error("Selected chats dropped.")
            else:
                log_error("Invalid input. Operation aborted.")
        

def main() -> None:
    """Main function to run the configuration menu."""
    check_config()
    console = Console()
    # Optional: Add a simple menu loop for interactivity
    while True:
        console.print("[bold yellow]Press 'q' to quit or 'e' to edit .env:[/bold yellow] ", end="")
        user_input = input("").lower()
        if user_input == 'q':
            log_success("Exiting program")
            break
        elif user_input == 'e':
            log_warning("Editing configuration...")
            edit_config()
        else:
            log_error("Invalid input. Press 'q' to quit or 'e' to edit.")

if __name__ == "__main__":
    main()