"""
Danger Sense Talent for kirby-cost.

Converted from com.hero.objects.talents.DangerSense.java

Danger Sense allows sensing danger before it happens.
"""

from typing import Optional, List
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.core.context import EngineContext
from kirby_cost.util.rounder import round_half_down, round_half_up
from copy import copy


class DangerSense(Talent, xmlid="DANGER_SENSE"):
    """
    Danger Sense Talent.
    
    Allows sensing danger before it happens.
    """
    
    def __init__(self, element=None):
        """Initialize a Danger Sense talent."""
        super().__init__(element, self.XMLID)
    
    @property
    def assigned_adders(self) -> List[Adder]:
        """
        Get assigned adders, with special handling for INTUITIONAL adder.
        
        Returns:
            List of assigned adders
        """
        adders = super().assigned_adders
        
        # Find specific adders
        area_adder = GenericObject.find_object_by_id(adders, "AREA")
        sensitivity_adder = GenericObject.find_object_by_id(adders, "SENSITIVITY")
        intuitional_adder = GenericObject.find_object_by_id(adders, "INTUITIONAL")
        
        # Remove INTUITIONAL if conditions are met
        if intuitional_adder:
            # Java reads where.getSelectedOption().getXMLID(); the port's
            # equivalent is the adder's persisted option id. Fall back to a
            # selected_option object if one was built.
            def _opt(adder):
                if adder is None:
                    return None
                oid = getattr(adder, "option_id", None)
                if oid:
                    return oid
                so = getattr(adder, "selected_option", None)
                return getattr(so, "xmlid", None) if so else None

            area_ok = (area_adder is None
                       or _opt(area_adder) == "IMMEDIATE_VICINITY")
            sensitivity_ok = (sensitivity_adder is None
                              or _opt(sensitivity_adder) == "OUT_OF_COMBAT")
            
            if area_ok and sensitivity_ok:
                return adders
            
            # Remove INTUITIONAL from list
            adders = [a for a in adders if a != intuitional_adder]
        
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    
    @property
    def available_adders(self) -> List[Adder]:
        """
        Get available adders, with special handling for INTUITIONAL adder.
        
        Returns:
            List of available adders
        """
        adders = copy(super().available_adders)
        
        # Find specific adders
        area_adder = GenericObject.find_object_by_id(adders, "AREA")
        sensitivity_adder = GenericObject.find_object_by_id(adders, "SENSITIVITY")
        intuitional_adder = GenericObject.find_object_by_id(adders, "INTUITIONAL")
        
        # Remove INTUITIONAL if conditions are met
        if intuitional_adder:
            area_ok = (area_adder is None or 
                      (area_adder.selected_option and 
                       area_adder.selected_option.xmlid == "IMMEDIATE_VICINITY"))
            sensitivity_ok = (sensitivity_adder is None or 
                             (sensitivity_adder.selected_option and 
                              sensitivity_adder.selected_option.xmlid == "OUT_OF_COMBAT"))
            
            if area_ok and sensitivity_ok:
                return adders
            
            # Remove INTUITIONAL from list
            adders = [a for a in adders if a != intuitional_adder]
        
        return adders
    
    @property
    def column2_output(self) -> str:
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        
        # Get area and sensitivity strings
        area_str = "self only"
        sensitivity_str = "in combat"
        
        area_adder = GenericObject.find_object_by_id(self.assigned_adders, "AREA")
        if area_adder:
            area_adder.display_in_string = False
            if area_adder.is_selected:
                area_str = area_adder.selected_option.alias
        
        sensitivity_adder = GenericObject.find_object_by_id(self.assigned_adders, "SENSITIVITY")
        if sensitivity_adder:
            sensitivity_adder.display_in_string = False
            if sensitivity_adder.is_selected:
                sensitivity_str = sensitivity_adder.selected_option.alias
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input
        if self.input and self.input.strip():
            output = output + ":  " + self.input
        
        # Add area, sensitivity, and selected option
        output = output + f" ({area_str}, {sensitivity_str}"
        
        if self._selected_option:
            output = output + ", " + self._selected_option.alias
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + ", " + adder_str
        else:
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + ", " + adder_str
        
        output = output + ")"
        
        # Add modifiers
        output = output + self.modifier_string
        
        # Add roll
        roll = self.roll
        if roll and roll.strip():
            output = output + " " + roll
        
        # Add END usage note
        if self.end_usage > 0:
            active_hero = EngineContext.active_hero()
            if active_hero:
                end_reserve = GenericObject.find_object_by_id(active_hero.powers, "ENDURANCERESERVE")
                if end_reserve:
                    all_mods = self.assigned_modifiers
                    end_reserve_mod = GenericObject.find_object_by_id(all_mods, "ENDRESERVEOREND")
                    prefs = EngineContext.prefs()
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output = output + " (uses END Reserve)"
                        else:
                            output = output + " (uses Personal END)"
        
        return output
    
    @property
    def roll(self) -> str:
        """
        Get roll value based on INT characteristic.
        
        Returns:
            Roll string (e.g., "11-")
        """
        active_hero = EngineContext.active_hero()
        if not active_hero:
            return "11-"
        
        # Get INT characteristic (type 5)
        int_char = active_hero.characteristic(5)
        
        roll_primary = 11
        roll_secondary = 11
        
        if int_char and int_char.per_increase > 0.0 and int_char.per_increase_levels > 0:
            # Calculate based on PER increase
            per_primary = int_char.per_increase * int_char.get_primary_value(active_hero) / int_char.per_increase_levels
            per_secondary = int_char.per_increase * int_char.get_secondary_value(active_hero) / int_char.per_increase_levels
            roll_primary = int(round_half_up(9.0 + round_half_up(per_primary)))
            roll_secondary = int(round_half_up(9.0 + round_half_up(per_secondary)))
        
        # Add talent levels
        roll_primary = int(round_half_up(roll_primary + self._levels * self._level_value))
        roll_secondary = int(round_half_up(roll_secondary + self._levels * self._level_value))
        
        if self._levels < 0:
            roll_primary = self._minimum_level
        
        result = f"{roll_primary}-"
        if roll_primary != roll_secondary:
            result = f"{roll_primary}-/{roll_secondary}-"
        
        return result
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with levels attribute
        """
        element = super().get_save_xml()
        element.set("LEVELS", str(self._levels))
        return element



