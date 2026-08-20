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
    
    @property
    def column2_output(self) -> str:
        """``Invisibility to Sight Group``.

        Ported from ``SenseAffectingPower.getColumn2Output``. A power that
        acts on the senses says which ones, and the shape is "<alias> to
        <groups>" — Invisibility had no column2_output of its own and
        inherited Power's, which names the power and then hands the group to
        the adder list, where it is not.

        Flash, Flash Defense and Images override this: they put the groups
        FIRST. Everything else in the family reads this one.

        The placeholder is HD's: a sense-affecting power with no group at all
        prints "[Unknown]" rather than nothing, because the sentence needs an
        object.
        """
        ret = self.alias or ""
        prefix = self._sense_prefix(default="[Unknown]")
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        ret += " to " + prefix
        ret += " " + self.damage_display
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        adders = self.adder_string
        if adders.strip():
            ret += f", {adders}"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret

    def _sense_prefix(self, default: str = "") -> str:
        return sense_prefix(self, default)

    def _sense_prefix_impl(self, default: str = "", joiner: str = " and ") -> str:
        """``Sight Group``, ``Sight and Hearing Groups``, ``Sight Group and Normal Smell``.

        Shared by Flash, Flash Defense and Images, which all put what they
        AFFECT in front of what they are: HD writes "Sight Group Flash 4d6",
        not "Flash 4d6 Sight Group". Ported from the identical opening of all
        three getColumn2Output methods.

        The word "Group" is stripped from each option's alias and re-added once
        at the end, pluralised, so two groups read "Sight and Hearing Groups"
        rather than "Sight Group and Hearing Group". Every adder that
        contributes a group or a sense is marked not-to-be-printed, because
        this line has just named it.
        """
        from kirby_cost.objects.base import GenericObject, option_alias
        from kirby_cost.objects.powers.sense import Sense

        def strip_group(text: str) -> str:
            upper = (text or "").upper()
            i = upper.find("GROUP")
            return text[:i].strip() if i > 0 else (text or "")

        groups: list = []
        senses: list = []
        first = (option_alias(self) or "").strip()
        if first or self._selected_option is not None:
            groups.append(strip_group(first))
        elif default:
            groups.append(strip_group(default))

        all_senses = Sense.all_senses()
        for ad in self.assigned_adders:
            if ad.xmlid == "ADDITIONAL_GROUP":
                ad.display_in_string = False
                groups.append(strip_group((option_alias(ad) or "").strip()))
            elif (ad.xmlid or "").endswith("GROUP"):
                ad.display_in_string = False
                groups.append(strip_group(ad.alias or ""))
            elif ad.xmlid == "ADDITIONAL_SENSE":
                ad.display_in_string = False
                senses.append((option_alias(ad) or "").strip())
            elif GenericObject.find_object_by_id(all_senses, ad.xmlid) is not None:
                ad.display_in_string = False
                senses.append(ad.alias or "")

        ret = ""
        for i, g in enumerate(groups):
            if 0 < i < len(groups) - 1:
                ret += ", "
            elif i == len(groups) - 1 and i > 0:
                # Clairsentience capitalises this one word — "Hearing And
                # Sight Groups" — and nothing else in the family does. It
                # looks like a typo in HD and it is what the oracle prints.
                ret += joiner
            ret += g
        ret += " Groups" if len(groups) > 1 else " Group"
        for i, sense in enumerate(senses):
            ret += ", " if i < len(senses) - 1 else " and "
            ret += sense
        return ret

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
    
    



def sense_prefix(obj, default: str = "", joiner: str = " and ") -> str:
    """``Sight Group``, ``Sight and Hearing Groups`` — for anything that names
    the senses it acts on.

    Shared rather than inherited: Clairsentience extends Power, not
    SenseAffectingPower, and needs exactly the same grouping.
    """
    return SenseAffectingPower._sense_prefix_impl(obj, default, joiner)
