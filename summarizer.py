"""Claude-powered message summarizer."""

import os
from datetime import datetime
import anthropic


class Summarizer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def summarize(
        self,
        messages: list[dict],
        channel_name: str,
        style: str = "detailed"
    ) -> str:
        """
        Summarize a list of Slack messages.

        Args:
            messages: List of message dicts from SlackClient
            channel_name: Name of the channel for context
            style: "detailed" or "brief"

        Returns:
            Formatted summary string
        """
        if not messages:
            return f"No messages found in #{channel_name} for the specified time period."

        # Format messages for the prompt
        formatted_messages = self._format_messages(messages)

        # Build the prompt
        prompt = self._build_prompt(formatted_messages, channel_name, style)

        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        summary = response.content[0].text

        # Add metadata header
        header = self._build_header(messages, channel_name)

        return f"{header}\n{summary}"

    def _format_messages(self, messages: list[dict]) -> str:
        """Format messages into a readable transcript, including thread replies."""
        lines = []
        for msg in messages:
            time_str = msg["timestamp"].strftime("%H:%M")
            user = msg["user"]
            text = msg["text"]

            # Add the main message
            reply_count = msg.get("reply_count", 0)
            if reply_count > 0:
                lines.append(f"[{time_str}] {user}: {text} [THREAD START - {reply_count} replies]")
            else:
                lines.append(f"[{time_str}] {user}: {text}")

            # Add thread replies if present
            replies = msg.get("replies", [])
            for reply in replies:
                reply_time = reply["timestamp"].strftime("%H:%M")
                reply_user = reply["user"]
                reply_text = reply["text"]
                lines.append(f"    └─ [{reply_time}] {reply_user}: {reply_text}")

            # Add thread end marker if there were replies
            if replies:
                lines.append("    [THREAD END]")

        return "\n".join(lines)

    def _build_prompt(
        self,
        formatted_messages: str,
        channel_name: str,
        style: str
    ) -> str:
        """Build the summarization prompt."""

        if style == "brief":
            style_instruction = "Provide a brief 2-3 sentence summary."
        else:
            style_instruction = """Provide a detailed summary with:
- Key discussions and topics covered
- Important decisions made
- Action items or tasks mentioned
- Notable announcements or updates
- Any unresolved questions or debates"""

        return f"""Summarize the following Slack conversation from the #{channel_name} channel.

{style_instruction}

Format the summary using Slack-compatible formatting:
- Use *bold* for emphasis
- Use bullet points for lists
- Keep it concise but comprehensive
- Group related topics together
- Highlight any @mentions of people or action items

Here are the messages:

{formatted_messages}

Provide the summary now:"""

    def _build_header(self, messages: list[dict], channel_name: str) -> str:
        """Build the metadata header for the summary."""
        # Get time range
        start_time = messages[0]["timestamp"]
        end_time = messages[-1]["timestamp"]

        # Count unique users (including from replies)
        users = set(msg["user"] for msg in messages)
        for msg in messages:
            for reply in msg.get("replies", []):
                users.add(reply["user"])

        # Count threads and total replies
        threads_with_replies = [m for m in messages if m.get("replies")]
        total_replies = sum(len(m.get("replies", [])) for m in messages)

        # Format date
        date_str = start_time.strftime("%B %d, %Y")
        time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

        # Build stats line
        stats = f"{len(messages)} messages | {len(users)} participants"
        if total_replies > 0:
            stats += f" | {len(threads_with_replies)} threads ({total_replies} replies)"

        return f"""*#{channel_name} Summary* - {date_str}
_{time_range} | {stats}_
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
