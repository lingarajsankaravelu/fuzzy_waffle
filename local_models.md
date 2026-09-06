# Local Model Options

| Model                     | Primary Use                                                                                                                                                                                                      | Pull Command                  |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **qwen2.5:7b**      | General-purpose assistant, solid balanced tool-calling, good default                                                                                                                                             | `ollama pull qwen2.5:7b`    |
| **qwen3:8b**        | Same general-purpose role but newer/more agent-focused; has a switchable "thinking mode" for harder multi-step reasoning tasks (planning, math, debugging) vs. fast mode for simple chat/tool calls              | `ollama pull qwen3:8b`      |
| **granite3.3:8b**   | Built specifically for enterprise agentic workflows — RAG (retrieval-augmented generation), structured tool/function calling, document Q&A. Best pick for practicing RAG pipelines or multi-tool agents         | `ollama pull granite3.3:8b` |
| **hermes3:8b**      | Specialized for*reliable structured output* — very consistent JSON/function-call formatting, good for testing strict tool-calling schemas. Weaker general knowledge recency (Llama 3.1 base, Dec 2023 cutoff) | `ollama pull hermes3:8b`    |
| **dolphin3:latest** | Uncensored, highly steerable via system prompt — best for experimenting with personas, creative/unrestricted output, or testing how much a model deviates when given unusual instructions                       | *(already pulled)*          |

## Rule of thumb

- Everyday agent + tool calling → qwen2.5:7b or qwen3:8b
- Multi-tool / RAG / document-heavy agent → granite3.3:8b
- Debugging why agent tool-call JSON keeps breaking → hermes3:8b (isolates the formatting question)
- Testing system-prompt steerability / persona work → dolphin3
