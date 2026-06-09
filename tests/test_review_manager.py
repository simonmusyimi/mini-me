from datetime import datetime
from pathlib import Path

from core.file_store import FileStore
from core.review_manager import save_daily_review


REVIEW_TIME = datetime(2026, 6, 9, 21, 30)


def make_store(tmp_path: Path) -> FileStore:
    store = FileStore(tmp_path / "data")
    store.write_file("reviews.md", "# Reviews\n")
    store.write_file(
        "memory.md",
        "# Memory\n\n"
        "## About Simon\n\n"
        "Simon is building Mini-Me.\n\n"
        "## Completed Tasks\n\n"
        "## Lessons\n\n"
        "## Recurring Blockers\n\n"
        "## Tomorrow Rules\n",
    )
    return store


def test_review_saved_to_reviews_file(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    save_daily_review(
        store,
        completed="Built V1.5 review loop",
        blocked="Got distracted by model choices",
        learned="Clean memory sections make planning sharper",
        change="Start with the highest-impact task",
        timestamp=REVIEW_TIME,
    )

    reviews = store.read_file("reviews.md")
    assert "## Review - 2026-06-09 21:30" in reviews
    assert "### Completed\nBuilt V1.5 review loop" in reviews
    assert "### Blocked\nGot distracted by model choices" in reviews
    assert "### Learned\nClean memory sections make planning sharper" in reviews
    assert "### Change Tomorrow\nStart with the highest-impact task" in reviews


def test_lesson_appended_to_memory(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    save_daily_review(store, "Shipped", "Noise", "Small loops win", "Plan first", REVIEW_TIME)

    assert "## Lessons\n- 2026-06-09: Small loops win" in store.read_file("memory.md")


def test_blocker_appended_to_memory(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    save_daily_review(store, "Shipped", "Doom scrolling", "Small loops win", "Plan first", REVIEW_TIME)

    assert "## Recurring Blockers\n- 2026-06-09: Doom scrolling" in store.read_file("memory.md")


def test_completed_item_appended_to_memory(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    save_daily_review(store, "Finished KCA assignment", "Noise", "Small loops win", "Plan first", REVIEW_TIME)

    assert "## Completed Tasks\n- 2026-06-09: Finished KCA assignment" in store.read_file("memory.md")


def test_memory_markdown_format_is_preserved(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "data")
    store.write_file("reviews.md", "# Reviews\n")
    store.write_file(
        "memory.md",
        "# Memory\n\n"
        "## Completed Tasks\n"
        "- 2026-06-08: Built the CLI\n\n"
        "## Lessons\n"
        "- 2026-06-08: Shipping beats polishing\n\n"
        "## Recurring Blockers\n"
        "- 2026-06-08: Tool research\n\n"
        "## Tomorrow Rules\n"
        "- 2026-06-08: Start with the assignment\n",
    )

    save_daily_review(
        store,
        completed="Added memory sections",
        blocked="Context switching",
        learned="Dated bullets are easy to scan",
        change="Work before browsing",
        timestamp=REVIEW_TIME,
    )

    memory = store.read_file("memory.md")
    assert memory == (
        "# Memory\n\n"
        "## Completed Tasks\n"
        "- 2026-06-08: Built the CLI\n"
        "- 2026-06-09: Added memory sections\n\n"
        "## Lessons\n"
        "- 2026-06-08: Shipping beats polishing\n"
        "- 2026-06-09: Dated bullets are easy to scan\n\n"
        "## Recurring Blockers\n"
        "- 2026-06-08: Tool research\n"
        "- 2026-06-09: Context switching\n\n"
        "## Tomorrow Rules\n"
        "- 2026-06-08: Start with the assignment\n"
        "- 2026-06-09: Work before browsing\n"
    )
