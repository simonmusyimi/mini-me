from pathlib import Path

from core.file_store import FileStore
from core.llm_provider import MissingLLMProvider, get_llm_provider
from core.local_planner import build_local_plan, rank_tasks
from core.planner import Planner
from core.task_manager import Task


GOALS = """# Goals

## 90-Day Vision
- Create a path to first tech income

## Current Focus
Mini-Me V2 first.
"""


def make_task(line_index: int, description: str, category: str = "GENERAL") -> Task:
    return Task(
        line_index=line_index,
        description=description,
        category=category,
        completed=False,
        raw_line=f"[ ] {description} — {category}",
    )


def test_focus_match_outranks_other_tasks() -> None:
    tasks = [
        make_task(0, "Study Python for 1 hour", "LEARNING"),
        make_task(1, "Write one X post about Mini-Me", "CONTENT"),
    ]

    ranked = rank_tasks(tasks, GOALS)

    assert ranked[0].task.description == "Write one X post about Mini-Me"
    assert ranked[0].reason == "matches your current focus"


def test_research_flavored_task_sinks_even_when_it_matches_focus() -> None:
    tasks = [
        make_task(0, "Research Mini-Me competitors", "PROJECT"),
        make_task(1, "Train today", "FITNESS"),
    ]

    ranked = rank_tasks(tasks, GOALS)

    assert ranked[0].task.description == "Train today"
    assert ranked[1].task.description == "Research Mini-Me competitors"
    assert "deprioritized" in ranked[1].reason


def test_ties_keep_file_order_and_output_is_deterministic() -> None:
    tasks = [
        make_task(0, "Train today", "FITNESS"),
        make_task(1, "Call my parents", "FAMILY"),
    ]

    first = build_local_plan(tasks, GOALS)
    second = build_local_plan(tasks, GOALS)

    assert first == second
    assert first.index("Train today") < first.index("Call my parents")


def test_plan_caps_at_three_and_names_ignored_count() -> None:
    tasks = [make_task(index, f"Task number {index}") for index in range(5)]

    plan = build_local_plan(tasks, GOALS)

    assert "3. Task number 2" in plan
    assert "4." not in plan
    assert "(2 other open tasks ignored on purpose. They can wait.)" in plan
    assert "Start with #1. Do not touch #2 until #1 is done." in plan


def test_plan_with_fewer_than_three_tasks_does_not_pad_or_ignore() -> None:
    tasks = [make_task(0, "Train today", "FITNESS")]

    plan = build_local_plan(tasks, GOALS)

    assert "1. Train today" in plan
    assert "2." not in plan
    assert "ignored" not in plan


def test_plan_with_no_open_tasks_gives_next_step() -> None:
    plan = build_local_plan([], GOALS)

    assert "No open tasks." in plan
    assert "/add-task" in plan


def test_empty_goals_still_produces_a_ranked_plan() -> None:
    tasks = [
        make_task(0, "Train today", "FITNESS"),
        make_task(1, "Write one X post about Mini-Me", "CONTENT"),
    ]

    plan = build_local_plan(tasks, "")

    assert plan.index("Train today") < plan.index("Write one X post")


def test_placeholder_api_key_counts_as_missing(monkeypatch) -> None:
    monkeypatch.setenv("MINIME_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "your_api_key_here")

    provider = get_llm_provider()

    assert provider.is_available is False


def test_planner_falls_back_to_local_plan_without_api_key(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "data")
    store.write_file("goals.md", GOALS)
    store.write_file(
        "tasks.md",
        "# Tasks\n\n"
        "[x] Build Mini-Me V1 — PROJECT\n"
        "[ ] Write one X post about Mini-Me — CONTENT\n"
        "[ ] Train today — FITNESS\n",
    )
    store.write_file(
        "memory.md",
        "# Memory\n\n"
        "## Patterns\n\n"
        "<!-- MINI-ME:PATTERNS:START -->\n"
        "### Attention Fragmentation\n\n"
        "Frequency: 5\n"
        "Evidence:\n"
        "- context switching\n\n"
        "Suggested Response:\n"
        "Start with one execution task.\n"
        "<!-- MINI-ME:PATTERNS:END -->\n",
    )
    planner = Planner(store, MissingLLMProvider("openai", "OPENAI_API_KEY is missing."))

    plan = planner.generate_plan()

    assert plan.startswith("=== Pattern Warnings ===")
    assert "* Attention Fragmentation is recurring: Start with one execution task." in plan
    assert "(Local plan" in plan
    assert "1. Write one X post about Mini-Me — CONTENT" in plan
    assert "Build Mini-Me V1" not in plan
    assert "Mini-Me cannot generate an LLM plan yet" not in plan
