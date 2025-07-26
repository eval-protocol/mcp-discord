import asyncio
import datetime
import os
from pathlib import Path
import zoneinfo

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

from mcp_discord.server import bot, read_messages  # noqa: E402


@pytest.mark.asyncio
async def test_read_messages_text_channel():
    """Test the read_messages function with real Discord client"""
    asyncio.create_task(bot.start(os.getenv("DISCORD_TOKEN")))
    while not bot.is_ready():
        await asyncio.sleep(0.1)
    channel_id = "1137072073399865409"  # general channel id
    pst = zoneinfo.ZoneInfo("America/Los_Angeles")  # noqa: F821
    after = datetime.datetime(2025, 7, 20, tzinfo=pst)
    result = await read_messages.fn(channel_id, after)
    assert "Retrieved" in result
    print(f"Test result: {result}")


@pytest.mark.asyncio
async def test_read_messages_forum_channel():
    """Test the read_messages function with real Discord client"""
    asyncio.create_task(bot.start(os.getenv("DISCORD_TOKEN")))
    while not bot.is_ready():
        await asyncio.sleep(0.1)
    channel_id = "1137075268138324079"  # questions channel id
    # Set 'after' to July 20, 2025 in US Pacific Time (PST/PDT) using only the standard library
    pst = zoneinfo.ZoneInfo("America/Los_Angeles")  # noqa: F821
    after = datetime.datetime(2025, 7, 20, tzinfo=pst)
    result = await read_messages.fn(channel_id, after)
    assert "Retrieved" in result
    print(f"Test result: {result}")
