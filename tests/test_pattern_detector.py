from pathlib import Path

from core.file_store import FileStore
from core.pattern_detector import detect_patterns, update_memory_patterns
from main import handle_patterns


SAMPLE_REVIEWS = """# Reviews

## Review - 2026-06-07 21:00

### Completed
Built review loop

### Blocked
Context switching

### Learned
Shipping beats polishing

### Change Tomorrow
Start with one execution task before research

## Review - 2026-06-08 21:00

### Completed
Added tests

### Blocked
Context switching

### Learned
Shipping beats polishing

### Change Tomorrow
Start with one execution task before research

## Review - 2026-06-09 21:00

### Completed
Updated docs

### Blocked
Too much tool research

### Learned
Small loops win

### Change Tomorrow
Sleep earlier
"""


def test_detects_repeated_blockers() -> None:
    patterns = detect_patterns(SAMPLE_REVIEWS)

    blocker = next(pattern for pattern in patterns if pattern.source == "blocker")

    assert blocker.pattern == "Context switching appears repeatedly"
    assert blocker.evidence == "Mentioned in 2 reviews as a blocker"
    assert blocker.suggested_response == "Start the day with one execution task before research"


def test_detects_repeated_lessons() -> None:
    patterns = detect_patterns(SAMPLE_REVIEWS)

    lesson = next(pattern for pattern in patterns if pattern.source == "lesson")

    assert lesson.pattern == "Lesson repeats: Shipping beats polishing"
    assert lesson.evidence == "Mentioned in 2 reviews as a lesson"


def test_detects_repeated_tomorrow_rules() -> None:
    patterns = detect_patterns(SAMPLE_REVIEWS)

    rule = next(pattern for pattern in patterns if pattern.source == "tomorrow rule")

    assert rule.pattern == "Tomorrow rule repeats: Start with one execution task before research"
    assert rule.evidence == "Mentioned in 2 reviews as a tomorrow rule"


def test_updates_memory_without_destroying_existing_sections() -> None:
    patterns = detect_patterns(SAMPLE_REVIEWS)
    memory = (
        "# Memory\n\n"
        "## About Simon\n\n"
        "Simon is building Mini-Me.\n\n"
        "## Patterns\n\n"
        "- Biggest risk: distraction\n"
        "- Needs simple next actions\n\n"
        "## Completed Tasks\n"
        "- 2026-06-09: Updated docs\n\n"
        "## Lessons\n"
        "- 2026-06-09: Small loops win\n"
    )

    updated = update_memory_patterns(memory, patterns)

    assert "- Biggest risk: distraction" in updated
    assert "- Needs simple next actions" in updated
    assert "## Completed Tasks\n- 2026-06-09: Updated docs" in updated
    assert "## Lessons\n- 2026-06-09: Small loops win" in updated
    assert "<!-- MINI-ME:PATTERNS:START -->" in updated
    assert "- Pattern: Context switching appears repeatedly" in updated
    assert "  Evidence: Mentioned in 2 reviews as a blocker" in updated
    assert "  Suggested response: Start the day with one execution task before research" in updated


def test_patterns_command_works(tmp_path: Path, capsys) -> None:
    store = FileStore(tmp_path / "data")
    store.write_file("reviews.md", SAMPLE_REVIEWS)
    store.write_file("memory.md", "# Memory\n\n## Patterns\n\n- Biggest risk: distraction\n")

    handle_patterns(store)

    output = capsys.readouterr().out
    memory = store.read_file("memory.md")

    assert "Detected 3 pattern(s):" in output
    assert "- Pattern: Context switching appears repeatedly" in output
    assert "Memory updated under ## Patterns." in output
    assert "- Pattern: Context switching appears repeatedly" in memory
    assert "## Patterns\n\n- Biggest risk: distraction" in memory
