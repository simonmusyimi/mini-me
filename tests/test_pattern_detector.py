from pathlib import Path

from core.file_store import FileStore
from core.pattern_detector import detect_patterns, update_memory_patterns
from core.planner import Planner
from main import handle_patterns, print_help, run


SEMANTIC_REVIEWS = """# Reviews

## Review - 2026-06-07 21:00

### Completed
Built review loop

### Blocked
context switching

### Learned
Shipping beats polishing

### Change Tomorrow
Start with one execution task before research

## Review - 2026-06-08 21:00

### Completed
Added tests

### Blocked
opening too many tabs

### Learned
Small loops win

### Change Tomorrow
Do first task

## Review - 2026-06-09 21:00

### Completed
Updated docs

### Blocked
tabs,lack of focus

### Learned
Small loops win

### Change Tomorrow
No context switching
"""


AVOIDANCE_REVIEWS = """# Reviews

## Review - 2026-06-07 21:00

### Completed
Worked out

### Blocked
doom scrolling

### Learned
Move early

### Change Tomorrow
No phone before work

## Review - 2026-06-08 21:00

### Completed
Studied Python

### Blocked
doomscroling

### Learned
Start sooner

### Change Tomorrow
Block feeds
"""


class FakeProvider:
    provider_name = "fake"

    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "PLAN BODY"


def test_context_switching_and_too_many_tabs_group_together() -> None:
    patterns = detect_patterns(SEMANTIC_REVIEWS)

    attention = next(pattern for pattern in patterns if pattern.name == "Attention Fragmentation")

    assert attention.frequency == 5
    assert "context switching" in attention.evidence
    assert "opening too many tabs" in attention.evidence
    assert "lack of focus" in attention.evidence


def test_doom_scrolling_and_doomscroling_group_together() -> None:
    patterns = detect_patterns(AVOIDANCE_REVIEWS)

    avoidance = next(pattern for pattern in patterns if pattern.name == "Avoidance / Escape Behavior")

    assert avoidance.frequency == 2
    assert "doom scrolling" in avoidance.evidence
    assert "doomscroling" in avoidance.evidence


def test_tabs_lack_still_matches_tabs() -> None:
    patterns = detect_patterns(SEMANTIC_REVIEWS)
    attention = next(pattern for pattern in patterns if pattern.name == "Attention Fragmentation")

    assert "tabs" in attention.evidence


def test_grouped_frequency_counts() -> None:
    reviews = """# Reviews

## Review - 2026-06-07 21:00

### Completed
Worked

### Blocked
researching tools

### Learned
Output first

### Change Tomorrow
Stop tool hopping

## Review - 2026-06-08 21:00

### Completed
Shipped

### Blocked
watching tutorials instead of building

### Learned
Ship first

### Change Tomorrow
Define one small output
"""

    patterns = detect_patterns(reviews)
    overplanning = next(pattern for pattern in patterns if pattern.name == "Overplanning Instead of Shipping")

    assert overplanning.frequency == 3


def test_updates_memory_without_destroying_existing_sections() -> None:
    patterns = detect_patterns(SEMANTIC_REVIEWS)
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
    assert "### Attention Fragmentation" in updated
    assert "Frequency: 5" in updated
    assert "- opening too many tabs" in updated
    assert "Suggested Response:" in updated


def test_patterns_command_works(tmp_path: Path, capsys) -> None:
    store = FileStore(tmp_path / "data")
    store.write_file("reviews.md", SEMANTIC_REVIEWS)
    store.write_file("memory.md", "# Memory\n\n## Patterns\n\n- Biggest risk: distraction\n")

    handle_patterns(store)

    output = capsys.readouterr().out
    memory = store.read_file("memory.md")

    assert "Detected 1 grouped pattern(s):" in output
    assert "### Attention Fragmentation" in output
    assert "Frequency: 5" in output
    assert "Memory updated under ## Patterns." in output
    assert "### Attention Fragmentation" in memory
    assert "## Patterns\n\n- Biggest risk: distraction" in memory


def test_plan_reads_grouped_patterns(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "data")
    store.write_file("goals.md", "# Goals\n\nShip Mini-Me.\n")
    store.write_file("tasks.md", "# Tasks\n\n[ ] Build pattern-aware planning - PROJECT\n")
    store.write_file(
        "memory.md",
        "# Memory\n\n"
        "## Patterns\n\n"
        "<!-- MINI-ME:PATTERNS:START -->\n"
        "### Attention Fragmentation\n\n"
        "Frequency: 5\n"
        "Evidence:\n"
        "- context switching\n"
        "- opening too many tabs\n\n"
        "Suggested Response:\n"
        "Start with one execution task. Close unrelated tabs. Do not research until the first task is complete.\n"
        "<!-- MINI-ME:PATTERNS:END -->\n",
    )
    provider = FakeProvider()
    planner = Planner(store, provider)

    plan = planner.generate_plan()

    assert plan.startswith("=== Pattern Warnings ===")
    assert (
        "* Attention Fragmentation is recurring: Start with one execution task. "
        "Close unrelated tabs. Do not research until the first task is complete."
    ) in plan
    assert "MINI-ME:PATTERNS:END" not in plan
    assert "PLAN BODY" in plan
    assert "### Attention Fragmentation" in provider.prompt


def test_all_existing_commands_are_still_listed(capsys) -> None:
    print_help()

    output = capsys.readouterr().out
    for command in ["/plan", "/patterns", "/add-task", "/show-tasks", "/done", "/review", "/exit"]:
        assert command in output


def test_cli_dispatch_keeps_existing_commands_working(tmp_path: Path, monkeypatch, capsys) -> None:
    commands = iter(["/show-tasks", "/patterns", "/plan", "/exit"])

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        return next(commands)

    monkeypatch.setattr("main.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("main.PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("builtins.input", fake_input)

    run()

    output = capsys.readouterr().out
    assert "Finish KCA assignment" in output
    assert "Analyzing recent reviews" in output
    assert "Mini-Me cannot generate an LLM plan yet" in output
    assert "Keep the loop alive" in output
