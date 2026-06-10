from __future__ import annotations

from dataclasses import dataclass
import re

from core.task_manager import Task


LOCAL_MODE_NOTE = "(Local plan — no API key. Set OPENAI_API_KEY for an LLM plan.)"
MAX_ACTIONS = 3

FOCUS_TIER = 0
NORMAL_TIER = 1
RESEARCH_TIER = 2

# Research-flavored tasks always sink to the bottom tier. This is the product
# thesis ("shipping beats researching"), not a tunable preference, so it is
# not gated on pattern state.
RESEARCH_WORDS = (
    "research",
    "explore",
    "compare",
    "look into",
    "watch",
    "read",
    "try out",
)

TIER_REASONS = {
    FOCUS_TIER: "matches your current focus",
    NORMAL_TIER: "next open task in line",
    RESEARCH_TIER: "research-flavored — deprioritized until something ships",
}


@dataclass(frozen=True)
class RankedTask:
    task: Task
    tier: int

    @property
    def reason(self) -> str:
        return TIER_REASONS[self.tier]


def extract_current_focus(goals_markdown: str) -> str:
    match = re.search(
        r"^## Current Focus[ \t]*\n(?P<body>.*?)(?=^## |\Z)",
        goals_markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    return match.group("body").strip()


def rank_tasks(open_tasks: list[Task], goals_markdown: str) -> list[RankedTask]:
    keywords = _focus_keywords(extract_current_focus(goals_markdown))
    ranked = [RankedTask(task=task, tier=_tier_for(task, keywords)) for task in open_tasks]
    return sorted(ranked, key=lambda item: item.tier)


def build_local_plan(open_tasks: list[Task], goals_markdown: str) -> str:
    if not open_tasks:
        return (
            f"{LOCAL_MODE_NOTE}\n\n"
            "No open tasks. Add one with /add-task, or run /review to close the day."
        )

    ranked = rank_tasks(open_tasks, goals_markdown)
    top = ranked[:MAX_ACTIONS]

    lines = [LOCAL_MODE_NOTE, "", "Today's highest-value actions:", ""]
    for number, item in enumerate(top, start=1):
        lines.append(f"{number}. {item.task.display_text()}")
        lines.append(f"   Why: {item.reason}")

    lines.append("")
    lines.append("Start with #1. Do not touch #2 until #1 is done.")

    ignored = len(ranked) - len(top)
    if ignored == 1:
        lines.append("(1 other open task ignored on purpose. It can wait.)")
    elif ignored > 1:
        lines.append(f"({ignored} other open tasks ignored on purpose. They can wait.)")

    return "\n".join(lines)


def _tier_for(task: Task, focus_keywords: set[str]) -> int:
    if _is_research_flavored(task.description):
        return RESEARCH_TIER
    if focus_keywords & set(_words(task.description)):
        return FOCUS_TIER
    return NORMAL_TIER


def _is_research_flavored(description: str) -> bool:
    normalized = " ".join(_words(description))
    return any(
        re.search(rf"(^|\s){re.escape(word)}($|\s)", normalized)
        for word in RESEARCH_WORDS
    )


def _focus_keywords(focus_text: str) -> set[str]:
    return {word for word in _words(focus_text) if len(word) >= 4}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9-]+", text.lower())
