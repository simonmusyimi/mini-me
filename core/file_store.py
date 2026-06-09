from __future__ import annotations

from pathlib import Path


DEFAULT_FILES = {
    "goals.md": """# Goals

## 90-Day Vision
- Ship Mini-Me V1
- Improve Python and software engineering fundamentals
- Build in public consistently
- Complete KCA assignments on time
- Create a path to first tech income
- Improve fitness and discipline

## Non-Negotiables
- Deep work daily
- Train consistently
- Avoid chasing new tools before shipping
- Post progress publicly

## Current Focus
Mini-Me V1 first.
""",
    "tasks.md": """# Tasks

[ ] Finish KCA assignment \u2014 SCHOOL
[ ] Build Mini-Me V1 \u2014 PROJECT
[ ] Study Python for 1 hour \u2014 LEARNING
[ ] Write one X post about Mini-Me \u2014 CONTENT
[ ] Train today \u2014 FITNESS
""",
    "memory.md": """# Memory

## About Simon

Simon is an IT student at KCA University in Nairobi.

He is learning AI and software engineering.

He prefers learning by building.

He wants to build in public and create income through tech.

## Current Project

Mini-Me is the main project.

## Patterns

- Biggest risk: distraction
- Often gets excited by new tools
- Needs simple next actions
- Should prioritize shipping over researching

## Completed Tasks

## Lessons

## Recurring Blockers

## Tomorrow Rules
""",
    "reviews.md": """# Reviews
""",
}


class FileStore:
    """Small markdown-backed store for Mini-Me V1."""

    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)

    def ensure_files(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for filename, default_content in DEFAULT_FILES.items():
            path = self.path_for(filename)
            if not path.exists():
                path.write_text(default_content, encoding="utf-8")

    def path_for(self, filename: str) -> Path:
        candidate = (self.data_dir / filename).resolve()
        data_root = self.data_dir.resolve()
        if candidate != data_root and data_root not in candidate.parents:
            raise ValueError(f"Refusing to access file outside data directory: {filename}")
        return candidate

    def read_file(self, filename: str, default: str = "") -> str:
        path = self.path_for(filename)
        if not path.exists():
            return default
        return path.read_text(encoding="utf-8")

    def write_file(self, filename: str, content: str) -> None:
        path = self.path_for(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def append_file(self, filename: str, content: str) -> None:
        path = self.path_for(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        prefix = ""
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing and not existing.endswith("\n"):
                prefix = "\n"

        with path.open("a", encoding="utf-8") as handle:
            handle.write(prefix + content)
