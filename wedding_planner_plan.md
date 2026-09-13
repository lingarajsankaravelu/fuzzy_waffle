# Wedding Planner — Multi-Agent Plan

Plan only — nothing below is implemented yet. Review and confirm before I start writing code.

## 1. Architecture

Orchestrator agent + 4 sub-agents, using the **"agent-as-tool"** pattern (no new
dependency like `langgraph-supervisor` needed):

- Each sub-agent (travel, venue, chef, dj) is its own `create_agent(...)`, built with a
  narrow toolset and persona.
- Each sub-agent is wrapped in a small `@tool` function that the orchestrator calls like
  any other tool: the wrapper invokes the sub-agent with the relevant slice of the
  user's request and returns its final text answer.
- The orchestrator is itself a `create_agent(...)` whose `tools=[...]` are those 4
  wrapper functions, plus a system prompt describing when to delegate to which one.

This keeps every agent's build logic in its own file (single responsibility) and avoids
teaching two different multi-agent frameworks in one project.

## 2. Models — no new models needed

Available locally via ollama: `qwen2.5vl:7b`, `hermes3:8b`, `qwen3:8b`, `dolphin3:latest`.

Recommendation: **reuse what's already wired up**, don't add more.

- `qwen3:8b` (already `model` in `model_config.py`, tool-calling + reasoning, ~5.2GB) —
  used as the LLM for the orchestrator **and** all 4 sub-agents. They differ by prompt
  and toolset, not by model.
- `qwen2.5vl:7b` (already `get_vision_model()`, `keep_alive=0`, ~6GB) — stays scoped to
  the chef agent's `analyze_image` tool, loaded on demand and evicted after use, exactly
  as today.
- `hermes3:8b` / `dolphin3:latest` — not needed. On a memory-constrained MacBook Air,
  keeping a single ~5GB text model resident (instead of swapping between several
  8b-class models across sub-agents) is the safer choice. No reason to add them unless
  you specifically want to compare model behavior per sub-agent later.

On "do we need a research model": no. A "research agent" in this context just means an
agent with web-search tool access, not a special model. `web_search` (already an MCP
tool, backed by your local Searx instance) is reused by the travel and venue agents. A
real deep-research model would be a multi-GB step up with little payoff for this
project's scope, so I'd skip it.

## 3. File layout (single responsibility)

```
start_dust_agent/
  model_config.py            # unchanged
  state.py                    # extended: shared wedding-planning state fields
  context.py                  # extended: WeddingContext alongside existing UserContext

  tools/                       # everything tool-related lives here
    registry.py                 # defines the single shared `mcp = FastMCP(...)` instance
    web_tools.py                 # web_search  (moved out of mcp_server.py)
    vision_tools.py              # analyze_image (moved out of mcp_server.py)
    mcp_server.py                 # thin: imports each tools/* module (registers on `mcp`), mcp.run()
                                   # launched via `python -m tools.mcp_server` (cwd = repo root)
                                   # so its `from tools.registry import mcp` imports resolve
    mcp_client.py                 # MultiServerMCPClient config: chef_tools / time / flights
    orchestrator_tools.py         # builds the 4 sub-agents + wraps each as a tool for the orchestrator

  agents/
    chef_agent.py                # build_chef_agent() — refactored out of agentic.py
    travel_agent.py              # build_travel_agent()
    venue_agent.py               # build_venue_agent()
    dj_agent.py                  # build_dj_agent()

  orchestrator.py              # wiring only: loads tools, builds context, calls
                                # build_agent_tools(), creates the orchestrator agent,
                                # runs the chat loop (replaces agentic.py as the entrypoint)
```

`agentic.py` becomes `agents/chef_agent.py` (logic moved, not duplicated) plus the
generic chat-loop code moves into `orchestrator.py` so there's one runnable entrypoint.

Splitting `mcp_server.py`'s tools into `tools/*.py` is a mechanical extraction — the
`@mcp.tool(...)` decorator calls stay identical, they just live next to the domain
they belong to instead of one another once there are 5 tools instead of 2.

Everything tool-related (MCP server, MCP client config, and the orchestrator's
tool-wrapping factories) now lives under `tools/` in one place, rather than split
between the repo root and `tools/`.

## 4. State schema changes (`state.py`)

Add wedding-level fields alongside the existing `dietary_restrictions` /
`preferred_cuisines`, written by tools as sub-agents make progress:

```python
@dataclass
class default_state_schema(AgentState):
    dietary_restrictions: Annotated[list[str], operator.add] = field(default_factory=list)
    preferred_cuisines: Annotated[list[str], operator.add] = field(default_factory=list)
    chosen_venue: str = ""
    chosen_flights: str = ""
    chosen_menu: str = ""
    chosen_playlist_genre: str = ""
```

Single scalar fields (last-write-wins, no reducer needed) since each represents "the
current decision," not an accumulating list. Written via the same `Command(update={...})`
pattern already used by `note_dietary_restriction`.

