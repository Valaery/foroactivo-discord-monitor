# Foroactivo Discord Monitor

Automatically monitor Foroactivo forums and send Discord notifications for new threads and replies.

## Features

- 🔐 Works with **private/login-required** forums
- 📬 **Two monitoring modes**:
  - 🆕 **Forum sections**: Get notified when new threads are created
  - 💬 **Specific threads**: Get notified when new replies are posted
- 🎨 Rich Discord embeds with author, preview, and direct links
- 🔄 Runs automatically via GitHub Actions (every 10 minutes)
- 💾 Smart state tracking to avoid duplicate notifications
- 🎯 Custom theme support (works with Foroactivo's custom templates)
- 🆓 Completely free (GitHub Actions free tier)
- ⚙️ Simple JSON configuration

## How It Works

1. The script runs every 10 minutes on GitHub Actions
2. Authenticates to your Foroactivo forum
3. Checks configured monitors:
   - **Forum sections** for new threads
   - **Specific threads** for new replies
4. Sends Discord webhook notifications with rich embeds
5. Saves state to avoid duplicate notifications

## Setup Instructions

### 1. Fork This Repository

Click the "Fork" button at the top of this page to create your own copy.

### 2. Create a Discord Webhook

1. Open your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Choose a channel for notifications
5. Copy the webhook URL

### 3. Configure GitHub Secrets

In your forked repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `FOROACTIVO_USERNAME` | Your forum username | `myusername` |
| `FOROACTIVO_PASSWORD` | Your forum password | `mypassword123` |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL | `https://discord.com/api/webhooks/...` |

### 4. Configure Monitors

1. Copy `config/threads.example.json` to `config/threads.json`
2. Edit `config/threads.json` to add what you want to monitor:

**Monitor Forum Sections (for new threads):**

```json
{
  "monitors": [
    {
      "id": "forum-announcements",
      "name": "Announcements",
      "type": "forum",
      "forum_url": "https://example.foroactivo.com",
      "section_url": "https://example.foroactivo.com/f5-announcements",
      "discord_webhook_env": "DISCORD_WEBHOOK_URL",
      "enabled": true
    }
  ]
}
```

**Monitor Specific Threads (for new replies):**

```json
{
  "monitors": [
    {
      "id": "thread-important",
      "name": "Important Discussion",
      "type": "thread",
      "forum_url": "https://example.foroactivo.com",
      "thread_url": "https://example.foroactivo.com/t123-thread-title",
      "discord_webhook_env": "DISCORD_WEBHOOK_URL",
      "enabled": true
    }
  ]
}
```

**Configuration Options:**
- `id`: Unique identifier (used for state tracking)
- `name`: Display name in Discord notifications
- `type`: `"forum"` for sections (new threads) or `"thread"` for specific threads (new replies)
- `forum_url`: Base URL of your Foroactivo forum
- `section_url`: Full URL of the forum section (for `type: "forum"`)
- `thread_url`: Full URL of the specific thread (for `type: "thread"`)
- `discord_webhook_env`: Name of the GitHub Secret containing the webhook URL
- `enabled`: Set to `false` to temporarily disable monitoring

### 5. Commit and Push

```bash
git add config/threads.json
git commit -m "Configure threads to monitor"
git push
```

### 6. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. Click "I understand my workflows, go ahead and enable them"

### 7. Test the Workflow

1. Go to **Actions** → **Monitor Foroactivo Forums**
2. Click **Run workflow** → **Run workflow**
3. Wait for completion and check Discord for a test notification

## How to Monitor Multiple Items

You can mix forum sections and specific threads in the `monitors` array:

```json
{
  "monitors": [
    {
      "id": "forum-announcements",
      "name": "Announcements",
      "type": "forum",
      "section_url": "https://example.foroactivo.com/f5-announcements",
      "enabled": true
    },
    {
      "id": "forum-applications",
      "name": "Applications",
      "type": "forum",
      "section_url": "https://example.foroactivo.com/f13-applications",
      "enabled": true
    },
    {
      "id": "thread-important",
      "name": "Important Thread",
      "type": "thread",
      "thread_url": "https://example.foroactivo.com/t123-important",
      "enabled": true
    }
  ]
}
```

**Note**:
- `type: "forum"` monitors for **new threads** in that section
- `type: "thread"` monitors for **new replies** in that specific thread

## How to Use Multiple Discord Channels

If you want different threads to notify different Discord channels:

1. Create multiple webhooks in Discord
2. Add them as GitHub Secrets with different names:
   - `DISCORD_WEBHOOK_URL_1`
   - `DISCORD_WEBHOOK_URL_2`
3. Reference them in your config:

```json
{
  "monitors": [
    {
      "id": "thread-1",
      "discord_webhook_env": "DISCORD_WEBHOOK_URL_1",
      ...
    },
    {
      "id": "thread-2",
      "discord_webhook_env": "DISCORD_WEBHOOK_URL_2",
      ...
    }
  ]
}
```

## Local Testing

To test the script locally before deploying:

### 1. Install Dependencies

```bash
cd foroactivo-discord-monitor

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 2. Create `.env` File

```bash
# Copy the example
cp .env.example .env

# Edit .env and add your credentials
FOROACTIVO_USERNAME=your_username
FOROACTIVO_PASSWORD=your_password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 3. Create Configuration

```bash
cp config/threads.example.json config/threads.json
# Edit config/threads.json with your threads
```

### 4. Run the Monitor

```bash
poetry run python -m src.monitor
```

## Troubleshooting

### No notifications are being sent

1. Check **Actions** tab for errors in the workflow runs
2. Verify GitHub Secrets are set correctly
3. Ensure `config/threads.json` exists and is valid JSON
4. Test your Discord webhook URL manually

### Login fails

- Verify your `FOROACTIVO_USERNAME` and `FOROACTIVO_PASSWORD` are correct
- Check if your forum requires special login steps (CAPTCHA, 2FA)
- Try logging in manually to ensure your account isn't locked

### Duplicate notifications

- Check if the `state.json` file is being committed properly
- Look for errors in the "Commit state changes" step in Actions

### GitHub Actions quota exceeded

The free tier provides 2000 minutes/month:
- 10-minute polling = ~4,320 runs/month × 0.5 min = ~2,160 min/month
- If you exceed this, change the cron to `*/15 * * * *` (15-minute polling)

## How It Works (Technical)

### Components

1. **Foroactivo Client** (`src/foroactivo_client.py`)
   - Authenticates to the forum using session cookies
   - Scrapes HTML with BeautifulSoup
   - **Two scraping modes**:
     - `get_forum_threads()`: Lists all threads in a forum section
     - `get_thread_posts()`: Gets all posts in a specific thread
   - Supports custom Foroactivo themes

2. **State Manager** (`src/state_manager.py`)
   - **For forum sections**: Tracks seen thread IDs
   - **For threads**: Tracks last seen post ID
   - Filters new content to avoid duplicates
   - Commits state file after each run

3. **Discord Notifier** (`src/discord_notifier.py`)
   - Sends rich embeds to Discord webhooks
   - **Two notification types**:
     - Green embeds for new threads (🆕)
     - Blue embeds for new replies (💬)
   - Handles rate limits (max 5 requests/2 seconds)
   - Includes retry logic for failed requests

4. **Main Monitor** (`src/monitor.py`)
   - Orchestrates the workflow
   - Loads configuration and credentials
   - Routes to appropriate handler based on monitor type
   - Processes each monitor sequentially
   - Error handling and logging

### State Persistence

The `state.json` file is committed to the repository after each run:

**For forum section monitors:**
```json
{
  "forum-announcements": {
    "seen_thread_ids": ["t31", "t42", "t55"],
    "last_checked_at": "2025-12-29T12:00:00Z",
    "total_threads": 3
  }
}
```

**For thread monitors:**
```json
{
  "thread-1": {
    "last_post_id": "p12345",
    "last_checked_at": "2025-12-29T12:00:00Z",
    "total_posts_seen": 42
  }
}
```

This ensures no duplicate notifications even if the workflow is interrupted.

## Security Notes

- Never commit `.env` or `config/threads.json` with real credentials
- Use GitHub Secrets for all sensitive data
- The script uses HTTPS for all connections
- Forum credentials are only used within the GitHub Actions runner

## Limitations

- **Forum monitors**: Only detects new threads, not deleted/edited threads
- **Thread monitors**: Only detects new replies, not edits to existing posts
- Notification delay: up to 10 minutes (adjustable via cron schedule)
- GitHub Actions free tier: 2000 minutes/month
- Discord rate limit: 5 requests per 2 seconds per webhook
- Pinned/stickied notes in forum sections are automatically skipped

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review workflow logs in the **Actions** tab
3. Open an issue in this repository

## Acknowledgments

- Built for monitoring Foroactivo (Forumotion) forums
- Uses BeautifulSoup for HTML parsing
- Discord webhook integration
- Runs on GitHub Actions
