# Telegram Message Forwarding Bot

A Telegram bot that monitors groups/chats for specific keywords and automatically forwards matching messages to a designated channel.

## Features

- 🔍 **Keyword Monitoring**: Track specific keywords in group messages
- 📤 **Auto-Forward**: Automatically forward matching messages to a channel
- 🚫 **Duplicate Detection**: Prevents forwarding duplicate messages
- 🛡️ **Blocked Words**: Filter out messages containing blocked words
- 📸 **Media Support**: Forwards photos, videos, documents, audio, GIFs, stickers, and text
- 🔢 **Number Requirement**: Only forwards messages that contain numbers
- 👥 **Group Filtering**: Optionally monitor only specific groups

## Prerequisites

- Python 3.8+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- Channel/Group ID for forwarding destination
- Group IDs (optional, for filtering)

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
BOT_TOKEN=your_bot_token_from_botfather
CHANNEL_ID=your_channel_id
KEYWORD=keyword1,keyword2,keyword3
GROUP_ID=group1_id,group2_id
BLOCKED_WORDS=blocked1,blocked2
```

## Getting Your Credentials

### Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions and copy your bot token

### Channel/Group ID
1. Search for [@userinfobot](https://t.me/userinfobot) or [@getidsbot](https://t.me/getidsbot)
2. Forward a message from your channel/group to the bot
3. The bot will show you the ID

### Keywords
List keywords separated by commas. The bot will forward messages containing any of these keywords.

### Group IDs (Optional)
Leave empty to monitor all groups. To monitor specific groups only, list their IDs separated by commas.

## Running the Bot

```bash
python bot\ \(1\).py
```

Or if using the folder structure:
```bash
python "New folder/bot (1).py"
```

## How It Works

1. The bot listens for messages in monitored groups
2. When a message contains a keyword:
   - Checks for numbers (must have at least one number)
   - Checks against blocked words
   - Verifies it's not a duplicate
3. If all checks pass, forwards the message to the configured channel
4. Tracks message hashes to prevent duplicates

## Configuration Details

- **KEYWORD**: Required - comma-separated list of keywords to match
- **CHANNEL_ID**: Required - destination channel for forwarded messages
- **GROUP_ID**: Optional - specific group IDs to monitor (all groups if empty)
- **BLOCKED_WORDS**: Optional - words that trigger message filtering
- **BOT_TOKEN**: Required - your Telegram bot token

## Logging

The bot logs all activities to the console including:
- Messages matched and forwarded
- Skipped messages and reasons
- Connection status
- Errors and retries

## Duplicate Detection

The bot maintains a `sent_hashes.json` file to track already-forwarded messages. This prevents the same message from being forwarded multiple times.

## Health Check

The bot runs a health check server on port 8080 that responds with "OK" to any GET request.

## Troubleshooting

### Bot doesn't receive messages
- Verify the bot has permission to read messages in the groups
- Check that keywords are correctly configured
- Ensure the bot is not muted

### Messages not forwarding
- Verify the channel ID is correct
- Check that the bot is an admin in the destination channel
- Review the logs for specific error messages

### Conflict error
- This means another instance of the bot is running
- The bot automatically handles this and retries

## Error Handling

The bot automatically:
- Retries on network errors
- Detects and handles conflicts (multiple instances)
- Maintains connection through polling
- Skips pending updates on restart

## License

MIT License - feel free to use and modify

## Support

For issues and questions, please open an issue on GitHub.
