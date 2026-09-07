import asyncio

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from model_config import model
from mcp_client import load_tools
from state import default_state_schema, note_dietary_restriction, note_preferred_cuisine
from context import UserContext, personalized_prompt, DEFAULT_USER_CONTEXT


async def main():
    tools = await load_tools() + [note_dietary_restriction, note_preferred_cuisine]
    agent = create_agent(
        model=model,
        tools=tools,
        middleware=[personalized_prompt],
        state_schema=default_state_schema,
        context_schema=UserContext,
        checkpointer=InMemorySaver(),
    )

    user_context = DEFAULT_USER_CONTEXT
    config = {"configurable": {"thread_id": "1"}}

    print("Chat started. Type 'exit' or 'quit' to end.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        thinking = False
        answering = False
        async for token, metadata in agent.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            context=user_context,
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

        state = agent.get_state(config)
        print(f"[state] dietary_restrictions={state.values.get('dietary_restrictions', [])} "
              f"preferred_cuisines={state.values.get('preferred_cuisines', [])}")


if __name__ == "__main__":
    asyncio.run(main())
