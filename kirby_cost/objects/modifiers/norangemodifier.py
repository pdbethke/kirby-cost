"""
NoRangeModifier modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NoRangeModifier.java

NoRangeModifier modifier with custom included() method.
Validates range requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NoRangeModifier(Modifier, xmlid="NORANGEMODIFIER"):
    """
    NoRangeModifier modifier.
    
    Power is not subject to range modifiers.
    """
    
    def __init__(self, element=None):
        """Initialize a NoRangeModifier modifier."""
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
        
        from kirby_cost.core.context import EngineContext
        from kirby_cost.objects.frameworks.multipower import Multipower
        from kirby_cost.objects.frameworks.elemental_control import ElementalControl
        from kirby_cost.objects.powers.teleportation import Teleportation
        template = EngineContext.active_template()
        if isinstance(generic_object, Teleportation) and template and template.is_6e():
            return ""
        if isinstance(generic_object, (Multipower, ElementalControl)):
            return ""
        if generic_object.range_value <= 0:
            return f"{self._display} can only be applied to Ranged Powers."

        return ""
