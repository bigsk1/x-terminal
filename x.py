#!/usr/bin/env python3
import sys
import os
import requests
from requests_oauthlib import OAuth1
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
import argparse

# Script version
VERSION = "1.3.0-cyberpunk"

# Custom cyberpunk theme for rich console
cyberpunk_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "success": "bold green",
    "preview": "cyan",
    "field": "bright_cyan",
    "value": "bright_green"
})
console = Console(theme=cyberpunk_theme)

# Retrieve API credentials from environment variables
consumer_key = os.getenv("X_CONSUMER_KEY")
consumer_secret = os.getenv("X_CONSUMER_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

# Validate credentials
if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
    console.print("[error]Missing X API credentials. Set them in your .zshrc or environment.[/error]")
    sys.exit(1)

# Windows emoji support warning
if os.name == "nt" and not os.environ.get("WT_SESSION"):
    console.print("[warning]For optimal emoji display, use Windows Terminal on this neon grid.[/warning]")

def split_message(message, limit=280):
    """Slice a message into cybernetic fragments under the character limit."""
    parts = []
    while len(message) > limit:
        split_point = message.rfind(" ", 0, limit)
        if split_point == -1:
            split_point = limit
        parts.append(message[:split_point])
        message = message[split_point:].lstrip()
    parts.append(message)
    return parts

def upload_image(image_url, verbose=False):
    """Upload an image from a URL to X's neon matrix, return media ID."""
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL {image_url} doesn't emit an image signal (content-type: {content_type})")
        auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
        files = {"media": ("image", response.content)}
        upload_response = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth,
            files=files
        )
        upload_response.raise_for_status()
        data = upload_response.json()
        if verbose:
            console.print(f"[info]Upload data stream: {data}[/info]")
        media_id = data.get("media_id_string")
        if not media_id:
            raise ValueError("No media ID detected in the data stream")
        return media_id
    except Exception as e:
        console.print(f"[error]Image upload failed in the grid: {e}[/error]")
        return None

def display_preview(message, image_url=None):
    """Render a cyberpunk-style preview of the post."""
    table = Table(title="Transmission Details", title_style="bold magenta")
    table.add_column("Field", style="field")
    table.add_column("Value", style="value")
    table.add_row("Data", message)
    if image_url:
        table.add_row("Visual", image_url)
    console.print(table)

def post_tweet(message, image_url=None, reply_to=None, dry_run=False, verbose=False):
    """Transmit a tweet or thread into the X cyberspace."""
    if not message.strip():
        console.print("[error]Transmission aborted: No data in the buffer.[/error]")
        return
    display_preview(message, image_url)
    parts = split_message(message)
    if dry_run:
        console.print("[warning]Dry run: Simulating transmission...[/warning]")
        for i, part in enumerate(parts, 1):
            console.print(f"[preview]Fragment {i}:[/preview] {part}")
            if i == 1 and image_url:
                console.print(f"[preview]Visual payload:[/preview] {image_url}")
        return
    auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
    media_id = None
    if image_url:
        with console.status("[info]Uploading visual to the matrix...[/info]", spinner="dots"):
            media_id = upload_image(image_url, verbose)
        if not media_id:
            return
    if len(parts) > 1:
        console.print(f"[warning]Data stream exceeds 280 units, splitting into {len(parts)} fragments.[/warning]")
    previous_id = None
    tweet_ids = []
    with console.status("[info]Transmitting to X cyberspace...[/info]", spinner="dots"):
        for i, part in enumerate(parts, 1):
            payload = {"text": part}
            if i == 1 and reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}
            elif previous_id:
                payload["reply"] = {"in_reply_to_tweet_id": previous_id}
            if media_id and i == 1:
                payload["media"] = {"media_ids": [media_id]}
            try:
                response = requests.post("https://api.twitter.com/2/tweets", auth=auth, json=payload)
                response.raise_for_status()
                data = response.json()
                if verbose:
                    console.print(f"[info]Fragment {i} response: {data}[/info]")
                tweet_id = data["data"]["id"]
                tweet_ids.append(tweet_id)
                previous_id = tweet_id
            except requests.RequestException as e:
                console.print(f"[error]Transmission error on fragment {i}: {e}[/error]")
                if response.text and verbose:
                    console.print(f"[error]System response: {response.text}[/error]")
                return
    console.print(f"[success]Transmission complete: {len(tweet_ids)} fragment(s) sent![/success]")
    for i, tweet_id in enumerate(tweet_ids, 1):
        console.print(f"[preview]Fragment {i} ID:[/preview] {tweet_id}")

