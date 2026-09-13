from tools.registry import mcp
from tools import web_tools, vision_tools  # import registers their @mcp.tool functions

if __name__ == "__main__":
    mcp.run(transport="stdio")
