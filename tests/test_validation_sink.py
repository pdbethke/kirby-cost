"""The validation sink is derived from the rules: every engine modifier that
overrides included() must be exercised by at least one authored state, and
every state must name the override(s) it exists for. HD's 81 overrides are
private; the engine's are the public mirror, so the contract is checked
against the engine's classes."""
from __future__ import annotations

from kirby_cost.objects.modifier import Modifier
from tests import validation_sink


def _engine_overrides() -> set[str]:
    from kirby_cost.objects import _registry_imports  # noqa: F401  registers every class
    out = set()

    def _walk(cls):
        for sub in cls.__subclasses__():
            if "included" in sub.__dict__:
                out.add(sub.__name__)
            _walk(sub)

    _walk(Modifier)
    return out


def test_every_override_has_a_state():
    covered = {name for s in validation_sink.STATES for name in s.overrides}
    missing = sorted(_engine_overrides() - covered)
    assert not missing, f"{len(missing)} included() overrides have no authored state: {missing}"


def test_every_state_names_a_real_override():
    real = _engine_overrides() | {"Modifier"}
    bogus = sorted({name for s in validation_sink.STATES for name in s.overrides} - real)
    assert not bogus, f"states name overrides that do not exist: {bogus}"


def test_build_is_deterministic():
    assert validation_sink.build() == validation_sink.build()


def test_build_is_a_parseable_character(tmp_path):
    import xml.etree.ElementTree as ET
    p = validation_sink.write(tmp_path / "ValidationSink.hdc")
    root = ET.fromstring(p.read_bytes().decode("utf-16"))
    assert root.tag == "CHARACTER"
    names = [e.get("NAME") for e in root.iter() if e.get("NAME")]
    assert len(names) == len(set(names)), "object NAMEs must be unique; they key the fixture back to STATES"
