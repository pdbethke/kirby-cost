"""
Disadvantage class for kirby-cost.

Converted from com.hero.objects.disads.Disadvantage.java

Disadvantages (Complications) provide extra character points.
"""

from typing import Optional, List
from kirby_cost.objects.base import GenericObject
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.modifier import Modifier
from kirby_cost.core.context import EngineContext
from kirby_cost.io.xml_utility import XMLUtility


def _option_alias(adder) -> str:
    """What HD would print for this adder's selected option.

    HD reads ``getSelectedOption().getAlias()`` — the template's option object.
    This loader never resolves that object for adders, so ``selected_option`` is
    None on every one of them and the display code below, which is a faithful
    port, had nothing to read.

    The document states the same string outright. HD writes OPTION_ALIAS from
    the option it selected, so the file's own value IS the option's alias:
    ``OPTION_ALIAS="(Frequently"`` on a Physical Complication's OCCURS adder.
    Using it is not an approximation; it is the same string by a shorter route,
    and it keeps this a display-only change. Resolving the option objects
    properly belongs in the loader, where it would also touch cost paths
    (Skill reads ``available_adders``), and that is a separate job with its own
    parity risk.
    """
    option = getattr(adder, "selected_option", None)
    if option is not None and (option.alias or "").strip():
        return option.alias
    return getattr(adder, "source_option_alias", "") or ""


