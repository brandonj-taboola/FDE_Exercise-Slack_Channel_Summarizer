"""Slack API client for fetching channel messages."""

import os
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN not found in environment")
        self.client = WebClient(token=self.token)
        self._user_cache = {}

    def get_channels(self) -> list[dict]:
        """Get list of public channels the bot has access to."""
        try:
            result = self.client.conversations_list(types="public_channel")
            return [
                {"id": ch["id"], "name": ch["name"]}
                for ch in result["channels"]
                if ch["is_member"]
            ]
        except SlackApiError as e:
            raise Exception(f"Failed to list channels: {e.response['error']}")

    def get_channel_id(self, channel_name: str) -> str:
        """Get channel ID from channel name."""
        channels = self.get_channels()
        for ch in channels:
            if ch["name"] == channel_name.lstrip("#"):
                return ch["id"]
        raise ValueError(f"Channel '{channel_name}' not found or bot not invited")

    def get_user_name(self, user_id: str) -> str:
        """Get display name for a user ID (cached)."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            result = self.client.users_info(user=user_id)
            user = result["user"]
            name = user.get("real_name") or user.get("name") or user_id
            self._user_cache[user_id] = name
            return name
        except SlackApiError:
            return user_id

    def fetch_thread_replies(
        self,
        channel_id: str,
        thread_ts: str
    ) -> list[dict]:
        """
        Fetch all replies in a thread.

        Args:
            channel_id: Channel ID
            thread_ts: Thread timestamp (parent message ts)

        Returns:
            List of reply message dicts
        """
        replies = []
        cursor = None

        try:
            while True:
                result = self.client.conversations_replies(
                    channel=channel_id,
                    ts=thread_ts,
                    cursor=cursor,
                    limit=200
                )

                for msg in result["messages"]:
                    # Skip the parent message (it has ts == thread_ts)
                    if msg["ts"] == thread_ts:
                        continue

                    # Skip bot messages and system messages
                    if msg.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                        continue

                    if "user" in msg and "text" in msg:
                        replies.append({
                            "timestamp": datetime.fromtimestamp(float(msg["ts"])),
                            "user": self.get_user_name(msg["user"]),
                            "text": msg["text"],
                            "is_reply": True
                        })

                # Check for pagination
                if result.get("has_more"):
                    cursor = result["response_metadata"]["next_cursor"]
                else:
                    break

        except SlackApiError as e:
            raise Exception(f"Failed to fetch thread replies: {e.response['error']}")

        return replies

    def fetch_messages(
        self,
        channel: str,
        hours: int = 24,
        limit: int = 500,
        include_threads: bool = False
    ) -> list[dict]:
        """
        Fetch messages from a channel within the time window.

        Args:
            channel: Channel name or ID
            hours: How many hours back to fetch (default 24)
            limit: Maximum messages to fetch (default 500)
            include_threads: Whether to fetch thread replies (default False)

        Returns:
            List of message dicts with timestamp, user, and text
        """
        # Get channel ID if name provided
        if not channel.startswith("C"):
            channel_id = self.get_channel_id(channel)
        else:
            channel_id = channel

        # Calculate time range
        oldest = datetime.now() - timedelta(hours=hours)
        oldest_ts = str(oldest.timestamp())

        messages = []
        cursor = None

        try:
            while len(messages) < limit:
                result = self.client.conversations_history(
                    channel=channel_id,
                    oldest=oldest_ts,
                    limit=min(200, limit - len(messages)),
                    cursor=cursor
                )

                for msg in result["messages"]:
                    # Skip bot messages and system messages
                    if msg.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                        continue

                    if "user" in msg and "text" in msg:
                        reply_count = msg.get("reply_count", 0)
                        thread_ts = msg.get("ts") if reply_count > 0 else None

                        messages.append({
                            "timestamp": datetime.fromtimestamp(float(msg["ts"])),
                            "user": self.get_user_name(msg["user"]),
                            "text": msg["text"],
                            "thread_ts": thread_ts,
                            "reply_count": reply_count,
                            "is_reply": False,
                            "replies": []
                        })

                # Check for pagination
                if result.get("has_more"):
                    cursor = result["response_metadata"]["next_cursor"]
                else:
                    break

        except SlackApiError as e:
            raise Exception(f"Failed to fetch messages: {e.response['error']}")

        # Fetch thread replies if requested
        if include_threads:
            for msg in messages:
                if msg["reply_count"] > 0 and msg["thread_ts"]:
                    msg["replies"] = self.fetch_thread_replies(
                        channel_id,
                        msg["thread_ts"]
                    )

        # Return in chronological order
        return sorted(messages, key=lambda m: m["timestamp"])

    def post_message(self, channel: str, text: str) -> bool:
        """Post a message to a channel."""
        # Get channel ID if name provided
        if not channel.startswith("C"):
            channel_id = self.get_channel_id(channel)
        else:
            channel_id = channel

        try:
            self.client.chat_postMessage(channel=channel_id, text=text)
            return True
        except SlackApiError as e:
            raise Exception(f"Failed to post message: {e.response['error']}")
