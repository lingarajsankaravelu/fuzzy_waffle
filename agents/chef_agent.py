from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

from context import PlanningContext, format_profile

CHEF_TOOL_NAMES = {"analyze_image", "web_search"}

BASE_INSTRUCTIONS = """You are the Chef sub-agent for a wedding planning system.
Given ingredients or a cuisine, suggest a wedding menu with dishes and cooking notes.
Given an image and text, answer what is in the image and describe ingredients and
cooking technique. When calling analyze_image, always pass
system_prompt="You are a chef's visual assistant. Identify all food items and
ingredients visible, their apparent freshness or condition, and note any cooking
equipment or techniques implied by the scene." so the analysis stays cooking-focused.
Scale the menu to the guest count you're given, and always include a rough total cost
estimate (clearly labeled as an estimate, not a real quote) based on typical
per-person catering costs for the cuisine and guest count."""


@dynamic_prompt
def chef_prompt(request: ModelRequest) -> str:
    ctx: PlanningContext = request.runtime.context
    return f"{BASE_INSTRUCTIONS}\n\n{format_profile(ctx)}"


def build_chef_agent(model, all_tools):
    tools = [t for t in all_tools if t.name in CHEF_TOOL_NAMES]
    return create_agent(
        model=model,
        tools=tools,
        middleware=[chef_prompt],
        context_schema=PlanningContext,
    )
