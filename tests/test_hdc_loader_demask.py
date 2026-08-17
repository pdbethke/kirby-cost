"""Tests for HDCLoader construction-error de-masking (FIX 3).

A class that IS registered for an xmlid but fails to construct is a bug in
the engine, never legitimate custom content.  The loader must surface it
(log at ERROR, or raise in strict mode) rather than silently returning a
``_FallbackObject`` — which is what historically hid the attack/perk/sense
construction bugs.  An xmlid with no registered class is legitimate custom
content and should fall back quietly (WARNING).
"""

import logging
import pytest

import kirby_cost.objects._registry_imports  # noqa: F401  (load registry)
from kirby_cost.io.hdc_loader import HDCLoader, _FallbackObject
from kirby_cost.objects.powers.power import Power


class _BrokenTypePower(Power, xmlid="BROKEN_TYPE_POWER"):
    """Registered power that raises a TypeError on construction (the guarded case)."""

    def __init__(self):
        super().__init__()
        # Mimic the historical bug shape: assigning to a read-only attribute.
        raise TypeError("intentional TypeError on construct")


def test_registered_typeerror_surfaces_and_does_not_silently_fallback(caplog):
    loader = HDCLoader()
    with caplog.at_level(logging.ERROR, logger="kirby_cost.io.hdc_loader"):
        obj = loader._create_instance("BROKEN_TYPE_POWER", "power")
    # It still returns a _FallbackObject (so non-strict loading continues),
    # but the failure was LOGGED at ERROR — not silently swallowed.
    assert isinstance(obj, _FallbackObject)
    assert any(
        r.levelno == logging.ERROR and "BROKEN_TYPE_POWER" in r.getMessage()
        for r in caplog.records
    ), "expected an ERROR log surfacing the registered construction failure"


def test_strict_mode_reraises_registered_construction_failure():
    loader = HDCLoader(strict=True)
    with pytest.raises(TypeError):
        loader._create_instance("BROKEN_TYPE_POWER", "power")


def test_unregistered_xmlid_falls_back_quietly(caplog):
    """An xmlid with no registered class is legit custom content: WARNING, not ERROR."""
    loader = HDCLoader()
    with caplog.at_level(logging.WARNING, logger="kirby_cost.io.hdc_loader"):
        obj = loader._create_instance("DEFINITELY_NOT_A_REAL_XMLID_XYZ", "power")
    assert isinstance(obj, _FallbackObject)
    assert not any(r.levelno == logging.ERROR for r in caplog.records), (
        "unregistered custom content must not log at ERROR"
    )
    assert any(
        r.levelno == logging.WARNING and "DEFINITELY_NOT_A_REAL_XMLID_XYZ" in r.getMessage()
        for r in caplog.records
    )
