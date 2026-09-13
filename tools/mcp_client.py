import os
from contextlib import AsyncExitStack

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

client = MultiServerMCPClient(
    {
        "chef_tools": {
            "command": "python",
            "args": ["-m", "tools.mcp_server"],
            "cwd": REPO_ROOT,
            "transport": "stdio",
        },
        "time": {
            "command": "uvx",
            "args": [
                "mcp-server-time",
                "--local-timezone=Asia/Kolkata",
            ],
            "transport": "stdio",
        },
        "flights": {
            "command": "uvx",
            "args": [
                "--from", "git+https://github.com/HaroldLeo/google-flights-mcp.git",
                "--with", "mcp<2",
                "mcp-server-google-flights",
            ],
            "transport": "stdio",
        },
    }
)


class PersistentTools:
    """Keeps one live stdio session per MCP server open for as long as this is used
    as a context manager, instead of `client.get_tools()`'s default of spawning a
    fresh subprocess for every individual tool call."""

    def __init__(self):
        self._stack = AsyncExitStack()
        self.tools = []

    async def __aenter__(self):
        for server_name in client.connections:
            session = await self._stack.enter_async_context(client.session(server_name))
            self.tools.extend(await load_mcp_tools(session, server_name=server_name))
        return self

    async def __aexit__(self, *exc_info):
        await self._stack.aclose()
