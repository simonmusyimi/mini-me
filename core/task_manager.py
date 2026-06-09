from __future__ import annotations

from dataclasses import dataclass, replace
import re

from core.file_store import FileStore


EM_DASH = "\u2014"
TASK_SEPARATOR = f" {EM_DASH} "
TASK_PATTERN = re.compile(
    r"^(?P<prefix>\s*)(?P<box>\[[ xX]\])\s+"
    r"(?P<body>.*?)(?:\s+(?:\u2014|--|-)\s+(?P<category>[A-Z][A-Z0-9 _/-]*))?\s*$"
)


@dataclass(frozen=True)
class Task:
    line_index: int
    description: str
    category: str
    completed: bool
    raw_line: str

    def display_text(self) -> str:
        if self.category:
            return f"{self.description}{TASK_SEPARATOR}{self.category}"
        return self.description


class TaskManager:
    def __init__(self, store: FileStore) -> None:
        self.store = store

    def list_tasks(self) -> list[Task]:
        lines = self._read_lines()
        tasks: list[Task] = []
        for index, line in enumerate(lines):
            task = self._parse_task_line(index, line)
            if task:
                tasks.append(task)
        return tasks

    def list_open_tasks(self) -> list[Task]:
        return [task for task in self.list_tasks() if not task.completed]

    def add_task(self, description: str, category: str = "GENERAL") -> Task:
        clean_description = " ".join(description.strip().split())
        if not clean_description:
            raise ValueError("Task description cannot be empty.")

        clean_category = self._clean_category(category)
        line = f"[ ] {clean_description}{TASK_SEPARATOR}{clean_category}"

        content = self.store.read_file("tasks.md")
        if not content.strip():
            content = "# Tasks\n\n"
        if not content.endswith("\n"):
            content += "\n"
        if content.strip() == "# Tasks":
            content += "\n"
        content += line + "\n"
        self.store.write_file("tasks.md", content)

        return Task(
            line_index=len(content.splitlines()) - 1,
            description=clean_description,
            category=clean_category,
            completed=False,
            raw_line=line,
        )

    def mark_done(self, open_task_number: int) -> Task:
        if open_task_number < 1:
            raise ValueError("Choose a task number from the open task list.")

        lines = self._read_lines()
        open_tasks = [task for task in self.list_tasks() if not task.completed]
        if open_task_number > len(open_tasks):
            raise ValueError("That task number does not exist.")

        target = open_tasks[open_task_number - 1]
        lines[target.line_index] = lines[target.line_index].replace("[ ]", "[x]", 1)
        self._write_lines(lines)
        return replace(target, completed=True, raw_line=lines[target.line_index])

    def _read_lines(self) -> list[str]:
        return self.store.read_file("tasks.md").splitlines()

    def _write_lines(self, lines: list[str]) -> None:
        self.store.write_file("tasks.md", "\n".join(lines).rstrip() + "\n")

    def _parse_task_line(self, line_index: int, line: str) -> Task | None:
        match = TASK_PATTERN.match(line)
        if not match:
            return None

        body = match.group("body").strip()
        category = (match.group("category") or "").strip()
        return Task(
            line_index=line_index,
            description=body,
            category=category,
            completed=match.group("box").lower() == "[x]",
            raw_line=line,
        )

    def _clean_category(self, category: str) -> str:
        clean = " ".join(category.strip().upper().split())
        return clean or "GENERAL"
