from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from json_helper import format_output
from pprint import pprint


from model_config import model
from agentic_tools import web_search

system_prompt ='You are a general purpose,  which answers people question'
agent = create_agent(model=model, tools=[web_search], system_prompt=system_prompt)
response = agent.invoke({"messages": [HumanMessage(content="who are you and what can you do!")]})
print(format_output(response))
#pprint(response)