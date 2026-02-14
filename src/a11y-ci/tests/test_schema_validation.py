
import pytest
import json
import jsonschema
from pathlib import Path
from click.testing import CliRunner
from a11y_ci.cli import main
from a11y_ci.scorecard import Scorecard

FIXTURES = Path(__file__).parent / "fixtures"

def test_load_scorecard_valid():
    # Should not raise
    s = Scorecard.load(str(FIXTURES / "current_ok.json"))
    assert isinstance(s, Scorecard)

def test_load_scorecard_invalid_schema(tmp_path):
    # Create invalid file
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps({"tool": "oops", "findings": []}), encoding="utf-8")
    
    with pytest.raises(jsonschema.ValidationError):
        Scorecard.load(str(bad_file))

def test_cli_schema_validation_error(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps({"tool": "oops", "findings": []}), encoding="utf-8")
    
    runner = CliRunner()
    result = runner.invoke(main, ["gate", "--current", str(bad_file)])
    
    # Should be exit code 2 (input error)
    assert result.exit_code == 2
    # Should contain our specific error message
    assert "Scorecard format invalid" in result.output
    assert "required property" in result.output or "is not of type" in result.output
