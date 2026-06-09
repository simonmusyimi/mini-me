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

If the API key is missing, the app prints setup instructions and keeps all non-LLM commands available.

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
