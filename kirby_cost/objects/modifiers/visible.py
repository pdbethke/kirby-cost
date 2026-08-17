"""
Visible modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Visible.java

Visible modifier with custom included() method.
Validates power type and checks for Invisible modifier conflicts.
Uses base class getColumn2Output() method.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Visible(Modifier, xmlid="VISIBLE"):
    """
    Visible modifier.
    
    Power is visible.
    """
    
    def __init__(self, element=None):
        """Initialize a Visible modifier."""
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
        
        from kirby_cost.objects.modifiers.focus import Focus
        if "MENTAL" in generic_object.types and not GenericObject.find_object_by_id(generic_object.assigned_modifiers, "BASEDONCON") and not GenericObject.find_object_by_id(generic_object.assigned_modifiers, "BOECV"):
            return ""
        if GenericObject.find_object_by_id(generic_object.assigned_modifiers, "INVISIBLE"):
            return f"{self._display} cannot be applied to a Power/ability with the Invisible Advantage on it."
        focus_mod = GenericObject.find_object_by_id(generic_object.assigned_modifiers, "FOCUS")
        if focus_mod and isinstance(focus_mod, Focus) and focus_mod.selected_option and focus_mod.selected_option.xmlid.startswith("O"):
            return f"{self._display} cannot be taken with the Limitation Focus if the Focus is Obvious."
        parent = generic_object.parent
        if parent:
            parent_focus = GenericObject.find_object_by_id(parent.assigned_modifiers, "FOCUS")
            if parent_focus and isinstance(parent_focus, Focus) and not parent_focus.private and parent_focus.selected_option and parent_focus.selected_option.xmlid.startswith("O"):
                return f"{self._display} cannot be taken with the Limitation Focus if the Focus is Obvious."

        return ""
