"""
NotThroughMindLink modifier for kirby-cost.

Converted from com.hero.objects.modifiers.NotThroughMindLink.java

NotThroughMindLink modifier with custom included() method.
Validates power type requirements. Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class NotThroughMindLink(Modifier, xmlid="NOTTHROUGHMINDLINK"):
    """
    NotThroughMindLink modifier.
    
    Power does not work through mind link.
    """
    
    def __init__(self, element=None):
        """Initialize a NotThroughMindLink modifier."""
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
        from kirby_cost.objects.powers.mind_link import MindLink
        if isinstance(generic_object, MindLink):
            return f"{self._display} cannot be applied to Mind Link."
        result = f"{self._display} can only be applied if the character has Mind Link."
        active_hero = EngineContext.active_hero()
        if active_hero:
            for power in active_hero.powers:
                if power.xmlid == "MINDLINK":
                    result = ""
                    break
        if not result and GenericObject.find_object_by_id(generic_object.assigned_modifiers, "BASEDONCON"):
            return f"{self._display} cannot be applied to an ability with Based On CON."
        return result
        
        return ""
