"""
Requires Skill Roll modifier for kirby-cost.

Converted from com.hero.objects.modifiers.RequiresSkillRoll.java

Requires a skill roll to activate the power.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class RequiresSkillRoll(Modifier, xmlid="REQUIRESASKILLROLL"):
    """
    Requires Skill Roll modifier.
    
    Requires a skill roll to activate the power.
    """
    
    def __init__(self, element=None):
        """Initialize a Requires Skill Roll modifier."""
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
        # RequiresSkillRoll modifier doesn't override included() in Java source
        return ""


