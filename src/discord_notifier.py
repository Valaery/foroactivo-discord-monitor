"""Discord Notifier - Send formatted notifications to Discord via webhooks."""

import time
from typing import Dict, List

import requests


class DiscordNotifier:
    """Handle Discord webhook notifications."""

    # Discord embed color (blue for new replies)
    EMBED_COLOR = 0x5865F2  # Discord Blurple

    def __init__(self, webhook_url: str):
        """Initialize the Discord notifier.

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url

    def send_thread_notification(self, thread: Dict[str, str], forum_name: str = "Forum") -> bool:
        """Send a notification for a new thread.

        Args:
            thread: Thread data dictionary with keys: id, title, author, url, last_post_date
            forum_name: Name of the forum section

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            embed = self._format_thread_embed(thread, forum_name)
            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 204:
                print(f"Discord notification sent for new thread {thread['id']}")
                return True
            elif response.status_code == 429:
                # Rate limited
                retry_after = response.json().get("retry_after", 5)
                print(f"Discord rate limit hit, waiting {retry_after}s")
                time.sleep(retry_after)
                # Retry once
                response = requests.post(self.webhook_url, json=payload, timeout=10)
                return response.status_code == 204
            else:
                print(f"Discord notification failed: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            print(f"Error sending Discord notification: {e}")
            return False

    def _format_thread_embed(self, thread: Dict[str, str], forum_name: str) -> Dict:
        """Format a thread as a Discord embed.

        Args:
            thread: Thread data dictionary
            forum_name: Name of the forum section

        Returns:
            Discord embed dictionary
        """
        embed = {
            "title": f"🆕 New Thread in {forum_name}",
            "description": f"**{thread.get('title', 'Untitled')}**",
            "color": 0x57F287,  # Discord Green for new threads
            "url": thread.get("url", ""),
            "fields": [
                {
                    "name": "Author",
                    "value": thread.get("author", "Unknown"),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Foroactivo Monitor"
            }
        }

        # Add last post date if available
        if thread.get("last_post_date"):
            embed["fields"].append({
                "name": "Posted",
                "value": thread["last_post_date"],
                "inline": True
            })

        return embed

    def send_batch_thread_notifications(self, threads: List[Dict[str, str]], forum_name: str = "Forum") -> int:
        """Send notifications for multiple new threads with rate limit handling.

        Args:
            threads: List of thread data dictionaries
            forum_name: Name of the forum section

        Returns:
            Number of successfully sent notifications
        """
        if not threads:
            return 0

        success_count = 0

        for i, thread in enumerate(threads):
            # Send notification
            if self.send_thread_notification(thread, forum_name):
                success_count += 1

            # Rate limit: Max 5 requests per 2 seconds
            if (i + 1) % 4 == 0 and i + 1 < len(threads):
                print(f"Sent {i + 1}/{len(threads)} notifications, pausing to respect rate limits...")
                time.sleep(2)

        print(f"Sent {success_count}/{len(threads)} Discord notifications successfully")
        return success_count

    def send_notification(self, post: Dict[str, str], thread_name: str = "Thread") -> bool:
        """Send a notification for a new post.

        Args:
            post: Post data dictionary with keys: id, author, content, timestamp, url
            thread_name: Name of the thread

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            embed = self._format_embed(post, thread_name)
            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 204:
                print(f"Discord notification sent for post {post['id']}")
                return True
            elif response.status_code == 429:
                # Rate limited
                retry_after = response.json().get("retry_after", 5)
                print(f"Discord rate limit hit, waiting {retry_after}s")
                time.sleep(retry_after)
                # Retry once
                response = requests.post(self.webhook_url, json=payload, timeout=10)
                return response.status_code == 204
            else:
                print(f"Discord notification failed: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            print(f"Error sending Discord notification: {e}")
            return False

    def send_batch_notifications(self, posts: List[Dict[str, str]], thread_name: str = "Thread") -> int:
        """Send notifications for multiple posts with rate limit handling.

        Args:
            posts: List of post data dictionaries
            thread_name: Name of the thread

        Returns:
            Number of successfully sent notifications
        """
        if not posts:
            return 0

        success_count = 0

        for i, post in enumerate(posts):
            # Send notification
            if self.send_notification(post, thread_name):
                success_count += 1

            # Rate limit: Max 5 requests per 2 seconds
            # Add delay between posts (wait 2s after every 4 posts)
            if (i + 1) % 4 == 0 and i + 1 < len(posts):
                print(f"Sent {i + 1}/{len(posts)} notifications, pausing to respect rate limits...")
                time.sleep(2)

        print(f"Sent {success_count}/{len(posts)} Discord notifications successfully")
        return success_count

    def _format_embed(self, post: Dict[str, str], thread_name: str) -> Dict:
        """Format a post as a Discord embed.

        Args:
            post: Post data dictionary
            thread_name: Name of the thread

        Returns:
            Discord embed dictionary
        """
        # Truncate content for preview (Discord embed description limit is 4096 chars)
        content_preview = post.get("content", "")
        if len(content_preview) > 200:
            content_preview = content_preview[:200] + "..."

        # Build embed
        embed = {
            "title": f"New Reply in {thread_name}",
            "description": content_preview if content_preview else "*No content preview available*",
            "color": self.EMBED_COLOR,
            "url": post.get("url", ""),
            "fields": [
                {
                    "name": "Author",
                    "value": post.get("author", "Unknown"),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Foroactivo Monitor"
            }
        }

        # Add timestamp if available
        if post.get("timestamp"):
            embed["fields"].append({
                "name": "Posted",
                "value": post["timestamp"],
                "inline": True
            })

        return embed

    def send_error_notification(self, error_message: str, thread_name: str = "Monitor") -> bool:
        """Send an error notification to Discord.

        Args:
            error_message: Error message to send
            thread_name: Name of the thread or monitor

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            embed = {
                "title": f"⚠️ Monitor Error - {thread_name}",
                "description": error_message,
                "color": 0xED4245,  # Discord Red
                "footer": {
                    "text": "Foroactivo Monitor"
                }
            }

            payload = {"embeds": [embed]}

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 204

        except Exception as e:
            print(f"Failed to send error notification: {e}")
            return False

    def test_webhook(self) -> bool:
        """Test if the webhook URL is valid and working.

        Returns:
            True if webhook is valid, False otherwise
        """
        try:
            embed = {
                "title": "✅ Foroactivo Monitor Test",
                "description": "Webhook connection successful!",
                "color": 0x57F287,  # Discord Green
                "footer": {
                    "text": "Foroactivo Monitor"
                }
            }

            payload = {"embeds": [embed]}

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 204:
                print("Discord webhook test successful")
                return True
            else:
                print(f"Discord webhook test failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"Discord webhook test error: {e}")
            return False
