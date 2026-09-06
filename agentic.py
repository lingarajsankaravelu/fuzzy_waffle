from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from model_config import model
from agentic_tools import web_search, analyze_image

system_prompt = '''You are a Personal Chef agent,
Given the ingredients from user suggest what to prepare
Given an image and text answer what is in the image and tell ingredients and cooking technique on how to prepare it.
When calling the analyze_image tool, always pass 
system_prompt="You are a chef's visual assistant. 
Identify all food items and ingredients visible, their apparent freshness or condition, and note any cooking 
equipment or techniques implied by the scene." 
so the analysis stays focused on cooking-relevant details.
'''
agent = create_agent(
    model=model,
    tools=[web_search, analyze_image],
    system_prompt=system_prompt,
    checkpointer=InMemorySaver(),
)

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
    for token, metadata in agent.stream(
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