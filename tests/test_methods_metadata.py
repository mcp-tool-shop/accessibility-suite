"""Tests for methods metadata (audit-only fields).

These tests verify:
1. Metadata is populated deterministically
2. Metadata does not affect rendering output
3. Evidence anchors are correct
"""

from pathlib import Path

import pytest

from a11y_assist.from_cli_error import assist_from_cli_error, load_cli_error
from a11y_assist.methods import (
    METHOD_GUARD_VALIDATE,
    METHOD_NORMALIZE_CLI_ERROR,
    METHOD_NORMALIZE_RAW_TEXT,
    METHOD_PROFILE_COGNITIVE_LOAD,
    METHOD_PROFILE_DYSLEXIA,
    METHOD_PROFILE_LOWVISION,
    METHOD_PROFILE_PLAIN_LANGUAGE,
    METHOD_PROFILE_SCREEN_READER,
    with_method,
    with_methods,
)
from a11y_assist.profiles import (
    apply_cognitive_load,
    apply_screen_reader,
    render_cognitive_load,
)
from a11y_assist.render import AssistResult, Evidence, render_assist

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCliErrorMetadata:
    """Tests for metadata from cli.error.v0.1 path."""

    @pytest.fixture
    def result(self):
        """Load high-confidence fixture and get AssistResult."""
        obj = load_cli_error(str(FIXTURES_DIR / "base_inputs" / "cli_error_high.json"))
        return assist_from_cli_error(obj)

    def test_methods_applied_contains_normalize(self, result):
        """Result should include normalization method."""
        assert METHOD_NORMALIZE_CLI_ERROR in result.methods_applied

    def test_evidence_for_safest_next_step(self, result):
        """Evidence should include safest_next_step source."""
        fields = [e.field for e in result.evidence]
        assert "safest_next_step" in fields

        # Find the evidence for safest_next_step
        for e in result.evidence:
            if e.field == "safest_next_step":
                assert e.source.startswith("cli.error.")
                break

    def test_evidence_for_plan_steps(self, result):
        """Evidence should include plan step sources."""
        plan_evidence = [e for e in result.evidence if e.field.startswith("plan[")]
        # Should have evidence for each plan step
        assert len(plan_evidence) == len(result.plan)

        # Each should reference cli.error.fix
        for e in plan_evidence:
            assert "cli.error.fix" in e.source

    def test_evidence_for_safe_commands(self, result):
        """Evidence should include safe command sources."""
        if result.next_safe_commands:
            cmd_evidence = [
                e for e in result.evidence if e.field.startswith("next_safe_commands[")
            ]
            assert len(cmd_evidence) == len(result.next_safe_commands)


class TestMetadataDoesNotAffectRendering:
    """Verify that metadata doesn't change rendered output."""

    @pytest.fixture
    def result(self):
        """Load fixture and get AssistResult."""
        obj = load_cli_error(str(FIXTURES_DIR / "base_inputs" / "cli_error_high.json"))
        return assist_from_cli_error(obj)

    def test_lowvision_render_unchanged_with_metadata(self, result):
        """Lowvision render should be same with or without metadata."""
        # Render with metadata
        output_with = render_assist(result)

        # Create same result without metadata
        result_without = AssistResult(
            anchored_id=result.anchored_id,
            confidence=result.confidence,
            safest_next_step=result.safest_next_step,
            plan=result.plan,
            next_safe_commands=result.next_safe_commands,
            notes=result.notes,
            methods_applied=(),
            evidence=(),
        )
        output_without = render_assist(result_without)

        assert output_with == output_without

    def test_cognitive_load_render_unchanged_with_metadata(self, result):
        """Cognitive load render should be same with or without metadata."""
        transformed = apply_cognitive_load(result)
        output_with = render_cognitive_load(transformed)

        # Same transform but clear metadata
        transformed_clean = AssistResult(
            anchored_id=transformed.anchored_id,
            confidence=transformed.confidence,
            safest_next_step=transformed.safest_next_step,
            plan=transformed.plan,
            next_safe_commands=transformed.next_safe_commands,
            notes=transformed.notes,
            methods_applied=(),
            evidence=(),
        )
        output_without = render_cognitive_load(transformed_clean)

        assert output_with == output_without


