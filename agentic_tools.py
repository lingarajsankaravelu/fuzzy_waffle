import base64
import mimetypes

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_community.utilities import SearxSearchWrapper

from model_config import get_vision_model

search = SearxSearchWrapper(searx_host="http://localhost:8080")


@tool("Web search", description="Search the web for current information.")
def web_search(query: str) -> str:
    return search.run(query)


@tool("Analyze image", description="Answer a question about an image given its local file path.")
def analyze_image(image_path: str, question: str = "Describe this image in detail.") -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    vision_model = get_vision_model()
    message = HumanMessage(content=[
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
    ])
    response = vision_model.invoke([message])
    return response.content
