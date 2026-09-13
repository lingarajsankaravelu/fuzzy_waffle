from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from state import note_dietary_restriction, note_preferred_cuisine, note_decision
from agents.travel_agent import build_travel_agent
from agents.venue_agent import build_venue_agent
from agents.chef_agent import build_chef_agent
from agents.dj_agent import build_dj_agent


TASK_ARG_DESCRIPTION = (
    "A single natural-language description of what's needed, including any relevant "
    "details (e.g. 'Find flights from BOM to GOI on 2026-12-12'). Do not pass separate "
    "fields — everything goes in this one string."
)


def make_subagent_tool(name, description, sub_agent, planning_context):
    async def _run(task: Annotated[str, TASK_ARG_DESCRIPTION]) -> str:
        result = await sub_agent.ainvoke(
            {"messages": [HumanMessage(content=task)]},
            context=planning_context,
        )
        return result["messages"][-1].content
    return tool(name, description=f"{description} Call with a single 'task' string — {TASK_ARG_DESCRIPTION}")(_run)


def make_chef_tool(sub_agent, planning_context):
    async def _run(
        task: Annotated[str, TASK_ARG_DESCRIPTION],
        dietary_restrictions: Annotated[list[str], InjectedState("dietary_restrictions")],
        preferred_cuisines: Annotated[list[str], InjectedState("preferred_cuisines")],
    ) -> str:
        enriched_task = (
            f"{task}\n\nKnown dietary restrictions: {', '.join(dietary_restrictions) or 'none'}. "
            f"Known preferred cuisines: {', '.join(preferred_cuisines) or 'none'}."
        )
        result = await sub_agent.ainvoke(
            {"messages": [HumanMessage(content=enriched_task)]},
            context=planning_context,
        )
        return result["messages"][-1].content
    return tool(
        "chef_agent",
        description=(
            "Delegate to the chef sub-agent for menu suggestions, recipes, food-image "
            f"analysis, and cost estimates for the wedding. Call with a single 'task' "
            f"string — {TASK_ARG_DESCRIPTION}"
        ),
    )(_run)


def build_agent_tools(model, all_tools, planning_context):
    """Builds the 4 sub-agents, wraps each as a tool, and returns the orchestrator's full tool list."""
    travel_agent = build_travel_agent(model, all_tools)
    venue_agent = build_venue_agent(model, all_tools)
    chef_agent = build_chef_agent(model, all_tools)
    dj_agent = build_dj_agent(model, all_tools)

    return [
        make_subagent_tool(
            "travel_agent",
            "Delegate to the travel sub-agent for flights to/from the wedding destination.",
            travel_agent, planning_context,
        ),
        make_subagent_tool(
            "venue_agent",
            "Delegate to the venue sub-agent to find and compare wedding venues.",
            venue_agent, planning_context,
        ),
        make_chef_tool(chef_agent, planning_context),
        make_subagent_tool(
            "dj_agent",
            "Delegate to the DJ sub-agent for playlist/music suggestions matching a genre.",
            dj_agent, planning_context,
        ),
        note_dietary_restriction,
        note_preferred_cuisine,
        note_decision,
    ]
