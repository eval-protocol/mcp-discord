import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional
from functools import wraps
import discord
from discord.ext import commands
from fastmcp import Server, tool
from fastmcp.server import stdio_server

def _configure_windows_stdout_encoding():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
app = Server("discord-server")

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

# Server Information Tools
@tool
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
        "explicit_content_filter": str(guild.explicit_content_filter)
    }
    return f"Server Information:\n" + "\n".join(f"{k}: {v}" for k, v in info.items())

@tool
@require_discord_client
async def get_channels(server_id: str) -> str:
    """Get a list of all channels in a Discord server"""
    try:
        guild = discord_client.get_guild(int(server_id))
        if guild:
            channel_list = []
            for channel in guild.channels:
                channel_list.append(f"#{channel.name} (ID: {channel.id}) - {channel.type}")
            
            return f"Channels in {guild.name}:\n" + "\n".join(channel_list)
        else:
            return "Guild not found"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
@require_discord_client
async def list_members(server_id: str, limit: int = 100) -> str:
    """Get a list of members in a server"""
    guild = await discord_client.fetch_guild(int(server_id))
    limit = min(limit, 1000)
    
    members = []
    async for member in guild.fetch_members(limit=limit):
        members.append({
            "id": str(member.id),
            "name": member.name,
            "nick": member.nick,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "roles": [str(role.id) for role in member.roles[1:]]  # Skip @everyone
        })
    
    return f"Server Members ({len(members)}):\n" + \
           "\n".join(f"{m['name']} (ID: {m['id']}, Roles: {', '.join(m['roles'])})" for m in members)

# Role Management Tools
@tool
@require_discord_client
async def add_role(server_id: str, user_id: str, role_id: str) -> str:
    """Add a role to a user"""
    guild = await discord_client.fetch_guild(int(server_id))
    member = await guild.fetch_member(int(user_id))
    role = guild.get_role(int(role_id))
    
    await member.add_roles(role, reason="Role added via MCP")
    return f"Added role {role.name} to user {member.name}"

@tool
@require_discord_client
async def remove_role(server_id: str, user_id: str, role_id: str) -> str:
    """Remove a role from a user"""
    guild = await discord_client.fetch_guild(int(server_id))
    member = await guild.fetch_member(int(user_id))
    role = guild.get_role(int(role_id))
    
    await member.remove_roles(role, reason="Role removed via MCP")
    return f"Removed role {role.name} from user {member.name}"

# Channel Management Tools
@tool
@require_discord_client
async def create_text_channel(
    server_id: str, 
    name: str, 
    category_id: Optional[str] = None, 
    topic: Optional[str] = None
) -> str:
    """Create a new text channel"""
    guild = await discord_client.fetch_guild(int(server_id))
    category = None
    if category_id:
        category = guild.get_channel(int(category_id))
    
    channel = await guild.create_text_channel(
        name=name,
        category=category,
        topic=topic,
        reason="Channel created via MCP"
    )
    
    return f"Created text channel #{channel.name} (ID: {channel.id})"

@tool
@require_discord_client
async def delete_channel(channel_id: str, reason: Optional[str] = None) -> str:
    """Delete a channel"""
    channel = await discord_client.fetch_channel(int(channel_id))
    await channel.delete(reason=reason or "Channel deleted via MCP")
    return "Deleted channel successfully"

# Message Reaction Tools
@tool
@require_discord_client
async def add_reaction(channel_id: str, message_id: str, emoji: str) -> str:
    """Add a reaction to a message"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    await message.add_reaction(emoji)
    return f"Added reaction {emoji} to message"

@tool
@require_discord_client
async def add_multiple_reactions(channel_id: str, message_id: str, emojis: List[str]) -> str:
    """Add multiple reactions to a message"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    for emoji in emojis:
        await message.add_reaction(emoji)
    return f"Added reactions: {', '.join(emojis)} to message"

