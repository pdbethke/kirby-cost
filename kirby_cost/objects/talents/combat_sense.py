"""
Combat Sense Talent for kirby-cost.

Converted from com.hero.objects.talents.CombatSense.java

Combat Sense allows sensing combat-related threats.
"""

from typing import Optional, List
from kirby_cost.objects.talents.talent import Talent
from kirby_cost.objects.skills.characteristic_choice import CharacteristicChoice
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.core.context import EngineContext
from kirby_cost.util.rounder import round_half_down, round_half_up
from kirby_cost.util.constants import characteristic_string, characteristic_integer
from kirby_cost.io.xml_utility import XMLUtility
from lxml import etree


class CombatSense(Talent, xmlid="COMBAT_SENSE"):
    """
    Combat Sense Talent.
    
    Allows sensing combat-related threats.
    Can be based on different characteristics.
    """
    
    def __init__(self, element=None):
        """Initialize a Combat Sense talent."""
        super().__init__(element, self.XMLID)
        self.characteristic: int = 0
        self.characteristic_choices: List[CharacteristicChoice] = []
    
    @property
    def column2_output(self) -> str:
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input
        if self.input and self.input.strip():
            output = output + ":  " + self.input
        
        # Add characteristic-based note if applicable
        prefs = EngineContext.prefs()
        if (not prefs.use_wg and 
            self.characteristic_choices and 
            len(self.characteristic_choices) > 1 and 
            self.characteristic != 0):
            output = output + f" ({characteristic_string(self.characteristic)}-based)"
        
        # Add adders
        adder_str = self.adder_string
        if adder_str.strip():
            output = output + " ("
            output = output + adder_str
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
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output = output + " (uses END Reserve)"
                        else:
                            output = output + " (uses Personal END)"
        
        return output
    
    @property
    def roll(self) -> str:
        """
        Get roll value based on characteristic.
        
        Returns:
            Roll string (e.g., "11-")
        """
        active_hero = EngineContext.active_hero()
        if not active_hero:
            return "11-"
        
        roll_primary = 11
        roll_secondary = 11
        
        if self._levels < 0:
            roll_primary = self._minimum_level
        else:
            char = active_hero.characteristic(self.characteristic)
            if char and char.xmlid != "GENERAL":
                # Calculate based on characteristic
                primary_val = char.primary_value()
                secondary_val = char.secondary_value()
                roll_primary = int(round_half_up(9.0 + primary_val / 5.0 + 
                                                          self._levels * self._level_value))
                roll_secondary = int(round_half_up(9.0 + secondary_val / 5.0 + 
                                                            self._levels * self._level_value))
            elif char and char.xmlid == "GENERAL":
                # Use template general level
                template = EngineContext.active_template()
                if template:
                    general_level = template.general_level
                    roll_primary = int(round_half_up(9.0 + general_level / 5.0 + 
                                                              self._levels * self._level_value))
            else:
                # Default calculation
                roll_primary = int(round_half_up(11.0 + self._levels * self._level_value))
                roll_secondary = int(round_half_up(11.0 + self._levels * self._level_value))
        
        result = f"{roll_primary}-"
        if roll_primary != roll_secondary:
            result = f"{roll_primary}-/{roll_secondary}-"
        
        return result
    
    def get_save_xml(self):
        """
        Get XML element for saving.
        
        Returns:
            XML element with characteristic attribute
        """
        element = super().get_save_xml()
        element.set("CHARACTERISTIC", characteristic_string(self.characteristic))
        element.set("LEVELS", str(self._levels))
        return element
    
    def _init(self, element) -> None:
        """
        Initialize from XML element.
        
        Args:
            element: XML element for initialization
        """
        self._display = "Combat Sense"
        self._base_cost = 15.0
        self._level_cost = 1.0
        self._level_value = 1.0
        self.exclusive = True
        self.characteristic_choices = []
        self.characteristic = 0
        
        super()._init(element)
        
        # Parse CHARACTERISTIC_CHOICE elements
        if hasattr(element, 'find'):
            choice_elem = element.find('CHARACTERISTIC_CHOICE')
            if choice_elem is not None:
                for item_elem in choice_elem.findall('ITEM'):
                    if item_elem is not None:
                        choice = CharacteristicChoice()
                        choice._init(item_elem)
                        self.characteristic_choices.append(choice)
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        char_str = XMLUtility.get_value(element, "CHARACTERISTIC")
        if char_str and char_str.strip():
            self.set_characteristic(characteristic_integer(char_str))
        
    
    
    def set_characteristic(self, char_type: int) -> None:
        """
        Set characteristic and update costs.
        
        Args:
            char_type: Characteristic type integer
        """
        for choice in self.characteristic_choices:
            if choice.characteristic == char_type:
                self.characteristic = char_type
                
                if choice.base_cost >= 0.0:
                    self.base_cost = choice.base_cost
                
                if choice.level_cost >= 0.0:
                    self.set_level_cost(choice.level_cost)
                
                if choice.level_value >= 0.0:
                    self.set_level_value(choice.level_value)
                
                if choice.minimum_cost > -999.0:
                    self.set_minimum_cost(choice.minimum_cost)
                
                if choice.minimum_level >= 0:
                    self._minimum_level = choice.minimum_level
                
                break



