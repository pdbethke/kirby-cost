"""The no-skip guard counts real skips, never an expected failure.

pytest reports an xfail as ``skipped`` with a ``wasxfail`` attribute. The
guard read ``report.skipped`` alone, so the strict xfail in
`test_build_doc_is_a_fixed_point` (Bokor's blank ALIAS, a known open defect
pinned on purpose) failed the whole run as "coverage gone missing".
"""
from types import SimpleNamespace

from tests.conftest import _counts_as_skip


def test_a_real_skip_counts():
    assert _counts_as_skip(SimpleNamespace(skipped=True))


def test_an_expected_failure_does_not_count():
    assert not _counts_as_skip(SimpleNamespace(skipped=True, wasxfail="known"))


def test_a_pass_does_not_count():
    assert not _counts_as_skip(SimpleNamespace(skipped=False))
