"""Tests for storage (last.log)."""

import os
from pathlib import Path

import pytest

from a11y_assist.storage import (
    default_state_dir,
    last_log_path,
    read_last_log,
    write_last_log,
)


class TestLastLogStorage:
    """Tests for last.log read/write operations."""

    def test_last_log_roundtrip(self, tmp_path, monkeypatch):
        """Write and read last.log successfully."""
        # Monkeypatch home dir to temp
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        write_last_log("hello world")
        assert read_last_log() == "hello world"

    def test_last_log_creates_directory(self, tmp_path, monkeypatch):
        """Writing creates the .a11y-assist directory if needed."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        write_last_log("test content")
        expected_dir = tmp_path / ".a11y-assist"
        assert expected_dir.exists()

    def test_read_nonexistent_returns_empty(self, tmp_path, monkeypatch):
        """Reading nonexistent last.log returns empty string."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        assert read_last_log() == ""

    def test_last_log_overwrites(self, tmp_path, monkeypatch):
        """Subsequent writes overwrite previous content."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        write_last_log("first")
        write_last_log("second")
        assert read_last_log() == "second"

    def test_default_state_dir_uses_home(self, tmp_path, monkeypatch):
        """default_state_dir returns ~/.a11y-assist."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        state_dir = default_state_dir()
        assert state_dir == tmp_path / ".a11y-assist"

    def test_last_log_path_in_state_dir(self, tmp_path, monkeypatch):
        """last_log_path returns path inside state dir."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        log_path = last_log_path()
        assert log_path == tmp_path / ".a11y-assist" / "last.log"
