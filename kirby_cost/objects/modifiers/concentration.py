"""
Concentration modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Concentration.java

Concentration modifier with custom getAssignedModifiers(), getAvailableModifiers(),
and getColumn2Output() methods. Filters CONTINUOUSCONCENTRATION modifier based on power type.
"""

from typing import List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Concentration(Modifier, xmlid="CONCENTRATION"):
    """
    Concentration modifier.
    
    Requires concentration to use.
    
    Has custom modifier filtering logic and formatting.
    Filters CONTINUOUSCONCENTRATION modifier for certain power types.
    """
    
    def __init__(self, element=None):
        """Initialize a Concentration modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    def _should_filter_continuous_concentration(self) -> bool:
        """Never — a cost engine does not apply HD's editing intelligence.

        Java drops a CONTINUOUSCONCENTRATION sub-modifier when the power it
        sits on is INSTANT: concentrating "throughout" a power that resolves
        instantly is meaningless, so the editor hides the option while you
        build. It is an authoring affordance, and it is gated on state a
        headless engine does not have (``Concentration.java:50-71``)::

            if ((HeroDesigner.getActiveHero() == null)
                    || HeroDesigner.getActiveHero().isLoading()
                    || !p.getDuration().equals("INSTANT")
                    || EXTRATIME / REGENEXTRATIME present
                    || progenitor is MINDCONTROL/MINDSCAN/MINDLINK/
                       TELEPATHY/FORCEWALL) {
                return ret;                    // keep it
            }

        — plus, in getAvailableModifiers, on
        ``getPrefs().isModifierIntelligenceOn()``, a user preference.

        This used to guess: a TODO stood in for the hero-state guard and
        assumed "hero present, not loading", so the filter ran. The corpus
        says it never should. All 8 sites in the 794-file corpus that nest a
        CONTINUOUSCONCENTRATION record the UNfiltered value; only two of them
        reach the filter at all (the rest are CONSTANT-duration or
        name-excluded), and both agree:

            JOSEPH_OTANGA  TRANSFORM    INSTANT + EXTRATIME -> kept,  -1.0
            SHADOW_COLOSSUS ENERGYBLAST INSTANT, no guard   -> kept,  -0.5

        The second is the one that used to be an oracle residual: a static
        read of the Java filters it to -0.25, and the oracle records -0.5.

        See tests/test_continuous_concentration_is_not_filtered.py.
        """
        return False

    @property
    def assigned_modifiers(self) -> List[Modifier]:
        """
        Get assigned modifiers, filtering CONTINUOUSCONCENTRATION if needed.
        
        Returns:
            List of assigned modifiers
        """
        modifiers = super().assigned_modifiers
        
        if not self._should_filter_continuous_concentration():
            return modifiers
        
        # Remove CONTINUOUSCONCENTRATION modifier
        for modifier in modifiers:
            if modifier.xmlid == "CONTINUOUSCONCENTRATION":
                modifiers.remove(modifier)
                break
        
        return modifiers
    
    @property
    def available_modifiers(self) -> List[Modifier]:
        """
        Get available modifiers, filtering CONTINUOUSCONCENTRATION if needed.
        
        Returns:
            List of available modifiers
        """
        modifiers = list(super().available_modifiers)
        
        if not self._should_filter_continuous_concentration():
            return modifiers
        
        # Remove CONTINUOUSCONCENTRATION modifier
        for modifier in modifiers:
            if modifier.xmlid == "CONTINUOUSCONCENTRATION":
                modifiers.remove(modifier)
                break
        
        return modifiers
    
    @property
    def column2_output(self) -> str:
        """
        Get column 2 output string.
        
        Custom formatting for Concentration modifier.
        """
        string = ""
        string2 = ""
        
        if not self.show_option_only:
            string2 = string2 + self._alias
        
        d = self.total_value
        
        # Add input
        if self.input and self.input.strip():
            if string2.strip():
                string2 = string2 + " "
            string2 = string2 + self.input
        
        string2 = string2.strip()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        # Count parentheses
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
        
        # Add selected option
        if (self._selected_option is not None and 
            self._selected_option.display_in_string and
            self._selected_option.alias.strip()):
            string2 = string2 + self._selected_option.alias + "; "
        
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
        
        if string.strip():
            if string2.strip():
                string2 = string2 + ", "
            string2 = string2 + string
        
        return string2
    
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
        # Concentration modifier doesn't override included() in Java source
        return ""
