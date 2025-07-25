# Discord MCP Server

A Model Context Protocol (MCP) server built with [FastMCP](https://gofastmcp.com/) that provides Discord integration capabilities to MCP clients like Claude Desktop.


### [See available tools in server.py](./src/discord_mcp/server.py)

## Installation

#### 1. Set up your Discord bot:
   1. Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
   2. Create a bot and copy the token
   3. Enable required privileged intents:
      - MESSAGE CONTENT INTENT
      - PRESENCE INTENT
      - SERVER MEMBERS INTENT
   4. Invite the bot to your server using OAuth2 URL Generator

#### 2. Clone and install the package:

```bash
# Clone the repository
git clone https://github.com/eval-protocol/mcp-discord.git
cd mcp-discord

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install the package
uv sync --all-extras
```

#### 3. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "discord": {
    "command": "uv",
    "args": [
        "--directory",
        "/Users/<USER>/<PATH_TO_THIS_REPO>/mcp-discord",
        "run",
        "mcp-discord"
      ],
    "env": {
        "DISCORD_TOKEN": "your_bot_token"
      }
    }
  }
}
```

## License

MIT License - see LICENSE file for details.

## Credits

[hanweg](https://github.com/hanweg)