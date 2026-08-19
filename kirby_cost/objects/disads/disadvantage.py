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


from kirby_cost.objects.base import option_alias as _option_alias


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
    def for_xmlid(cls, xmlid: str) -> 'Disadvantage':
        """The class HD uses for this complication.

        Four complications print nothing like the generic one — Hunted names
        its hunter and orders three parenthesised clauses; Enraged leads with
        the word "Berserk"; Reputation and Susceptibility punctuate
        differently — and Java gives each its own class.

        This existed as `get_instance(element)` and the loader called it with
        None, so `XMLUtility.get_value(None, "XMLID")` found nothing and every
        one of them fell back to the generic Disadvantage. The four-way branch
        had never run. The loader already knows the xmlid at the call site;
        taking it directly removes the element it was never given.
        """
        key = (xmlid or "").strip().upper()
        if key == "ENRAGED":
            from kirby_cost.objects.disads.enraged import Enraged
            return Enraged()
        if key == "HUNTED":
            from kirby_cost.objects.disads.hunted import Hunted
            return Hunted()
        if key == "REPUTATION":
            from kirby_cost.objects.disads.reputation import Reputation
            return Reputation()
        if key == "SUSCEPTIBILITY":
            from kirby_cost.objects.disads.susceptibility import Susceptibility
            return Susceptibility()
        return cls()

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
    
    # ── How the four specialised complications differ ─────────────────
    #
    # Java gives Enraged, Hunted, Reputation and Susceptibility their own
    # getColumn2Output, and diffing them against this one shows the whole
    # difference is four small things. They are named here rather than
    # copied into four near-identical 150-line methods, which is what the
    # Java does and what makes the differences so easy to miss.

    #: Whether the adder loops advance their counter. Susceptibility's do
    #: not, so its `count == 1` branch can never fire and every separator
    #: falls through to the default.
    _counts_adders: bool = True
    #: Separator before the FIRST adder, and before every later one.
    #: Susceptibility swaps these two; Reputation uses ", " for the first
    #: adder in its required branch only.
    _first_adder_sep: str = " "
    _later_adder_sep: str = ", "
    _first_required_sep: str | None = None      # None = use _first_adder_sep
    #: Whether an already-open bracket makes the next one continue with "; "
    #: rather than nest. Reputation does this and drops the new bracket's
    #: opening "(" when it happens.
    _merges_brackets: bool = False
    #: Whether an adder's own displayInString flag is honoured in the adder
    #: loops. Enraged sets it False on BERSERK after printing it in the head,
    #: and relies on this to not print it twice.
    _honours_display_in_string: bool = False
    #: Whether the object's input is printed after the modifiers. Enraged
    #: prints it in the head instead.
    _input_after_modifiers: bool = True

    def _column2_head(self) -> str:
        """Anything this complication prints before its modifiers."""
        return ""

    def _adder_sep(self, count: int, parens: int, *, required: bool = False) -> str:
        """What goes between the previous clause and this adder."""
        if count == 1:
            if required and self._first_required_sep is not None:
                return self._first_required_sep
            return self._first_adder_sep
        if parens > 0:
            return self.adder_separator + " "
        return self._later_adder_sep

    def _adder_walk(self):
        """The adders to render, paired with their position in the TEMPLATE.

        Returns ``(walk, in_template)`` where *walk* is a list of
        ``(position, assigned_adder_or_None)`` in the template's declared
        order, and *in_template* is the set of xmlids the template offers —
        used by the custom-adder pass to skip what this loop already printed.

        With no template entry there is no order to walk, so the document's
        own order stands in.
        """
        from kirby_cost.objects.base import GenericObject
        order = getattr(self, "_template_adder_order", None)
        if not order:
            return ([(i + 1, a) for i, a in enumerate(self.assigned_adders)],
                    set())
        walk = [(pos, GenericObject.find_object_by_id(self.assigned_adders, xmlid))
                for pos, xmlid in enumerate(order, 1)]
        return walk, set(order)

    @property
    def column2_output(self) -> str:
        """
        Get the formatted output for column 2 display.
        
        Returns:
            Formatted string representation
        """
        output = self._alias
        output = output + ": "
        output = output + self._column2_head()

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
        if self._input_after_modifiers and self.input and self.input.strip():
            output = output + " " + self.input
        
        # Process adders
        paren_count = 0
        adder_count = 0
        
        # HD walks the TEMPLATE's adder list, not the character's. `count`
        # increments BEFORE the "did they buy it" check, so it is the adder's
        # position in the TEMPLATE — which decides both the order the clauses
        # print in and whether the `count == 1` branch fires. Hunted is where
        # the difference shows: its template lists NCI third and MOTIVATION
        # sixth, so HD prints "(Mo Pow; NCI; Harshly Punish)" where document
        # order gives "(Mo Pow; Harshly Punish; NCI)".
        #
        # `available_adders` is never populated by the loader, so this reads
        # the order the template itself declared (captured in apply_template).
        _walk, _in_template = self._adder_walk()
        for adder_count, assigned_adder in _walk:
            if assigned_adder is None:
                continue
            if not self._counts_adders:
                adder_count = 0
            if (self._honours_display_in_string
                    and not assigned_adder.display_in_string):
                continue
            
            # Handle required adders with selected options
            if assigned_adder.is_required:
                option_alias = _option_alias(assigned_adder)
                if option_alias and option_alias.strip():
                    if option_alias.strip().startswith("("):
                        if self._merges_brackets and paren_count > 0:
                            output = output + "; "
                            option_alias = option_alias.strip()[1:]
                        elif ")" not in option_alias:
                            paren_count += 1
                        output = output + " "
                    else:
                        output += self._adder_sep(adder_count, paren_count,
                                                  required=True)
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
                if self._merges_brackets and paren_count > 0:
                    output = output + "; "
                    adder_str = adder_str.strip()[1:]
                elif ")" not in adder_str:
                    paren_count += 1
                output = output + " "
            else:
                output += self._adder_sep(adder_count, paren_count)
            
            output = output + adder_str
        
        # Process assigned adders not in available list
        adder_count = 0
        for adder in self.assigned_adders:
            if self._counts_adders:
                adder_count += 1
            if self._honours_display_in_string and not adder.display_in_string:
                continue
            if adder.xmlid in _in_template:
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
                if self._merges_brackets and paren_count > 0:
                    output = output + "; "
                    adder_str = adder_str.strip()[1:]
                elif ")" not in adder_str:
                    paren_count += 1
                output = output + " "
            else:
                output += self._adder_sep(adder_count, paren_count)
            
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
