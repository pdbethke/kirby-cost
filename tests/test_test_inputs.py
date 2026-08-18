"""The suite's own plumbing: how test inputs are located, and when a skip is a bug.

Both pieces under test here exist because a skip is green. `missing_inputs`
decides whether the suite is entitled to skip at all, and `_parse_env_file`
decides what it was pointed at — so a quiet mistake in either one restores
exactly the failure mode the guard was built to catch.
"""
import os
from pathlib import Path

from tests import corpus
from tests.conftest import _parse_env_file, _skip_reason


class TestParseEnvFile:
    def test_plain_assignment(self):
        assert _parse_env_file("KEY=value") == {"KEY": "value"}

    def test_export_prefix_is_tolerated(self):
        """So the same file can be `source`d by a shell if anyone wants to."""
        assert _parse_env_file("export KEY=value") == {"KEY": "value"}

    def test_quotes_are_stripped_but_only_matching_pairs(self):
        assert _parse_env_file('A="v"\nB=\'v\'\nC="v') == {
            "A": "v", "B": "v", "C": '"v',
        }

    def test_comments_and_blank_lines_are_ignored(self):
        text = "# a comment\n\n  \nKEY=value\n"
        assert _parse_env_file(text) == {"KEY": "value"}

    def test_leading_tilde_expands(self):
        assert _parse_env_file("KEY=~/x")["KEY"] == os.path.expanduser("~/x")

    def test_a_path_may_contain_spaces(self):
        """Character paths routinely do. No quoting required."""
        parsed = _parse_env_file("KEY=/a/Champions Legacy/b.hdc")
        assert parsed["KEY"] == "/a/Champions Legacy/b.hdc"

    def test_a_path_may_contain_equals_and_hash(self):
        """Only the FIRST = splits, and # is a comment only at line start."""
        parsed = _parse_env_file("KEY=/a/b=c#d")
        assert parsed["KEY"] == "/a/b=c#d"

    def test_a_line_without_equals_is_not_a_setting(self):
        assert _parse_env_file("just some prose") == {}


class TestMissingInputs:
    def test_unset_counts_as_missing(self, monkeypatch):
        """Subset, not equality: whether GENERATED is also missing depends on
        whether this checkout has generated its fixtures, and asserting on that
        would make this test pass or fail by machine — the very thing the guard
        exists to stop."""
        for var in corpus.INPUTS:
            monkeypatch.delenv(var, raising=False)
        missing = corpus.missing_inputs()
        for var in corpus.INPUTS:
            assert var in missing

    def test_a_path_that_does_not_exist_counts_as_missing(self, monkeypatch):
        """The dangerous case: configured-looking, absent in fact.

        This is precisely what the roundtrip character's variable was between
        ed775fb and 2026-08-18 — a default that named nothing, so the tests
        skipped and the suite stayed green.
        """
        monkeypatch.setenv("KIRBY_COST_CORPUS", "/nonexistent/corpus")
        assert "KIRBY_COST_CORPUS" in corpus.missing_inputs()

    def test_an_existing_path_counts_as_present(self, monkeypatch, tmp_path):
        monkeypatch.setenv("KIRBY_COST_CORPUS", str(tmp_path))
        assert "KIRBY_COST_CORPUS" not in corpus.missing_inputs()

    def test_generated_fixtures_count_as_inputs(self, monkeypatch):
        """The guard fails a run that skips while nothing is missing.

        A fresh clone with all five variables set still has no fixtures — they
        are gitignored Hero Games derivatives — and skips ~45 tests. If those
        did not count as inputs, that clone would be told its coverage had
        gone missing when it had simply never generated them.
        """
        monkeypatch.setattr(corpus, "_FIXTURES", Path("/nonexistent"))
        missing = corpus.missing_inputs()
        for name in corpus.GENERATED:
            assert name in missing

    def test_every_input_is_documented_in_the_example_file(self):
        """A new input must be discoverable by someone who has none of them."""
        example = (Path(__file__).resolve().parent.parent
                   / ".env.test.example").read_text()
        for var in corpus.INPUTS:
            assert var in example, f"{var} is not named in .env.test.example"


class TestSkipReason:
    def test_reads_pytests_tuple_form(self):
        report = type("R", (), {"longrepr": ("f.py", 12, "Skipped: corpus absent")})
        assert _skip_reason(report) == "corpus absent"

    def test_reads_a_bare_string(self):
        assert _skip_reason(type("R", (), {"longrepr": "corpus absent"})) == "corpus absent"

    def test_survives_no_reason_at_all(self):
        assert _skip_reason(type("R", (), {"longrepr": None})) == "no reason given"
