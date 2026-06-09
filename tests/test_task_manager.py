from pathlib import Path

from core.file_store import FileStore
from core.task_manager import TaskManager


def make_task_manager(tmp_path: Path) -> tuple[FileStore, TaskManager]:
    store = FileStore(tmp_path / "data")
    store.write_file(
        "tasks.md",
        "# Tasks\n\n[ ] Finish KCA assignment \u2014 SCHOOL\n[ ] Build Mini-Me V1 \u2014 PROJECT\n",
    )
    return store, TaskManager(store)


def test_adding_tasks_uses_checkbox_markdown(tmp_path: Path) -> None:
    store, task_manager = make_task_manager(tmp_path)

    task = task_manager.add_task("Study Python for 1 hour", "learning")

    assert task.description == "Study Python for 1 hour"
    assert task.category == "LEARNING"
    assert "[ ] Study Python for 1 hour \u2014 LEARNING" in store.read_file("tasks.md")


def test_marking_task_done_updates_only_selected_open_task(tmp_path: Path) -> None:
    store, task_manager = make_task_manager(tmp_path)

    completed = task_manager.mark_done(2)

    assert completed.description == "Build Mini-Me V1"
    assert completed.completed is True
    assert store.read_file("tasks.md") == (
        "# Tasks\n\n"
        "[ ] Finish KCA assignment \u2014 SCHOOL\n"
        "[x] Build Mini-Me V1 \u2014 PROJECT\n"
    )


def test_list_tasks_preserves_markdown_task_data(tmp_path: Path) -> None:
    _store, task_manager = make_task_manager(tmp_path)

    tasks = task_manager.list_tasks()

    assert len(tasks) == 2
    assert tasks[0].description == "Finish KCA assignment"
    assert tasks[0].category == "SCHOOL"
    assert tasks[0].completed is False
    assert tasks[0].raw_line == "[ ] Finish KCA assignment \u2014 SCHOOL"
