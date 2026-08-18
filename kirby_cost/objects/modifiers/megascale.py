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
        
        # No additional validation needed - uses base class validation
        # Megascale modifier doesn't override included() in Java source
        return ""
    
    # Still unported, and not needed to cost an imported build:
    # - getColumn2Output() - formats scale and subtracts adder costs
    # - getDialog() - returns MegascaleDialog (UI layer)
    # - getScaleValue() - derives the default scale from levels and edition
