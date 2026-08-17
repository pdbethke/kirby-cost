"""
Sense Affecting Power class for kirby-cost.

Converted from com.hero.objects.powers.SenseAffectingPower.java

Base class for powers that affect senses (Invisibility, Flash, Darkness, Images, etc.).
"""

from typing import List, Optional
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.base import GenericObject


class SenseAffectingPower(Power):
    """
    Sense Affecting Power.
    
    Base class for powers that affect senses (Invisibility, Flash, Darkness, Images).
    Handles targeting vs non-targeting costs, sense groups, and individual senses.
    """
    
    def __init__(self):
        """Initialize a Sense Affecting Power."""
        super().__init__()
        self._duration = "INSTANT"
        
        # Cost attributes
        self.nontargeting_cost: float = -1.0
        self.nontargeting_group_cost: float = -1.0
        self.nontargeting_half_cost: float = -1.0
        self.nontargeting_sense_cost: float = -1.0
        self.targeting_cost: float = -1.0
        self.targeting_group_cost: float = -1.0
        self.targeting_half_cost: float = -1.0
        self.targeting_sense_cost: float = -1.0
        
        # Flags
        self.old_method: bool = False
        self.restoring: bool = False
        
        # Cached results
        self._available_adders_saver: Optional[List[Adder]] = None
        self._options_saver: Optional[List[Adder]] = None
        self._selected_option_saver: Optional[Adder] = None
    
    @property
    def assigned_adders(self) -> List[Adder]:
        """Get assigned adders with sense-specific processing."""
        result = list(super().assigned_adders)

        if self.old_method:
            return result

        # Stub: would process GROUP, ADDITIONAL_GROUP, ADDITIONAL_SENSE, SINGLE adders
        # and convert them to proper sense/group adders with appropriate costs

        self._assigned_adders = result
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

        if self.old_method:
            return result

        # Stub: would add sense groups and individual senses as available adders
        # based on targeting/non-targeting costs

        self._available_adders_saver = result
        return result
    
    @property
    def options(self) -> List[Adder]:
        """Get options for this sense-affecting power."""
        result: List[Adder] = []

        # Stub: would build options from sense groups
        # based on targeting_cost and nontargeting_cost

        if len(result) == 0:
            self.old_method = True
            self._options_saver = super().options
            return self._options_saver

        result.sort()
        self._options_saver = result
        return result
    
    @property
    def selected_option(self) -> Optional[Adder]:
        """Get selected option."""
        option = self._selected_option

        if option is None and not self.restoring:
            options = self.options
            if len(options) > 0:
                option = options[0]

        if self.old_method or option is None:
            return option

        # Stub: would process selected option for sense groups

        self._selected_option_saver = option
        return option
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        # Build sense group and sense lists
        groups: List[str] = []
        senses: List[str] = []
        
        # Stub: would extract groups and senses from assigned adders
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        output += " to "
        
        # Add groups
        for i, group in enumerate(groups):
            if i > 0 and i < len(groups) - 1:
                output += ", "
            elif i == len(groups) - 1 and i > 0:
                output += " and "
            output += group
        
        if len(groups) > 1:
            output += " Groups"
        elif len(groups) == 1:
            output += " Group"
        
        # Add senses
        for i, sense in enumerate(senses):
            if i < len(senses) - 1:
                output += ", "
            else:
                output += " and "
            output += sense
        
        output += " " + self.damage_display
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += ", " + adder_str
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    def translate_sense(self, sense_name: str) -> str:
        """
        Translate old sense names to new XML IDs.
        
        Args:
            sense_name: Old sense name
            
        Returns:
            Translated XML ID
        """
        if self.old_method:
            return sense_name
        
        translations = {
            "HEARING": "NORMALHEARING",
            "SONAR": "ACTIVESONAR",
            "MA": "MENTALAWARENESS",
            "MS": "MINDSCAN",
            "RP": "RADIOPERCEPTION",
            "RT": "RADIOPERCEIVETRANSMIT",
            "RADIOTRANSMISSION": "RADIOPERCEIVETRANSMIT",
            "SIGHT": "NORMALSIGHT",
            "SMELL": "NORMALSMELL",
            "TASTE": "NORMALTASTE",
            "TOUCH": "NORMALTOUCH",
            "IR": "INFRAREDPERCEPTION",
            "IRPERCEPTION": "INFRAREDPERCEPTION",
            "NRAY": "NRAYPERCEPTION",
            "SENSORYTALENTS": "DANGER_SENSE",
            "UV": "ULTRAVIOLETPERCEPTION",
            "UVPERCEPTION": "ULTRAVIOLETPERCEPTION",
            "ULTRASONIC": "ULTRASONICPERCEPTION",
        }
        
        return translations.get(sense_name, sense_name)
    
    @selected_option.setter
    def selected_option(self, adder: Optional[Adder]) -> None:
        """Set selected option."""
        if self.old_method or adder is None:
            self._selected_option = adder
            return
        
        # Stub: would handle GROUP/ADDITIONAL_GROUP/SENSEGROUP adders
        # and convert them to proper sense group options
        
        self._selected_option = adder
    
    @property
    def adder_string(self) -> str:
        """Get adder string (stub)."""
        return ""
    
    @property
    def modifier_string(self) -> str:
        """Get modifier string (stub)."""
        return ""

