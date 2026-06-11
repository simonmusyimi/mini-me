from __future__ import annotations

import re

from core.file_store import FileStore
from core.llm_provider import LLMProvider
from core.local_planner import extract_current_focus


LOCAL_MODE_NOTE = "(Local draft — no API key. Set OPENAI_API_KEY for a sharper LLM draft.)"

EMPTY_COMPLETION_VALUES = {"nothing recorded.", "nothing recorded", "nothing", "none", "n/a", "na"}


class PostDrafter:
    def __init__(self, store: FileStore, llm_provider: LLMProvider) -> None:
        self.store = store
        self.llm_provider = llm_provider

    def draft_post(self) -> str:
        memory = self.store.read_file("memory.md", "# Memory\n")
        completions = extract_latest_completions(memory)
        if not completions:
            return (
                "Nothing completed yet to post about.\n"
                "Finish one real task with /done or record a /review, then run /post again."
            )

        goals = self.store.read_file("goals.md", "# Goals\n")
        focus = extract_current_focus(goals)
        if self.llm_provider.is_available:
            return self.llm_provider.generate(build_post_prompt(completions, focus))
        return f"{LOCAL_MODE_NOTE}\n\n{build_local_draft(completions, focus)}"


def extract_latest_completions(memory_markdown: str) -> list[str]:
    section = re.search(
        r"^## Completed Tasks[ \t]*\n(?P<body>.*?)(?=^## |\Z)",
        memory_markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section:
        return []

    dated = re.findall(
        r"^- (?P<date>\d{4}-\d{2}-\d{2}): (?P<text>.+)$",
        section.group("body"),
        flags=re.MULTILINE,
    )
    if not dated:
        return []

    latest = max(date for date, _text in dated)
    completions: list[str] = []
    seen: set[str] = set()
    for date, text in dated:
        cleaned = text.strip()
        key = cleaned.lower()
        if date != latest or not cleaned or key in seen or key in EMPTY_COMPLETION_VALUES:
            continue
        seen.add(key)
        completions.append(cleaned)
    return completions


def build_local_draft(completions: list[str], focus: str) -> str:
    lines = ["Building Mini-Me in public.", "", "Latest progress:"]
    lines.extend(f"- {item}" for item in completions)
    if focus:
        lines.extend(["", f"Next: {focus}"])
    lines.extend(["", "#buildinpublic"])
    return "\n".join(lines)


def build_post_prompt(completions: list[str], focus: str) -> str:
    completed_lines = "\n".join(f"- {item}" for item in completions)
    focus_line = focus or "Not recorded."

    return f"""Draft one X (Twitter) post for Simon, who builds in public.

Latest completed work:
{completed_lines}

Current focus:
{focus_line}

Rules:
- Under 280 characters.
- Direct, concrete, first person.
- Mention real progress, not vague motivation.
- At most one hashtag.
- Return only the post text, nothing else.
"""
