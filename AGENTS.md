# AGENTS

## Mission

Build Mini-Me as a personal feedback loop engine for Simon: observe, reflect, learn, improve.

## Product Philosophy

Mini-Me is not a chatbot, note-taking app, or generic productivity dashboard. It should help Simon answer: what is the highest-value thing I should do right now?

Every feature must satisfy at least one rule:

- Help Mini-Me know Simon better.
- Help Simon execute faster.

## V1 Constraints

- Python CLI only.
- Local markdown files only.
- No database.
- No GUI.
- No browser automation.
- No voice.
- No Telegram or WhatsApp.
- No Notion, Gmail, or calendar integrations.
- No autonomous actions.
- No multi-agent swarm.

## Architecture Rules

- Keep state in `data/*.md`.
- Keep domain logic in `core/`.
- Keep the CLI thin in `main.py`.
- Keep provider logic behind `core/llm_provider.py`.
- Future agents may plug into `agents/supervisor.py`, but V1 should not pretend to be a swarm.

## Coding Style

- Prefer boring, readable Python.
- Use small functions and clear names.
- Add comments only when they clarify non-obvious choices.
- Do not expose API keys.
- When unsure, choose the simpler implementation.

## Testing Expectations

- Use pytest.
- Test file reads and writes.
- Test task adding and completion.
- Preserve markdown checkbox format.
- Avoid tests that require network access or real API keys.
