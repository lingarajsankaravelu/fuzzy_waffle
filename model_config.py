from langchain.chat_models import init_chat_model

model = init_chat_model(model="qwen2.5:7b", model_provider="ollama")
