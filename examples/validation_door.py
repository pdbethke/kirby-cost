"""Runnable walkthrough of ``kirby_cost.validation`` -- the doors a
character builder walks through before (and after) adding a modifier.

Builds a power through the LIBRARY path (``build_power_from_spec``, the same
entry point a VPP reconfigure flow uses -- see
``kirby_cost/services/power_builder.py``), not a test helper, so this is what
consuming code actually looks like.

Needs a real HERO Designer template: set ``KIRBY_COST_HDT`` to a ``.hdt``
file before running (kirby-cost ships no template data of its own)::

    KIRBY_COST_HDT=/path/to/Main6E.hdt venv/bin/python examples/validation_door.py
"""
from __future__ import annotations

from kirby_cost import allowed_modifiers, check, exclusive_conflict, verify
from kirby_cost.services.power_builder import build_power_from_spec


def main() -> None:
    blast, active, real = build_power_from_spec(
        {"xmlid": "ENERGYBLAST", "levels": 12, "modifiers": []}
    )
    print(f"built {blast.xmlid}: {blast.levels} levels, "
          f"active {active}, real {real}")

    # check() -- may this ONE modifier go here, and if not, why.
    verdict = check("ZEROPHASE", blast)
    print(f"\ncheck('ZEROPHASE', blast) -> allowed={verdict.allowed!r}")
    print(f"  reason: {verdict.reason!r}")

    # allowed_modifiers() -- the whole "add a modifier" list, each with its
    # verdict, so a UI can grey the refused ones with their reason.
    rows = allowed_modifiers(blast)
    refused = [(data, verdict) for data, verdict in rows if not verdict.allowed]
    print(f"\nallowed_modifiers(blast): {len(rows)} template modifiers, "
          f"{len(refused)} refused. First 5 refused:")
    for data, verdict in refused[:5]:
        print(f"  {data.xmlid}: {verdict.reason!r}")

    # exclusive_conflict() -- the add-time rule HD keeps OUTSIDE included():
    # an EXCLUSIVE modifier may appear once per object.
    before = exclusive_conflict("HALFRANGEMODIFIER", blast)
    print(f"\nexclusive_conflict('HALFRANGEMODIFIER', blast) before adding it "
          f"-> allowed={before.allowed!r}")
    blast, _active2, _real2 = build_power_from_spec(
        {"xmlid": "ENERGYBLAST", "levels": 12,
         "modifiers": [{"xmlid": "HALFRANGEMODIFIER"}]}
    )
    after = exclusive_conflict("HALFRANGEMODIFIER", blast)
    print(f"exclusive_conflict('HALFRANGEMODIFIER', blast) after adding it "
          f"-> allowed={after.allowed!r}")
    print(f"  reason: {after.reason!r}")

    # verify() -- HD's verifyModifiers(): re-check what is ALREADY on the
    # object. A power built from a legal spec has nothing to say.
    illegal, _a, _r = build_power_from_spec(
        {"xmlid": "ENERGYBLAST", "levels": 12,
         "modifiers": [{"xmlid": "STOPSWHENSTUNNED"}]}
    )
    print(f"\nverify(a clean Blast) -> {verify(blast)}")
    print("verify(a Blast carrying a mentalist-only limitation):")
    for f in verify(illegal):
        print(f"  {f.modifier_xmlid}: {f.verdict.reason!r}")

    # ...and the half a single power cannot show: a FRAMEWORK, whose common
    # modifiers are checked against every slot. ``build_power_from_spec``
    # builds standalone powers only -- it has no slot wiring -- so the
    # framework here is loaded from tests/validation_sink.py, the generated
    # character the validation fixtures are built from.
    print("\nverify(the validation sink's Multipower) -- common modifier x slot:")
    for f in verify(_sink_multipower()):
        print(f"  {f.modifier_xmlid} on slot {f.slot_id}: {f.verdict.reason!r}")


def _sink_multipower():
    """The sink's Multipower, loaded through the real loader. Needs
    ``KIRBY_COST_HDT``; ``tests.validation_sink`` is a generator, not a
    redistributed .hdc."""
    import sys
    import tempfile
    from pathlib import Path

    from kirby_cost.io.hdc_loader import HDCLoader

    # run from anywhere: the sink generator lives in the repo's tests/, which
    # is not on the path when this file is run as a script.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tests.validation_sink import write

    path = Path(tempfile.gettempdir()) / "kirby-cost-ValidationSink.hdc"
    write(path)
    hero = HDCLoader().load_file(str(path))
    return next(o for o in hero.powers if o.name == "Multipower")


if __name__ == "__main__":
    main()
