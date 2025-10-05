
# Personal Unified Feed Aggregator

A **terminal-based personal feed aggregator** that collects your messages from **Telegram**, **Gmail**, and **Outlook**, and displays them in a live log. Think of it as a personal RSS feed for all your messages.

---

## Features

- Unified terminal log for Telegram, Gmail, and Outlook messages
- Easy to monitor multiple accounts at once
- Minimal, lightweight, and runs in the background

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/personal-unified-feed.git
cd personal-unified-feed
```

### 2. Create your credentials

- **Gmail / Outlook:**  
  Set up a **Google Cloud Console OAuth Client** and download your credentials JSON file.
  
- **Telegram:**  
  Create a **Telegram API App** to obtain your `api_id` and `api_hash`.

> ⚠️ Each user must create their own credentials. Do not share your credentials publicly.

### 3. Create a `.env` file

In the project root, create a `.env` file with the following format:

```env
GMAIL_ACCOUNTS='{
  "user1@gmail.com": {"Credentials": "something_credentials.json", "Token": "token1.json"},
  "user2@gmail.com": {"Credentials": "something_credentials.json", "Token": "token2.json"},
  ... if want to add more
}'
TG_API_ID=0
TG_API_HASH=''
TG_CHAT_IDS=[chat_id1, chat_id2, ...]
```

- `GMAIL_ACCOUNTS`: JSON object mapping Gmail/Outlook accounts to their credentials and token files.  
- `TG_API_ID` / `TG_API_HASH`: Your Telegram API credentials.  
- `TG_CHAT_IDS`: List of Telegram chat IDs to monitor.

---

## Usage

```bash
python main.py
```

> The program will start monitoring your configured accounts and display new messages in real-time in the terminal log.

---

## Contributing

Feel free to open issues or submit pull requests to improve the aggregator!

---

## License

This project is licensed under the MIT License.
