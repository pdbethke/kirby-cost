"""Read-only accessors over the loaded framework + AVAD model.

The build engine already computes all of this.  Downstream consumers
(kirby-combat) read framework kind / reserve / slot-variable-flag / AVAD
alternate-defense through this module instead of reaching into object
internals.  No cost paths are touched here.

Design notes (discovered from real HDC loads):
- The HDCLoader does NOT populate ``framework.objects``; slots are linked
  via ``slot.parent = framework`` and remain in the flat ``hero.powers``
  list.  Use ``framework_slots(hero, fw)`` to enumerate them.
- ``column1_suffix(slot)`` on Multipower returns ``"u"`` for Ultra slots
  and ``"m"`` (or ``"f"``/``"v"`` in 6E mode) for Variable slots.  A slot
  is variable when the suffix is NOT the ultra marker ("u" / "f").
- The AVAD/NND alternate defense is stored in ``modifier.input`` (free-text
  entered by the designer), NOT in ``option_id`` (which carries the rarity
  band, e.g. ``"VERYRARE"``).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from kirby_cost.objects.frameworks import (
    is_multipower,
    is_vpp,
    is_elemental_control,
)

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero
    from kirby_cost.objects.base import GenericObject


# ──────────────────────────────────────────────────────────────────────────────
#  Framework classification
# ──────────────────────────────────────────────────────────────────────────────

def framework_kind(power: "GenericObject") -> str | None:
    """Return the framework kind string, or None for non-frameworks.

    Returns one of ``"multipower"``, ``"vpp"``, ``"elemental_control"``,
    or ``None``.
    """
    if is_multipower(power):
        return "multipower"
    if is_vpp(power):
        return "vpp"
    if is_elemental_control(power):
        return "elemental_control"
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  Reserve / pool size
# ──────────────────────────────────────────────────────────────────────────────

def reserve_or_pool(framework: "GenericObject") -> int:
    """Return the Multipower reserve or VPP pool size in Active Points.

    For Elemental Controls (which have no reserve), returns 0.  The value is
    read from ``framework.base_cost``, which the build engine sets from the HDC
    ``BASECOST`` attribute during load.
    """
    if is_elemental_control(framework):
        return 0
    return int(getattr(framework, "base_cost", 0) or 0)


# ──────────────────────────────────────────────────────────────────────────────
#  Slot enumeration
# ──────────────────────────────────────────────────────────────────────────────

def framework_slots(hero: "LoadedHero", framework: "GenericObject") -> list["GenericObject"]:
    """Return the ordered list of slots that belong to *framework*.

    The HDCLoader stores slots in the flat ``hero.powers`` list and links each
    slot to its parent framework via ``slot.parent = framework``.  This function
    collects them in list order, which matches the character-sheet order.
    """
    return [p for p in hero.powers if getattr(p, "parent", None) is framework]


# ──────────────────────────────────────────────────────────────────────────────
#  Slot variable/ultra flag
# ──────────────────────────────────────────────────────────────────────────────

# Ultra-slot markers returned by Multipower.column1_suffix().
# Non-6E: "u" = Ultra, "m" = Variable (moveable).
# 6E:     "f" = Fixed, "v" = Variable.
_ULTRA_MARKERS = frozenset({"u", "f"})


def slot_is_variable(framework: "GenericObject", slot: "GenericObject") -> bool:
    """Return True for a Variable Multipower slot, False for a Fixed/Ultra slot.

    HD encodes this in ``Multipower.column1_suffix(slot)``:
      - Non-6E: ``"u"`` = Ultra (fixed), ``"m"`` = Variable (moveable)
      - 6E:     ``"f"`` = Fixed, ``"v"`` = Variable

    Falls back to reading the ``slot.ultra`` boolean attribute if
    ``column1_suffix`` is not callable (e.g. on the base ``List`` class).
    """
    suffix_fn = getattr(framework, "column1_suffix", None)
    if callable(suffix_fn):
        try:
            suffix = (suffix_fn(slot) or "").lower()
            return suffix not in _ULTRA_MARKERS
        except Exception:
            pass
    # Fallback: use the raw ultra flag set during HDC load
    ultra = getattr(slot, "ultra", True)  # default True matches HD default
    return not ultra


# ──────────────────────────────────────────────────────────────────────────────
#  AVAD / NND alternate defense
# ──────────────────────────────────────────────────────────────────────────────

_AVAD_XMLIDS = frozenset({"AVAD", "NND"})


def avad_alternate_defense(power: "GenericObject") -> str | None:
    """Return the named alternate defense for an AVAD/NND power, or None.

    Reads the ``input`` field on the AVAD or NND modifier — this is the
    free-text defense description entered by the designer in HD (e.g.
    ``"Life Support (Safe Environment: Intense Heat) Or Fire/Heat Powers"``).

    Returns the raw HD text (non-empty string) or ``None`` when the power
    has no AVAD/NND modifier.  Returns ``"UNSPECIFIED"`` when the modifier
    exists but no input text was recorded.
    """
    for mod in (getattr(power, "assigned_modifiers", None) or []):
        if (getattr(mod, "xmlid", "") or "").upper() in _AVAD_XMLIDS:
            val = (getattr(mod, "input", None) or "").strip()
            if val:
                return val
            return "UNSPECIFIED"
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  VPP pool + change-restriction control
# ──────────────────────────────────────────────────────────────────────────────

def vpp_pool(framework) -> int:
    """VPP pool size in Active Points. For a VPP the pool is carried on
    ``levels`` (NOT ``base_cost``, which is 0 for a VPP). 0 if not a VPP."""
    if not is_vpp(framework):
        return 0
    return int(getattr(framework, "levels", 0) or 0)


def vpp_control(framework) -> dict:
    """The VPP's change-restriction mechanics, read from its modifiers. Returns
    a dict with optional keys: 'skill_xmlid' (a Skill Roll required to change),
    'roll_mod' (modifier to that roll), 'extra_time' (the change's time cost).
    Empty dict = change freely (just costs a phase). Defensive: unknown shapes
    omitted."""
    out: dict = {}
    for mod in (getattr(framework, "assigned_modifiers", None) or []):
        x = (getattr(mod, "xmlid", "") or "").upper()
        if x in ("REQUIRESASKILLROLL", "REQUIRESKILLROLL", "ACTIVATIONROLL"):
            out["skill_xmlid"] = (getattr(mod, "input", "") or "").upper() or None
        if x in ("EXTRATIME",):
            out["extra_time"] = (getattr(mod, "option_id", "") or getattr(mod, "input", "") or "")
    return out


def vpp_restriction_text(framework) -> str:
    """Human-readable SFX restriction for a VPP, assembled from the pool's
    INPUT/NAME plus any LIMITEDPOWER limitation aliases/comments. '' if the
    framework is not a VPP or carries no descriptive restriction.

    Categories are NOT a cost concern — this only surfaces text for the
    kirby-api extractor to read. No cost math here.
    """
    if not is_vpp(framework):
        return ""
    parts: list[str] = []
    for attr in ("name", "input"):
        v = (getattr(framework, attr, "") or "").strip()
        if v:
            parts.append(v)
    for mod in (getattr(framework, "assigned_modifiers", None) or []):
        if (getattr(mod, "xmlid", "") or "").upper() == "LIMITEDPOWER":
            for a in ("alias", "comments"):
                v = (getattr(mod, a, "") or "").strip()
                if v:
                    parts.append(v)
    return " | ".join(dict.fromkeys(parts))  # de-dup, preserve order
