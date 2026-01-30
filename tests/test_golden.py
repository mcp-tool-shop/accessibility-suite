"""Golden fixture tests for deterministic output verification.

Golden tests ensure that profile outputs remain stable and any changes
are explicit and reviewable. These are the memory of the engine.

Rules for updating golden files:
1. The change must be intentional
2. ENGINE.md must still hold
3. Guard invariants must still pass
4. Commit message must explain why output changed
"""

from pathlib import Path

import pytest

from a11y_assist.from_cli_error import load_cli_error, assist_from_cli_error
from a11y_assist.profiles import (
    apply_cognitive_load,
    apply_dyslexia,
    apply_plain_language,
    apply_screen_reader,
    render_cognitive_load,
    render_dyslexia,
    render_plain_language,
    render_screen_reader,
)
from a11y_assist.render import render_assist

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASE_INPUTS = FIXTURES_DIR / "base_inputs"
EXPECTED = FIXTURES_DIR / "expected"


def load_fixture(path: Path) -> str:
    """Load a fixture file as string."""
    return path.read_text(encoding="utf-8")


def load_json_input(name: str):
    """Load and parse a JSON input fixture."""
    return load_cli_error(str(BASE_INPUTS / name))


class TestGoldenHighConfidence:
    """Golden tests for high-confidence cli.error.v0.1 input."""

    @pytest.fixture
    def base_result(self):
        """Load base AssistResult from cli_error_high.json."""
        obj = load_json_input("cli_error_high.json")
        return assist_from_cli_error(obj)

    def test_lowvision_golden(self, base_result):
        """Lowvision profile output must match golden fixture."""
        # Lowvision is the default, no transform needed
        rendered = render_assist(base_result)
        expected = load_fixture(EXPECTED / "lowvision_high.txt")
        assert rendered.strip() == expected.strip()

    def test_cognitive_load_golden(self, base_result):
        """Cognitive-load profile output must match golden fixture."""
        transformed = apply_cognitive_load(base_result)
        rendered = render_cognitive_load(transformed)
        expected = load_fixture(EXPECTED / "cognitive_load_high.txt")
        assert rendered.strip() == expected.strip()

    def test_screen_reader_golden(self, base_result):
        """Screen-reader profile output must match golden fixture."""
        transformed = apply_screen_reader(base_result)
        rendered = render_screen_reader(transformed)
        expected = load_fixture(EXPECTED / "screen_reader_high.txt")
        assert rendered.strip() == expected.strip()

    def test_dyslexia_golden(self, base_result):
        """Dyslexia profile output must match golden fixture."""
        transformed = apply_dyslexia(base_result)
        rendered = render_dyslexia(transformed)
        expected = load_fixture(EXPECTED / "dyslexia_high.txt")
        assert rendered.strip() == expected.strip()

    def test_plain_language_golden(self, base_result):
        """Plain-language profile output must match golden fixture."""
        transformed = apply_plain_language(base_result)
        rendered = render_plain_language(transformed)
        expected = load_fixture(EXPECTED / "plain_language_high.txt")
        assert rendered.strip() == expected.strip()


class TestGoldenDeterminism:
    """Verify determinism: same input always produces same output."""

    def test_multiple_runs_identical(self):
        """Running the same input multiple times must produce identical output."""
        obj = load_json_input("cli_error_high.json")

        outputs = []
        for _ in range(5):
            result = assist_from_cli_error(obj)
            transformed = apply_cognitive_load(result)
            rendered = render_cognitive_load(transformed)
            outputs.append(rendered)

        # All outputs must be identical
        assert len(set(outputs)) == 1, "Output must be deterministic"

    def test_all_profiles_deterministic(self):
        """All profiles must produce deterministic output."""
        obj = load_json_input("cli_error_high.json")

        profiles = [
            (lambda r: r, render_assist),
            (apply_cognitive_load, render_cognitive_load),
            (apply_screen_reader, render_screen_reader),
            (apply_dyslexia, render_dyslexia),
            (apply_plain_language, render_plain_language),
        ]

        for transform, renderer in profiles:
            outputs = []
            for _ in range(3):
                result = assist_from_cli_error(obj)
                transformed = transform(result)
                rendered = renderer(transformed)
                outputs.append(rendered)

            assert len(set(outputs)) == 1, f"Profile must be deterministic"
