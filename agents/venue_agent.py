from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

from context import PlanningContext, format_profile

BASE_INSTRUCTIONS = """You are the Venue sub-agent for a wedding planning system.
Use web search to find and compare wedding venues at the destination, matching the
guest count and budget. Report concrete options (name, location, approximate cost)
rather than generic advice."""


@dynamic_prompt
def venue_prompt(request: ModelRequest) -> str:
    ctx: PlanningContext = request.runtime.context
    return f"{BASE_INSTRUCTIONS}\n\n{format_profile(ctx)}"


def build_venue_agent(model, all_tools):
    tools = [t for t in all_tools if t.name == "web_search"]
    return create_agent(
        model=model,
        tools=tools,
        middleware=[venue_prompt],
        context_schema=PlanningContext,
    )
