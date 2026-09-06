from langchain_core.tools import tool
from langchain_community.utilities import SearxSearchWrapper

search = SearxSearchWrapper(searx_host="http://localhost:8080")


@tool("Web search", description="Search the web for current information.")
def web_search(query: str) -> str:
    return search.run(query)
