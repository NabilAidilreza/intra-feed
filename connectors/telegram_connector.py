import asyncio
from time import sleep
from telethon import TelegramClient, events
from telethon.tl.types import MessageService
from display.terminal_display import display_message,Console,Text


def login(): # If .session file is lost
    api_id = 0
    api_hash = ''
    client = TelegramClient('session_name', api_id, api_hash)

    async def main():
        await client.start()
        print("Logged in as:", (await client.get_me()).username)

    with client:
        client.loop.run_until_complete(main())

# Put the chat IDs of the groups/chats you want to monitor

last_seen = {}
def is_likely_advert(msg_text):
    if not msg_text:
        return True
    if "http://" in msg_text or "https://" in msg_text or "bit.ly" in msg_text:
        return True
    if msg_text.count("\n") > 5:
        return True
    return False

async def get_chat_name(client,chat_id):
    entity = await client.get_entity(chat_id)
    return entity.title if hasattr(entity, "title") else entity.username or str(entity.id)

def create_telegram_client(api_id, api_hash, target_chat_ids):
    client = TelegramClient("session_name", api_id, api_hash)

    @client.on(events.NewMessage(chats=target_chat_ids))
    async def tg_handler(event):
        msg = event.message
        if isinstance(msg, MessageService):
            return
        if is_likely_advert(msg.text):
            return

        chat_id = event.chat_id
        if chat_id in last_seen and msg.id <= last_seen[chat_id]:
            return
        last_seen[chat_id] = msg.id

        sender = await msg.get_sender()
        sender_name = sender.username or f"{sender.first_name or ''} {sender.last_name or ''}".strip()

        telegram_data = {
            "sender": sender_name,
            "text": msg.text,
            "chat_id": chat_id
        }
        display_message(telegram_data, service_name="TELEGRAM")

    return client

async def monitor_telegram(api_id, api_hash, target_chat_ids):
    client = create_telegram_client(api_id, api_hash, target_chat_ids)
    await client.start()
    console = Console()
    console.print("\n> Initializing Telegram monitor...", style="bold magenta")
    console.print("[bright_black]Scanning target chats...[/bright_black]")

    for cid in target_chat_ids:
        # start fetching name concurrently
        fetch_task = asyncio.create_task(get_chat_name(client, cid))

        # animate a short dot-progress on the same line while waiting
        dots_cycle = [" .  ", " .. ", " ...", " .. "]
        dot_index = 0
        # print initial resolving line (no newline so we can overwrite)
        console.print(f"[bright_green]→[/bright_green] [bright_black]Resolving{dots_cycle[dot_index]}[/bright_black]", end="\r")

        # loop until fetch_task completes; animate quickly
        while not fetch_task.done():
            await asyncio.sleep(0.06)            # small delay to keep it snappy
            dot_index = (dot_index + 1) % len(dots_cycle)
            console.print(f"[bright_green]→[/bright_green] [bright_black]Resolving{dots_cycle[dot_index]}[/bright_black]", end="\r")

        # when done, get the result and print final resolved line
        try:
            name = fetch_task.result()
        except Exception as e:
            name = f"<error: {e}>"

        # clear the resolving line and print the final styled line
        # printing a padded blank line first avoids leftover characters from shorter strings
        clear_padding = " " * 40
        console.print(f"{clear_padding}", end="\r")  # clear
        console.print(
            f"[bright_green]→[/bright_green] [bold white]{name}[/bold white] "
            f"[bright_black]• resolved[/bright_black]"
        )

        # tiny stagger so lines don't all appear at once
        await asyncio.sleep(0.04)

    console.print("\n[bright_black]Scan complete. Monitoring started...[/bright_black]\n")
    console.rule("[bold green]•[/bold green]")
    console.print("\n[bright_yellow]Awaiting first message...[/bright_yellow]\n")
    # Run the live monitor
    await client.run_until_disconnected()

