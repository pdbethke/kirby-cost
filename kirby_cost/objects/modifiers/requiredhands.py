"""
RequiredHands modifier for kirby-cost.

Converted from com.hero.objects.modifiers.RequiredHands.java

RequiredHands modifier with custom included() method.
Validates power type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class RequiredHands(Modifier, xmlid="REQUIREDHANDS"):
    """
    RequiredHands modifier.
    
    Requires specific number of hands to use.
    """
    
    def __init__(self, element=None):
        """Initialize a RequiredHands modifier."""
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
        
        from kirby_cost.objects.skills.penalty_skill_levels import PenaltySkillLevels
        from kirby_cost.objects.skills.combat_levels import CombatLevels
        if isinstance(generic_object, (PenaltySkillLevels, CombatLevels)):
            return ""
        types_list = generic_object.types
        if "ATTACK" not in types_list and "DEFENSE" not in types_list:
            return f"{self._display} can only be applied to Attack Powers, Defense Powers, or CSLs/PSLs."
        
        return ""
