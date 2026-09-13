from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

from context import PlanningContext, format_profile

BASE_INSTRUCTIONS = """You are the DJ sub-agent for a wedding planning system.
Suggest a playlist matching the genre the user asks for, scaled to the guest count
(e.g. enough variety for the wedding's duration). You may use web search to find
currently popular songs in that genre. There is no music-streaming integration —
give concrete song and artist suggestions as text, not a real playlist link."""


@dynamic_prompt
def dj_prompt(request: ModelRequest) -> str:
    ctx: PlanningContext = request.runtime.context
    return f"{BASE_INSTRUCTIONS}\n\n{format_profile(ctx)}"


def build_dj_agent(model, all_tools):
    tools = [t for t in all_tools if t.name == "web_search"]
    return create_agent(
        model=model,
        tools=tools,
        middleware=[dj_prompt],
        context_schema=PlanningContext,
    )