class TestMetadataDeterminism:
    """Verify metadata is deterministic."""

    def test_same_input_same_methods(self):
        """Same input should produce same methods_applied."""
        obj = load_cli_error(str(FIXTURES_DIR / "base_inputs" / "cli_error_high.json"))

        results = []
        for _ in range(3):
            result = assist_from_cli_error(obj)
            results.append(result.methods_applied)

        # All should be identical
        assert all(r == results[0] for r in results)

    def test_same_input_same_evidence(self):
        """Same input should produce same evidence."""
        obj = load_cli_error(str(FIXTURES_DIR / "base_inputs" / "cli_error_high.json"))

        results = []
        for _ in range(3):
            result = assist_from_cli_error(obj)
            results.append(result.evidence)

        # All should be identical
        assert all(r == results[0] for r in results)


class TestWithMethodsHelpers:
    """Tests for the methods.py helper functions."""

    @pytest.fixture
    def base_result(self):
        """Create a minimal AssistResult."""
        return AssistResult(
            anchored_id="TEST.001",
            confidence="High",
            safest_next_step="Do something.",
            plan=["Step 1", "Step 2"],
            next_safe_commands=[],
            notes=[],
            methods_applied=(),
            evidence=(),
        )

    def test_with_method_adds_single(self, base_result):
        """with_method should add a single method ID."""
        updated = with_method(base_result, "test.method")
        assert "test.method" in updated.methods_applied

    def test_with_method_preserves_existing(self, base_result):
        """with_method should preserve existing methods."""
        updated = with_method(base_result, "first.method")
        updated = with_method(updated, "second.method")
        assert "first.method" in updated.methods_applied
        assert "second.method" in updated.methods_applied

    def test_with_method_deduplicates(self, base_result):
        """with_method should not add duplicates."""
        updated = with_method(base_result, "test.method")
        updated = with_method(updated, "test.method")
        assert updated.methods_applied.count("test.method") == 1

    def test_with_methods_adds_multiple(self, base_result):
        """with_methods should add multiple method IDs."""
        updated = with_methods(base_result, ["method.a", "method.b", "method.c"])
        assert "method.a" in updated.methods_applied
        assert "method.b" in updated.methods_applied
        assert "method.c" in updated.methods_applied


class TestMethodIDConstants:
    """Verify method ID constants are stable and well-formed."""

    def test_normalize_methods_exist(self):
        """Normalization method IDs should exist."""
        assert METHOD_NORMALIZE_CLI_ERROR == "engine.normalize.from_cli_error_v0_1"
        assert METHOD_NORMALIZE_RAW_TEXT == "engine.normalize.from_raw_text"

    def test_profile_methods_exist(self):
        """Profile method IDs should exist."""
        assert METHOD_PROFILE_LOWVISION == "profile.lowvision.apply"
        assert METHOD_PROFILE_COGNITIVE_LOAD == "profile.cognitive_load.apply"
        assert METHOD_PROFILE_SCREEN_READER == "profile.screen_reader.apply"
        assert METHOD_PROFILE_DYSLEXIA == "profile.dyslexia.apply"
        assert METHOD_PROFILE_PLAIN_LANGUAGE == "profile.plain_language.apply"

    def test_guard_methods_exist(self):
        """Guard method IDs should exist."""
        assert METHOD_GUARD_VALIDATE == "guard.validate_profile_transform"

    def test_method_ids_are_dotted_namespace(self):
        """All method IDs should follow dotted namespace convention."""
        all_methods = [
            METHOD_NORMALIZE_CLI_ERROR,
            METHOD_NORMALIZE_RAW_TEXT,
            METHOD_PROFILE_LOWVISION,
            METHOD_PROFILE_COGNITIVE_LOAD,
            METHOD_PROFILE_SCREEN_READER,
            METHOD_PROFILE_DYSLEXIA,
            METHOD_PROFILE_PLAIN_LANGUAGE,
            METHOD_GUARD_VALIDATE,
        ]
        for method in all_methods:
            # Should have at least one dot (namespace.name)
            assert "." in method, f"{method} should be dotted"
            # Should not have uppercase
            assert method == method.lower(), f"{method} should be lowercase"
