from __future__ import annotations

from datetime import date

from core.file_store import FileStore
from core.llm_provider import LLMProvider


class Planner:
    def __init__(self, store: FileStore, llm_provider: LLMProvider) -> None:
        self.store = store
        self.llm_provider = llm_provider

    def generate_plan(self) -> str:
        prompt = self.build_prompt()
        return self.llm_provider.generate(prompt)

    def build_prompt(self) -> str:
        goals = self.store.read_file("goals.md", "# Goals\n")
        tasks = self.store.read_file("tasks.md", "# Tasks\n")
        memory = self.store.read_file("memory.md", "# Memory\n")

        return f"""Today is {date.today().isoformat()}.

You are planning for Simon.

Given this person's goals, open tasks, patterns, risks, and current context, what are the 3 highest-value actions they should take today?

Rank by impact.

For each action, include:
- action
- category
- reason
- estimated effort
- what to avoid

Be direct, practical, and specific.

Avoid generic motivation.

The goal is to help this user execute, not feel inspired.

Use unchecked tasks as the active task pool. Completed tasks can inform context but should not be planned again unless clearly necessary.

GOALS:
{goals}

TASKS:
{tasks}

MEMORY:
{memory}
"""
