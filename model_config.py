from langchain.chat_models import init_chat_model

qwen_3_8b = "qwen3:8b"
hermes_3_8b = "hermes3:8b"
qwen_2_5_vl_7b = "qwen2.5vl:7b"

# Primary Model used by the agent#
model = init_chat_model(model=qwen_3_8b, model_provider="ollama", reasoning=True)

def get_vision_model():
    """Load qwen2.5vl:7b on demand; keep_alive=0 unloads it from Ollama right after use."""
    return init_chat_model(model=qwen_2_5_vl_7b, model_provider="ollama", keep_alive=0, num_predict=512, num_ctx=8192)
