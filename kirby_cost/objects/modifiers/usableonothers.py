"""
UsableOnOthers modifier for kirby-cost.

Converted from com.hero.objects.modifiers.UsableOnOthers.java

UsableOnOthers modifier with custom getColumn2Output(), getAlias(), 
and getAssignedAdders() methods. Formats target counts for SIMULTANEOUSLY and UAA options.
Uses base class included() method for validation.

TODO: Implement custom methods from Java source:
- getColumn2Output() - formats target counts and adders
- getAlias() - returns selected option alias or first option alias
- getAssignedAdders() - filters TARGETS adder for modifier intelligence
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class UsableOnOthers(Modifier, xmlid="UOO"):
    """
    UsableOnOthers modifier.
    
    Power can be used on others.
    
    Has custom formatting for SIMULTANEOUSLY and UAA options with target counts.
    Uses base class included() method for validation.
    """
    
    def __init__(self, element=None):
        """Initialize a UsableOnOthers modifier."""
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
        
        # No additional validation needed - uses base class validation
        # UsableOnOthers modifier doesn't override included() in Java source
        return ""
    
    # TODO: Implement custom methods from Java source:
    # - getColumn2Output() - formats target counts and adders
    # - getAlias() - returns selected option alias or first option alias
    # - getAssignedAdders() - filters TARGETS adder for modifier intelligence

    @property
    def column2_output(self) -> str:
        """``Usable By Other (+1/4)``, or ``Usable Simultaneously (up to 8 people at once; +1/2)``.

        Ported from ``UsableOnOthers.getColumn2Output``. The generic modifier
        line prints the alias and then the selected option's alias, and for
        this modifier they are the SAME STRING — so it read "Usable By Other
        Usable By Other (+1/4)". HD never prints the option here; it prints
        what the option MEANS, and only for the two that have something to
        say: SIMULTANEOUSLY names how many people, UAA how much weight.
        """
        from kirby_cost.objects.base import GenericObject
        ret = self.alias or ""
        if self.input and self.input.strip():
            if ret.strip():
                ret += ":  "
            ret += self.input

        option = self._selected_option
        option_id = (getattr(option, "xmlid", "") or "").upper() or \
            (getattr(self, "option_id", "") or "").upper()

        if option_id == "SIMULTANEOUSLY":
            everyone = GenericObject.find_object_by_id(
                self.assigned_adders, "ALLINRANGE")
            if everyone is not None:
                ret += f" ({everyone.alias or ''}"
                everyone.display_in_string = False
            else:
                number = 2
                for ad in self.assigned_adders:
                    if ad.xmlid == "TARGETS":
                        ad.display_in_string = False
                        number = int(number * (ad._level_power_for_display ** ad.levels))
                ret += f" (up to {number:,} people at once"
        elif option_id == "UAA":
            number = 1
            for ad in self.assigned_adders:
                if ad.xmlid == "TARGETS":
                    ad.display_in_string = False
                    number = int(number * (ad._level_power_for_display ** ad.levels))
                    ret += f" (x{number:,} maximum weight per inanimate target"

        paren = ret.count("(") - ret.count(")")
        ret += " (" if paren <= 0 else "; "
        if (self.comments or "").strip():
            ret += self.comments + "; "
        ret += self.get_fraction(self.total_value) + ")"

        adder_str = ""
        for ad in self.assigned_adders:
            if not ad.display_in_string:
                continue
            if adder_str:
                adder_str += ", "
            adder_str += ad.alias or ""
        for mod in self.assigned_modifiers:
            ret += ", " + (mod.alias or "")
        if adder_str.strip():
            ret += ", " + adder_str
        return ret
