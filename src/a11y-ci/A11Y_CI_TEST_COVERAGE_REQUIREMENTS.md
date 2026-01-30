# A11y-CI Test Coverage Requirements

**Goal:** Reach 100% coverage across CI gates, scorecard processing, and rendering.

**Current State:**
- Source modules: a11y_ci/*
- Tests exist but edge cases remain

---

## 1) a11y_ci/cli.py
**Priority: CRITICAL**
- `test_cli_main_help`
- `test_cli_gate_command`
- `test_cli_scorecard_command`
- `test_cli_invalid_arguments`
- `test_cli_exit_codes`
- `test_cli_verbose_mode`

## 2) a11y_ci/gate.py
**Priority: CRITICAL**
- `test_gate_pass_threshold`
- `test_gate_fail_threshold`
- `test_gate_exact_threshold`
- `test_gate_missing_scorecard`
- `test_gate_invalid_scorecard_format`
- `test_gate_with_allowlist`
- `test_gate_strict_mode`

## 3) a11y_ci/scorecard.py
**Priority: HIGH**
- `test_scorecard_parse`
- `test_scorecard_validate`
- `test_scorecard_calculate_score`
- `test_scorecard_merge_multiple`
- `test_scorecard_empty_data`
- `test_scorecard_malformed_json`

## 4) a11y_ci/allowlist.py
**Priority: HIGH**
- `test_allowlist_load`
- `test_allowlist_check_rule`
- `test_allowlist_pattern_matching`
- `test_allowlist_empty_file`
- `test_allowlist_invalid_format`
- `test_allowlist_wildcard_patterns`

## 5) a11y_ci/render.py
**Priority: MEDIUM**
- `test_render_scorecard_summary`
- `test_render_gate_result`
- `test_render_with_colors`
- `test_render_low_vision_mode`
- `test_render_json_output`
- `test_render_markdown_output`

## 6) a11y_ci/schemas/*
**Priority: MEDIUM**
- `test_schema_validation`
- `test_schema_required_fields`
- `test_schema_type_checking`
- `test_schema_versioning`

## 7) Integration Tests
**Priority: CRITICAL**
- `test_end_to_end_gate_pass`
- `test_end_to_end_gate_fail`
- `test_ci_pipeline_integration`
- `test_allowlist_gate_interaction`
- `test_multiple_scorecards`

---

## Suggested Test Layout
```
accessibility/a11y-ci/tests/
  test_cli.py
  test_gate.py
  test_scorecard.py
  test_allowlist.py
  test_render.py
  test_schemas.py
  test_integration.py
```

---

## Notes
- Test with real a11y-lint scorecard examples
- Include CI environment variable scenarios
- Test threshold edge cases (exactly at limit)
- Mock file system for scorecard loading
- Test both pass and fail scenarios thoroughly
- Include regression tests for allowlist patterns
