"""Re-derive the "reachable for free" claims in validation_sink.NOT_AUTHORED_BRANCHES.

**Why this exists.** The `--included` oracle's `template` tier calls every registered
modifier's `included()` against every object in the document, not just the ones that
modifier happens to be assigned to. Round 1's fix pass leaned on that: several branches
NOT_AUTHORED_BRANCHES calls "prototype-covered" or omits entirely are ones this sweep proved
already fire somewhere in the sink, without a state built specifically for them. This module
is how those claims were derived, and how a future editor re-checks them after adding or
removing a state -- not a pytest module (no `test_` prefix; nothing here is collected).

Run it directly::

    KIRBY_COST_HDT=/path/to/Main6E.hdt venv/bin/python -m tests.validation_sink_sweep
    KIRBY_COST_HDT=/path/to/Main6E.hdt venv/bin/python -m tests.validation_sink_sweep AreaEffect

An optional argument filters to override names containing that substring (case-insensitive).
For each matching override, prints every distinct reason `included()` returned across every
object in the sink, with an example object name and a count -- "ALLOWED" for a pass. A
branch this prints under exactly one reason bucket, with no visible diversity, is a branch to
look at by hand (it may mean only one code path is reachable, which is what
NOT_AUTHORED_BRANCHES is for).
"""
from __future__ import annotations

import collections
import sys
import tempfile
from pathlib import Path

from kirby_cost.core.context import EngineContext
from kirby_cost.io.hdc_loader import HDCLoader
from kirby_cost.objects import _registry_imports  # noqa: F401  registers every class
from kirby_cost.objects.modifier import Modifier

from tests import validation_sink


def _override_classes() -> dict[str, type]:
    """Every Modifier subclass overriding included(), recursively -- same walk as
    test_validation_sink.py's _engine_overrides(), but returning classes, not just names."""
    out: dict[str, type] = {}

    def _walk(cls: type) -> None:
        for sub in cls.__subclasses__():
            if "included" in sub.__dict__:
                out[sub.__name__] = sub
            _walk(sub)

    _walk(Modifier)
    return out


def _walk_objects(obj):
    yield obj
    for p in getattr(obj, "powers", []) or []:
        yield from _walk_objects(p)


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    name_filter = argv[0].lower() if argv else None

    with tempfile.TemporaryDirectory() as tmp:
        hdc_path = validation_sink.write(Path(tmp) / "ValidationSink.hdc")
        hero = HDCLoader().load_file(str(hdc_path))
    EngineContext.set_active_hero(hero)

    objects = []
    for characteristic in hero.characteristics:
        objects.extend(_walk_objects(characteristic))
    for power in hero.powers:
        objects.extend(_walk_objects(power))

    for override_name, cls in sorted(_override_classes().items()):
        if name_filter and name_filter not in override_name.lower():
            continue
        try:
            instance = cls()
        except Exception as exc:  # noqa: BLE001  -- reported, not raised
            print(f"=== {override_name} ===\n  CANNOT INSTANTIATE: {exc}")
            continue
        buckets: dict[str, list[str]] = collections.defaultdict(list)
        crashes: list[str] = []
        for obj in objects:
            obj_name = getattr(obj, "name", "") or obj.xmlid
            try:
                reason = instance.included(obj)
            except Exception as exc:  # noqa: BLE001  -- reported, not raised
                crashes.append(f"{obj_name}: {exc}")
                continue
            buckets[reason or "ALLOWED"].append(obj_name)
        print(f"=== {override_name} ===")
        for reason, obj_names in buckets.items():
            print(f"  [{len(obj_names):3d}x] {reason!r}  e.g. {obj_names[:2]}")
        for crash in crashes[:3]:
            print(f"  CRASH: {crash}")


if __name__ == "__main__":
    main()
