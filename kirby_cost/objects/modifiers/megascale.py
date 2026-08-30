"""
Megascale modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Megascale.java

Megascale modifier with custom getColumn2Output(), getDialog(), getSaveXML(),
and getScale() methods. Formats scale information and subtracts adder costs from total.
Uses base class included() method for validation.

SCALE is carried through the round trip (see XML_ATTRS below). Still unported
from the Java source, and unneeded while this engine only costs imported
builds:
- getColumn2Output() - formats scale and subtracts adder costs
- getDialog() - returns MegascaleDialog (UI layer)
- getScaleValue() - derives the default scale from levels and edition
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Megascale(Modifier, xmlid="MEGASCALE"):
    """
    Megascale modifier.
    
    Power works at megascale distances.
    
    Has custom formatting for scale display and adder cost handling.
    Uses base class included() method for validation.
    """
    
    #: The scale reads back out as the document stated it — "1m = 1 km broad
    #: and wide" and the rest. It was neither read nor written, so 56
    #: characters exported their megascaled powers with no scale at all, and HD
    #: recomputes one from the levels on load: a power bought at one scale and
    #: overridden to another silently reverts to the default.
    #:
    #: Java DERIVES the default (``getScaleValue``: edition, levels, and a +5
    #: for a Mind Scan progenitor) and stores ``scale`` only as an override,
    #: rewriting it whenever levels change back into agreement. That machinery
    #: is not ported and is not needed here — this engine costs an imported
    #: build and never changes a level after load, so the document's own value
    #: is the value, and carrying it is strictly more faithful than deriving a
    #: default we would then have to keep in sync.
    XML_ATTRS = (
        XMLAttr("SCALE", "scale"),
    )

    def __init__(self, element=None):
        """Initialize a Megascale modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        self.scale: str = ""
        if element is not None:
            self._init(element)
    
    def included(self, generic_object: GenericObject) -> str:
        """
        Check if this modifier can be applied to the given object.
        
        Args:
            generic_object: The object to check
            
        Returns:
            Empty string if allowed, error message if not
        """
        result = super().included(generic_object)
        if result and result.strip():
            return result
        
        if self.force_allow:
            return result
        
        # Megascale.java:191-209.
        if generic_object.effective_target() == "HEX":
            return ""
        if ("MOVEMENT" in (generic_object.types or ())
                and generic_object.xmlid not in ("FTL", "EXTRADIMENSIONALMOVEMENT")):
            return ""
        if generic_object.range_value > 0:
            return ""
        from kirby_cost.objects.powers.mind_scan import MindScan
        from kirby_cost.objects.powers.sense import Sense
        if isinstance(generic_object, MindScan):
            return ""
        if isinstance(generic_object, Sense):
            if "RANGE" in generic_object.built_in_sense_adders():
                return ""
        return (f"{self.display} can only be applied to Powers which already "
                "affect an area, Movement Powers (except Extradimensional "
                "Movement and FTL Travel), and Powers which work at Range.")
    
    # Still unported, and not needed to cost an imported build:
    # - getColumn2Output() - formats scale and subtracts adder costs
    # - getDialog() - returns MegascaleDialog (UI layer)
    # - getScaleValue() - derives the default scale from levels and edition

    @property
    def scale_value(self) -> str:
        """``1m = 1 km``, ``1m = 2 lightyears``, ``1m = a LONG way``.

        Ported from ``Megascale.getScaleValue`` (6E branch). MegaScale's whole
        content is the ratio it buys, and it was not being printed at all:
        "MegaScale (+1)" instead of "MegaScale (1m = 1 km; +1)".

        The 6E offsets are deliberate — one extra doubling for the edition,
        five more when the modifier sits on a Mind Scan, which reaches further
        than anything physical. The overflow check compares against the
        previous power of ten because at these magnitudes the float stops
        being able to hold the answer, and HD says so rather than printing a
        wrong number.
        """
        ret = "1m = "
        additional = 1
        progenitor = self.progenitor
        if progenitor is not None and progenitor.xmlid == "MINDSCAN":
            additional += 5
        power = self._level_power_for_display
        levels = self._levels

        val = 1.0
        if levels == 1:
            val = 10.0
        if levels > 1:
            val = float(power) ** (levels - 1 + additional)
        check = 0.0
        if levels > 2:
            check = float(power) ** (levels - 2 + additional)

        def n(x: float) -> str:
            return f"{int(x):,}".replace(",", ",")

        if val <= 0 or val < check:
            return ret + "a LONG way"
        if val < 1_000_000:
            return ret + f"{int(val):,} km"
        if val < 1_000_000_000:
            return ret + f"{int(val / 1_000_000):,} million km"
        if val < 1_000_000_000_000:
            return ret + f"{int(val / 1_000_000_000):,} billion km"
        if val < 10_000_000_000_000:
            return ret + f"{int(val / 1_000_000_000_000):,} trillion km"
        if val < 1e31:
            val = val / 10_000_000_000_000
            if val < 1_000_000:
                plural = "" if val < 1.5 else "s"
                return ret + f"{int(val):,} lightyear{plural}"
            if val < 1_000_000_000:
                return ret + f"{int(val / 1_000_000):,} million lightyears"
            if val < 1_000_000_000_000:
                return ret + f"{int(val / 1_000_000_000):,} billion lightyears"
            if val < 1_000_000_000_000_000:
                return ret + f"{int(val / 1_000_000_000_000):,} trillion lightyears"
            return ret + f"{int(val / 1_000_000_000_000_000):,} quadrillion lightyears"
        return ret + "a LONG way"

    @property
    def scale_display(self) -> str:
        """The stated scale, or the computed one when none was stated.

        NOT named `scale`: that is the serialised field, and a property of the
        same name shadowed it — the writer then lost SCALE on 76 modifiers.
        HD lets a character reword the ratio ("1m = 1 km broad and wide") and
        keeps that wording; the computed value is only the fallback.
        """
        computed = self.scale_value
        stated = (getattr(self, "scale", "") or "").strip()
        if not stated or stated == computed:
            return computed
        return stated

    @property
    def column2_output(self) -> str:
        """``MegaScale (1m = 1 km; +1)``.

        Ported from ``Megascale.getColumn2Output``. The scale leads the
        bracket; without it the modifier says only that it is expensive.
        """
        from kirby_cost.objects.base import option_alias
        ret = self.alias or ""
        val = self.total_value
        adder_str = ""
        for ad in self.assigned_adders:
            if adder_str:
                adder_str += ", "
            adder_str += f"{ad.column2_output} ({self.get_fraction(ad.base_cost)})"
            val -= ad.base_cost
        if self.input and self.input.strip():
            if ret.strip():
                ret += ":  "
            ret += self.input
        for mod in self.assigned_modifiers:
            ret += ", " + (mod.alias or "")
        ret += " ("
        ret += self.scale_display + "; "
        option = (option_alias(self) or "").strip()
        if option:
            ret += option + "; "
        if (self.comments or "").strip():
            ret += self.comments + "; "
        if adder_str.strip():
            ret += adder_str + "; "
        ret += self.get_fraction(val) + ")"
        return ret
