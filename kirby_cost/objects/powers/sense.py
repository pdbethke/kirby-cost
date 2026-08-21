"""
Sense power class for kirby-cost.

Converted from com.hero.objects.powers.Sense.java

Base class for all senses (Detect, Radar, Nightvision, etc.).
"""

from typing import List, Optional
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.adder import Adder
from kirby_cost.objects.base import GenericObject


class Sense(Power):
    """
    Sense power.
    
    Base class for all senses in Hero Designer.
    """

    def to_build_dict(self) -> dict:
        d = super().to_build_dict()
        if getattr(self, "group_id", ""):
            d["group"] = self.group_id
        if getattr(self, "active", False):
            d["sense_active"] = True
        provides = list(getattr(self, "sense_adders", []) or [])
        if provides:
            d["provides"] = provides
        return d

    
    # Static class variables
    _all_senses: List['Sense'] = []
    _built_in_senses: List['Sense'] = []
    
    def __init__(self, xmlid: Optional[str] = None):
        """Initialize a Sense."""
        super().__init__()
        self.xmlid = xmlid or "SENSE"
        self._duration = "CONSTANT"
        
        # Sense attributes
        self.active: bool = False
        self.active_selectable: bool = False
        self.allow_any_group: bool = True
        self.allow_sense_modifiers: bool = True
        
        # Group association
        self._group: Optional['SenseGroup'] = None
        self.group_id: Optional[str] = None
        
        # Sense adders
        self.sense_adders: List[str] = []

        # False when the character declared no TEMPLATE: HD registers sense
        # groups during template load, so without one there are no groups for
        # a capability to be provided by. Set by the loader; see total_cost.
        self.sense_groups_defined: bool = True
        
        # Cached results
        self._assigned_adders_saver: Optional[List[Adder]] = None
        self._available_adders_saver: Optional[List[Adder]] = None
        self._built_in_sense_adders_last_id: int = 0
        self._built_in_sense_adders_saver: Optional[List[str]] = None
        self._sense_modifiers_saver: Optional[List[str]] = None
        
        # Add to static list if valid
        if self.xmlid and self.xmlid.strip() and self._display and self._display.strip() and self.included_in_template:
            # Remove existing if present
            existing = GenericObject.find_object_by_id(Sense._all_senses, self.xmlid)
            while existing:
                Sense._all_senses.remove(existing)
                existing = GenericObject.find_object_by_id(Sense._all_senses, self.xmlid)
            Sense._all_senses.append(self)
    
    #: The xmlids the template defines as <SENSE>, which is what Java's
    #: static Sense registry holds. _all_senses only ever receives senses
    #: this engine actually constructs, and it constructs none from the
    #: template, so it is empty for every character.
    _template_sense_xmlids: frozenset = frozenset()

    @classmethod
    def set_template_sense_xmlids(cls, xmlids) -> None:
        cls._template_sense_xmlids = frozenset(xmlids or ())

    @classmethod
    def is_sense_xmlid(cls, xmlid: str) -> bool:
        """Java's ``findObjectByID(Sense.getAllSenses(), xmlid) != null``."""
        if not xmlid:
            return False
        if GenericObject.find_object_by_id(cls._all_senses, xmlid) is not None:
            return True
        return xmlid in cls._template_sense_xmlids

    @classmethod
    def clear(cls) -> None:
        """Clear all senses."""
        cls._all_senses.clear()
        cls._built_in_senses.clear()
    
    @classmethod
    def all_senses(cls) -> List['Sense']:
        """Get all senses."""
        return cls._all_senses
    
    @classmethod
    def built_in_senses(cls) -> List['Sense']:
        """Get built-in senses."""
        return cls._built_in_senses
    
    @classmethod
    def owned_senses(cls) -> List['Sense']:
        """Get senses owned by the active hero."""
        result: List['Sense'] = []
        result.extend(cls._built_in_senses)

        # Stub: would check active hero's talents, powers, and equipment
        # for senses and add them to result

        return result
    
    @classmethod
    def sense_by_id(cls, xmlid: str) -> Optional['Sense']:
        """Get a sense by XML ID."""
        for sense in cls.all_senses():
            if sense.xmlid == xmlid:
                return sense
        return None
    
    def allow_sense_modifiers(self) -> bool:
        """Check if this sense allows sense modifiers."""
        return self.allow_sense_modifiers
    
    @property
    def group(self) -> Optional['SenseGroup']:
        """Get the sense group this sense belongs to."""
        if self._group is None:
            from kirby_cost.objects.powers.sense_group import SenseGroup
            groups = SenseGroup.all_groups()
            for group in groups:
                if group.xmlid == self.group_id:
                    self._group = group
                    return self._group
            
            # Return default "no Sense Group" if not found
            no_group = SenseGroup()
            no_group.display = "no Sense Group"
            no_group.alias = "no Sense Group"
            no_group.xmlid = "NOGROUP"
            return no_group
        
        return self._group
    
    @group.setter
    def group(self, group: Optional['SenseGroup']) -> None:
        """Set the sense group for this sense."""
        self._group = group
        # Stub: would update Power.last_sense_edit
    
    def built_in_sense_adders(self, sense_id: Optional[int] = None) -> List[str]:
        """
        Get built-in sense adders for this sense.

        Args:
            sense_id: Optional sense ID to filter by
        """
        if sense_id is not None:
            self._built_in_sense_adders_last_id = sense_id

        result = list(self.sense_adders)

        # Add group sense adders
        group = self.group
        if group:
            if sense_id is not None:
                result.extend(group.sense_adders(sense_id))
            else:
                result.extend(group.sense_adders)

        # Stub: would check active hero's powers/equipment for sense modifiers
        # that apply to this sense

        if sense_id is not None:
            self._built_in_sense_adders_saver = result

        return result
    
    @property
    def sense_modifiers(self) -> List[str]:
        """Get sense modifiers for this sense."""
        result: List[str] = []

        # Stub: would check active hero's powers/equipment for sense adders
        # that apply to this sense

        self._sense_modifiers_saver = result
        return result
    
    @property
    def assigned_adders(self) -> List[Adder]:
        """Get assigned adders with sense-specific filtering."""
        result = list(super().assigned_adders)

        # Get group sense adders
        group_adders: List[str] = []
        group = self.group
        if group:
            group_adders = group.sense_adders

        # Get built-in sense adders
        built_in = self.built_in_sense_adders()

        # Filter out adders that are already provided by group or built-in
        result = [a for a in result
                 if a.xmlid not in group_adders and
                    a.xmlid not in built_in]

        # Two sense adders do not take their DISPLAY from the template: the
        # sense names itself inside the string, so Sense builds it (Sense.java
        # :365 and :455). The "[LVL]" is load-bearing, not decoration —
        # Adder.addAliasToVector appends ":  +N" only when the display lacks
        # it, and the computed alias already states the level, so without
        # this the level is printed twice:
        #   "Concealed (-8 with Detect PER Rolls):  +8"
        # DISPLAY is not serialised, so setting it here cannot reach the
        # writer. The removal branches Java pairs with these (drop CONCEALED
        # when the sense is neither active nor TRANSMIT) are NOT ported here:
        # they change which adders are costed, and this is a display fix.
        for adder in result:
            if adder.xmlid == "CONCEALED":
                adder._display = f"Concealed (-[LVL] with {self.alias} PER Rolls)"
            elif adder.xmlid == "ENHANCEDPERCEPTION":
                adder._display = "+[LVL] to PER Roll"

        self._assigned_adders_saver = result
        return result

    @assigned_adders.setter
    def assigned_adders(self, value):
        # Java GenericObject.setAssignedAdders (GenericObject.java:3916) is
        # never overridden; getter-only Python overrides must re-expose it.
        self._assigned_adders = value

    
    @property
    def available_adders(self) -> List[Adder]:
        """Get available adders for this sense."""
        result = list(super().available_adders)
        built_in = self.built_in_sense_adders()
        assigned = self.assigned_adders

        # Stub: would add sense adders from all available sense adders
        # that aren't already built-in or assigned

        result.sort()
        self._available_adders_saver = result
        return result
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Add group if multiple groups available
        group = self.group
        available_groups = self.available_groups
        if group and len(available_groups) > 1:
            output += f" ({group.alias})"
        elif group is None and len(available_groups) > 1:
            output += " (Unusual Group)"
        
        if self.input and self.input.strip():
            output += f":  {self.input}"
        
        if self._selected_option:
            output += ", " + self._selected_option.alias
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += ", " + adder_str
        else:
            adder_str = self.adder_string
            if adder_str and adder_str.strip():
                output += ", " + adder_str
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    
    @property
    def available_groups(self) -> List['SenseGroup']:
        """Get available sense groups for this sense."""
        from kirby_cost.objects.powers.sense_group import SenseGroup
        result: List['SenseGroup'] = []
        
        # Java appends getGroup() UNCONDITIONALLY, so the list always has at
        # least one entry even when that entry is null — which is what makes
        # `size() > 1` mean "there is a choice" rather than "there is a group".
        result.append(self.group)
        
        if self.allow_any_group:
            all_groups = SenseGroup.all_groups()
            for g in all_groups:
                if g not in result:
                    result.append(g)
        
        return result
    
    def get_save_xml(self):
        """Serialize sense including group and provides info."""
        from lxml import etree
        element = self.get_general_save_xml()
        if self.group_id:
            element.set("GROUP", self.group_id)
        if self.active:
            element.set("ACTIVE", "Yes")
        # Only when the document stated them: sense_adders is filled from the
        # template for every sense, so echoing it back invents elements.
        if "PROVIDES" in getattr(self, "_source_child_tags", frozenset()):
            for sa in self.sense_adders:
                prov = etree.SubElement(element, "PROVIDES")
                prov.text = sa
        return element

    @property
    def total_cost(self) -> float:
        """Get total cost, accounting for 6E sense group deduction.

        In 6E, if a sense provides a capability (e.g. Enhanced Perception)
        that the sense's group ALSO already provides, the sense_cost of
        that capability is deducted because the character is already paying
        for it at the group level.

        Mirrors Java Sense.getTotalCost() lines 564-581.

        The group's effective adders are determined at load time by the HDC
        loader, which snapshots the group's defaults PLUS any SenseAdder
        powers that appeared earlier in the hero's power list.  This
        matches the Java SenseGroup cache behaviour during Hero
        construction, where ``getSenseAdders()`` sees only SenseAdder
        powers already added to the hero (i.e. those at an earlier
        position in the powers list).
        """
        cost = super().total_cost

        group = self.group
        if group is not None:
            # Use the frozen group adders computed at load time (if
            # available).  This mirrors the Java SenseGroup cache which
            # captures the hero's SenseAdder powers present at the time
            # the Sense was loaded.  Fall back to the group's template
            # defaults when no frozen snapshot exists.
            group_adders = getattr(self, '_frozen_group_adders', None)
            if group_adders is None:
                group_adders = group.default_sense_adders

            if group_adders and len(group_adders) > 0:
                if self.sense_adders is None:
                    self.sense_adders = []
                from kirby_cost.objects.powers.sense_adder import SenseAdder
                for adder_xmlid in self.sense_adders:
                    if adder_xmlid not in group_adders:
                        continue
                    # Find the SenseAdder template to get its sense_cost
                    for sa in SenseAdder.all_sense_adders():
                        if sa.xmlid and sa.xmlid.upper() == adder_xmlid.upper() and sa.sense_cost >= 0:
                            cost -= float(sa.sense_cost)
                            break

        return cost
    
    @property
    def adder_string(self) -> str:
        """Get adder string with proper sorting."""
        from kirby_cost.objects.powers.sense_adder import SenseAdder
        
        adders = self.assigned_adders
        # Sort adders (ANALYZE should come after DISCRIMINATORY)
        def sort_key(adder):
            key = adder.sorting_value.upper()
            if key == "ANALYZE":
                return "DISCRIMINATORYANALYZE"
            return key
        
        adders.sort(key=sort_key)
        
        # Java calls addAliasToVector, which is gated on
        # `isSelected() && displayInString` and recurses into sub-adders
        # (Adder.java:561). Reading alias_for_vector straight skipped both
        # checks, so an adder Detect had already hidden came back: Detect
        # folds its EXTRA adders into the power's own name -- "Detect Living
        # Souls and Physical Objects" -- and turns displayInString off so the
        # list below does not say it twice.
        parts: list = []

        def collect(adder) -> None:
            if (getattr(adder, "is_selected", True)
                    and getattr(adder, "display_in_string", True)):
                alias = adder.alias_for_vector
                if alias and alias.strip():
                    parts.append(alias.strip())
            for sub in adder.assigned_adders:
                collect(sub)

        for adder in adders:
            collect(adder)

        return ", ".join(parts)
    
    
    @property
    def included_in_template(self) -> bool:
        """Check if included in template (stub)."""
        return True
    
    @property
    def sorting_value(self) -> str:
        """Get sorting value (stub)."""
        return self.xmlid or ""
    
    @property
    def alias_for_vector(self) -> str:
        """Get alias for vector (stub)."""
        return self._alias or ""

