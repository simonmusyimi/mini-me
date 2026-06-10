from __future__ import annotations

from datetime import date

from core.file_store import FileStore
from core.llm_provider import LLMProvider
from core.local_planner import build_local_plan
from core.pattern_detector import format_pattern_warnings
from core.task_manager import TaskManager


class Planner:
    def __init__(self, store: FileStore, llm_provider: LLMProvider) -> None:
        self.store = store
        self.llm_provider = llm_provider

    def generate_plan(self) -> str:
        memory = self.store.read_file("memory.md", "# Memory\n")
        warnings = format_pattern_warnings(memory)
        if self.llm_provider.is_available:
            plan = self.llm_provider.generate(self.build_prompt())
        else:
            goals = self.store.read_file("goals.md", "# Goals\n")
            open_tasks = TaskManager(self.store).list_open_tasks()
            plan = build_local_plan(open_tasks, goals)
        if warnings:
            return f"{warnings}\n\n{plan}"
        return plan

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

Pay special attention to memory sections named Completed Tasks, Lessons, Recurring Blockers, and Tomorrow Rules.

Treat the ## Patterns section as behavioral risk context. If a grouped pattern is recurring, account for it in what to avoid and in the first action.

GOALS:
{goals}

TASKS:
{tasks}

MEMORY:
{memory}
"""
