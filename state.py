import operator
from dataclasses import dataclass, field
from typing import Annotated, Literal

from langchain.agents import AgentState
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


# Custom state fields on top of the built-in "messages" state: unlike context (fixed
# per call, supplied by the app), these are written by tools mid-conversation and
# persisted by the checkpointer for the rest of the thread. Only the orchestrator's
# graph carries this state — sub-agents are invoked stateless, per call.
@dataclass
class default_state_schema(AgentState):
    dietary_restrictions: Annotated[list[str], operator.add] = field(default_factory=list)
    preferred_cuisines: Annotated[list[str], operator.add] = field(default_factory=list)
    chosen_venue: str = ""
    chosen_flights: str = ""
    chosen_menu: str = ""
    chosen_playlist_genre: str = ""


@tool(
    "note_dietary_restriction",
    description="Record a dietary restriction, allergy, or preference the user mentions (e.g. 'vegan', 'nut allergy').",
)
def note_dietary_restriction(
    restriction: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    existing_restrictions: Annotated[list[str], InjectedState("dietary_restrictions")],
) -> Command:
    if restriction in existing_restrictions:
        return Command(update={
            "messages": [ToolMessage(f"Already noted: {restriction}", tool_call_id=tool_call_id)],
        })
    return Command(update={
        "dietary_restrictions": [restriction],
        "messages": [ToolMessage(f"Noted dietary restriction: {restriction}", tool_call_id=tool_call_id)],
    })


note_dietary_restriction.metadata = {
    "title": "Note Dietary Restriction",
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
}


@tool(
    "note_preferred_cuisine",
    description="Record a cuisine the user says they like or prefer (e.g. 'Italian', 'Thai', 'South Indian').",
)
def note_preferred_cuisine(
    cuisine: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    existing_cuisines: Annotated[list[str], InjectedState("preferred_cuisines")],
) -> Command:
    if cuisine in existing_cuisines:
        return Command(update={
            "messages": [ToolMessage(f"Already noted: {cuisine}", tool_call_id=tool_call_id)],
        })
    return Command(update={
        "preferred_cuisines": [cuisine],
        "messages": [ToolMessage(f"Noted preferred cuisine: {cuisine}", tool_call_id=tool_call_id)],
    })


note_preferred_cuisine.metadata = {
    "title": "Note Preferred Cuisine",
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
}


_DECISION_FIELDS = {
    "venue": "chosen_venue",
    "flights": "chosen_flights",
    "menu": "chosen_menu",
    "playlist": "chosen_playlist_genre",
}


@tool(
    "note_decision",
    description="Record the current decision for one part of the wedding plan (venue, flights, menu, or playlist) after a sub-agent has answered, so it's remembered for the rest of the conversation.",
)
def note_decision(
    category: Literal["venue", "flights", "menu", "playlist"],
    value: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    return Command(update={
        _DECISION_FIELDS[category]: value,
        "messages": [ToolMessage(f"Noted {category} decision.", tool_call_id=tool_call_id)],
    })


note_decision.metadata = {
    "title": "Note Decision",
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
}
