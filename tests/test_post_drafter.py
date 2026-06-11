from pathlib import Path

from core.file_store import FileStore
from core.llm_provider import MissingLLMProvider
from core.post_drafter import PostDrafter, extract_latest_completions


MEMORY = """# Memory

## Completed Tasks
- 2026-06-09: Built the CLI
- 2026-06-10: Shipped V2.2 local planner
- 2026-06-10: shipped v2.2 local planner
- 2026-06-10: Scrubbed repo history
- 2026-06-10: Nothing recorded.

## Lessons
- 2026-06-10: things take time
"""

GOALS = """# Goals

## Current Focus
Mini-Me V2 first.
"""


class FakeProvider:
    provider_name = "fake"
    is_available = True

    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "DRAFTED POST"


def make_store(tmp_path: Path, memory: str = MEMORY) -> FileStore:
    store = FileStore(tmp_path / "data")
    store.write_file("memory.md", memory)
    store.write_file("goals.md", GOALS)
    return store


def test_extracts_only_latest_date_dedupes_and_skips_empty_values() -> None:
    completions = extract_latest_completions(MEMORY)

    assert completions == ["Shipped V2.2 local planner", "Scrubbed repo history"]


def test_no_completed_tasks_section_returns_empty() -> None:
    assert extract_latest_completions("# Memory\n\n## Lessons\n- 2026-06-10: x\n") == []


def test_local_draft_includes_progress_focus_and_label(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    drafter = PostDrafter(store, MissingLLMProvider("openai", "OPENAI_API_KEY is missing."))

    draft = drafter.draft_post()

    assert draft.startswith("(Local draft")
    assert "- Shipped V2.2 local planner" in draft
    assert "- Scrubbed repo history" in draft
    assert "Built the CLI" not in draft
    assert "Next: Mini-Me V2 first." in draft
    assert "#buildinpublic" in draft


def test_no_completions_gives_next_step_instead_of_empty_post(tmp_path: Path) -> None:
    store = make_store(tmp_path, memory="# Memory\n\n## Completed Tasks\n")
    drafter = PostDrafter(store, MissingLLMProvider("openai", "OPENAI_API_KEY is missing."))

    draft = drafter.draft_post()

    assert "Nothing completed yet to post about." in draft
    assert "/done" in draft


def test_llm_path_sends_completions_and_focus_in_prompt(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    provider = FakeProvider()
    drafter = PostDrafter(store, provider)

    draft = drafter.draft_post()

    assert draft == "DRAFTED POST"
    assert "- Shipped V2.2 local planner" in provider.prompt
    assert "Mini-Me V2 first." in provider.prompt
    assert "Under 280 characters." in provider.prompt
