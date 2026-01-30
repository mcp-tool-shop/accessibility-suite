"""Storage for last.log capture."""

from __future__ import annotations

from pathlib import Path


def default_state_dir() -> Path:
    """Get the default state directory (~/.a11y-assist)."""
    home = Path.home()
    return home / ".a11y-assist"


def last_log_path() -> Path:
    """Get the path to last.log."""
    return default_state_dir() / "last.log"


def write_last_log(text: str) -> None:
    """Write text to last.log, creating directory if needed."""
    p = last_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", errors="replace")


def read_last_log() -> str:
    """Read last.log, returning empty string if not found."""
    p = last_log_path()
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")
