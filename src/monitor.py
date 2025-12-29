"""Main Monitor - Orchestrate forum monitoring and Discord notifications."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from .discord_notifier import DiscordNotifier
from .foroactivo_client import ForoactivoClient
from .state_manager import StateManager


class ForoactivoMonitor:
    """Main monitor orchestrator."""

    def __init__(self, config_file: str = "config/threads.json"):
        """Initialize the monitor.

        Args:
            config_file: Path to the configuration file
        """
        # Load environment variables
        load_dotenv()

        # Resolve paths relative to project root
        project_root = Path(__file__).parent.parent
        self.config_file = project_root / config_file

        # Initialize state manager
        self.state_manager = StateManager()

        # Load configuration
        self.config = self._load_config()

        # Get forum credentials from environment
        self.username = os.getenv("FOROACTIVO_USERNAME")
        self.password = os.getenv("FOROACTIVO_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("FOROACTIVO_USERNAME and FOROACTIVO_PASSWORD environment variables must be set")

    def _load_config(self) -> Dict:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                f"Please create it based on config/threads.example.json"
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            if "monitors" not in config:
                raise ValueError("Configuration must have a 'monitors' array")

            print(f"Loaded configuration with {len(config['monitors'])} monitor(s)")
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")

    def run(self) -> int:
        """Run the monitoring process.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            print("=" * 60)
            print("Foroactivo Discord Monitor - Starting")
            print("=" * 60)

            # Load state
            self.state_manager.load_state()

            # Process each monitor configuration
            monitors = self.config.get("monitors", [])
            enabled_monitors = [m for m in monitors if m.get("enabled", True)]

            print(f"\nProcessing {len(enabled_monitors)} enabled monitor(s)...")

            total_notifications = 0

            for monitor_config in enabled_monitors:
                notifications_sent = self._process_monitor(monitor_config)
                total_notifications += notifications_sent

            # Save updated state
            self.state_manager.save_state()

            print("\n" + "=" * 60)
            print(f"Monitor completed successfully")
            print(f"Total notifications sent: {total_notifications}")
            print("=" * 60)

            return 0

        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def _process_monitor(self, monitor_config: Dict) -> int:
        """Process a single monitor configuration.

        Args:
            monitor_config: Monitor configuration dictionary

        Returns:
            Number of notifications sent
        """
        monitor_id = monitor_config.get("id")
        monitor_name = monitor_config.get("name", "Monitor")
        monitor_type = monitor_config.get("type", "thread")  # "thread" or "forum"
        forum_url = monitor_config.get("forum_url")
        webhook_env = monitor_config.get("discord_webhook_env", "DISCORD_WEBHOOK_URL")

        print(f"\n--- Processing: {monitor_name} (ID: {monitor_id}, Type: {monitor_type}) ---")

        # Validate common configuration
        if not all([monitor_id, forum_url, webhook_env]):
            print(f"ERROR: Incomplete configuration for monitor {monitor_id}")
            return 0

        # Route to appropriate handler
        if monitor_type == "forum":
            return self._process_forum_monitor(monitor_config)
        else:
            return self._process_thread_monitor(monitor_config)

    def _process_forum_monitor(self, monitor_config: Dict) -> int:
        """Process a forum section monitor (new threads).

        Args:
            monitor_config: Monitor configuration dictionary

        Returns:
            Number of notifications sent
        """
        forum_id = monitor_config.get("id")
        forum_name = monitor_config.get("name", "Forum")
        base_forum_url = monitor_config.get("forum_url")
        section_url = monitor_config.get("section_url")
        webhook_env = monitor_config.get("discord_webhook_env", "DISCORD_WEBHOOK_URL")

        # Validate configuration
        if not section_url:
            print(f"ERROR: section_url required for forum monitor {forum_id}")
            return 0

        # Get Discord webhook URL from environment
        webhook_url = os.getenv(webhook_env)
        if not webhook_url:
            print(f"ERROR: Environment variable {webhook_env} not set")
            return 0

        try:
            # Initialize client and notifier
            client = ForoactivoClient(base_forum_url, self.username, self.password)
            notifier = DiscordNotifier(webhook_url)

            # Authenticate
            print(f"Authenticating to {base_forum_url}...")
            if not client.login():
                error_msg = f"Failed to authenticate to forum: {base_forum_url}"
                print(f"ERROR: {error_msg}")
                notifier.send_error_notification(error_msg, forum_name)
                return 0

            # Fetch forum threads
            print(f"Fetching threads from: {section_url}")
            all_threads = client.get_forum_threads(section_url)

            if not all_threads:
                print("WARNING: No threads found in forum section")
                return 0

            # Determine new threads
            new_threads = self.state_manager.get_new_threads(forum_id, all_threads)

            # Update state with all current thread IDs
            all_thread_ids = [thread["id"] for thread in all_threads]
            self.state_manager.update_forum_state(forum_id, all_thread_ids)

            if not new_threads:
                print("No new threads to notify about")
                return 0

            # Send notifications
            print(f"Sending {len(new_threads)} notification(s) to Discord...")
            notifications_sent = notifier.send_batch_thread_notifications(new_threads, forum_name)

            return notifications_sent

        except Exception as e:
            error_msg = f"Error processing forum monitor {forum_id}: {str(e)}"
            print(f"ERROR: {error_msg}")

            # Try to send error notification
            try:
                webhook_url = os.getenv(webhook_env)
                if webhook_url:
                    notifier = DiscordNotifier(webhook_url)
                    notifier.send_error_notification(error_msg, forum_name)
            except:
                pass

            return 0

    def _process_thread_monitor(self, monitor_config: Dict) -> int:
        """Process a thread monitor (new replies).

        Args:
            monitor_config: Monitor configuration dictionary

        Returns:
            Number of notifications sent
        """
        thread_id = monitor_config.get("id")
        thread_name = monitor_config.get("name", "Thread")
        forum_url = monitor_config.get("forum_url")
        thread_url = monitor_config.get("thread_url")
        webhook_env = monitor_config.get("discord_webhook_env", "DISCORD_WEBHOOK_URL")

        # Validate configuration
        if not thread_url:
            print(f"ERROR: thread_url required for thread monitor {thread_id}")
            return 0

        # Get Discord webhook URL from environment
        webhook_url = os.getenv(webhook_env)
        if not webhook_url:
            print(f"ERROR: Environment variable {webhook_env} not set")
            return 0

        try:
            # Initialize client and notifier
            client = ForoactivoClient(forum_url, self.username, self.password)
            notifier = DiscordNotifier(webhook_url)

            # Authenticate
            print(f"Authenticating to {forum_url}...")
            if not client.login():
                error_msg = f"Failed to authenticate to forum: {forum_url}"
                print(f"ERROR: {error_msg}")
                notifier.send_error_notification(error_msg, thread_name)
                return 0

            # Fetch thread posts
            print(f"Fetching posts from: {thread_url}")
            all_posts = client.get_thread_posts(thread_url)

            if not all_posts:
                print("WARNING: No posts found in thread")
                return 0

            # Determine new posts
            new_posts = self.state_manager.get_new_posts(thread_id, all_posts)

            if not new_posts:
                print("No new posts to notify about")
                # Still update state with latest post
                latest_post = all_posts[-1]
                self.state_manager.update_thread_state(
                    thread_id,
                    latest_post["id"],
                    len(all_posts)
                )
                return 0

            # Send notifications
            print(f"Sending {len(new_posts)} notification(s) to Discord...")
            notifications_sent = notifier.send_batch_notifications(new_posts, thread_name)

            # Update state with latest post
            latest_post = all_posts[-1]
            self.state_manager.update_thread_state(
                thread_id,
                latest_post["id"],
                len(all_posts)
            )

            return notifications_sent

        except Exception as e:
            error_msg = f"Error processing monitor {thread_id}: {str(e)}"
            print(f"ERROR: {error_msg}")

            # Try to send error notification
            try:
                webhook_url = os.getenv(webhook_env)
                if webhook_url:
                    notifier = DiscordNotifier(webhook_url)
                    notifier.send_error_notification(error_msg, thread_name)
            except:
                pass  # Ignore errors when sending error notification

            return 0


def main():
    """Main entry point for the monitor."""
    try:
        monitor = ForoactivoMonitor()
        exit_code = monitor.run()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFATAL ERROR during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
