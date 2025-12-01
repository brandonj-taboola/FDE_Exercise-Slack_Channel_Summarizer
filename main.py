"""Slack Channel Summarizer - CLI Interface."""

import os
import sys
import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from slack_client import SlackClient
from summarizer import Summarizer

# Load environment variables
load_dotenv()

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console(force_terminal=True)


@click.group()
def cli():
    """Slack Channel Summarizer - Summarize your Slack channels with AI."""
    pass


@cli.command()
@click.argument("channel")
@click.option("--hours", "-h", default=24, help="Hours of history to summarize (default: 24)")
@click.option("--style", "-s", type=click.Choice(["detailed", "brief"]), default="detailed", help="Summary style")
@click.option("--threads/--no-threads", "-t", default=False, help="Include thread replies for full context")
@click.option("--post/--no-post", default=False, help="Post summary to Slack")
@click.option("--post-to", "-p", default=None, help="Channel to post summary to (default: same channel)")
def summarize(channel: str, hours: int, style: str, threads: bool, post: bool, post_to: str):
    """
    Summarize messages from a Slack channel.

    CHANNEL: The channel name to summarize (e.g., 'general' or '#general')
    """
    try:
        # Initialize clients
        with console.status("[bold blue]Connecting to Slack..."):
            slack = SlackClient()
            summarizer = Summarizer()

        # Fetch messages
        channel_name = channel.lstrip("#")
        status_msg = f"Fetching messages from #{channel_name}..."
        if threads:
            status_msg = f"Fetching messages and threads from #{channel_name}..."
        with console.status(f"[bold blue]{status_msg}"):
            messages = slack.fetch_messages(channel_name, hours=hours, include_threads=threads)

        if not messages:
            console.print(f"[yellow]No messages found in #{channel_name} in the last {hours} hours.[/yellow]")
            return

        # Count thread replies
        total_replies = sum(len(m.get("replies", [])) for m in messages)
        if threads and total_replies > 0:
            console.print(f"[green]Found {len(messages)} messages with {total_replies} thread replies[/green]")
        else:
            console.print(f"[green]Found {len(messages)} messages[/green]")

        # Generate summary
        with console.status("[bold blue]Generating summary with Claude..."):
            summary = summarizer.summarize(messages, channel_name, style=style)

        # Display summary
        console.print()
        console.print(Panel(summary, title="Channel Summary", border_style="blue"))

        # Post to Slack if requested
        if post:
            target_channel = post_to or channel_name
            with console.status(f"[bold blue]Posting to #{target_channel}..."):
                slack.post_message(target_channel, summary)
            console.print(f"[green]Summary posted to #{target_channel}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command()
def channels():
    """List available channels the bot can access."""
    try:
        with console.status("[bold blue]Fetching channels..."):
            slack = SlackClient()
            channel_list = slack.get_channels()

        if not channel_list:
            console.print("[yellow]No channels found. Make sure the bot is invited to channels.[/yellow]")
            return

        console.print("\n[bold]Available Channels:[/bold]\n")
        for ch in sorted(channel_list, key=lambda x: x["name"]):
            console.print(f"  #{ch['name']}")

        console.print(f"\n[dim]{len(channel_list)} channels available[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command()
def test():
    """Test your API connections."""
    console.print("\n[bold]Testing connections...[/bold]\n")

    # Test Slack
    try:
        slack = SlackClient()
        channels = slack.get_channels()
        console.print(f"[green]✓ Slack connected[/green] - {len(channels)} channels accessible")
    except Exception as e:
        console.print(f"[red]✗ Slack failed: {e}[/red]")

    # Test Anthropic
    try:
        summarizer = Summarizer()
        console.print("[green]✓ Anthropic API key valid[/green]")
    except Exception as e:
        console.print(f"[red]✗ Anthropic failed: {e}[/red]")

    console.print()


if __name__ == "__main__":
    cli()
