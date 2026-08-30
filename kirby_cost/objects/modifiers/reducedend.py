"""
ReducedEND modifier for kirby-cost.

Converted from com.hero.objects.modifiers.ReducedEND.java

ReducedEND modifier with custom getColumn2Output() and included() methods.
Formats END cost reduction. Cannot be applied with Increased END.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class ReducedEND(Modifier, xmlid="REDUCEDEND"):
    """
    ReducedEND modifier.
    
    Reduces END cost.
    
    Has custom formatting for END cost reduction. Cannot be applied with Increased END.
    """
    
    def __init__(self, element=None):
        """Initialize a ReducedEND modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for ReducedEND modifier.
        """
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        string2 = string2 + " ("
        
        # Add selected option
        if self._selected_option is not None:
            string2 = string2 + self._selected_option.alias
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip() and not string2.endswith("("):
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Count parentheses for proper closing
        n = 0
        n2 = 0
        while string2.find("(", n) >= 0:
            n2 += 1
            n = string2.find("(", n) + 1
        
        n = 0
        while string2.find(")", n) >= 0:
            n2 -= 1
            n = string2.find(")", n) + 1
        
        string2 = string2 + " (" if n2 <= 0 else string2 + "; "
        
        # Add adders
        for adder in self.assigned_adders:
            if not adder.is_selected or not adder.column2_output.strip():
                continue
            string2 = string2 + adder.column2_output.strip() + "; "
        
        # Add comments
        if self.comments.strip():
            string2 = string2 + self.comments + "; "
        
        # Apply min/max limits
        if d > self._max_cost and self.max_set:
            d = self._max_cost
        if d < self._minimum_cost and self.min_set:
            d = self._minimum_cost
        
        string2 = string2 + self.get_fraction(d) + ")"
        n2 -= 1
        
        # Close remaining parentheses
        while n2 > 0:
            string2 = string2 + ")"
            n2 -= 1
        
        # Append adders string (if any)
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
    @property
    def total_value(self) -> float:
        """
        Get total value of this modifier.
        
        Doubles value if parent has Autofire.
        """
        d = super().total_value
        
        if self.parent is not None:
            if GenericObject.find_object_by_id(
                self.parent.assigned_modifiers, "AUTOFIRE") is not None:
                d *= 2.0
        
        return d
    
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

        # Java clones the object and detaches parent/main_power before
        # asking anything further (ReducedEND.java:132-134), so the reads
        # below see it in isolation rather than picking up a framework's
        # own modifiers through ``compute_end_usage``'s parent walk. This
        # engine has no ``clone()``; the same isolation is done by mutating
        # the real object and restoring it in ``finally`` -- the pattern
        # ``Linked.base_cost`` already uses for the same reason.
        orig_parent = generic_object.parent
        orig_main_power = generic_object.main_power
        generic_object.parent = None
        generic_object.main_power = None
        try:
            # Cannot be applied with Increased END
            if GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "INCREASEDEND") is not None:
                return f"{self.display} cannot be applied to an ability with the Increased END Limitation."

            # Cannot be applied with Costs END
            if GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "COSTSEND") is not None:
                return f"{self.display} cannot be applied to an ability with the Costs END Limitation."

            # Cannot be applied with Costs END Only To Activate
            if GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "COSTSENDONLYTOACTIVATE") is not None:
                return f"{self.display} cannot be applied to an ability with Costs END Only To Activate."

            # Cannot be applied with Costs END To Maintain
            if GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "COSTSENDTOMAINTAIN") is not None:
                return f"{self.display} cannot be applied to an ability with Costs END To Maintain."

            # Can be applied to Multipower or ElementalControl
            from kirby_cost.objects.frameworks.multipower import Multipower
            from kirby_cost.objects.frameworks.elemental_control import ElementalControl
            if isinstance(generic_object, (Multipower, ElementalControl)):
                return ""

            # Can be applied to NakedModifier or CustomPower with APPerEnd
            from kirby_cost.objects.powers.naked_modifier import NakedModifier
            from kirby_cost.objects.powers.custom_power import CustomPower
            if isinstance(generic_object, (NakedModifier, CustomPower)):
                if generic_object.ap_per_end != 0:
                    return ""

            # ReducedEND.java:162-166: a Charges modifier's own END
            # exemption would otherwise hide the ability's TRUE per-use END
            # cost -- Charges is a discount on how the ability is BOUGHT,
            # not a statement that it never costs END. Removed here so
            # ``end_usage`` below reads the underlying cost, restored before
            # returning either way.
            charges_mod = GenericObject.find_object_by_id(
                generic_object.assigned_modifiers, "CHARGES")
            orig_assigned = generic_object.assigned_modifiers
            if charges_mod is not None:
                generic_object.assigned_modifiers = [
                    m for m in orig_assigned if m is not charges_mod]
            try:
                # ReducedEND.java:167-198: for a Characteristic, HD reads
                # the ACTIVE HERO's OWN copy of that characteristic -- the
                # hero-level read this override exists to port -- not the
                # object under test. Strength's END usage is its
                # getPrimaryEND() (:174-176), which folds in every power
                # bought as added Strength; every other Characteristic uses
                # its plain end_usage.
                from kirby_cost.objects.characteristics.characteristic import Characteristic
                from kirby_cost.objects.characteristics.strength import Strength
                if isinstance(generic_object, Characteristic):
                    active_hero = None
                    if generic_object.add_modifiers_to_base:
                        from kirby_cost.core.context import EngineContext
                        active_hero = EngineContext.active_hero()
                    if active_hero is not None:
                        hero_char = next(
                            (c for c in active_hero.characteristics
                             if c.xmlid == generic_object.xmlid), None)
                        char_end = (hero_char.end_usage if hero_char is not None
                                    else generic_object.end_usage)
                        if isinstance(hero_char, Strength):
                            char_end = hero_char.primary_end(active_hero)
                        if char_end == 0 and generic_object.end_usage == 0:
                            return f"{generic_object.display} does not cost END."
                        return ""
                    if generic_object.end_usage == 0:
                        return f"{generic_object.display} does not cost END."
                    return ""

                # For other objects, check END usage
                if generic_object.end_usage == 0:
                    return f"{generic_object.display} does not cost END."
                return ""
            finally:
                generic_object.assigned_modifiers = orig_assigned
        finally:
            generic_object.parent = orig_parent
            generic_object.main_power = orig_main_power