class Disadvantage(GenericObject):
    """
    Disadvantage (Complication) class.
    
    Disadvantages provide extra character points and have special
    cost calculation and display formatting.
    """
    
    def __init__(self, element=None):
        """
        Initialize a Disadvantage.
        
        Args:
            element: Optional XML element for initialization
        """
        super().__init__()
        self.adder_separator: str = ";"
        
        if element is not None:
            self._init(element)
    
    @classmethod
    def get_instance(cls, element) -> 'Disadvantage':
        """
        Factory method to create the appropriate Disadvantage type.
        
        Args:
            element: XML element containing disadvantage data
            
        Returns:
            Appropriate Disadvantage subclass instance
        """
        xmlid = XMLUtility.get_value(element, "XMLID")
        if not xmlid:
            return cls(element)
        
        xmlid_upper = xmlid.strip().upper()
        
        # Import specific types
        if xmlid_upper == "ENRAGED":
            from kirby_cost.objects.disads.enraged import Enraged
            return Enraged(element)
        elif xmlid_upper == "HUNTED":
            from kirby_cost.objects.disads.hunted import Hunted
            return Hunted(element)
        elif xmlid_upper == "REPUTATION":
            from kirby_cost.objects.disads.reputation import Reputation
            return Reputation(element)
        elif xmlid_upper == "SUSCEPTIBILITY":
            from kirby_cost.objects.disads.susceptibility import Susceptibility
            return Susceptibility(element)
        
        return cls(element)
    
    def included_in_template(self) -> bool:
        """
        Check if this disadvantage should be included based on source preferences.
        
        Returns:
            True if included, False otherwise
        """
        prefs = EngineContext.prefs()
        sources = prefs.sources
        
        if len(sources) > 0:
            for source in sources:
                if source in self._sources:
                    return True
            return False
        
        return True
    
    def allows_other_modifiers(self) -> bool:
        """
        Check if this disadvantage allows other modifiers.
        
        Returns:
            True if 6E template, False otherwise
        """
        template = EngineContext.active_template()
        if template:
            # Would check if template is 6E
            return True
        return False
    
    @property
    def column2_output(self) -> str:
        """
        Get the formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        output = output + ": "
        
        # Process modifiers
        modifier_count = 0
        for modifier in self.assigned_modifiers:
            modifier_str = ""
            if modifier_count > 0:
                modifier_str = ", "
            else:
                modifier_str = " "
            
            modifier_value = modifier.total_value
            
            # Process adders within modifier
            adder_str = ""
            for adder in modifier.assigned_adders:
                if len(adder_str) > 0:
                    adder_str = adder_str + ", "
                adder_str = adder_str + adder.alias
                modifier_value -= adder.base_cost
            
            # Add modifier input
            if modifier.input and modifier.input.strip():
                if modifier_str.strip():
                    modifier_str = modifier_str + ":  "
                modifier_str = modifier_str + modifier.input
            
            # Add nested modifiers
            for nested_mod in modifier.assigned_modifiers:
                modifier_str = modifier_str + ", " + nested_mod.alias
            
            # Add selected option
            if modifier.selected_option:
                modifier_str = modifier_str + modifier.selected_option.alias
            
            # Add adder string
            if adder_str.strip():
                if modifier_str.strip():
                    modifier_str = modifier_str + ", "
                modifier_str = modifier_str + adder_str
            
            if modifier_str.strip():
                output = output + modifier_str
                modifier_count += 1
        
        # Add input
        if self.input and self.input.strip():
            output = output + " " + self.input
        
        # Process adders
        paren_count = 0
        adder_count = 0
        
        # HD walks the TEMPLATE's adder list so that `adder_count` counts
        # template position, including adders this character did not buy. That
        # list is empty here — the loader never populates it — so the document's
        # own order stands in. It agrees wherever a character bought every adder
        # its template offers, which the corpus says is the normal case; where
        # it does not, the ledger will say so rather than this pretending.
        _available = self.available_adders or self.assigned_adders
        for adder in _available:
            adder_count += 1
            if adder not in self.assigned_adders:
                continue

            assigned_adder = self.assigned_adders[self.assigned_adders.index(adder)]
            
            # Handle required adders with selected options
            if assigned_adder.is_required:
                option_alias = _option_alias(assigned_adder)
                if option_alias and option_alias.strip():
                    if option_alias.strip().startswith("("):
                        output = output + " "
                        if ")" not in option_alias:
                            paren_count += 1
                    else:
                        if adder_count == 1:
                            output = output + " "
                        elif paren_count > 0:
                            output = output + self.adder_separator + " "
                        else:
                            output = output + ", "
                    output = output + option_alias
                    continue
            
            if assigned_adder.is_required:
                continue
            
            # Handle optional adders
            adder_str = assigned_adder.alias
            _opt = _option_alias(assigned_adder)
            if _opt:
                if adder_str.strip():
                    adder_str = adder_str + ":  "
                adder_str = adder_str + _opt
            
            if assigned_adder.input and assigned_adder.input.strip():
                if adder_str.strip():
                    adder_str = adder_str + ":  "
                adder_str = adder_str + assigned_adder.input
            
            if not adder_str.strip():
                continue
            
            if adder_str.strip().startswith("("):
                output = output + " "
                if ")" not in adder_str:
                    paren_count += 1
            else:
                if adder_count == 1:
                    output = output + " "
                elif paren_count > 0:
                    output = output + self.adder_separator + " "
                else:
                    output = output + ", "
            
            output = output + adder_str
        
        # Process assigned adders not in available list
        adder_count = 0
        for adder in self.assigned_adders:
            adder_count += 1
            if adder in _available:
                continue
            
            adder_str = adder.alias
            _opt = _option_alias(adder)
            if _opt:
                if adder_str.strip():
                    adder_str = adder_str + ":  "
                adder_str = adder_str + _opt
            
            if adder.input and adder.input.strip():
                if adder_str.strip():
                    adder_str = adder_str + ":  "
                adder_str = adder_str + adder.input
            
            if not adder_str.strip():
                continue
            
            if adder_str.strip().startswith("("):
                output = output + " "
                if ")" not in adder_str:
                    paren_count += 1
            else:
                if adder_count == 1:
                    output = output + " "
                elif paren_count > 0:
                    output = output + self.adder_separator + " "
                else:
                    output = output + ", "
            
            output = output + adder_str
        
        # Close parentheses
        while paren_count > 0:
            output = output + ")"
            paren_count -= 1
        
        # Remove trailing colon
        if output.strip().endswith(":"):
            output = output.strip()
            output = output[:-1]
        
        return output
    
    def _init(self, element) -> None:
        """Initialize from XML element."""
        super()._init(element)
        
        adder_sep = XMLUtility.get_value(element, "ADDERSEPARATOR")
        if adder_sep:
            self.adder_separator = adder_sep
    
    def get_save_xml(self):
        """Get XML element for saving."""
        element = super().get_save_xml()
        element.tag = "DISAD"
        return element
    
    @property
    def real_cost_pre_list(self) -> float:
        """Zero-cost complications have real_cost 0, not the minimum-1 that powers get."""
        if self.active_cost == 0.0:
            return 0.0
        return super().real_cost_pre_list

    @property
    def total_cost(self) -> float:
        """
        Calculate total cost for this disadvantage.
        
        Disadvantages calculate cost as:
        - Base cost
        - Plus level costs
        - Plus required adders
        - Plus optional adders
        - Apply min/max limits
        
        Returns:
            Total cost (negative value for disadvantages)
        """
        self.enhancer_applied = None
        
        cost = self.base_cost
        
        # Add level costs
        if self._level_value != 0.0:
            cost += float(self._levels) / self._level_value * self._level_cost
        
        # Add required adders first
        for adder in self.assigned_adders:
            if adder.is_required:
                cost += adder.real_cost
        
        # Add optional adders
        for adder in self.assigned_adders:
            if not adder.is_required:
                cost += adder.real_cost
        
        # Apply min/max limits
        if cost < self._minimum_cost and self.min_set:
            cost = self._minimum_cost
        elif cost > self._max_cost and self.max_set:
            cost = self._max_cost
        
        return cost
