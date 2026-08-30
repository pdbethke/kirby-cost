"""
Transdimensional modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Transdimensional.java

Transdimensional modifier with custom getColumn2Output() method.
Formats with parentheses handling and adder display.
Uses base class included() method for validation.

TODO: Implement custom getColumn2Output() method from Java source.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Transdimensional(Modifier, xmlid="TRANSDIMENSIONAL"):
    """
    Transdimensional modifier.
    
    Power works across dimensions.
    
    Requires custom getColumn2Output() implementation for proper formatting.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a Transdimensional modifier."""
        super().__init__()
        self.xmlid = self.XMLID
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
        
        # Transdimensional.java:111-128. The port claimed Java has no
        # override; it has one.
        from kirby_cost.objects.powers.stretching import Stretching
        if isinstance(generic_object, Stretching):
            return ""
        if generic_object.effective_target() not in ("DCV", "ECV", "HEX"):
            return (f"{self.display} can only be applied to Powers which "
                    "affect/are targeted on others.")
        return ""
    
    # TODO: Implement custom getColumn2Output() method from Java source
    # Formats with parentheses handling and adder display

    @property
    def column2_output(self) -> str:
        """``Transdimensional (Single Dimension; Waking World targets; +1/2)``.

        Ported from ``Transdimensional.getColumn2Output``. WHICH dimensions
        goes inside the bracket with everything else, not after the alias:
        the generic line put it outside and produced "Transdimensional Single
        Dimension (Waking World targets; +1/2)", which reads as a different
        modifier entirely.
        """
        from kirby_cost.objects.base import option_alias
        ret = "" if self.show_option_only else (self.alias or "")
        val = self.total_value
        if self.input and self.input.strip():
            if ret.strip():
                ret += " "
            ret += self.input
        ret = ret.strip()
        for mod in self.assigned_modifiers:
            ret += ", " + (mod.alias or "")

        paren = ret.count("(") - ret.count(")")
        ret += " (" if paren <= 0 else "; "

        option = self._selected_option
        alias = (option_alias(self) or "").strip()
        if option is not None and getattr(option, "display_in_string", True) and alias:
            ret += alias + "; "
        for ad in self.assigned_adders:
            if not getattr(ad, "is_selected", True):
                continue
            text = (ad.column2_output or "").strip()
            if text:
                ret += text + "; "
        if (self.comments or "").strip():
            ret += self.comments + "; "
        if val > self._max_cost and self.max_set:
            val = self._max_cost
        if val < self._minimum_cost and self.min_set:
            val = self._minimum_cost
        ret += self.get_fraction(val) + ")"
        paren -= 1
        while paren > 0:
            ret += ")"
            paren -= 1
        return ret
