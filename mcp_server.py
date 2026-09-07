import base64
import mimetypes

import requests
from mcp.server.fastmcp import FastMCP
from langchain_core.messages import HumanMessage, SystemMessage

from model_config import get_vision_model

mcp = FastMCP("tools")

SEARX_HOST = "http://localhost:8080"
SEARX_RESULT_COUNT = 5

DEFAULT_VISION_SYSTEM_PROMPT = "You are a precise visual analysis assistant. Describe what you see accurately and factually."


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


@mcp.tool(
    name="analyze_image",
    description=(
        "Answer a question about an image given its local file path. Optionally pass "
        "system_prompt to steer the vision model's focus toward the calling agent's "
        "persona (e.g. ingredients and cooking technique for a chef agent); defaults "
        "to a neutral, factual description."
    ),
    annotations={"title": "Analyze Image", "readOnlyHint": True, "openWorldHint": False},
)
def analyze_image(
    image_path: str,
    question: str = "Describe this image in detail.",
    system_prompt: str = DEFAULT_VISION_SYSTEM_PROMPT,
) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    vision_model = get_vision_model()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=[
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
        ]),
    ]
    response = vision_model.invoke(messages)
    return response.content


if __name__ == "__main__":
    mcp.run(transport="stdio")
