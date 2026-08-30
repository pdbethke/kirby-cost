"""examples/validation_door.py stays runnable -- imported and executed here so
a later refactor that breaks it fails the suite instead of rotting quietly."""
import runpy
from pathlib import Path

_EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "validation_door.py"


def test_the_example_runs_end_to_end(capsys):
    result = runpy.run_path(str(_EXAMPLE), run_name="__main__")
    assert "main" in result
    out = capsys.readouterr().out
    assert "check('ZEROPHASE', blast)" in out
    assert "exclusive_conflict" in out
