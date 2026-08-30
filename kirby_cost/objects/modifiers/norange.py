"""
NoRange modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NoRange.java

NoRange modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NoRange(Modifier, xmlid="NORANGE"):
    """
    NoRange modifier.
    
    Power has no range.
    """
    
    def __init__(self, element=None):
        """Initialize a NoRange modifier."""
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
        
        from kirby_cost.objects.frameworks.multipower import Multipower
        from kirby_cost.objects.frameworks.elemental_control import ElementalControl
        from kirby_cost.objects.powers.duplication import Duplication
        if isinstance(generic_object, (Multipower, ElementalControl)):
            return ""
        if isinstance(generic_object, Duplication):
            return f"{self.display} cannot be applied to Duplication."
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "RANGED"):
            return f"{self.display} cannot be applied to Powers that have taken the Ranged Advantage."
        if generic_object.range_value == 0:
            return f"{self.display} can only be applied to Ranged Powers."

        return ""
