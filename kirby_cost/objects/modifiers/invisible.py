"""
Invisible modifier for kirby-cost.

Converted from com.hero.objects.modifiers.Invisible.java

Invisible modifier with extensive custom logic:
- getColumn2Output() - complex formatting for 6E vs pre-6E, sense groups
- included() - validates power types and checks for Visible limitation
- getAssignedAdders() - filters adders for mental powers
- getAvailableAdders() - filters adders for mental powers
- getOptions() - special handling for mental powers
- getSelectedOption() - calls getOptions() first
- setSelectedOption() - clears adders for FULL option
"""

from typing import List
from kirby_cost.objects.modifier import Modifier
from kirby_cost.objects.base import GenericObject


class Invisible(Modifier, xmlid="INVISIBLE"):
    """
    Invisible modifier.
    
    Power is invisible.
    
    Has extensive custom logic for formatting, validation, and adder handling.
    Different behavior for 6E vs pre-6E templates.
    """
    
    def __init__(self, element=None):
        """Initialize a Invisible modifier."""
        super().__init__()
        self.xmlid = self.XMLID
        if element is not None:
            self._init(element)
    
    def _is_6e_template(self) -> bool:
        """
        Check if current template is 6E.
        
        Returns:
            True if 6E template, False otherwise
        """
        # Java asks HeroDesigner.getActiveTemplate().is6E() (Invisible.java:291).
        # This used to return a hardcoded False, so the 5E-only "already
        # invisible" refusal fired under every 6E template.
        from kirby_cost.objects.base import is_6e
        return is_6e()
    
    def _is_mental_power_without_based_on_con(self, generic_object: GenericObject) -> bool:
        """
        Check if power is mental power without Based On CON or BOECV.
        
        Args:
            generic_object: The power to check
            
        Returns:
            True if mental power without Based On CON/BOECV
        """
        types = generic_object.types
        if not types or "MENTAL" not in types:
            return False
        
        # Check for Based On CON or BOECV modifiers
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "BASEDONCON") is not None:
            return False
        
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "BOECV") is not None:
            return False
        
        return True
    
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
        
        # Mental powers always allowed
        types = generic_object.types
        if types and "MENTAL" in types:
            return ""
        
        # For non-6E, can't apply if already invisible
        if not self._is_6e_template():
            # Check if power is already invisible
            # Note: Would need generic_object.is_visible() method
            # For now, check if it has base visible flag set to False
            if hasattr(generic_object, 'visible') and not generic_object.visible:
                # Check if it's made visible by modifiers
                if (GenericObject.find_object_by_id(
                    generic_object.assigned_modifiers, "BASEDONCON") is None and
                    GenericObject.find_object_by_id(
                    generic_object.assigned_modifiers, "COSTSEND") is None and
                    GenericObject.find_object_by_id(
                    generic_object.assigned_modifiers, "VISIBLE") is None):
                    return f"{generic_object.display} is already invisible."
        
        # Can't apply if Visible limitation is present
        if GenericObject.find_object_by_id(
            generic_object.assigned_modifiers, "VISIBLE") is not None:
            return f"{self.display} cannot be applied to a Power/ability with the Visible Limitation on it."
        
        return ""
    
    @property
    def assigned_adders(self) -> list:
        """
        Get assigned adders, filtering for mental powers (pre-6E only).
        
        Returns:
            List of assigned adders
        """
        if self._is_6e_template():
            return super().assigned_adders
        
        adders = super().assigned_adders
        progenitor = self.progenitor
        
        if progenitor and self._is_mental_power_without_based_on_con(progenitor):
            return []
        
        return adders

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    
    @property
    def available_adders(self) -> list:
        """
        Get available adders, filtering for mental powers (pre-6E only).
        
        Returns:
            List of available adders
        """
        if self._is_6e_template():
            return super().available_adders
        
        adders = super().available_adders
        progenitor = self.progenitor
        
        if progenitor and self._is_mental_power_without_based_on_con(progenitor):
            return []
        
        return adders
    
    @property
    def options(self) -> list:
        """
        Get options with special handling for mental powers.
        
        Returns:
            List of option adders
        """
        options = super().options
        progenitor = self.progenitor
        
        if (progenitor and self._is_mental_power_without_based_on_con(progenitor)):
            # Find MENTAL option and modify it
            for option in options:
                if option.xmlid == "MENTAL":
                    try:
                        # Clone the option
                        from copy import deepcopy
                        new_option = deepcopy(option)
                        new_option.alias = "Fully Invisible"
                        
                        # Adjust base cost if needed (pre-6E)
                        if not self._is_6e_template() and new_option.base_cost < 0.5:
                            new_option.base_cost = 0.5
                        
                        self._selected_option = new_option
                        return [new_option]
                    except (AttributeError, TypeError):
                        pass
        
        return options
    
    @property
    def selected_option(self):
        """
        Get selected option, calling getOptions() first.
        
        Returns:
            Selected option adder or None
        """
        self.options  # Ensure options are updated
        return self._selected_option
    
    @selected_option.setter
    def selected_option(self, adder) -> None:
        """
        Set selected option, clearing adders for FULL option.
        
        Args:
            adder: The option adder to select
        """
        self._selected_option = adder
        
        if adder and adder.xmlid == "FULL":
            # Clear assigned adders for FULL option
            from kirby_cost.objects.adder import Adder
            self.set_assigned_adders([])
    
    @property
    def column2_output(self) -> str:
        """``Invisible Power Effects (Can't be traced; +1/4)``.

        Ported from ``Invisible.getColumn2Output`` (6E branch). The option is
        the whole content — what about the power is hidden — and the generic
        modifier line dropped it, leaving "Invisible Power Effects (+1/4)":
        the cost of hiding something, without saying what.

        The two prefixes it strips are HD's: an option written "Obvious Power,
        Can't be traced" is answering a question the sheet has already asked,
        so only the answer is printed.

        EFFECTSTARGET and EFFECTSOTHER are read as a PAIR and rendered as one
        clause, because "invisible to the target" and "invisible to everyone
        else" are the same sentence when they agree and two when they do not.
        """
        from kirby_cost.objects.base import GenericObject, option_alias
        ret = self.alias or ""
        val = self.total_value
        adder_str = self.adder_string

        for mod in self.assigned_modifiers:
            ret += ", " + (mod.alias or "")
        ret += " ("

        option = (option_alias(self) or "").strip()
        for prefix in ("Obvious Power,", "Inobvious Power,"):
            if option.startswith(prefix):
                option = option[len(prefix):].strip()
                break
        ret += option

        target = GenericObject.find_object_by_id(self.assigned_adders, "EFFECTSTARGET")
        other = GenericObject.find_object_by_id(self.assigned_adders, "EFFECTSOTHER")
        if target is not None and other is not None:
            target.display_in_string = False
            other.display_in_string = False
            t_id = (getattr(target.selected_option, "xmlid", "") or "").upper()
            o_id = (getattr(other.selected_option, "xmlid", "") or "").upper()
            t_alias = (option_alias(target) or "").strip()
            o_alias = (option_alias(other) or "").strip()
            if t_id == "DEFAULT" and o_id != "DEFAULT":
                ret += f", effects of Power are {o_alias} to other characters"
            elif t_id != "DEFAULT" and o_id == "DEFAULT":
                ret += f", effects of Power are {t_alias} to target"
            elif t_id != "DEFAULT" and o_id != "DEFAULT":
                if t_id == o_id:
                    ret += (f", effects of Power are {t_alias} to both target "
                            "and other characters")
                else:
                    ret += (f", effects of Power are {t_alias} to target and "
                            f"{o_alias} to other characters")

        ret += "; "
        if adder_str.strip():
            ret += adder_str + "; "
        ret += self.get_fraction(val) + ")"
        return ret
    def _get_column2_output_6e(self) -> str:
        """Get column 2 output for 6E template."""
        string = ""
        string2 = ""
        string2 = string2 + self._alias
        d = self.total_value
        
        # Get adder string
        string = self._get_adder_string()
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string2 = string2 + ", " + modifier.alias
        
        string2 = string2 + " ("
        
        # Handle selected option alias
        selected_option = self._selected_option
        if selected_option:
            alias = selected_option.alias
            if alias.startswith("Obvious Power,"):
                string2 = string2 + alias[14:].strip()
            elif alias.startswith("Inobvious Power,"):
                string2 = string2 + alias[16:].strip()
            else:
                string2 = string2 + alias.strip()
            
            # Handle EFFECTSTARGET and EFFECTSOTHER adders
            effect_target = GenericObject.find_object_by_id(
                self.assigned_adders, "EFFECTSTARGET")
            effect_other = GenericObject.find_object_by_id(
                self.assigned_adders, "EFFECTSOTHER")
            
            if effect_target and effect_other:
                effect_target.display_in_string = False
                effect_other.display_in_string = False
                
                target_option = effect_target.selected_option
                other_option = effect_other.selected_option
                
                if target_option and other_option:
                    if target_option.xmlid == "DEFAULT":
                        if other_option.xmlid != "DEFAULT":
                            string2 = string2 + ", effects of Power are " + other_option.alias + " to other characters"
                    elif other_option.xmlid == "DEFAULT":
                        string2 = string2 + ", effects of Power are " + target_option.alias + " to target"
                    elif target_option.xmlid == other_option.xmlid:
                        string2 = string2 + ", effects of Power are " + target_option.alias + " to both target and other characters"
                    else:
                        string2 = string2 + (f", effects of Power are {target_option.alias} to target "
                                            f"and {other_option.alias} to other characters")
        
        string2 = string2 + "; "
        
        if string.strip():
            string2 = string2 + string + "; "
        
        string2 = string2 + self.get_fraction(d) + ")"
        
        return string2
    
    def _get_column2_output_pre6e(self) -> str:
        """Get column 2 output for pre-6E template."""
        string = ""
        string3 = ""
        string3 = string3 + self._alias
        string4 = ""
        
        selected_option = self._selected_option
        progenitor = self.progenitor
        
        # Determine invisibility description
        if (selected_option is None or selected_option.xmlid == "FULL" or
            (progenitor and self._is_mental_power_without_based_on_con(progenitor) and
             selected_option and selected_option.alias == "Fully Invisible")):
            string4 = "Fully Invisible"
        else:
            # Build sense list
            sense_list = []
            group_list = []
            
            if selected_option and selected_option.xmlid == "SINGLE":
                sense_list.append(selected_option.alias)
            elif selected_option:
                alias = selected_option.alias
                if alias.upper().find("GROUP") > 0:
                    group_name = alias[:alias.upper().find("GROUP")].strip()
                    group_list.append(group_name)
            
            # Process adders
            for adder in self.assigned_adders:
                if (adder.xmlid == "ADDITIONALSENSE" and adder.selected_option and
                    adder.selected_option.alias.strip()):
                    sense_list.append(adder.selected_option.alias)
                    adder.display_in_string = False
                elif (adder.xmlid == "ADDITIONALGROUP" and adder.selected_option and
                      adder.selected_option.alias.strip()):
                    group_alias = adder.selected_option.alias
                    if group_alias.upper().find("GROUP") > 0:
                        group_name = group_alias[:group_alias.upper().find("GROUP")].strip()
                    else:
                        group_name = group_alias
                    group_list.append(group_name)
                    adder.display_in_string = False
            
            # Sort lists
            sense_list.sort()
            group_list.sort()
            
            # Build description string
            desc = ""
            n = -1
            for sense in sense_list:
                n += 1
                if desc.strip():
                    desc = desc + ", "
                if n == len(sense_list) - 1 and len(group_list) == 0 and n > 0:
                    desc = desc + "and "
                desc = desc + sense
            
            n = -1
            for group in group_list:
                n += 1
                if desc.strip():
                    desc = desc + ", "
                if n == len(group_list) - 1 and len(sense_list) + len(group_list) > 1:
                    desc = desc + "and "
                desc = desc + group
                if n == len(group_list) - 1:
                    desc = desc + " Group"
                    if len(group_list) > 1:
                        desc = desc + "s"
            
            if desc.strip():
                string3 = "Invisible to " + desc
                string4 = ""
        
        d = self.total_value
        string = self._get_adder_string()
        
        # Add input
        if self.input and self.input.strip():
            if string3.strip():
                string3 = string3 + ":  "
            string3 = string3 + self.input
        
        # Add assigned modifiers
        for modifier in self.assigned_modifiers:
            string3 = string3 + ", " + modifier.alias
        
        string3 = string3 + " ("
        
        if string4.strip():
            string3 = string3 + string4 + "; "
        
        if self.comments.strip():
            string3 = string3 + self.comments + "; "
        
        string3 = string3 + self.get_fraction(d) + ")"
        
        if string.strip():
            if string3.strip():
                string3 = string3 + ", "
            string3 = string3 + string
        
        return string3
    
    def _get_adder_string(self) -> str:
        """
        Get formatted string for adders.
        
        Returns:
            Formatted adder string
        """
        adder_string = ""
        for adder in self.assigned_adders:
            if not adder.is_selected or not adder.display_in_string:
                continue
            
            if adder_string:
                adder_string = adder_string + ", "
            
            adder_output = adder.column2_output
            if adder_output.strip():
                adder_string = adder_string + adder_output
            else:
                adder_string = adder_string + adder.alias
        
        return adder_string
