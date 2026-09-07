import os

from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVER_PATH = os.path.join(os.path.dirname(__file__), "mcp_server.py")

client = MultiServerMCPClient(
    {
        "chef_tools": {
            "command": "python",
            "args": [MCP_SERVER_PATH],
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
    }
)


async def load_tools():
    return await client.get_tools()
