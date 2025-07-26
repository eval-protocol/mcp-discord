import asyncio
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

from mcp_discord.server import bot, read_messages  # noqa: E402


@pytest.mark.asyncio
async def test_read_messages():
    """Test the read_messages function with real Discord client"""
    asyncio.create_task(bot.start(os.getenv("DISCORD_TOKEN")))
    while not bot.is_ready():
        await asyncio.sleep(0.1)
    channel_id = "1137072073399865409"  # general channel id
    result = await read_messages.fn(channel_id, 5)
    assert "Retrieved" in result
    print(f"Test result: {result}")
