"""Foroactivo Forum Client - Handle authentication and thread scraping."""

import re
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class ForoactivoClient:
    """Client for interacting with Foroactivo forums."""

    def __init__(self, forum_url: str, username: str, password: str):
        """Initialize the Foroactivo client.

        Args:
            forum_url: Base URL of the forum (e.g., https://example.foroactivo.com)
            username: Forum username
            password: Forum password
        """
        self.forum_url = forum_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()

        # Browser-like headers to avoid detection
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    def login(self) -> bool:
        """Authenticate with the forum.

        Returns:
            True if login successful, False otherwise
        """
        try:
            # Get login page to extract form data
            login_page_url = urljoin(self.forum_url, "/login")
            response = self.session.get(login_page_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Find login form
            login_form = soup.find("form", {"method": "post"})
            if not login_form:
                print("Error: Could not find login form")
                return False

            # Extract form action
            form_action = login_form.get("action", "/login")
            if not form_action.startswith("http"):
                form_action = urljoin(self.forum_url, form_action)

            # Build login payload
            payload = {
                "username": self.username,
                "password": self.password,
                "login": "Log in",
                "autologin": "on",
                "redirect": ""
            }

            # Submit login
            response = self.session.post(form_action, data=payload, timeout=30, allow_redirects=True)
            response.raise_for_status()

            # Check if login was successful by looking for logout link
            soup = BeautifulSoup(response.content, "html.parser")
            logout_link = soup.find("a", href=re.compile(r"/logout"))

            if logout_link:
                print(f"Successfully logged in as {self.username}")
                return True
            else:
                # Debug: Check for common login error indicators
                error_msg = soup.find(class_=re.compile(r"error|message"))
                if error_msg:
                    print(f"Login failed with error: {error_msg.get_text(strip=True)}")
                else:
                    print("Login failed: No logout link found")
                    # Check if username appears in page (might be logged in under different selector)
                    if self.username.lower() in response.text.lower():
                        print("Username found in page - might be logged in but logout link selector is different")
                        print("Proceeding anyway...")
                        return True
                return False

        except requests.RequestException as e:
            print(f"Login error: {e}")
            return False

    def get_forum_threads(self, forum_url: str) -> List[Dict[str, str]]:
        """Fetch all threads from a forum section.

        Args:
            forum_url: Full URL of the forum section (e.g., https://forum.com/f13-section)

        Returns:
            List of thread dictionaries with keys: id, title, author, url, last_post_date
        """
        try:
            response = self.session.get(forum_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            threads = []

            # Find all thread/topic containers
            # This forum uses a custom theme, so look for thread containers
            thread_containers = soup.find_all("div", class_="unr-wtp")

            if not thread_containers:
                # Fallback to standard phpBB structure
                thread_containers = soup.find_all("dl", class_=re.compile(r"topic"))

            print(f"Found {len(thread_containers)} thread container(s)")

            for container in thread_containers:
                thread_data = self._parse_thread_from_custom_theme(container, forum_url)
                if thread_data:
                    threads.append(thread_data)

            if not threads:
                print(f"Warning: No threads found in forum section {forum_url}")
            else:
                print(f"Found {len(threads)} thread(s) in forum section")

            return threads

        except requests.RequestException as e:
            print(f"Error fetching forum section: {e}")
            return []

    def _parse_thread_from_custom_theme(self, container, base_url: str) -> Optional[Dict[str, str]]:
        """Parse a thread from the custom theme structure.

        Args:
            container: BeautifulSoup element containing the thread (div.unr-wtp)
            base_url: Base URL for constructing full URLs

        Returns:
            Dictionary with thread data or None if parsing fails
        """
        try:
            # Find the topic link (not within a <strong>Nota:</strong> for pinned topics)
            topic_div = container.find("div", class_="unr-listopic-topic")
            if not topic_div:
                return None

            # Check if it's a pinned note (skip those)
            if topic_div.find("strong"):
                strong_text = topic_div.find("strong").get_text(strip=True)
                if "Nota" in strong_text:
                    print("Skipping pinned note")
                    return None

            # Get the thread link
            link = topic_div.find("a")
            if not link:
                return None

            title = link.get_text(strip=True)
            thread_url = link.get("href", "")

            # Make URL absolute
            if thread_url and not thread_url.startswith("http"):
                thread_url = urljoin(base_url, thread_url)

            # Extract thread ID
            thread_id = None
            if thread_url:
                match = re.search(r'/t(\d+)-', thread_url)
                if match:
                    thread_id = f"t{match.group(1)}"

            if not thread_id:
                return None

            # Find author
            author = "Unknown"
            info_div = container.find("div", class_="unr-listopic-info")
            if info_div:
                author_link = info_div.find("a")
                if author_link:
                    author = author_link.get_text(strip=True)

            # Find last post date (last div in info)
            last_post_date = ""
            if info_div:
                date_divs = info_div.find_all("div")
                if len(date_divs) >= 3:
                    # Third div contains the date
                    last_post_date = date_divs[2].get_text(strip=True)
                    # Remove the username that appears after the date
                    if "por" in last_post_date:
                        last_post_date = last_post_date.split("por")[0].strip()

            return {
                "id": thread_id,
                "title": title,
                "author": author,
                "url": thread_url,
                "last_post_date": last_post_date
            }

        except Exception as e:
            print(f"Error parsing thread from custom theme: {e}")
            return None

    def _parse_thread(self, thread_elem, base_url: str) -> Optional[Dict[str, str]]:
        """Parse a thread element from forum listing.

        Args:
            thread_elem: BeautifulSoup element containing the thread
            base_url: Base URL for constructing full URLs

        Returns:
            Dictionary with thread data or None if parsing fails
        """
        try:
            # Find title and URL
            title_link = thread_elem.find("a", class_="topictitle")
            if not title_link:
                return None

            title = title_link.get_text(strip=True)
            thread_url = title_link.get("href", "")

            # Make URL absolute if needed
            if thread_url and not thread_url.startswith("http"):
                from urllib.parse import urljoin
                thread_url = urljoin(base_url, thread_url)

            # Extract thread ID from URL (e.g., /t31-title -> t31)
            thread_id = None
            if thread_url:
                match = re.search(r'/t(\d+)-', thread_url)
                if match:
                    thread_id = f"t{match.group(1)}"

            if not thread_id:
                return None

            # Find author (in <dt> element, after "by")
            dt_elem = thread_elem.find("dt")
            author = "Unknown"
            if dt_elem:
                # Look for text after "by" or "par"
                text = dt_elem.get_text()
                by_match = re.search(r'(?:by|par)\s+(.+?)(?:\s+»|\s*$)', text, re.IGNORECASE)
                if by_match:
                    author = by_match.group(1).strip()

            # Find last post date
            dd_elem = thread_elem.find("dd")
            last_post_date = ""
            if dd_elem:
                time_elem = dd_elem.find(class_=re.compile(r"time|date"))
                if time_elem:
                    last_post_date = time_elem.get_text(strip=True)
                else:
                    # Try to get any date-like text
                    last_post_date = dd_elem.get_text(strip=True)

            return {
                "id": thread_id,
                "title": title,
                "author": author,
                "url": thread_url,
                "last_post_date": last_post_date
            }

        except Exception as e:
            print(f"Error parsing thread: {e}")
            return None

    def get_thread_posts(self, thread_url: str) -> List[Dict[str, str]]:
        """Fetch all posts from a thread.

        Args:
            thread_url: Full URL of the thread to scrape

        Returns:
            List of post dictionaries with keys: id, author, content, timestamp, url
        """
        try:
            response = self.session.get(thread_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            posts = []

            # Find all post elements (Foroactivo uses various templates)
            # Try phpBB3 style first
            post_elements = soup.find_all("div", class_=re.compile(r"post\s|postbody|message"))

            # If not found, try alternative selectors
            if not post_elements:
                post_elements = soup.find_all("td", class_=re.compile(r"post|message"))

            for post_elem in post_elements:
                post_data = self._parse_post(post_elem, thread_url)
                if post_data:
                    posts.append(post_data)

            if not posts:
                print(f"Warning: No posts found in thread {thread_url}")
            else:
                print(f"Found {len(posts)} posts in thread")

            return posts

        except requests.RequestException as e:
            print(f"Error fetching thread: {e}")
            return []

    def _parse_post(self, post_elem, thread_url: str) -> Optional[Dict[str, str]]:
        """Parse a post element to extract data.

        Args:
            post_elem: BeautifulSoup element containing the post
            thread_url: URL of the thread (for constructing post URLs)

        Returns:
            Dictionary with post data or None if parsing fails
        """
        try:
            # Extract post ID from element attributes
            post_id = None
            if post_elem.get("id"):
                post_id = post_elem.get("id")
            elif post_elem.find_parent(id=re.compile(r"p\d+")):
                post_id = post_elem.find_parent(id=re.compile(r"p\d+")).get("id")

            if not post_id:
                # Try to find anchor with post ID
                anchor = post_elem.find("a", id=re.compile(r"p\d+"))
                if anchor:
                    post_id = anchor.get("id")

            # If still no ID, skip this post
            if not post_id:
                return None

            # Extract author
            author = "Unknown"
            author_elem = post_elem.find(class_=re.compile(r"author|username|postername"))
            if not author_elem:
                author_elem = post_elem.find("a", class_=re.compile(r"author|username"))
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Extract content
            content = ""
            content_elem = post_elem.find(class_=re.compile(r"content|postbody|message-text"))
            if content_elem:
                # Get text, preserving some structure
                content = content_elem.get_text(separator=" ", strip=True)
                # Limit to 500 chars for preview
                if len(content) > 500:
                    content = content[:500] + "..."

            # Extract timestamp
            timestamp = ""
            time_elem = post_elem.find(class_=re.compile(r"time|date|postdate"))
            if not time_elem:
                time_elem = post_elem.find("span", class_=re.compile(r"time|date"))
            if time_elem:
                timestamp = time_elem.get_text(strip=True)

            # Construct post URL
            post_url = f"{thread_url}#{post_id}"

            return {
                "id": post_id,
                "author": author,
                "content": content,
                "timestamp": timestamp,
                "url": post_url
            }

        except Exception as e:
            print(f"Error parsing post: {e}")
            return None

    def retry_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a request with exponential backoff retry logic.

        Args:
            url: URL to request
            max_retries: Maximum number of retry attempts

        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Request failed after {max_retries} attempts: {e}")
                    return None
        return None
