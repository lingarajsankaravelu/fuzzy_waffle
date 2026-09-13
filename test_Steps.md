# Wedding Planner Orchestration — Test Steps

Run with `uv run orchestrator.py`.

Prerequisites: Ollama serving `qwen3:8b` (and `qwen2.5vl:7b` if testing image analysis),
Searx up on `localhost:8080` with `format: json` enabled, and internet access on first
run so `uvx` can fetch `mcp-server-time` and `google-flights-mcp` (that one builds from
GitHub, so the first launch will be slower).

Tests against the hardcoded `DEFAULT_PLANNING_CONTEXT`: John Doe, Goa India,
2026-12-12, 120 guests, ₹15,00,000.

## Phase 1 — turn-by-turn (do this first)

Isolates each sub-agent/tool call so if something breaks, it's obvious which piece
failed.

**1. Venue** (→ `venue_agent`, then `note_decision(category="venue", ...)`)

> We're looking for a wedding venue in Goa for around 120 guests, something beachy, within our ₹15,00,000 budget. Can you find some options?  Limit the options to 3. 

**2. Flights** (→ `travel_agent`, using `google-flights-mcp` + `time` tools)

> Can you find flights from Mumbai (BOM) to Goa (GOI) for December 12, 2026?  Looking only for two tickets and one way journey

**3. Dietary restriction, said in passing** (→ orchestrator calls `note_dietary_restriction` directly, *not* via chef_agent)

> By the way, my partner is vegan — please keep that in mind.

**4. Preferred cuisine**

> We'd also love South Indian food at the wedding.and

**5. Chef agent, should already know #3/#4** (→ `chef_agent`, task text enriched via `InjectedState` with the noted restriction/cuisine, then `note_decision(category="menu", ...)`)

> Can you suggest a wedding menu and a rough cost estimate for 120 guests?

Watch that the menu actually accounts for "vegan" and "South Indian" without you
repeating them — that's the `InjectedState` enrichment working.

**6. DJ agent** (→ `dj_agent`, then `note_decision(category="playlist", ...)`)

> We want a Bollywood and Tollywood fusion playlist for the reception.

**7. Idempotency check** — repeat #3 verbatim:

> My partner is vegan.

Expect `"Already noted: vegan"`, not a duplicate entry — this is the InjectedState
dedup fix.

**8. Recap**

> Can you summarize everything we've decided so far?

After every turn the loop also prints a raw
`[state] dietary_restrictions=... chosen_venue=... chosen_flights=... chosen_menu=... chosen_playlist_genre=...`
line — that's the ground truth for whether state is actually persisting, independent of
what the model says in prose.

## Phase 2 — one combined message (do this second, once Phase 1 works)

This is the more honest test of the orchestrator itself — its job is to take one
compound request and decide what to delegate to which sub-agent, in what order, making
several tool calls across one turn (`create_agent`'s loop keeps calling tools until the
model is ready to answer in plain text).

> We're planning our wedding in Goa on Dec 12 2026 for 120 guests, budget ₹15,00,000. Can you find a beachy venue, flights from Mumbai (BOM) to Goa (GOI), suggest a menu (my partner's vegan, we like South Indian food) with a cost estimate, and put together a Bollywood/EDM playlist for the reception?

Worth knowing going in: `qwen3:8b` is an 8B local model, and correctly sequencing
~6-8 tool calls with the right arguments from one compound message is a much harder ask
than one call per turn — local models at this size are noticeably weaker at multi-step
tool planning than something like GPT-4/Claude. If the combined version misfires (skips
a sub-agent, gets order wrong, drops the dietary restriction), that's not necessarily a
bug in the code — check the `[state]` line to see what actually landed before assuming
the orchestration logic is broken.
