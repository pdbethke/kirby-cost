"""
Sense Group power class for kirby-cost.

Converted from com.hero.objects.powers.SenseGroup.java

Base class for sense groups that organize senses.
"""

from typing import List, Optional
from kirby_cost.objects.powers.power import Power
from kirby_cost.objects.base import GenericObject


class SenseGroup(Power):
    """
    Sense Group power.
    
    Organizes senses into groups for cost calculation and management.
    """
    
    # Static class variables
    _all_groups: List['SenseGroup'] = []
    _initializing: bool = False  # Guard against clear() ↔ __init__() recursion

    def __init__(self):
        """Initialize a Sense Group."""
        super().__init__()
        self.xmlid = "SENSEGROUP"
        self._duration = "INHERENT"
        self.sense_adders: List[str] = []
        self._sense_adders_saver: Optional[List[str]] = None
        self._sense_adders_has_hero: bool = False

        # Initialize static groups if empty (guarded to prevent recursion:
        # clear() creates SenseGroup instances which re-enter __init__)
        if len(SenseGroup._all_groups) == 0 and not SenseGroup._initializing:
            SenseGroup.clear()

        # Add to all groups if valid (skip during clear() — clear() appends
        # explicitly after setting the real xmlid)
        if not SenseGroup._initializing and self.xmlid and self.xmlid.strip() and self.included_in_template():
            while self in SenseGroup._all_groups:
                SenseGroup._all_groups.remove(self)
            SenseGroup._all_groups.append(self)

    # 6E sense groups from Main6E.hdt with their PROVIDES (built-in capabilities).
    _TEMPLATE_GROUPS = [
        {"xmlid": "HEARINGGROUP",  "display": "Hearing Group",    "provides": ["RANGE", "MAKEASENSE"]},
        {"xmlid": "MENTALGROUP",   "display": "Mental Group",     "provides": ["RANGE"]},
        {"xmlid": "RADIOGROUP",    "display": "Radio Group",      "provides": ["RANGE", "MAKEASENSE"]},
        {"xmlid": "SIGHTGROUP",    "display": "Sight Group",      "provides": ["RANGE", "MAKEASENSE", "TARGETINGSENSE"]},
        {"xmlid": "SMELLGROUP",    "display": "Smell/Taste Group","provides": ["MAKEASENSE"]},
        {"xmlid": "TOUCHGROUP",    "display": "Touch Group",      "provides": ["MAKEASENSE"]},
    ]

    @classmethod
    def clear(cls) -> None:
        """Clear all sense groups and add default groups.

        Initialises the standard 6E sense groups (from Main6E.hdt) with their
        built-in PROVIDES capabilities, plus the two special groups.
        """
        cls._all_groups.clear()
        cls._initializing = True
        try:
            # Add "Unusual Group"
            unusual = SenseGroup()
            unusual.display = "Unusual Group"
            unusual.alias = "Unusual Group"
            unusual.xmlid = "UNUSUALGROUP"
            cls._all_groups.append(unusual)

            # Add "no Sense Group"
            no_group = SenseGroup()
            no_group.display = "no Sense Group"
            no_group.alias = "no Sense Group"
            no_group.xmlid = "NOGROUP"
            cls._all_groups.append(no_group)

            # Add standard 6E sense groups from template
            for tpl in cls._TEMPLATE_GROUPS:
                grp = SenseGroup()
                grp.xmlid = tpl["xmlid"]
                grp.display = tpl["display"]
                grp.alias = tpl["display"]
                grp.sense_adders = list(tpl["provides"])
                cls._all_groups.append(grp)
        finally:
            cls._initializing = False
    
    @classmethod
    def all_groups(cls) -> List['SenseGroup']:
        """Get all sense groups."""
        return cls._all_groups
    
    @classmethod
    def group_by_id(cls, xmlid: str) -> Optional['SenseGroup']:
        """Get a sense group by XML ID."""
        for group in cls.all_groups():
            if group.xmlid == xmlid:
                return group
        return None
    
    @classmethod
    def owned_groups(cls) -> List['SenseGroup']:
        """Get sense groups owned by the active hero."""
        owned: List['SenseGroup'] = []
        if cls._all_groups is None:
            cls._all_groups = []

        # Stub: would get owned senses from active hero
        # For now, return all groups except special ones
        for group in cls._all_groups:
            if (group.xmlid == "UNUSUALGROUP" or
                group.xmlid == "NOGROUP" or
                group in owned):
                continue

            # Stub: would check if hero has senses in this group
            # For now, add all non-special groups
            if group.xmlid not in ["UNUSUALGROUP", "NOGROUP"]:
                owned.append(group)

        owned.sort()
        return owned
    
    @property
    def default_sense_adders(self) -> List[str]:
        """Get default sense adders for this group."""
        if self.sense_adders is None:
            self.sense_adders = []
        return self.sense_adders
    
    def set_sense_adders(self, sense_id: Optional[int] = None) -> List[str]:
        """
        Get sense adders for this group.

        Args:
            sense_id: Optional sense ID to filter by
        """
        if self.sense_adders is None:
            self.sense_adders = []
        
        result = list(self.sense_adders)  # Clone

        # Scan hero's powers and equipment for SenseAdder instances
        # targeting this group (mirrors Java SenseGroup.getSenseAdders())
        hero = getattr(self, '_loaded_hero', None)
        if hero is not None:
            from kirby_cost.objects.powers.sense_adder import SenseAdder
            from kirby_cost.objects.powers.compound_power import CompoundPower

            def _check_object(obj):
                """Check if obj is a SenseAdder targeting this group and add it."""
                if isinstance(obj, SenseAdder):
                    # If sense_id is provided, skip the adder with that id
                    if sense_id is not None and getattr(obj, 'id', None) == sense_id:
                        return
                    if self.xmlid in obj.sense_groups and obj.xmlid not in result:
                        result.append(obj.xmlid)

            powers = hero.powers if hasattr(hero, 'powers') else getattr(hero, 'powers', [])
            equipment = hero.equipment if hasattr(hero, 'equipment') else getattr(hero, 'equipment', [])

            for obj in (powers or []):
                _check_object(obj)
                if isinstance(obj, CompoundPower):
                    for sub in obj.powers:
                        _check_object(sub)

            for obj in (equipment or []):
                _check_object(obj)
                if isinstance(obj, CompoundPower):
                    for sub in obj.powers:
                        _check_object(sub)

        if sense_id is None:
            # `hero`, not `has_hero` — the latter was never defined, so this
            # raised NameError on the method's own default argument. It had no
            # callers, which is the only reason nothing noticed.
            self._sense_adders_saver = result
            self._sense_adders_has_hero = hero is not None

        return result
    
    def __eq__(self, other) -> bool:
        """Check equality based on XML ID."""
        if isinstance(other, SenseGroup):
            return other.xmlid == self.xmlid
        return False
    
    def __hash__(self) -> int:
        """Hash based on XML ID."""
        return hash(self.xmlid)
    
    def included_in_template(self) -> bool:
        """Check if included in template (stub)."""
        return True

