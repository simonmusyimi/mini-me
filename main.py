from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.file_store import FileStore
from core.llm_provider import get_llm_provider
from core.pattern_detector import analyze_and_update_patterns
from core.planner import Planner
from core.review_manager import save_daily_review
from core.task_manager import TaskManager


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


def print_intro() -> None:
    print("Mini-Me")
    print("The infrastructure of ambition for people without mentors, money, or network.")
    print()
    print("Type /plan, /patterns, /add-task, /show-tasks, /done, /review, /help, or /exit.")
    print()


def print_help() -> None:
    print("Available commands:")
    print("/plan       Generate today's 3 highest-value actions")
    print("/patterns   Detect repeated blockers, lessons, and tomorrow rules")
    print("/add-task   Add a new task")
    print("/show-tasks Show current tasks")
    print("/done       Mark an open task complete")
    print("/review     Review the day and save lessons")
    print("/exit       Quit")


def show_tasks(task_manager: TaskManager) -> None:
    tasks = task_manager.list_tasks()
    if not tasks:
        print("No tasks yet. Add one with /add-task.")
        return

    for index, task in enumerate(tasks, start=1):
        marker = "[x]" if task.completed else "[ ]"
        print(f"{index}. {marker} {task.display_text()}")


def handle_add_task(task_manager: TaskManager) -> None:
    description = input("Task: ").strip()
    if not description:
        print("No task added. A task needs a clear action.")
        return

    category = input("Category (SCHOOL, PROJECT, LEARNING, CONTENT, FITNESS, INCOME): ").strip()
    task = task_manager.add_task(description, category or "GENERAL")
    print(f"Added: {task.display_text()}")


def append_memory_entry(store: FileStore, title: str, body: str) -> None:
    entry = f"\n## {title}\n\n{body.strip()}\n"
    store.append_file("memory.md", entry)


def handle_done(store: FileStore, task_manager: TaskManager) -> None:
    open_tasks = task_manager.list_open_tasks()
    if not open_tasks:
        print("No open tasks. Nice. Use /add-task when the next real action appears.")
        return

    print("Open tasks:")
    for index, task in enumerate(open_tasks, start=1):
        print(f"{index}. {task.display_text()}")

    raw_choice = input("Mark which task done? ").strip()
    try:
        choice = int(raw_choice)
        completed_task = task_manager.mark_done(choice)
    except ValueError as exc:
        print(f"Could not mark task done: {exc}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    append_memory_entry(
        store,
        f"Completion - {today}",
        f"- Completed: {completed_task.display_text()}",
    )
    print(f"Done: {completed_task.display_text()}")


def handle_review(store: FileStore) -> None:
    print("Daily review. Be honest and concrete.")
    completed = input("1. What did you complete today? ").strip()
    blocked = input("2. What blocked you? ").strip()
    learned = input("3. What did you learn? ").strip()
    change = input("4. What should change tomorrow? ").strip()

    save_daily_review(store, completed, blocked, learned, change)
    print("Review saved. Memory updated with today's completed tasks, lessons, blockers, and tomorrow rules.")


def handle_plan(planner: Planner) -> None:
    print("Building today's plan from goals, tasks, and memory...")
    print()
    print(planner.generate_plan())


def handle_patterns(store: FileStore) -> None:
    print("Analyzing recent reviews for repeated blockers, lessons, and tomorrow rules...")
    patterns = analyze_and_update_patterns(store)
    if not patterns:
        print("No repeated patterns detected yet. Keep completing daily reviews.")
        print("Memory updated with the current pattern status.")
        return

    print(f"Detected {len(patterns)} pattern(s):")
    for pattern in patterns:
        print(f"- Pattern: {pattern.pattern}")
        print(f"  Evidence: {pattern.evidence}")
        print(f"  Suggested response: {pattern.suggested_response}")
    print("Memory updated under ## Patterns.")


def run() -> None:
    store = FileStore(DATA_DIR)
    store.ensure_files()

    task_manager = TaskManager(store)
    llm_provider = get_llm_provider(PROJECT_ROOT)
    planner = Planner(store, llm_provider)

    print_intro()

    while True:
        try:
            command = input("mini-me> ").strip()
        except EOFError:
            print()
            break

        if not command:
            continue

        if command == "/plan":
            handle_plan(planner)
        elif command == "/patterns":
            handle_patterns(store)
        elif command == "/add-task":
            handle_add_task(task_manager)
        elif command == "/show-tasks":
            show_tasks(task_manager)
        elif command == "/done":
            handle_done(store, task_manager)
        elif command == "/review":
            handle_review(store)
        elif command == "/help":
            print_help()
        elif command == "/exit":
            print("Keep the loop alive. Ship the next useful thing.")
            break
        else:
            print(f"Unknown command: {command}")
            print("Type /help to see available commands.")


if __name__ == "__main__":
    run()
