from langchain.agents.middleware import SummarizationMiddleware

from model_config import model

# Only the orchestrator has a checkpointer + persistent thread_id, so it's the only
# graph whose `messages` actually grows across turns — sub-agents are stateless,
# single-shot calls with nothing to summarize.
summarization_middleware = SummarizationMiddleware(
    model=model,
    trigger=("messages", 30),
    keep=("messages", 20),
)
