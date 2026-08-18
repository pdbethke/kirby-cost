"""
Reputation Perk for kirby-cost.

Converted from com.hero.objects.perks.Reputation.java

Reputation represents the character's reputation (positive or negative).
"""

from typing import Optional
from kirby_cost.objects.perks.perk import Perk
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.powers.automaton import Automaton
from kirby_cost.core.context import EngineContext
from kirby_cost.util.rounder import round_half_down, round_half_up
from kirby_cost.io.xml_utility import XMLUtility


class Reputation(Perk, xmlid="REPUTATION"):
    """
    Reputation Perk.
    
    Represents the character's reputation (positive or negative).
    """
    
    def __init__(self, element=None):
        """Initialize a Reputation perk."""
        super().__init__(element, self.XMLID)
    
    @property
    def base_cost(self) -> float:
        """
        Get base cost.

    @base_cost.setter
    def base_cost(self, value) -> None:
        self._base_cost = value
        
        Returns:
            Base cost value
        """
        return self._base_cost
    
    @property
    def column2_output(self) -> str:
        """
        Get formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        # Use old format if options exist
        if len(self.options) > 0:
            return self.old_column2_output
        
        output = self._alias
        
        # Add name if present
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add input
        if self.input and self.input.strip():
            output = output + ":  " + self.input
        
        # Get HOWWELL and HOWWIDE adders
        how_well = GenericObject.find_object_by_id(self.assigned_adders, "HOWWELL")
        how_wide = GenericObject.find_object_by_id(self.assigned_adders, "HOWWIDE")
        
        if how_well and how_wide:
            how_well.display_in_string = False
            how_wide.display_in_string = False
            output = output + " ("
            output = output + how_wide.selected_option.alias
            output = output + ") "
            output = output + how_well.selected_option.alias
        
        # Add levels
        output = output + f", +{self._levels}/+{self._levels}d6"
        
        # Add adders
        adder_str = self.adder_string
        if adder_str.strip():
            output = output + " (" + adder_str + ")"
        
        # Add modifiers
        output = output + self.modifier_string
        
        # Add END usage note
        if self.end_usage > 0:
            active_hero = EngineContext.active_hero()
            if active_hero:
                end_reserve = GenericObject.find_object_by_id(active_hero.powers, "ENDURANCERESERVE")
                if end_reserve:
                    all_mods = self.all_assigned_modifiers
                    end_reserve_mod = GenericObject.find_object_by_id(all_mods, "ENDRESERVEOREND")
                    prefs = EngineContext.prefs()
                    if not end_reserve_mod and not prefs.use_wg:
                        if self._use_end_reserve:
                            output = output + " (uses END Reserve)"
                        else:
                            output = output + " (uses Personal END)"
        
        return output
    
    @property
    def level_cost(self) -> float:
        """
        Get level cost based on HOWWELL and HOWWIDE adders.

    @level_cost.setter
    def level_cost(self, value) -> None:
        self._level_cost = value
        
        Returns:
            Level cost value
        """
        # Use parent if options exist
        if len(self.options) > 0:
            return super().level_cost
        
        cost = 0.0
        for adder in self.assigned_adders:
            if adder.xmlid == "HOWWELL":
                cost += adder.base_cost
            elif adder.xmlid == "HOWWIDE":
                cost += adder.base_cost
        
        if cost < 1.0:
            cost = 1.0
        
        return cost
    
    @property
    def old_column2_output(self) -> str:
        """
        Get old format column 2 output (when options exist).
        
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
        
        # Add selected option
        if self._selected_option:
            output = output + " ("
            output = output + self._selected_option.alias
            adder_str = self.adder_string
            if adder_str.strip():
                output = output + "; " + adder_str
            output = output + ")"
        
        # Add levels
        output = output + f" +{self._levels}/+{self._levels}d6"
        
        # Add modifiers
        output = output + self.modifier_string
        
        return output
    
    @property
    def total_cost(self) -> float:
        """
        Calculate total cost.
        
        Returns:
            Total cost value
        """
        cost = self.base_cost
        
        # Add level cost
        if self._level_value != 0.0:
            cost += (self._levels / self._level_value) * self.level_cost
            if self.level_cost < self._level_value:
                if cost > 0.0 and cost < 1.0:
                    cost = 1.0
                else:
                    cost = round_half_down(cost)
        
        # Add required adders (except HOWWELL and HOWWIDE)
        for adder in self.assigned_adders:
            if adder.is_required and adder.xmlid not in ["HOWWELL", "HOWWIDE"]:
                cost += adder.real_cost
        
        # Add optional adders with positive cost
        for adder in self.assigned_adders:
            if not adder.is_required and adder.real_cost > 0.0:
                cost += adder.real_cost
        
        # Apply min/max
        if cost < self._minimum_cost and self.min_set:
            cost = self._minimum_cost
        elif cost > self._max_cost and self.max_set:
            cost = self._max_cost
        
        # Add optional adders with negative cost
        for adder in self.assigned_adders:
            if not adder.is_required and adder.real_cost < 0.0:
                cost += adder.real_cost
        
        # Apply Automaton defense multiplier if applicable
        if "DEFENSE" in self.types:
            active_hero = EngineContext.active_hero()
            if active_hero:
                automaton = GenericObject.find_object_by_id(active_hero.powers, "AUTOMATON")
                if automaton and isinstance(automaton, Automaton):
                    selected_option = automaton.selected_option
                    if selected_option and selected_option.xmlid.upper().startswith("NOSTUN"):
                        cost *= automaton.defense_cost_multiplier
        
        return cost
    
    def _init(self, element) -> None:
        """Read this element. Was restore_from_save."""
        super()._init(element)
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        # Handle HOWWELL and HOWWIDE adders if options don't exist
        if (len(self.options) == 0 and 
            GenericObject.find_object_by_id(self.available_adders, "HOWWELL") and
            GenericObject.find_object_by_id(self.available_adders, "HOWWIDE")):
            
            how_well = GenericObject.find_object_by_id(self.available_adders, "HOWWELL")
            if GenericObject.find_object_by_id(self.assigned_adders, "HOWWELL"):
                how_well = GenericObject.find_object_by_id(self.assigned_adders, "HOWWELL")
            else:
                self.assigned_adders.append(how_well)
            
            how_wide = GenericObject.find_object_by_id(self.available_adders, "HOWWIDE")
            if GenericObject.find_object_by_id(self.assigned_adders, "HOWWIDE"):
                how_wide = GenericObject.find_object_by_id(self.assigned_adders, "HOWWIDE")
            else:
                self.assigned_adders.append(how_wide)
            
            # Parse OPTIONID or OPTION_ALIAS
            option_id = XMLUtility.get_value(element, "OPTIONID")
            option_alias = XMLUtility.get_value(element, "OPTION_ALIAS")
            
            if option_id and option_id.strip():
                # Parse option ID (format: HOWWIDE_ID;HOWWELL_ID)
                parts = option_id.split(";")
                if len(parts) == 2:
                    wide_id, well_id = parts
                else:
                    # Try comma separator
                    parts = option_id.split(",")
                    if len(parts) == 2:
                        wide_id, well_id = parts
                    else:
                        return
                
                # Set HOWWIDE option
                for option in how_wide.options:
                    if wide_id.startswith(option.xmlid):
                        if option_alias:
                            # Extract wide alias
                            alias_parts = option_alias.split(";")
                            if len(alias_parts) == 2:
                                wide_alias = alias_parts[0]
                                option.alias = wide_alias
                        how_wide.selected_option = option
                        break
                
                # Set HOWWELL option
                for option in how_well.options:
                    if well_id.endswith(option.xmlid):
                        if option_alias:
                            # Extract well alias
                            alias_parts = option_alias.split(";")
                            if len(alias_parts) == 2:
                                well_alias = alias_parts[1]
                                option.alias = well_alias
                        how_well.selected_option = option
                        break
            elif option_alias and option_alias.strip():
                # Parse OPTION (display name format)
                option_str = XMLUtility.get_value(element, "OPTION")
                if option_str:
                    # Try to match against display names
                    for option in how_wide.options:
                        if option_str.startswith(option.display):
                            how_wide.selected_option = option
                            break
                    
                    for option in how_well.options:
                        if option_str.endswith(option.display):
                            how_well.selected_option = option
                            break



