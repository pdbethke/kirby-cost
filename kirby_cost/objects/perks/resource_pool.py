"""
Resource Pool Perk for kirby-cost.

Converted from com.hero.objects.perks.ResourcePool.java

Resource Pool represents a pool of points that can be allocated to various uses.
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.modifier import Modifier
from kirby_cost.core.context import EngineContext
from kirby_cost.util.rounder import round_half_down, round_half_up
from kirby_cost.io.xml_utility import XMLUtility


class ResourcePool(Perk, xmlid="RESOURCE_POOL"):
    """
    Resource Pool Perk.
    
    Represents a pool of points that can be allocated to various uses.
    """
    
    def __init__(self, element=None):
        """Initialize a Resource Pool perk."""
        super().__init__(element, self.XMLID)
        self.free_points: int = 0
        self._init_defaults()
    
    def _init_defaults(self) -> None:
        """Initialize default values."""
        self._base_cost = 0.0
        self._minimum_cost = 0.0
        self._max_cost = 999.0
        self._levels = 0
        self._minimum_level = 0
        # APG p194: "Equipment Points: 1 Character Point for 5 Equipment
        # Points." These two were transposed (5.0 cost per 1.0 value),
        # charging 5 CP per point instead of 1 CP per 5 -- a 25x overcharge.
        # Vehicle/Base and Follower/Contact are 1 CP per 2; the template
        # supplies those, this is the Equipment rate (APG p196: the most
        # common category).
        self._level_value = 5.0
        self._level_cost = 1.0
        self.level_power = 1
        self.min_set = True
        self.max_set = False
        self.free_points = 0
        if not hasattr(self, 'types') or not self._types:
            self._types = []
        self.user_input = False
        self.other_input_allowed = False
        self.option_lbl = "Type"
        self.abbreviation = "Resource Pool"
        self._name = ""
        self.allows_other_modifiers = True
        self.allows_other_adders = True
    
    @property
    def column2_output(self) -> str:
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        
        # Use selected option alias if present
        if self._selected_option and self._selected_option.alias.strip():
            output = self._selected_option.alias
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input
        if self.input and self.input.strip():
            output = output + " (" + self.input + ")"
        
        # Add total points (levels + free points)
        output = output + f": {self._levels + self.free_points}"
        
        # Add adders
        adder_str = self.adder_string
        if adder_str.strip():
            output = output + "; " + adder_str
        
        # Add modifiers
        output = output + self.modifier_string
        
        return output
    
    @property
    def real_cost_pre_list(self) -> float:
        """
        Calculate real cost before list modifiers.
        
        Special handling when levels is 0.
        
        Returns:
            Real cost value
        """
        if self._levels == 0:
            self.enhancer_applied = None
            active_cost = self.active_cost
            has_limitations = False
            limitation_total = 0.0
            
            # Sum up limitation values
            for mod in self._assigned_modifiers:
                if mod.total_value < 0.0:
                    limitation_total += mod.total_value
                    has_limitations = True
            
            # Check parent list for limitations
            parent_list = self._parent
            if self.main_power:
                parent_list = self.main_power.parent
            
            if parent_list:
                parent_mods = parent_list.assigned_modifiers
                for mod in parent_mods:
                    # Skip VPP modifiers, Charges in Multipower, or already assigned
                    if (mod.types and "VPP" in mod.types):
                        continue
                    if (mod.xmlid == "CHARGES" and 
                        hasattr(parent_list, '__class__') and 
                        parent_list.__class__.__name__ == "Multipower"):
                        continue
                    if GenericObject.find_object_by_id(self._assigned_modifiers, mod.xmlid):
                        continue
                    if mod.xmlid in ["GENERIC_OBJECT", "CUSTOM_MODIFIER", "MODIFIER"]:
                        continue
                    
                    if mod.total_value < 0.0:
                        limitation_total += mod.total_value
                        has_limitations = True
            
            # Apply limitations
            real_cost = active_cost / (1.0 + abs(limitation_total))
            if has_limitations:
                real_cost = round_half_down(real_cost)
            
            # Apply multiplier
            active_hero = EngineContext.active_hero()
            if active_hero and active_hero.rules.multiplier_allowed:
                if self.multiplier != 1.0:
                    real_cost *= self.multiplier
                    real_cost = round_half_down(real_cost)
                elif parent_list and parent_list.multiplier != 1.0:
                    real_cost *= parent_list.multiplier
                    real_cost = round_half_down(real_cost)
            
            # Apply quantity modifier
            if self._quantity > 1:
                quantity = self._quantity
                multiplier_count = 0
                while quantity > 1.0:
                    quantity /= 2.0
                    multiplier_count += 1
                real_cost += multiplier_count * 5
            
            return real_cost
        
        return super().real_cost_pre_list
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with free points attribute
        """
        element = super().get_save_xml()
        element.set("FREE_POINTS", str(self.free_points))
        return element
    
    def _init(self, element) -> None:
        """
        Initialize from XML element.
        
        Args:
            element: XML element for initialization
        """
        self._init_defaults()
        super()._init(element)
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        self._available_modifiers = []
        
        # Parse free points
        free_points_str = XMLUtility.get_value(element, "FREE_POINTS")
        if free_points_str and free_points_str.strip():
            try:
                self.free_points = int(free_points_str)
            except (ValueError, TypeError):
                self.free_points = 0
    



