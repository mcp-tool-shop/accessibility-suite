"""Rule help registry for actionable fixes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class HelpInfo:
    """Help information for a finding."""

    title: str
    hint: str
    url: str


# Base URL for rule documentation
DOCS_BASE_URL = "https://github.com/microsoft/accessibility-suite/blob/main/docs/rules.md"


def _make_url(anchor: str) -> str:
    """Generate a URL for a rule anchor."""
    return f"{DOCS_BASE_URL}#{anchor}"


# Static registry of help info
_REGISTRY: Dict[str, HelpInfo] = {
    "A11Y.IMG.ALT": HelpInfo(
        title="Missing Image Alt Text",
        hint="Add an 'alt' attribute describing the image content, or alt='' if decorative.",
        url=_make_url("a11yimgalt"),
    ),
    "A11Y.FORM.LABEL": HelpInfo(
        title="Missing Form Label",
        hint="Ensure every input has a <label>, aria-label, or aria-labelledby.",
        url=_make_url("a11yformlabel"),
    ),
    "A11Y.BTN.NAME": HelpInfo(
        title="Button Missing Name",
        hint="Buttons must have text content or an aria-label.",
        url=_make_url("a11ybtnname"),
    ),
    "A11Y.LINK.NAME": HelpInfo(
        title="Link Missing Name",
        hint="Links must have text content or an aria-label to be navigable.",
        url=_make_url("a11ylinkname"),
    ),
    "A11Y.COLOR.CONTRAST": HelpInfo(
        title="Low Color Contrast",
        hint="Ensure text contrast ratio matches WCAG requirements (4.5:1 normal, 3:1 large).",
        url=_make_url("a11ycolorcontrast"),
    ),
    "A11Y.DOC.TITLE": HelpInfo(
        title="Missing Document Title",
        hint="The <title> element must be present and non-empty.",
        url=_make_url("a11ydoctitle"),
    ),
    # Legacy/Fixture IDs
    "CLI.COLOR.ONLY": HelpInfo(
        title="Color-Only Information",
        hint="Do not rely solely on color to convey meaning; use text or icons too.",
        url=_make_url("clicoloronly"),
    ),
}


def get_help(finding_id: str) -> Optional[HelpInfo]:
    """Get help info for a finding ID (case-insensitive normalization)."""
    if not finding_id:
        return None
    
    # Normalize: uppercase, trimmed
    key = finding_id.strip().upper()
    return _REGISTRY.get(key)
