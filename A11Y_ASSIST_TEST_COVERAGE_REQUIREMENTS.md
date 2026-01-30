# A11y-Assist Test Coverage Requirements

**Goal:** Reach 100% coverage across CLI parsing, error ingestion, rendering, and storage.

**Current State:**
- Source modules: a11y_assist/*
- Tests exist but edge cases remain

---

## 1) a11y_assist/cli.py
**Priority: CRITICAL**
- `test_cli_main_help`
- `test_cli_parse_arguments`
- `test_cli_invalid_arguments`
- `test_cli_profile_selection`
- `test_cli_error_handling`

## 2) a11y_assist/from_cli_error.py
**Priority: HIGH**
- `test_parse_cli_error_basic`
- `test_parse_cli_error_multiline`
- `test_parse_cli_error_unknown_format`
- `test_extract_command_from_error`
- `test_extract_exit_code`

## 3) a11y_assist/ingest.py
**Priority: HIGH**
- `test_ingest_error_message`
- `test_ingest_handles_ansi_codes`
- `test_ingest_sanitizes_input`
- `test_ingest_batch_errors`
- `test_ingest_large_error_messages`

## 4) a11y_assist/guard.py
**Priority: CRITICAL**
- `test_guard_validates_schemas`
- `test_guard_rejects_invalid_data`
- `test_guard_handles_missing_fields`
- `test_guard_type_checking`
- `test_guard_nested_validation`

## 5) a11y_assist/render.py
**Priority: HIGH**
- `test_render_basic_output`
- `test_render_with_profile`
- `test_render_color_coding`
- `test_render_low_vision_mode`
- `test_render_unicode_content`
- `test_render_long_messages`

## 6) a11y_assist/storage.py
**Priority: MEDIUM**
- `test_storage_save_error`
- `test_storage_load_error`
- `test_storage_update_error`
- `test_storage_delete_error`
- `test_storage_persistence`

## 7) a11y_assist/parse_raw.py
**Priority: MEDIUM**
- `test_parse_raw_text`
- `test_parse_raw_handles_encoding`
- `test_parse_raw_binary_data`
- `test_parse_raw_empty_input`

## 8) a11y_assist/methods.py
**Priority: HIGH**
- `test_methods_suggest_fixes`
- `test_methods_analyze_error`
- `test_methods_format_recommendation`
- `test_methods_priority_ranking`

## 9) Integration Tests
**Priority: CRITICAL**
- `test_end_to_end_error_flow`
- `test_cli_to_render_pipeline`
- `test_profile_switching`
- `test_error_persistence_and_retrieval`

---

## Suggested Test Layout
```
accessibility/a11y-assist/tests/
  test_cli.py
  test_from_cli_error.py
  test_ingest.py
  test_guard.py
  test_render.py
  test_storage.py
  test_parse_raw.py
  test_methods.py
  test_integration.py
```

---

## Notes
- Test with various terminal emulator outputs
- Include ANSI escape code handling
- Test low-vision profiles thoroughly
- Mock file system operations for storage tests
- Test with real CLI error examples
