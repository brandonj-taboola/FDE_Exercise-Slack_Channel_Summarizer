"""Flask server for Slack slash command integration."""

import os
import re
import sys
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from slack_client import SlackClient
from summarizer import Summarizer

# Load environment variables
load_dotenv()

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__)

# Initialize clients
slack = SlackClient()
summarizer = Summarizer()


def process_summary(channel_name: str, response_url: str, include_threads: bool, days: int):
    """Process the summary in a background thread and post results."""
    import requests

    try:
        # Convert days to hours for the API
        hours = days * 24

        # Fetch messages
        messages = slack.fetch_messages(
            channel_name,
            hours=hours,
            include_threads=include_threads
        )

        if not messages:
            result = f"No messages found in #{channel_name} in the last {days} day{'s' if days != 1 else ''}."
        else:
            # Generate summary
            result = summarizer.summarize(messages, channel_name, style="detailed")

        # Post result back to Slack
        requests.post(response_url, json={
            "response_type": "in_channel",
            "text": result
        })

    except Exception as e:
        # Post error back to Slack
        requests.post(response_url, json={
            "response_type": "ephemeral",
            "text": f"Error generating summary: {str(e)}"
        })


@app.route("/slack/summarize", methods=["POST"])
def handle_summarize():
    """
    Handle /summarize slash command from Slack.

    Usage in Slack:
        /summarize                    - Summarize current channel, last 30 days (with threads)
        /summarize no-threads         - Summarize current channel without threads
        /summarize 7d                 - Summarize current channel, last 7 days (with threads)
        /summarize #channel           - Summarize specified channel, last 30 days (with threads)
        /summarize #channel no-threads - Summarize specified channel without threads
        /summarize #channel 14d       - Summarize specified channel, last 14 days (with threads)
    """
    # Parse the command text
    text = request.form.get("text", "").strip()
    response_url = request.form.get("response_url")
    current_channel_id = request.form.get("channel_id")
    current_channel_name = request.form.get("channel_name")

    # Parse arguments
    parts = text.split() if text else []

    # Determine channel: use specified channel or current channel
    channel_name = None
    if parts and parts[0].startswith(("#", "<#")):
        # Channel specified in command
        channel_name = parts[0].lstrip("#").strip("<>").split("|")[0]
        parts = parts[1:]  # Remove channel from parts for further parsing
    else:
        # No channel specified, use current channel
        # Try to get channel name, fall back to ID if not available
        channel_name = current_channel_name or current_channel_id
        if not channel_name:
            return jsonify({
                "response_type": "ephemeral",
                "text": "Error: Could not determine channel. Please specify a channel explicitly."
            })

    # Threads are included by default, unless "no-threads" is specified
    include_threads = "no-threads" not in [p.lower() for p in parts]

    # Parse days (look for pattern like "1d", "7d", "30d", etc.)
    days = 30  # Default to 30 days
    for part in parts:
        match = re.match(r"(\d+)d", part.lower())
        if match:
            days = int(match.group(1))
            # Enforce maximum of 30 days
            if days > 30:
                return jsonify({
                    "response_type": "ephemeral",
                    "text": f"Error: Maximum timeframe is 30 days. You requested {days} days."
                })
            break

    # Acknowledge immediately (Slack requires response within 3 seconds)
    # Then process in background
    thread = threading.Thread(
        target=process_summary,
        args=(channel_name, response_url, include_threads, days)
    )
    thread.start()

    return jsonify({
        "response_type": "ephemeral",
        "text": f"Generating summary for #{channel_name} (last {days} day{'s' if days != 1 else ''})... This may take a moment."
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"Starting server on port {port}...")
    print("Slash command endpoint: /slack/summarize")
    app.run(host="0.0.0.0", port=port, debug=True)
