# Architecture

## V1 Architecture

Mini-Me V1 is a Python CLI with a few small modules:

- `main.py` handles user commands.
- `core/file_store.py` reads and writes markdown files.
- `core/task_manager.py` manages checkbox tasks.
- `core/planner.py` builds the planning prompt.
- `core/llm_provider.py` hides provider-specific LLM calls.
- `agents/supervisor.py` is a small placeholder for future agent orchestration.

## Why Flat Files

Flat markdown files are enough for V1. They are easy to inspect, easy to edit manually, easy to commit, and hard to over-engineer. Simon can see the system's memory directly.

## How Planning Works

When `/plan` runs, Mini-Me reads:

- `data/goals.md`
- `data/tasks.md`
- `data/memory.md`

It builds a structured prompt asking for the three highest-value actions, ranked by impact. The planner asks the configured LLM provider for the answer and prints it in the terminal.

## Local Fallback Planner (V2.2)

If the API key is missing (or still the `.env.example` placeholder), `/plan` falls back to `core/local_planner.py`: a pure, deterministic ranker with no network access.

Ranking is three tiers, not a scoring formula:

1. Research-flavored tasks (`research`, `explore`, `compare`, `watch`, `read`, ...) always sink to the bottom tier. This encodes the product thesis — shipping beats researching — so it is always on, not gated on pattern state.
2. Tasks sharing a significant word (4+ characters) with `## Current Focus` in `goals.md` rise to the top tier.
3. Everything else stays in the middle. Ties keep file order, so older tasks surface first.

The output is capped at 3 actions, states how many open tasks were deliberately ignored, and instructs serial execution ("Start with #1"). Pattern warnings are prefixed in both local and LLM modes. The local plan labels itself so heuristics are never confused with LLM reasoning.

## Post Drafter (V2.3)

`/post` turns completed work into a build-in-public X post draft. `core/post_drafter.py` reads the most recent dated bullets under `## Completed Tasks` in memory (deduplicated, empty values skipped) plus `## Current Focus` from goals. With an API key it asks the LLM for a sub-280-character draft; without one it produces a plain local template. The user always copies, edits, and posts manually — Mini-Me drafts, it does not publish.

## How The Review Loop Works

When `/review` runs, Mini-Me asks four questions:

- What did you complete today?
- What blocked you?
- What did you learn?
- What should change tomorrow?

The full review is appended to `data/reviews.md`. V1.5 keeps memory easier to scan by updating stable dated sections in `data/memory.md`:

- `Completed Tasks`
- `Lessons`
- `Recurring Blockers`
- `Tomorrow Rules`

Each section receives bullets in this shape:

```md
- YYYY-MM-DD: Concrete review answer
```

## How Pattern Detection Works

When `/patterns` runs, Mini-Me reads `data/reviews.md` and parses recent daily reviews. V2.1 uses local semantic grouping from `core/pattern_taxonomy.py`, with no API required.

The first taxonomy groups are:

- `Attention Fragmentation`
- `Avoidance / Escape Behavior`
- `Overplanning Instead of Shipping`

The detector normalizes text by lowercasing, removing punctuation, and collapsing spaces. This lets rough inputs such as `tabs,lack`, `doomscroling`, and `doom scroling` still match useful groups.

The detector counts grouped evidence from `Blocked`, `Learned`, and `Change Tomorrow` answers. It writes generated results into `data/memory.md` under `## Patterns` without deleting Simon's existing notes or other memory sections. Each detected pattern includes:

- `Frequency`
- `Evidence`
- `Suggested Response`

The LLM is not required for V2.1 pattern detection or pattern warnings.

## Pattern-Aware Planning

When `/plan` runs, Mini-Me reads `data/memory.md`, extracts generated grouped patterns from `## Patterns`, and prints pattern warnings before the plan. This makes recurring risks visible even when no API key is configured.

The pattern warnings also remain inside the planning prompt so the LLM can account for recurring behavior in today's recommendations.

## LLM Provider Abstraction

`core/llm_provider.py` defines a small provider interface. V1 implements OpenAI through the chat completions API using environment variables:

- `MINIME_LLM_PROVIDER`
- `MINIME_LLM_MODEL`
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`

Future providers such as Anthropic, DeepSeek, or local models should be added as new provider classes and registered in `get_llm_provider`.

## Future Agents

Future specialist agents should plug in after the core loop is useful. Good candidates are:

- Memory engine.
- Pattern detection.
- Study agent.
- Builder agent.
- Content agent.
- Telegram interface.
- Multi-agent supervisor.

The rule stays the same: every addition must improve memory or execution.
