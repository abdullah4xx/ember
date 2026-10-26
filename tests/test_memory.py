from pathlib import Path

import pytest

from ember.memory import LocalMemoryStore


def test_memory_store_saves_searches_and_removes_only_exact_facts(
    tmp_path: Path,
) -> None:
    store = LocalMemoryStore(tmp_path / "ember" / "memory.sqlite3")

    assert store.add("I prefer concise answers.")
    assert not store.add("I prefer concise answers.")
    assert store.add("My timezone is UTC.")
    assert store.search("concise") == ["I prefer concise answers."]
    assert store.search("prefer concise") == ["I prefer concise answers."]
    assert len(store.list_all()) == 2

    assert not store.remove_fact("I prefer concise answers")
    assert store.remove_fact("I prefer concise answers.")
    assert store.search() == ["My timezone is UTC."]


def test_memory_store_rejects_empty_or_oversized_facts(tmp_path: Path) -> None:
    store = LocalMemoryStore(tmp_path / "memory.sqlite3")

    with pytest.raises(ValueError):
        store.add("   ")
    with pytest.raises(ValueError):
        store.add("x" * 1001)


def test_memory_database_is_private_on_creation(tmp_path: Path) -> None:
    store = LocalMemoryStore(tmp_path / "ember" / "memory.sqlite3")

    store.add("Private memory")

    assert store.path.stat().st_mode & 0o777 == 0o600
    assert store.path.parent.stat().st_mode & 0o777 == 0o700
