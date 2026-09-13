import requests

from tools.registry import mcp

SEARX_HOST = "http://localhost:8080"
SEARX_RESULT_COUNT = 5


@mcp.tool(
    name="web_search",
    description="Search the web for current information.",
    annotations={"title": "Web Search", "readOnlyHint": True, "openWorldHint": True},
)
def web_search(query: str) -> str:
    response = requests.get(SEARX_HOST + "/search", params={"q": query, "format": "json"})
    response.raise_for_status()
    results = response.json().get("results", [])[:SEARX_RESULT_COUNT]
    if not results:
        return "No results found."
    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('url', '')}\n{r.get('content', '')}"
        for r in results
    )
