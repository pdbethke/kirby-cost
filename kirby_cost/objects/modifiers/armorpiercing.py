"""
ArmorPiercing modifier for kirby-cost.

Converted from com.hero.objects.modifiers.ArmorPiercing.java

ArmorPiercing modifier with custom included() method.
Validates target and defense requirements. Uses base class getColumn2Output().
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class ArmorPiercing(Modifier, xmlid="ARMORPIERCING"):
    """
    ArmorPiercing modifier.
    
    Attack is armor piercing.
    
    Has custom validation for target and defense requirements.
    Uses base class getColumn2Output() method.
    """
    
    def __init__(self, element=None):
        """Initialize a ArmorPiercing modifier."""
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
        
        from kirby_cost.objects.characteristics.strength import Strength
        from kirby_cost.objects.martial_arts.maneuver import Maneuver
        from kirby_cost.objects.powers.naked_modifier import NakedModifier
        from kirby_cost.objects.powers.teleportation import Teleportation
        
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "NND"):
            return f"{self.display} cannot be applied to abilities which have No Normal Defense."
        
        if isinstance(generic_object, (Strength, Teleportation, Maneuver, NakedModifier)):
            return ""
        
        target = generic_object.target
        if target in ("SELFONLY", "N/A"):
            return f"{self.display} can only be applied to abilities which affect/are targeted on others."
        
        if generic_object.defense == "NONE":
            return f"{self.display} can only be applied to abilities which act against a target's defenses."
        
        return ""
    
    @property
    def column2_output(self) -> str:
        """
        Get the column 2 output string for this modifier.
        
        Returns:
            Formatted string for display
        """
        result = ""
        adder_string = ""
        result = result + self._alias
        total_value = self.total_value
        
        if self._selected_option:
            result = result + " " + self._selected_option.alias
        
        if self.input and self.input.strip():
            if result.strip():
                result = result + " "
            result = result + self.input
        
        result = result.strip()
        
        for modifier in self.assigned_modifiers:
            result = result + ", " + modifier.alias
        
        if self._levels > 1:
            result = result + " (x" + str(self._levels)
        
        # Count parentheses
        paren_count = result.count("(") - result.count(")")
        result = result + (" (" if paren_count <= 0 else "; ")
        
        for adder in self.assigned_adders:
            if not adder.is_selected or not adder.column2_output.strip():
                continue
            result = result + adder.column2_output.strip() + "; "
        
        if self.comments and self.comments.strip():
            result = result + self.comments + "; "
        
        if total_value > self._max_cost and self.max_set:
            total_value = self._max_cost
        if total_value < self._minimum_cost and self.min_set:
            total_value = self._minimum_cost
        
        result = result + self.get_fraction(total_value) + ")"
        
        # Close any remaining parentheses
        paren_count = result.count("(") - result.count(")")
        while paren_count > 0:
            result = result + ")"
            paren_count -= 1
        
        if adder_string.strip():
            if result.strip():
                result = result + ", "
            result = result + adder_string
        
        return result