@tool
@require_discord_client
async def remove_reaction(channel_id: str, message_id: str, emoji: str) -> str:
    """Remove a reaction from a message"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    await message.remove_reaction(emoji, discord_client.user)
    return f"Removed reaction {emoji} from message"

# Message Tools
@tool
@require_discord_client
async def send_message(channel_id: str, content: str) -> str:
    """Send a message to a specific channel"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.send(content)
    return f"Message sent successfully. Message ID: {message.id}"

@tool
@require_discord_client
async def read_messages(channel_id: str, limit: int = 10) -> str:
    """Read recent messages from a channel"""
    channel = await discord_client.fetch_channel(int(channel_id))
    limit = min(limit, 100)
    
    messages = []
    async for message in channel.history(limit=limit):
        reaction_data = []
        for reaction in message.reactions:
            emoji_str = str(reaction.emoji.name) if hasattr(reaction.emoji, 'name') and reaction.emoji.name else str(reaction.emoji.id) if hasattr(reaction.emoji, 'id') else str(reaction.emoji)
            reaction_info = {
                "emoji": emoji_str,
                "count": reaction.count
            }
            logger.error(f"Emoji: {emoji_str}")
            reaction_data.append(reaction_info)
        messages.append({
            "id": str(message.id),
            "author": str(message.author),
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "reactions": reaction_data
        })
    
    # Helper function to format reactions
    def format_reaction(r):
        return f"{r['emoji']}({r['count']})"
        
    return f"Retrieved {len(messages)} messages:\n\n" + \
           "\n".join([
               f"{m['author']} ({m['timestamp']}): {m['content']}\n" +
               f"Reactions: {', '.join([format_reaction(r) for r in m['reactions']]) if m['reactions'] else 'No reactions'}"
               for m in messages
           ])

@tool
@require_discord_client
async def get_user_info(user_id: str) -> str:
    """Get information about a Discord user"""
    user = await discord_client.fetch_user(int(user_id))
    user_info = {
        "id": str(user.id),
        "name": user.name,
        "discriminator": user.discriminator,
        "bot": user.bot,
        "created_at": user.created_at.isoformat()
    }
    return f"User information:\n" + \
           f"Name: {user_info['name']}#{user_info['discriminator']}\n" + \
           f"ID: {user_info['id']}\n" + \
           f"Bot: {user_info['bot']}\n" + \
           f"Created: {user_info['created_at']}"

@tool
@require_discord_client
async def moderate_message(
    channel_id: str, 
    message_id: str, 
    reason: str, 
    timeout_minutes: Optional[int] = None
) -> str:
    """Delete a message and optionally timeout the user"""
    channel = await discord_client.fetch_channel(int(channel_id))
    message = await channel.fetch_message(int(message_id))
    
    # Delete the message
    await message.delete(reason=reason)
    
    # Handle timeout if specified
    if timeout_minutes and timeout_minutes > 0:
        if isinstance(message.author, discord.Member):
            duration = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
            await message.author.timeout(duration, reason=reason)
            return f"Message deleted and user timed out for {timeout_minutes} minutes."
    
    return "Message deleted successfully."

@tool
@require_discord_client
async def list_servers() -> str:
    """Get a list of all Discord servers the bot has access to with their details such as name, id, member count, and creation date."""
    servers = []
    for guild in discord_client.guilds:
        servers.append({
            "id": str(guild.id),
            "name": guild.name,
            "member_count": guild.member_count,
            "created_at": guild.created_at.isoformat()
        })
    
    return f"Available Servers ({len(servers)}):\n" + \
           "\n".join(f"{s['name']} (ID: {s['id']}, Members: {s['member_count']})" for s in servers)

async def main():
    # Start Discord bot in the background
    asyncio.create_task(bot.start(DISCORD_TOKEN))
    
    # Run FastMCP server
    await app.run(stdio_server())

if __name__ == "__main__":
    asyncio.run(main())
