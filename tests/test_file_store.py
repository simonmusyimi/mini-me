from pathlib import Path

import pytest

from core.file_store import FileStore


def test_reading_and_writing_files(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "data")

    store.write_file("memory.md", "# Memory\n\nSimon ships.\n")

    assert store.read_file("memory.md") == "# Memory\n\nSimon ships.\n"


def test_appending_preserves_existing_markdown(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "data")
    store.write_file("reviews.md", "# Reviews\n")

    store.append_file("reviews.md", "\n## Review - 2026-06-09\n\nShipped V1.\n")

    assert store.read_file("reviews.md") == (
        "# Reviews\n\n## Review - 2026-06-09\n\nShipped V1.\n"
    )


def test_refuses_paths_outside_data_directory(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "data")

    with pytest.raises(ValueError):
        store.write_file("../secrets.md", "nope")