This state is shared at the **orchestrator** level, so it remembers what's already been
decided across turns even though the actual work happens inside sub-agent tool calls.

## 5. Context schema changes (`context.py`)

Keep `UserContext` as-is (name/age/activities). Add a second, separate dataclass for
wedding-level fixed facts — supplied once per session, same idea as
`DEFAULT_USER_CONTEXT`:

```python
@dataclass
class WeddingContext:
    destination: str
    wedding_date: str
    guest_count: int
    budget: str = "not specified"
```

Both get passed via `context_schema`/`context=` the same way `UserContext` does today
(LangGraph's `context` accepts one object — likely wraps both in one combined dataclass,
e.g. `PlanningContext(user: UserContext, wedding: WeddingContext)`, rather than two
separate `context_schema`s).

## 6. New tools needed

- **Flights — decided: [`google-flights-mcp`](https://github.com/HaroldLeo/google-flights-mcp),
  no new tool code.** This is a standalone stdio MCP server (real-time Google Flights
  data via `fast-flights`, no API key required) — it plugs into `mcp_client.py` as a
  third server entry, exactly like the existing `time` server:
  ```python
  "flights": {
      "command": "uvx",
      "args": [
          "--from", "git+https://github.com/HaroldLeo/google-flights-mcp.git",
          "--with", "mcp<2",
          "mcp-server-google-flights",
      ],
      "transport": "stdio",
  },
  ```
  Note: `mcp-server-google-flights` isn't published on PyPI (confirmed 404), so plain
  `uvx mcp-server-google-flights` fails — installing straight from the GitHub repo via
  `--from git+...` is required. Its `mcp>=1.2.0` dependency also resolves to `mcp` 2.x by
  default, which renamed `FastMCP`, so `--with "mcp<2"` is needed too. Verified working
  live end-to-end.

  Exposes `search_one_way_flights`, `search_round_trip_flights`,
  `search_round_trips_in_date_range`, `search_flights_by_airline`, `get_travel_dates`,
  `generate_google_flights_url` — the travel agent gets these via `load_tools()` like
  every other MCP tool, filtered to just this agent. No `tools/travel_tools.py` needed.
  Also filters in `get_current_time`/`convert_time` from the existing `time` server, for
  resolving relative dates. (Optional: set `SERPAPI_API_KEY` env var later for richer
  data — not required to work.)

  Considered and ruled out: [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite)
  (a local macOS browser-automation app for agents — real browser, no API key, which is
  why it came up: `web_search` only returns static indexed text and can't fill in a
  flights site's form to read live JS-rendered prices). Its interface is an agent
  driving JS snippets in a chat/skill context, not an importable Python function with a
  stable signature — doesn't fit as a plain MCP tool call the way `google-flights-mcp`
  does.
- **`search_venues`** — decided: no new tool. The venue agent just uses the existing
  `web_search` tool with a venue-focused persona (`agents/venue_agent.py`).
- **`suggest_playlist`** — decided: no Spotify/API integration, no new tool. The DJ
  agent (`agents/dj_agent.py`) uses `web_search` plus its own persona/reasoning for
  LLM-generated song/artist suggestions. No real playlist-creation.
- **Chef agent price quoting** — decided: LLM-estimated cost based on menu + guest
  count, folded into `agents/chef_agent.py`'s persona, clearly framed as an estimate.
  No real pricing database/API.

## 7. Decisions (previously open questions)

1. Flights: `google-flights-mcp`, see §6.
2. Playlist: LLM suggestions only (no Spotify integration).
3. Sub-agents are stateless per-call — no checkpointer, no memory of their own past
   turns. Only the orchestrator's `default_state_schema` persists across turns; a
   sub-agent's own `Command(update=...)` would only mutate its own throwaway graph
   state, not bubble up, so state-writing tools (`note_dietary_restriction`,
   `note_preferred_cuisine`, `note_decision`) live only on the orchestrator, not on
   any sub-agent.
4. `agentic.py` retired — its chat-loop logic now lives in `orchestrator.py`.

## 8. Build order (completed)

1. `tools/registry.py` + split `mcp_server.py` into `tools/web_tools.py` +
   `tools/vision_tools.py` — verified via import checks.
2. Extended `state.py` and `context.py` per §4/§5.
3. Added the `flights` server entry to `tools/mcp_client.py` (§6) — live-verified
   against the real subprocess, corrected the install command after the first attempt
   failed (see §6 note).
4. Built the 4 `agents/*.py` sub-agents.
5. Built `orchestrator.py` + `tools/orchestrator_tools.py` (sub-agent tool-wrapping
   factories split out separately per single-responsibility), retired `agentic.py`.
   Moved `mcp_server.py`, `mcp_client.py`, `orchestrator_tools.py` into `tools/` so all
   tool-related code lives in one place (launches `mcp_server.py` via
   `python -m tools.mcp_server` with `cwd` set to the repo root, so its
   `tools.registry` import still resolves from its new location) — live-verified.
6. Still pending: one full end-to-end wedding-planning conversation touching all 4
   sub-agents.
