"""
OnlyToStarting modifier for kirby-cost.

Converted from com.hero.objects.modifiers.OnlyToStarting.java

OnlyToStarting modifier with custom included() method.
Validates power type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class OnlyToStarting(Modifier, xmlid="ONLYTOSTARTING"):
    """
    OnlyToStarting modifier.
    
    Limits power to only restore to starting values.
    """
    
    def __init__(self, element=None):
        """Initialize a OnlyToStarting modifier."""
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
        
        from kirby_cost.objects.powers.healing import Healing
        if isinstance(generic_object, Healing):
            return f"{generic_object.display} already restores only to starting values."
        
        return ""
