"""
Gestures modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Gestures.java

Gestures modifier with custom getAssignedModifiers() and getAvailableModifiers() methods
for modifier intelligence logic. Filters THROUGHOUT modifier for instant powers.
Uses base class included() and getColumn2Output() methods.
"""

from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Gestures(Modifier, xmlid="GESTURES"):
    """
    Gestures modifier.
    
    Requires gestures to activate.
    
    Has custom modifier filtering logic for modifier intelligence feature.
    Uses base class included() and getColumn2Output() methods.
    """
    
    def __init__(self, element=None):
        """Initialize a Gestures modifier."""
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
        # Gestures modifier doesn't override included() in Java source
        return ""
    
    def _should_filter_throughout(self) -> bool:
        """
        Check if THROUGHOUT modifier should be filtered.
        
        Returns:
            True if should filter, False otherwise
        """
        # TODO: Would need HeroDesigner.getInstance().getPrefs().isModifierIntelligenceOn()
        # For now, assume modifier intelligence is on
        modifier_intelligence_on = True
        
        if not modifier_intelligence_on:
            return False
        
        progenitor = self.progenitor
        if progenitor is None:
            return False
        
        # TODO: Would need HeroDesigner.getActiveHero() access
        # For now, assume hero is available and not loading
        # active_hero = HeroDesigner.getActiveHero()
        # if active_hero is None or active_hero.isLoading():
        #     return False
        
        # Check if progenitor is a List
        from kirby_cost.objects.list import List
        if isinstance(progenitor, List):
            objects = progenitor.objects
            if objects:
                for obj in objects:
                    if (obj.duration == "INSTANT" and
                        GenericObject.find_object_by_id(obj.assigned_modifiers, "EXTRATIME") is None and
                        GenericObject.find_object_by_id(obj.assigned_modifiers, "REGENEXTRATIME") is None and
                        obj.xmlid not in ("MINDCONTROL", "MINDSCAN", "MINDLINK", "TELEPATHY", "FORCEWALL")):
                        return True
            return False
        
        # Check single power
        duration = progenitor.duration
        if duration != "INSTANT":
            return False
        
        if GenericObject.find_object_by_id(progenitor.assigned_modifiers, "EXTRATIME") is not None:
            return False
        
        if GenericObject.find_object_by_id(progenitor.assigned_modifiers, "REGENEXTRATIME") is not None:
            return False
        
        xmlid = progenitor.xmlid
        if xmlid in ("MINDCONTROL", "MINDSCAN", "MINDLINK", "TELEPATHY", "FORCEWALL"):
            return False
        
        return True
    
    @property
    def assigned_modifiers(self):
        """
        Get assigned modifiers, filtering THROUGHOUT if needed.
        
        Returns:
            List of assigned modifiers
        """
        modifiers = super().assigned_modifiers
        
        if not self._should_filter_throughout():
            return modifiers
        
        # Remove THROUGHOUT modifier
        throughout = GenericObject.find_object_by_id(modifiers, "THROUGHOUT")
        if throughout:
            modifiers.remove(throughout)
        
        return modifiers
    
    @property
    def available_modifiers(self):
        """
        Get available modifiers, filtering THROUGHOUT if needed.
        
        Returns:
            List of available modifiers
        """
        modifiers = list(super().available_modifiers)
        
        if not self._should_filter_throughout():
            return modifiers
        
        # Remove THROUGHOUT modifier
        throughout = GenericObject.find_object_by_id(modifiers, "THROUGHOUT")
        if throughout:
            modifiers.remove(throughout)
        
        return modifiers
