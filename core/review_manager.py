from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from core.file_store import FileStore


@dataclass(frozen=True)
class DailyReview:
    completed: str
    blocked: str
    learned: str
    change: str
    timestamp: datetime

    @property
    def date_key(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d")

    @property
    def timestamp_key(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M")


def save_daily_review(
    store: FileStore,
    completed: str,
    blocked: str,
    learned: str,
    change: str,
    timestamp: datetime | None = None,
) -> DailyReview:
    review = DailyReview(
        completed=_clean_answer(completed),
        blocked=_clean_answer(blocked),
        learned=_clean_answer(learned),
        change=_clean_answer(change),
        timestamp=timestamp or datetime.now(),
    )

    store.append_file("reviews.md", _format_full_review(review))
    _update_memory_sections(store, review)
    return review


def _clean_answer(answer: str) -> str:
    return answer.strip() or "Nothing recorded."


def _format_full_review(review: DailyReview) -> str:
    return f"""
## Review - {review.timestamp_key}

### Completed
{review.completed}

### Blocked
{review.blocked}

### Learned
{review.learned}

### Change Tomorrow
{review.change}
"""


def _update_memory_sections(store: FileStore, review: DailyReview) -> None:
    memory = store.read_file("memory.md", "# Memory\n")
    if not memory.strip():
        memory = "# Memory\n"

    updates = {
        "Completed Tasks": review.completed,
        "Lessons": review.learned,
        "Recurring Blockers": review.blocked,
        "Tomorrow Rules": review.change,
    }

    for section, value in updates.items():
        memory = _append_dated_bullet(memory, section, review.date_key, value)

    store.write_file("memory.md", memory.rstrip() + "\n")


def _append_dated_bullet(content: str, section: str, date_key: str, value: str) -> str:
    bullet = f"- {date_key}: {value}"
    heading = f"## {section}"
    pattern = re.compile(
        rf"(^## {re.escape(section)}[ \t]*\n)(.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)

    if not match:
        return content.rstrip() + f"\n\n{heading}\n{bullet}\n"

    heading_line = match.group(1)
    section_body = match.group(2).strip()
    if section_body:
        replacement = f"{heading_line}{section_body}\n{bullet}\n\n"
    else:
        replacement = f"{heading_line}{bullet}\n\n"

    return content[: match.start()] + replacement + content[match.end() :]
