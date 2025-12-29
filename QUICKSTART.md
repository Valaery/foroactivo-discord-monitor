# Quick Start Guide

Get your Foroactivo Discord Monitor running in 5 minutes!

## Prerequisites

- A Foroactivo forum account
- A Discord server where you can create webhooks
- A GitHub account

## Step-by-Step Setup

### 1. Create Discord Webhook (2 minutes)

1. Open Discord → Your Server
2. Click **Server Settings** (gear icon)
3. Go to **Integrations** → **Webhooks**
4. Click **New Webhook**
5. Name it "Foroactivo Monitor"
6. Select the channel for notifications
7. Click **Copy Webhook URL**
8. Save this URL somewhere safe

### 2. Set Up Repository (1 minute)

**Option A: Use this repository directly**
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these three secrets (one at a time):

   | Name | Value |
   |------|-------|
   | `FOROACTIVO_USERNAME` | Your forum username |
   | `FOROACTIVO_PASSWORD` | Your forum password |
   | `DISCORD_WEBHOOK_URL` | The webhook URL you copied |

**Option B: Fork for your own copy**
1. Click **Fork** at the top of this page
2. Follow Option A steps in your forked repository

### 3. Configure Monitors (1 minute)

1. Copy `config/threads.example.json` to `config/threads.json`
2. Edit the file to add what you want to monitor:

**Option A: Monitor a Forum Section (for NEW threads)**

```json
{
  "monitors": [
    {
      "id": "forum-section-1",
      "name": "Forum Section Name",
      "type": "forum",
      "forum_url": "https://yourforum.foroactivo.com",
      "section_url": "https://yourforum.foroactivo.com/f13-section-name",
      "discord_webhook_env": "DISCORD_WEBHOOK_URL",
      "enabled": true
    }
  ]
}
```

**Option B: Monitor a Specific Thread (for NEW replies)**

```json
{
  "monitors": [
    {
      "id": "thread-1",
      "name": "My Thread Name",
      "type": "thread",
      "forum_url": "https://yourforum.foroactivo.com",
      "thread_url": "https://yourforum.foroactivo.com/t123-thread-title",
      "discord_webhook_env": "DISCORD_WEBHOOK_URL",
      "enabled": true
    }
  ]
}
```

**Finding URLs:**
- **Forum section URL**: Go to the forum section, copy URL from address bar
  - Example: `https://myforum.foroactivo.com/f13-announcements`
- **Thread URL**: Go to the thread, copy URL from address bar
  - Example: `https://myforum.foroactivo.com/t42-my-thread`

### 4. Commit Configuration (30 seconds)

```bash
git add config/threads.json
git commit -m "Add my threads to monitor"
git push
```

Or use GitHub's web interface:
1. Navigate to `config/threads.json`
2. Click **Edit file** (pencil icon)
3. Make your changes
4. Click **Commit changes**

### 5. Enable GitHub Actions (30 seconds)

1. Go to the **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**

### 6. Test It! (30 seconds)

1. Still in **Actions** tab
2. Click **Monitor Foroactivo Forums** (left sidebar)
3. Click **Run workflow** → **Run workflow**
4. Wait 20-30 seconds
5. Check your Discord channel for a notification!

## Troubleshooting

### ❌ "No posts/threads found"
- **For threads**: Verify your `thread_url` is correct
- **For forums**: Verify your `section_url` is correct
- Make sure you can access the content when logged in
- Check that the forum section isn't empty

### ❌ "Login failed"
- Double-check `FOROACTIVO_USERNAME` and `FOROACTIVO_PASSWORD`
- Try logging in manually to verify credentials

### ❌ "Webhook failed"
- Verify `DISCORD_WEBHOOK_URL` is correct
- Test webhook URL in your browser (should show JSON response)

### ❌ Workflow doesn't run
- Check that GitHub Actions is enabled
- Verify the cron schedule hasn't been disabled
- Check Actions quota (Settings → Billing)

## What Happens Next?

- ✅ The workflow runs **every 10 minutes** automatically
- ✅ **Forum monitors**: Get notified when NEW threads are posted
- ✅ **Thread monitors**: Get notified when NEW replies are posted
- ✅ State is saved to avoid duplicate notifications
- ✅ Errors are logged in the Actions tab

## Monitoring Multiple Items

You can mix forum sections and specific threads in `config/threads.json`:

```json
{
  "monitors": [
    {
      "id": "forum-announcements",
      "name": "Announcements Section",
      "type": "forum",
      "section_url": "https://forum.com/f5-announcements",
      "enabled": true
    },
    {
      "id": "thread-important",
      "name": "Important Discussion",
      "type": "thread",
      "thread_url": "https://forum.com/t123-important",
      "enabled": true
    }
  ]
}
```

**Note**: All monitors need `forum_url`, but:
- `type: "forum"` requires `section_url`
- `type: "thread"` requires `thread_url`

## Need Help?

Check the full [README.md](README.md) for detailed documentation.
