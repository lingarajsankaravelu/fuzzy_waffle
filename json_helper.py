import json
from langchain_core.messages import BaseMessage

class LangChainEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle LangChain message objects
        if isinstance(obj, BaseMessage):
            return {
                'type': obj.__class__.__name__,
                'content': obj.content,
                'additional_kwargs': obj.additional_kwargs,
                'response_metadata': obj.response_metadata,
                'id': obj.id
            }
        return super().default(obj)

def format_output(data):
    return json.dumps(data, cls=LangChainEncoder, indent=4)
