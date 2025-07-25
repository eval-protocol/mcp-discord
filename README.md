# Discord MCP Server

A Model Context Protocol (MCP) server built with [FastMCP](https://gofastmcp.com/) that provides Discord integration capabilities to MCP clients like Claude Desktop.


### [See available tools in server.py](./src/discord_mcp/server.py)

Search for `@tool` to see decorated methods that are available as tools

## Installation

### 1. Set up your Discord bot:


   1. In Discord, activate "Developer Mode" by navigating to Settings -> Advanced -> Developer Mode.
   1. Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
   1. Navigate to the "Bot" tab and click Reset Token to generate a new token.
   1. Create a bot and copy the token
   1. On the Bot tab of the Discord developer portal, scroll to the "Privileged
   Gateway Intents" section and enable the following intents:
      - `MESSAGE CONTENT INTENT`
      - `PRESENCE INTENT`
      - `SERVER MEMBERS INTENT`
   1. Then, navigate to the OAuth2 tab and enable the following scopes:
      - Under Scopes, select `bot`
      - Under Bot Permissions, select Administrator
      - Under Integration type, leave the default Guild Install value selected.
   1. Now copy the Generated URL at the end of the page and paste it in a
   channel in your Discord server to send a message. On the sent message, click
   the link you pasted and you will be prompted to authorize the bot. Click
   Continue.

### 2. Clone and install the package:

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

### 3. Configure Claude Desktop:
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