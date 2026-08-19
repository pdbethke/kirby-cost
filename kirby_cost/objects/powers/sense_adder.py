"""
Sense Adder power class for kirby-cost.

Converted from com.hero.objects.powers.SenseAdder.java

Base class for sense adders that modify senses.
"""

from typing import List, Optional
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.base import GenericObject


class SenseAdder(Power):
    """
    Sense Adder power.
    
    Base class for adders that modify senses (Telescopic, Rapid, etc.).
    """
    
    # Static class variables
    _all_sense_adders: List['SenseAdder'] = []
    _templates_initialized: bool = False

    # 6E sense adder templates from Main6E.hdt.
    # Each entry maps xmlid -> (group_cost, sense_cost, all_cost).
    # -1 means "not applicable".
    _TEMPLATE_DATA = {
        "ADJACENTFIXED":       (3, 2, -1),
        "ADJACENT":            (5, 3, -1),
        "CONCEALED":           (1, 1, -1),
        "MAKEASENSE":          (-1, 2, -1),
        "DIMENSIONALSINGLE":   (10, 5, -1),
        "DIMENSIONALGROUP":    (20, 10, -1),
        "DIMENSIONALALL":      (25, 15, -1),
        "DISCRIMINATORY":      (10, 5, -1),
        "ANALYZESENSE":        (10, 5, -1),
        "ENHANCEDPERCEPTION":  (2, 1, 3),
        "INCREASEDARC240":     (5, 2, 10),
        "INCREASEDARC360":     (10, 5, 25),
        "MICROSCOPIC":         (5, 3, -1),
        "PARTIALLYPENETRATIVE":(10, 5, -1),
        "PENETRATIVE":         (15, 10, -1),
        "RANGE":               (10, 5, -1),
        "RAPID":               (5, 3, -1),
        "TARGETINGSENSE":      (20, 10, -1),
        "TELESCOPIC":          (3, 1, -1),
        "TRACKINGSENSE":       (10, 5, -1),
        "TRANSMIT":            (5, 2, -1),
    }
    
    def __init__(self, xmlid: Optional[str] = None):
        """Initialize a Sense Adder."""
        super().__init__()
        self.xmlid = xmlid or "SENSEADDER"
        self._duration = "CONSTANT"
        
        # Cost attributes
        self.all_cost: int = -1
        self.group_cost: int = -1
        self.sense_cost: int = -1
        
        # Cached results
        self._assigned_adders_saver: Optional[List[Adder]] = None
        self._automatic_adders_saver: Optional[List[Adder]] = None
        self._available_adders_saver: Optional[List[Adder]] = None
        self._options_saver: Optional[List[Adder]] = None
        self._sense_groups_saver: Optional[List[str]] = None
        self._senses_saver: Optional[List[str]] = None
        
        self.selected_option_lock: bool = False

        # Whether sense groups exist to be bought. Java resolves a sense
        # adder's option against the global SenseGroup registry, which a
        # loaded template fills; a character that names no template leaves it
        # empty, so nothing can be bought "for a group" however the option is
        # spelled, and the single-sense rate applies.
        self.sense_groups_defined: bool = True

        # Add to static list if valid
        if self.xmlid and self.xmlid.strip() and self.included_in_template():
            # Remove existing if present
            existing = GenericObject.find_object_by_id(
                SenseAdder._all_sense_adders, self.xmlid)
            if existing:
                SenseAdder._all_sense_adders.remove(existing)
            SenseAdder._all_sense_adders.append(self)
    
    @classmethod
    def _ensure_templates(cls) -> None:
        """Initialise template SenseAdder entries from Main6E.hdt data (once)."""
        if cls._templates_initialized:
            return
        cls._templates_initialized = True
        for xmlid, (group_cost, sense_cost, all_cost) in cls._TEMPLATE_DATA.items():
            existing = GenericObject.find_object_by_id(cls._all_sense_adders, xmlid)
            if existing:
                continue
            sa = SenseAdder(xmlid)
            sa.group_cost = group_cost
            sa.sense_cost = sense_cost
            sa.all_cost = all_cost

    @classmethod
    def all_sense_adders(cls) -> List['SenseAdder']:
        """Get all sense adders."""
        cls._ensure_templates()
        return cls._all_sense_adders
    
    @classmethod
    def detect_display(cls, detect) -> str:
        """
        Get display string for Detect sense.
        
        Args:
            detect: Detect power instance
        """
        display = detect.alias
        if detect.selected_option:
            option_display = detect.selected_option.alias
            # Check for EXTRA adders
            extra_adders = []
            for adder in detect.assigned_adders:
                if adder.xmlid == "EXTRA":
                    extra_adders.append(adder.alias)
                    adder.display_in_string = False
            
            if extra_adders:
                option_display += ", " + ", ".join(extra_adders)
                # Replace last comma with "and"
                if ", " in option_display:
                    last_comma = option_display.rfind(", ")
                    option_display = (option_display[:last_comma] + 
                                    " and" + 
                                    option_display[last_comma+1:])
            
            display += " " + option_display
        
        return display
    
    @property
    def sense_groups(self) -> List[str]:
        """Get sense groups this adder applies to."""
        result: List[str] = []

        # Check selected option (or fall back to option_id if selected_option
        # was not resolved — common for SenseAdder powers loaded from HDC)
        opt_xmlid = None
        if self._selected_option:
            opt_xmlid = self._selected_option.xmlid
        elif getattr(self, 'option_id', None):
            opt_xmlid = self.option_id

        if opt_xmlid:
            if opt_xmlid == "ALL":
                # Get all groups
                from kirby_cost.objects.powers.sense_group import SenseGroup
                for group in SenseGroup.all_groups():
                    result.append(group.xmlid)
            elif opt_xmlid.endswith("GROUP"):
                result.append(opt_xmlid)
        
        # Check assigned adders (use super() to avoid recursion with
        # get_assigned_adders which calls get_sense_groups)
        for adder in super().assigned_adders:
            if adder.xmlid == "GROUP" and adder.selected_option:
                if adder.selected_option.xmlid not in result:
                    result.append(adder.selected_option.xmlid)
            elif adder.xmlid.endswith("GROUP") and adder.xmlid not in result:
                result.append(adder.xmlid)

        self._sense_groups_saver = result
        return result

    @property
    def senses(self) -> List[str]:
        """Get individual senses this adder applies to."""
        result: List[str] = []

        # Check selected option
        if self._selected_option and not self._selected_option.xmlid.endswith("GROUP"):
            result.append(self._selected_option.xmlid)

        # Check assigned adders (use super() to avoid recursion)
        for adder in super().assigned_adders:
            if adder.xmlid.endswith("GROUP"):
                continue
            if adder.selected_option:
                if adder.selected_option.xmlid not in result:
                    result.append(adder.selected_option.xmlid)
            elif adder.xmlid not in result:
                result.append(adder.xmlid)
        
        self._senses_saver = result
        return result
    
    @property
    def assigned_adders(self) -> List[Adder]:
        """Get assigned adders with sense-specific filtering."""
        result = list(super().assigned_adders)
        sense_groups = self.sense_groups
        
        if sense_groups is None:
            sense_groups = []
        
        # Stub: would filter adders based on sense group membership
        # and built-in sense adders
        
        self._assigned_adders_saver = result
        return result

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value


    @property
    def available_adders(self) -> List[Adder]:
        """Get available adders with sense-specific additions."""
        result = list(super().available_adders)
        assigned = self.assigned_adders
        
        # Stub: would add automatic adders based on sense groups and senses
        
        result.sort()
        self._available_adders_saver = result
        return result

    @property
    def options(self) -> List[Adder]:
        """Get options for this sense adder."""
        result = list(super().options)
        
        # Add "ALL" option if all_cost > 0
        if self.all_cost > 0:
            all_adder = Adder()
            all_adder.xmlid = "ALL"
            if self._level_value > 0.0:
                all_adder.level_cost = float(self.all_cost)
            else:
                all_adder.base_cost = float(self.all_cost)
            all_adder.display = "all Sense Groups"
            all_adder.alias = "all Sense Groups"
            result.append(all_adder)
        
        # Stub: would add group and sense options
        
        result.sort()
        self._options_saver = result
        return result
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        # Build "with" string
        with_str = " with "
        if self._selected_option:
            with_str += self._selected_option.alias
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                with_str += ", " + adder_str
                # Replace last comma with "and"
                if ", " in with_str:
                    last_comma = with_str.rfind(", ")
                    with_str = (with_str[:last_comma] + 
                              " and" + 
                              with_str[last_comma+1:])
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                with_str += adder_str
                # Replace last comma with "and"
                if ", " in with_str:
                    last_comma = with_str.rfind(", ")
                    with_str = (with_str[:last_comma] + 
                              " and" + 
                              with_str[last_comma+1:])
        
        if with_str.strip() != "with":
            output += with_str
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def selected_option(self) -> Optional[Adder]:
        """Get the selected option."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, adder: Optional[Adder]) -> None:
        """Set selected option and update costs."""
        # Stub: would update Power.last_sense_edit
        self._selected_option = adder
        
        if adder:
            # Reset costs
            self._base_cost = 0.0
            self._level_cost = 0.0
            
            if adder.xmlid == "ALL":
                if self._level_value > 0.0:
                    self._level_cost = float(self.all_cost)
                else:
                    self._base_cost = float(self.all_cost)
            # A *GROUP option takes the group rate, full stop. There used to
            # be an extra `and self.sense_groups_defined` here, on the theory
            # that a character declaring no TEMPLATE has no sense groups and so
            # must fall back to the single-sense rate (UNDEAD_GHOUL). That was
            # fitted to a broken oracle: the headless fork could not resolve
            # builtIn. template names, so even the Main6E bootstrap loaded
            # without the parent chain that registers the groups. With the
            # oracle fixed (2026-08-17) the GHOUL takes the group rate like
            # everyone else — 3 levels x 2 = 6, not 3.
            elif adder.xmlid.endswith("GROUP") and self.group_cost > 0:
                if self._level_value > 0.0:
                    self._level_cost = float(self.group_cost)
                else:
                    self._base_cost = float(self.group_cost)
            elif self._level_value > 0.0:
                self._level_cost = float(self.sense_cost)
            else:
                self._base_cost = float(self.sense_cost)
    
    def included_in_template(self) -> bool:
        """Check if included in template (stub)."""
        return True
    
    @property
    def adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    

