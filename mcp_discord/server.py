import asyncio
import datetime
import logging
import os
import sys
from functools import wraps
from typing import Dict, Optional

import discord
from discord.ext import commands
from fastmcp import FastMCP
from pydantic import BaseModel, Field


def _configure_windows_stdout_encoding():
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


_configure_windows_stdout_encoding()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

# Discord bot setup
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Initialize Discord bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize FastMCP server
mcp = FastMCP("discord-server")

# Store Discord client reference
discord_client = None


@bot.event
async def on_ready():
    global discord_client
    discord_client = bot
    logger.info(f"Logged in as {bot.user.name}")


# Helper function to ensure Discord client is ready
def require_discord_client(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not discord_client:
            raise RuntimeError("Discord client not ready")
        return await func(*args, **kwargs)

    return wrapper


# Pydantic models for channel data
class ChannelInfo(BaseModel):
    name: str
    type: str
    position: int
    archived: bool = Field(default=False)
    category_id: Optional[str] = None
    topic: Optional[str] = None
    nsfw: Optional[bool] = None
    slowmode_delay: Optional[int] = None
    user_limit: Optional[int] = None
    bitrate: Optional[int] = None
    created_at: Optional[str] = None


class ServerChannelsResponse(BaseModel):
    server_name: str
    server_id: str
    channels: Dict[str, ChannelInfo]
    total_channels: int


# Server Information Tools
@mcp.tool
@require_discord_client
async def get_server_info(server_id: str) -> str:
    """Get information about a Discord server"""
    guild = await discord_client.fetch_guild(int(server_id))
    info = {
        "name": guild.name,
        "id": str(guild.id),
        "owner_id": str(guild.owner_id),
        "member_count": guild.member_count,
        "created_at": guild.created_at.isoformat(),
        "description": guild.description,
        "premium_tier": guild.premium_tier,
        "explicit_content_filter": str(guild.explicit_content_filter),
    }
    return "Server Information:\n" + "\n".join(f"{k}: {v}" for k, v in info.items())


@mcp.tool
@require_discord_client
async def get_channels(server_id: str) -> ServerChannelsResponse:
    """Get a list of all channels in a Discord server"""
    try:
        guild = discord_client.get_guild(int(server_id))
        if guild:
            channels = {}
            for channel in guild.channels:
                channels[str(channel.id)] = ChannelInfo(
                    name=channel.name,
                    type=str(channel.type),
                    position=channel.position,
                    category_id=str(channel.category_id)
                    if channel.category_id
                    else None,
                    topic=channel.topic if hasattr(channel, "topic") else None,
                    nsfw=channel.nsfw if hasattr(channel, "nsfw") else None,
                    slowmode_delay=channel.slowmode_delay
                    if hasattr(channel, "slowmode_delay")
                    else None,
                    user_limit=channel.user_limit
                    if hasattr(channel, "user_limit")
                    else None,
                    bitrate=channel.bitrate if hasattr(channel, "bitrate") else None,
                    created_at=channel.created_at.isoformat()
                    if hasattr(channel, "created_at")
                    else None,
                )

            return ServerChannelsResponse(
                server_name=guild.name,
                server_id=str(guild.id),
                channels=channels,
                total_channels=len(channels),
            )
        else:
            raise ValueError("Guild not found")
    except Exception as e:
        raise RuntimeError(f"Error fetching channels: {str(e)}")


@mcp.tool
@require_discord_client
async def list_members(server_id: str, limit: int = 100) -> str:
    """Get a list of members in a server"""
    guild = await discord_client.fetch_guild(int(server_id))
    limit = min(limit, 1000)

    members = []
    async for member in guild.fetch_members(limit=limit):
        members.append(
            {
                "id": str(member.id),
                "name": member.name,
                "nick": member.nick,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "roles": [str(role.id) for role in member.roles[1:]],  # Skip @everyone
            }
        )

    return f"Server Members ({len(members)}):\n" + "\n".join(
        f"{m['name']} (ID: {m['id']}, Roles: {', '.join(m['roles'])})" for m in members
    )


async def get_last_activity_date(thread: discord.Thread) -> datetime.datetime:
    if thread.message_count > 0:
        last_message = await thread.fetch_message(thread.last_message_id)
        return last_message.created_at
    else:
        return thread.created_at


async def format_thread(thread: discord.Thread, idx: int) -> str:
    # Fetch messages from the thread
    thread_messages = []
    async for message in thread.history(limit=None):
        reaction_data = []
        for reaction in message.reactions:
            emoji_str = (
                str(reaction.emoji.name)
                if hasattr(reaction.emoji, "name") and reaction.emoji.name
                else str(reaction.emoji.id)
                if hasattr(reaction.emoji, "id")
                else str(reaction.emoji)
            )
            reaction_data.append({"emoji": emoji_str, "count": reaction.count})

        thread_messages.append(
            {
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "reactions": reaction_data,
            }
        )

    # Format thread header
    thread_header = (
        f"Thread {idx}:\n"
        f"  Name: {thread.name}\n"
        f"  ID: {thread.id}\n"
        f"  Owner: {thread.owner}\n"
        f"  Created: {thread.created_at}\n"
        f"  Archived: {thread.archived}\n"
        f"  Locked: {thread.locked}\n"
        f"  Messages: {len(thread_messages)}/{thread.message_count}\n"
        f"  Members: {thread.member_count}"
    )

    # Format messages in the thread
    if thread_messages:

        def format_reaction(r):
            return f"{r['emoji']}({r['count']})"

        messages_formatted = []
        for msg_idx, msg in enumerate(thread_messages, 1):
            messages_formatted.append(
                f"    Message {msg_idx}:\n"
                f"      Author: {msg['author']}\n"
                f"      Timestamp: {msg['timestamp']}\n"
                f"      Content: {msg['content'] or '[No content]'}\n"
                f"      Reactions: "
                + (
                    ", ".join([format_reaction(r) for r in msg["reactions"]])
                    if msg["reactions"]
                    else "No reactions"
                )
            )

        return thread_header + "\n\n" + "\n\n".join(messages_formatted)
    else:
        return thread_header + "\n  No messages found after specified datetime"


@mcp.tool
@require_discord_client
async def read_messages(channel_id: str, after: datetime.datetime) -> str:  # noqa: F821
    """Read recent messages from a channel after a given datetime"""
    channel = await discord_client.fetch_channel(int(channel_id))
    after_str = f" after {after.isoformat()}" if after else ""
    if channel.type == discord.ChannelType.text:
        messages = []

        # Use after parameter to filter messages
        async for message in channel.history(after=after, limit=None):
            reaction_data = []
            for reaction in message.reactions:
                emoji_str = (
                    str(reaction.emoji.name)
                    if hasattr(reaction.emoji, "name") and reaction.emoji.name
                    else str(reaction.emoji.id)
                    if hasattr(reaction.emoji, "id")
                    else str(reaction.emoji)
                )
                reaction_info = {"emoji": emoji_str, "count": reaction.count}
                reaction_data.append(reaction_info)

            messages.append(
                {
                    "id": str(message.id),
                    "author": str(message.author),
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "reactions": reaction_data,
                }
            )

        # Helper function to format reactions
        def format_reaction(r):
            return f"{r['emoji']}({r['count']})"

        # Format messages in a more LLM-friendly, readable way
        formatted = []
        for idx, m in enumerate(messages, 1):
            formatted.append(
                f"Message {idx}:\n"
                f"  Author: {m['author']}\n"
                f"  Timestamp: {m['timestamp']}\n"
                f"  Content: {m['content'] or '[No content]'}\n"
                f"  Reactions: "
                + (
                    ", ".join([format_reaction(r) for r in m["reactions"]])
                    if m["reactions"]
                    else "No reactions"
                )
            )

        result = f"Retrieved {len(messages)} messages{after_str}:\n\n" + "\n\n".join(
            formatted
        )
        formatted_threads = []
        for idx, thread in enumerate(channel.threads, 1):
            formatted_threads.append(await format_thread(thread, idx))
        result += f"\n\nRetrieved {len(channel.threads)} threads:\n\n"
        result += "\n\n".join(formatted_threads)
        return result

    elif channel.type == discord.ChannelType.forum:
        # Format threads and their messages
        formatted = []

        for idx, thread in enumerate(channel.threads, 1):
            formatted.append(await format_thread(thread, idx))

        return f"Retrieved {len(channel.threads)} threads:\n\n" + "\n\n".join(formatted)

    else:
        return "Unsupported channel type"


@mcp.tool
@require_discord_client
async def send_message(channel_id: str, content: str) -> str:
    """Send a message to a specific channel"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.send(content)
    return f"Message sent successfully. Message ID: {message.id}"


@mcp.tool
@require_discord_client
async def add_reaction(channel_id: str, message_id: str, emoji: str) -> str:
    """Add a reaction to a message"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    await message.add_reaction(emoji)
    return f"Added reaction {emoji} to message"


@mcp.tool
@require_discord_client
async def remove_reaction(channel_id: str, message_id: str, emoji: str) -> str:
    """Remove a reaction from a message"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    await message.remove_reaction(emoji, discord_client.user)
    return f"Removed reaction {emoji} from message"


@mcp.tool
@require_discord_client
async def get_user_info(user_id: str) -> str:
    """Get information about a Discord user"""
    user = await discord_client.fetch_user(int(user_id))
    user_info = {
        "id": str(user.id),
        "name": user.name,
        "discriminator": user.discriminator,
        "bot": user.bot,
        "created_at": user.created_at.isoformat(),
    }
    return (
        "User information:\n"
        + f"Name: {user_info['name']}#{user_info['discriminator']}\n"
        + f"ID: {user_info['id']}\n"
        + f"Bot: {user_info['bot']}\n"
        + f"Created: {user_info['created_at']}"
    )


@mcp.tool
@require_discord_client
async def list_servers() -> str:
    """Get a list of all Discord servers the bot has access to with their details such as name, id, member count, and creation date."""
    servers = []
    for guild in discord_client.guilds:
        servers.append(
            {
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "created_at": guild.created_at.isoformat(),
            }
        )

    return f"Available Servers ({len(servers)}):\n" + "\n".join(
        f"{s['name']} (ID: {s['id']}, Members: {s['member_count']})" for s in servers
    )


async def main():
    # Start Discord bot in the background
    asyncio.create_task(bot.start(DISCORD_TOKEN))
    await mcp.run_async()


if __name__ == "__main__":
    asyncio.run(main())
