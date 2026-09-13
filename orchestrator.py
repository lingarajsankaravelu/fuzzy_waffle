import asyncio

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from model_config import model
from tools.mcp_client import PersistentTools
from state import default_state_schema
from context import DEFAULT_PLANNING_CONTEXT
from tools.orchestrator_tools import build_agent_tools
from middleware import summarization_middleware

ORCHESTRATOR_INSTRUCTIONS = """You are the Wedding Planning orchestrator. The user is
planning a wedding; delegate specialized work to the right sub-agent tool instead of
answering it yourself:
- travel_agent: flights to/from the wedding destination.
- venue_agent: finding and comparing wedding venues.
- chef_agent: food menu, recipes, food-image analysis, and cost estimates.
- dj_agent: music/playlist suggestions for a requested genre.

After a sub-agent answers, call note_decision with the matching category
(venue/flights/menu/playlist) summarizing what was decided, so it's remembered for the
rest of the conversation. If the user directly mentions a dietary restriction, allergy,
or preferred cuisine, call note_dietary_restriction / note_preferred_cuisine yourself.

Keep your replies to the user crisp: a short list of the concrete options/details a
sub-agent returned (names, prices, dates), not a restated essay. Don't repeat the same
information across multiple sentences or add filler like restating the question back."""


async def main():
    planning_context = DEFAULT_PLANNING_CONTEXT

    async with PersistentTools() as tool_session:
        agent_tools = build_agent_tools(model, tool_session.tools, planning_context)

        orchestrator = create_agent(
            model=model,
            tools=agent_tools,
            system_prompt=ORCHESTRATOR_INSTRUCTIONS,
            state_schema=default_state_schema,
            checkpointer=InMemorySaver(),
            middleware=[summarization_middleware],
        )

        config = {"configurable": {"thread_id": "1"}}

        print("Wedding planner chat started. Type 'exit' or 'quit' to end.")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue

            thinking = False
            answering = False
            async for token, metadata in orchestrator.astream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages",
            ):
                reasoning = token.additional_kwargs.get("reasoning_content")
                if reasoning:
                    if not thinking:
                        print("Thinking: ", end="", flush=True)
                        thinking = True
                    print(reasoning, end="", flush=True)
                if token.content:
                    if not answering:
                        print("\nAssistant: ", end="", flush=True)
                        answering = True
                    print(token.content, end="", flush=True)
            print()

            state = orchestrator.get_state(config)
            v = state.values
            print(f"[state] dietary_restrictions={v.get('dietary_restrictions', [])} "
                  f"preferred_cuisines={v.get('preferred_cuisines', [])} "
                  f"chosen_venue={v.get('chosen_venue', '')!r} chosen_flights={v.get('chosen_flights', '')!r} "
                  f"chosen_menu={v.get('chosen_menu', '')!r} chosen_playlist_genre={v.get('chosen_playlist_genre', '')!r}")


if __name__ == "__main__":
    asyncio.run(main())
