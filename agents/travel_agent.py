from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

from context import PlanningContext, format_profile

TRAVEL_TOOL_NAMES = {
    "search_one_way_flights",
    "search_round_trip_flights",
    "search_round_trips_in_date_range",
    "search_flights_by_airline",
    "get_travel_dates",
    "generate_google_flights_url",
    "get_current_time",
    "convert_time",
}

BASE_INSTRUCTIONS = """You are the Travel sub-agent for a wedding planning system.
Find flights to and from the wedding destination using the available flight-search
tools. Report concrete options (airline, price, dates) rather than generic advice.

The flight-search tools return a JSON object with a "flights" list, where each entry
has "airlines", "price", "departure_time", "arrival_time", "total_duration", and
"stops" fields — read those fields directly out of the tool result. Never invent or
guess flight numbers, airlines, times, or prices; only report values that actually
appear in the tool's returned JSON. If a tool call fails or returns no usable data,
say so plainly instead of making up a plausible-looking answer.

The wedding's guest count is how many people are attending the wedding overall — it is
NOT the number of flight passengers. Unless the user tells you otherwise, search for
just 1-2 passengers (the couple). Google Flights also rejects any search over 9
passengers, so never pass the guest count as a passenger count. Only search round-trip,
multi-city, or specific return dates if the user actually asked for them — a one-way
question should get a one-way search, not an assumed return trip."""


@dynamic_prompt
def travel_prompt(request: ModelRequest) -> str:
    ctx: PlanningContext = request.runtime.context
    return f"{BASE_INSTRUCTIONS}\n\n{format_profile(ctx)}"


def build_travel_agent(model, all_tools):
    tools = [t for t in all_tools if t.name in TRAVEL_TOOL_NAMES]
    return create_agent(
        model=model,
        tools=tools,
        middleware=[travel_prompt],
        context_schema=PlanningContext,
    )