def delete_tweet(tweet_id, no_confirm=False, verbose=False):
    """Purge a tweet from the X matrix."""
    if not no_confirm:
        confirmation = input(f"Confirm purge of tweet {tweet_id} from the grid? [y/N] ")
        if confirmation.lower() != "y":
            console.print("[warning]Purge operation aborted.[/warning]")
            return
    auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
    with console.status("[info]Purging from cyberspace...[/info]", spinner="dots"):
        try:
            response = requests.delete(f"https://api.twitter.com/2/tweets/{tweet_id}", auth=auth)
            response.raise_for_status()
            if verbose:
                console.print(f"[info]Purge response: {response.text}[/info]")
            console.print(f"[success]Tweet {tweet_id} successfully erased from the matrix.[/success]")
        except requests.RequestException as e:
            console.print(f"[error]Purge failed: {e}[/error]")
            if response.text and verbose:
                console.print(f"[error]System response: {response.text}[/error]")

def show_version():
    """Reveal the cybernetic core version."""
    console.print(f"[preview]X CLI Cyberdeck version {VERSION}[/preview]")

def main():
    parser = argparse.ArgumentParser(
        description="X CLI Cyberdeck: Command the X matrix from your terminal.",
        epilog=(
            "System Initialization:\n"
            "1. Install cyber-modules: pip install requests requests-oauthlib rich\n"
            "2. Configure auth-keys in your .zshrc:\n"
            "   export X_CONSUMER_KEY='your_key'\n"
            "   export X_CONSUMER_SECRET='your_secret'\n"
            "   export X_ACCESS_TOKEN='your_token'\n"
            "   export X_ACCESS_TOKEN_SECRET='your_token_secret'\n"
            "3. Activate config: source ~/.zshrc\n"
            "Cyber-Commands:\n"
            "  python x.py post 'Enter the grid!' --image-url <url>\n"
            "  python x.py delete 12345 --no-confirm"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--verbose", action="store_true", help="Expose raw data streams from the matrix")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Cyber-commands to manipulate X")

    # Post command
    post_parser = subparsers.add_parser("post", help="Transmit a message or thread into cyberspace")
    post_parser.add_argument("message", type=str, help="Data packet to transmit (emojis supported)")
    post_parser.add_argument("-i", "--image-url", type=str, help="Visual payload URL (e.g., Cloudflare Image)")
    post_parser.add_argument("--reply-to", type=str, help="Target ID for reply in the grid")
    post_parser.add_argument("--dry-run", action="store_true", help="Simulate transmission without sending")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Purge a tweet from the matrix")
    delete_parser.add_argument("tweet_id", type=str, help="ID of the tweet to erase")
    delete_parser.add_argument("--no-confirm", action="store_true", help="Bypass purge confirmation")

    # Version command
    subparsers.add_parser("version", help="Reveal the cyberdeck’s version")

    args = parser.parse_args()

    if args.command == "post":
        post_tweet(args.message, args.image_url, args.reply_to, args.dry_run, args.verbose)
    elif args.command == "delete":
        delete_tweet(args.tweet_id, args.no_confirm, args.verbose)
    elif args.command == "version":
        show_version()

if __name__ == "__main__":
    main()
