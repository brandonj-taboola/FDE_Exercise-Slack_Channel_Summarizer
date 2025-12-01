# Slack Channel Summarizer

AI-powered Slack channel summarizer that uses Claude (Anthropic) to generate intelligent summaries of your Slack conversations. Supports both CLI usage and Slack slash commands.

## Features

- **Smart Summarization**: Uses Claude Sonnet 4 to analyze and summarize Slack conversations
- **Thread Support**: Includes thread replies by default for comprehensive context
- **Flexible Time Ranges**: Summarize from 1 to 30 days of history
- **Multiple Interfaces**:
  - Slack slash command (`/summarize`)
  - Command-line interface (CLI)
- **Rich Metadata**: Includes participant counts, message stats, and thread information
- **Automatic Formatting**: Slack-compatible markdown output

## Prerequisites

- Python 3.10 or higher
- Slack workspace with admin access
- Anthropic API key
- ngrok (for exposing local server to Slack)

## Installation

### 1. Clone or Download the Project

```bash
cd slack-summarizer
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install ngrok

**Windows (using winget):**
```bash
winget install Ngrok.Ngrok
```

**macOS:**
```bash
brew install ngrok
```

**Linux:**
```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

## Configuration

### 1. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Slack Bot Token (starts with xoxb-)
SLACK_BOT_TOKEN=xoxb-your-token-here

# Anthropic API Key (starts with sk-ant-)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Server port (defaults to 3000)
PORT=3000
```

### 2. Get Your Slack Bot Token

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Channel Summarizer") and select your workspace
4. Navigate to **OAuth & Permissions**
5. Add the following **Bot Token Scopes**:
   - `channels:history` - Read messages from public channels
   - `channels:read` - View basic channel info
   - `chat:write` - Post messages (for CLI posting feature)
   - `users:read` - Read user information
6. Click **Install to Workspace** at the top
7. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 3. Get Your Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

### 4. Invite Bot to Channels

In Slack, invite your bot to channels you want to summarize:
```
/invite @YourBotName
```

## Local Deployment

### Method 1: Slack Slash Command (Recommended)

#### Step 1: Start the Flask Server

```bash
python server.py
```

The server will start on `http://localhost:3000`

#### Step 2: Authenticate and Start ngrok

```bash
# Authenticate ngrok (one-time setup)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start ngrok tunnel
ngrok http 3000
```

Copy the **Forwarding URL** (e.g., `https://abc123.ngrok-free.app`)

#### Step 3: Configure Slack Slash Command

1. Go to your Slack app settings: [Slack API Apps](https://api.slack.com/apps)
2. Select your app
3. Click **Slash Commands** in the sidebar
4. Click **Create New Command**
5. Configure:
   - **Command**: `/summarize`
   - **Request URL**: `https://your-ngrok-url.ngrok-free.app/slack/summarize`
   - **Short Description**: "Summarize channel messages with AI"
   - **Usage Hint**: `[#channel] [no-threads] [Xd]`
6. Click **Save**
7. **Reinstall** your app to the workspace (OAuth & Permissions page)

#### Step 4: Test in Slack

In any channel where your bot is invited:
```
/summarize
```

### Method 2: Command-Line Interface (CLI)

Test the summarizer directly from the command line:

```bash
# Test API connections
python main.py test

# List available channels
python main.py channels

# Summarize a channel
python main.py summarize general

# With options
python main.py summarize general --hours 48 --threads
python main.py summarize general --style brief
python main.py summarize general --post  # Post summary back to Slack
```

## Usage

### Slash Command Options

The `/summarize` command defaults to **30 days** with **threads included**:

**Basic Usage:**
```
/summarize                          # Current channel, 30 days, with threads
/summarize no-threads               # Current channel, 30 days, no threads
/summarize 7d                       # Current channel, 7 days, with threads
/summarize #channel-name            # Specific channel, 30 days, with threads
```

**Advanced Usage:**
```
/summarize 1d                       # Current channel, 1 day, with threads
/summarize 14d                      # Current channel, 14 days, with threads
/summarize no-threads 7d            # Current channel, 7 days, no threads
/summarize #general 7d              # #general, 7 days, with threads
/summarize #general no-threads 14d  # #general, 14 days, no threads
```

**Parameters:**
- **Time Range**: `1d` to `30d` (default: `30d`)
- **Threads**: Included by default, use `no-threads` to exclude
- **Channel**: Specify `#channel-name` or omit to use current channel

### CLI Options

```bash
# Summarize command
python main.py summarize CHANNEL [OPTIONS]

Options:
  --hours, -h INTEGER              Hours of history (default: 24)
  --style, -s [detailed|brief]     Summary style (default: detailed)
  --threads/--no-threads, -t       Include thread replies (default: no threads)
  --post/--no-post                 Post summary back to Slack
  --post-to, -p TEXT               Channel to post to (default: same channel)

# Other commands
python main.py channels              # List available channels
python main.py test                  # Test API connections
```

## Project Structure

```
slack-summarizer/
├── server.py           # Flask server for Slack integration
├── slack_client.py     # Slack API client
├── summarizer.py       # Claude-powered summarizer
├── main.py            # CLI interface
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## Testing Locally

### 1. Test API Connections

```bash
python main.py test
```

Expected output:
```
Testing connections...

✓ Slack connected - X channels accessible
✓ Anthropic API key valid
```

### 2. Test Channel Listing

```bash
python main.py channels
```

### 3. Test CLI Summarization

```bash
python main.py summarize general --hours 24
```

### 4. Test Slash Command

1. Ensure server is running: `python server.py`
2. Ensure ngrok is running: `ngrok http 3000`
3. In Slack, type: `/summarize`

### 5. Check Server Health

Visit: `http://localhost:3000/health`

Expected response:
```json
{"status": "ok"}
```

## Troubleshooting

### Bot Can't Access Channels
- Make sure you invited the bot: `/invite @YourBotName`
- Check bot has required scopes in Slack API settings

### "SLACK_BOT_TOKEN not found"
- Verify `.env` file exists in project root
- Check token starts with `xoxb-`
- Make sure `.env` has no extra spaces

### "ANTHROPIC_API_KEY not found"
- Verify `.env` file exists
- Check key starts with `sk-ant-`
- Ensure you have API credits in Anthropic console

### Slash Command Not Working
- Verify ngrok is running and URL matches Slack config
- Check server is running on correct port
- Reinstall Slack app after changing command settings
- Check ngrok URL hasn't changed (free tier URLs change on restart)

### ngrok Version Error
- Update ngrok: `ngrok update`
- Minimum version required: 3.7.0

### Summary Times Out
- Large time ranges (30 days) with many messages may take time
- Check Anthropic API rate limits
- Consider reducing time range for very active channels

## Rate Limits

- **Slack API**: ~1 request per second (handled automatically)
- **Anthropic API**: Depends on your plan tier
- **ngrok Free**: 40 requests/minute (sufficient for testing)

## Security Notes

- Never commit `.env` file to version control
- Keep your API keys secret
- ngrok URLs are temporary on free tier - update Slack config when they change
- Consider using environment variables in production

## Development

To modify the summarization prompt, edit `summarizer.py`:
```python
def _build_prompt(self, formatted_messages, channel_name, style):
    # Customize the prompt here
```

To change default settings, edit `server.py`:
```python
days = 30  # Default time range
include_threads = True  # Default thread behavior
```

## License

This project is provided as-is for personal and commercial use.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review [Slack API Documentation](https://api.slack.com/docs)
3. Review [Anthropic API Documentation](https://docs.anthropic.com/)
