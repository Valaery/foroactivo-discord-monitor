"""State Manager - Track seen posts to avoid duplicate notifications."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class StateManager:
    """Manage state persistence for tracking seen posts."""

    def __init__(self, state_file: str = "state.json"):
        """Initialize the state manager.

        Args:
            state_file: Path to the state file (relative to project root)
        """
        # Resolve path relative to the script's parent directory (project root)
        project_root = Path(__file__).parent.parent
        self.state_file = project_root / state_file
        self.state: Dict[str, Dict] = {}

    def load_state(self) -> Dict[str, Dict]:
        """Load state from file.

        Returns:
            Dictionary mapping thread IDs to their state
        """
        if not self.state_file.exists():
            print(f"State file not found, creating new state: {self.state_file}")
            self.state = {}
            return self.state

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                self.state = json.load(f)
            print(f"Loaded state for {len(self.state)} threads")
            return self.state
        except json.JSONDecodeError as e:
            print(f"Error reading state file: {e}")
            print("Starting with empty state")
            self.state = {}
            return self.state
        except Exception as e:
            print(f"Unexpected error loading state: {e}")
            self.state = {}
            return self.state

    def save_state(self) -> bool:
        """Save current state to file.

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Write state to file with pretty formatting
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)

            print(f"State saved successfully: {self.state_file}")
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def get_last_post_id(self, thread_id: str) -> Optional[str]:
        """Get the last seen post ID for a thread.

        Args:
            thread_id: Unique identifier for the thread

        Returns:
            Last seen post ID or None if thread not tracked
        """
        thread_state = self.state.get(thread_id, {})
        return thread_state.get("last_post_id")

    def update_thread_state(self, thread_id: str, last_post_id: str, total_posts: int) -> None:
        """Update state for a thread.

        Args:
            thread_id: Unique identifier for the thread
            last_post_id: ID of the most recent post
            total_posts: Total number of posts seen in the thread
        """
        self.state[thread_id] = {
            "last_post_id": last_post_id,
            "last_checked_at": datetime.utcnow().isoformat() + "Z",
            "total_posts_seen": total_posts
        }
        print(f"Updated state for thread {thread_id}: last_post={last_post_id}, total={total_posts}")

    def get_new_threads(self, forum_id: str, all_threads: List[Dict]) -> List[Dict]:
        """Filter threads to get only new ones not yet seen.

        Args:
            forum_id: Unique identifier for the forum section
            all_threads: List of all threads from the forum section

        Returns:
            List of new threads that haven't been notified yet
        """
        if not all_threads:
            return []

        # Get list of seen thread IDs
        forum_state = self.state.get(forum_id, {})
        seen_thread_ids = set(forum_state.get("seen_thread_ids", []))

        # Find new threads
        new_threads = [
            thread for thread in all_threads
            if thread["id"] not in seen_thread_ids
        ]

        if new_threads:
            print(f"Found {len(new_threads)} new thread(s) in forum {forum_id}")
        else:
            print(f"No new threads in forum {forum_id}")

        return new_threads

    def update_forum_state(self, forum_id: str, thread_ids: List[str]) -> None:
        """Update state for a forum section.

        Args:
            forum_id: Unique identifier for the forum section
            thread_ids: List of all thread IDs currently in the forum
        """
        self.state[forum_id] = {
            "seen_thread_ids": thread_ids,
            "last_checked_at": datetime.utcnow().isoformat() + "Z",
            "total_threads": len(thread_ids)
        }
        print(f"Updated state for forum {forum_id}: {len(thread_ids)} threads tracked")

    def get_new_posts(self, thread_id: str, all_posts: List[Dict]) -> List[Dict]:
        """Filter posts to get only new ones not yet seen.

        Args:
            thread_id: Unique identifier for the thread
            all_posts: List of all posts from the thread

        Returns:
            List of new posts that haven't been notified yet
        """
        if not all_posts:
            return []

        last_post_id = self.get_last_post_id(thread_id)

        # If no state exists, treat all posts as old (avoid spam on first run)
        # Only notify about the very last post to establish state
        if last_post_id is None:
            print(f"First time tracking thread {thread_id}, establishing initial state")
            # Return only the last post to avoid spamming
            return [all_posts[-1]] if all_posts else []

        # Find the index of the last seen post
        last_post_index = -1
        for i, post in enumerate(all_posts):
            if post["id"] == last_post_id:
                last_post_index = i
                break

        # If last post not found, something changed - notify about last post only
        if last_post_index == -1:
            print(f"Warning: Last post ID {last_post_id} not found in current posts")
            print(f"Thread structure may have changed. Returning only the latest post.")
            return [all_posts[-1]] if all_posts else []

        # Return all posts after the last seen post
        new_posts = all_posts[last_post_index + 1:]

        if new_posts:
            print(f"Found {len(new_posts)} new post(s) in thread {thread_id}")
        else:
            print(f"No new posts in thread {thread_id}")

        return new_posts

    def get_state_summary(self) -> Dict[str, any]:
        """Get a summary of the current state.

        Returns:
            Dictionary with state statistics
        """
        return {
            "total_threads": len(self.state),
            "threads": {
                thread_id: {
                    "last_post": data.get("last_post_id"),
                    "last_checked": data.get("last_checked_at"),
                    "total_posts": data.get("total_posts_seen")
                }
                for thread_id, data in self.state.items()
            }
        }
