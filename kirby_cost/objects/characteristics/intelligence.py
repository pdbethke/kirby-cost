"""
Intelligence characteristic class.

Converted from com.hero.objects.characteristics.Intelligence.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up
from kirby_cost.objects.characteristics.characteristic import _active_hero

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type
    from kirby_cost.objects.powers.compound_power import CompoundPower

# Import EnhancedPerception at runtime to avoid circular imports
try:
    from kirby_cost.objects.powers.enhanced_perception import EnhancedPerception
except ImportError:
    EnhancedPerception = None


class Intelligence(Characteristic, xmlid="INT"):
    """Intelligence (INT) characteristic."""
    
    def __init__(self):
        """Initialize Intelligence."""
        super().__init__(self.XMLID)
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.INT)
    
    @property
    def display_notes(self) -> str:
        """Get display notes with PER roll."""
        active_hero = _active_hero()
        return f"PER Roll {self.per_roll(active_hero)}"
    
    def per_roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Get PER roll string."""
        # CompoundPower is imported under TYPE_CHECKING and used in a
        # runtime isinstance() below — invisible until this method
        # actually runs, which nothing made it do until Detect asked
        # for a PER roll.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        if active_hero is None:
            return "11-"
        
        n3 = 11  # Primary PER roll
        n4 = 11  # Secondary PER roll
        
        # Calculate base PER roll from INT
        if self.per_increase > 0.0 and self.per_increase_levels > 0:
            n2 = int(round_half_up(self.get_primary_value(active_hero) / float(self.per_increase_levels)))
            n3 = int(9 + round_half_up(float(n2) * self.per_increase))
            n2 = int(round_half_up(self.get_secondary_value(active_hero) / float(self.per_increase_levels)))
            n4 = int(9 + round_half_up(float(n2) * self.per_increase))
        
        n2 = 0  # All senses bonus
        n5 = 0  # Other senses bonus
        
        # Check powers for Enhanced Perception
        for power in active_hero.powers:
            if isinstance(power, EnhancedPerception):
                if _is_all_senses(power):
                    n2 += power.levels
                else:
                    n5 += power.levels
                continue
            
            if isinstance(power, CompoundPower):
                for sub_power in power.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if _is_all_senses(sub_power):
                            n2 += sub_power.levels
                        elif sub_power.selected_option is not None:
                            n5 += sub_power.levels
        
        # Check equipment for Enhanced Perception
        for equip in active_hero.equipment:
            if isinstance(equip, EnhancedPerception):
                if _is_all_senses(equip):
                    n2 += equip.levels
                else:
                    n5 += equip.levels
                continue
            
            if isinstance(equip, CompoundPower):
                for sub_power in equip.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if _is_all_senses(sub_power):
                            n2 += sub_power.levels
                        elif sub_power.selected_option is not None:
                            n5 += sub_power.levels
        
        n4 = n4 + n2 + n5
        n3 = n3 + n2
        
        string = f"{n3}-"
        if n3 != n4:
            string = f"{string}/{n4}-"
        
        return string
    
    def primary_per_roll(self, active_hero: Optional['Hero'] = None) -> int:
        """Get primary PER roll."""
        # CompoundPower is imported under TYPE_CHECKING and used in a
        # runtime isinstance() below — invisible until this method
        # actually runs, which nothing made it do until Detect asked
        # for a PER roll.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        if active_hero is None:
            return 11
        
        n2 = int(9 + round_half_up(self.get_primary_value(active_hero) / 5.0))
        n3 = 0  # All senses bonus
        
        # Check powers for Enhanced Perception with ALL option
        if EnhancedPerception is None:
            return 11
        
        for power in active_hero.powers:
            if EnhancedPerception and isinstance(power, EnhancedPerception):
                if _is_all_senses(power):
                    n3 += power.levels
                continue
            
            if isinstance(power, CompoundPower):
                for sub_power in power.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if _is_all_senses(sub_power):
                            n3 += sub_power.levels
        
        # Check equipment for Enhanced Perception with ALL option
        for equip in active_hero.equipment:
            if isinstance(equip, EnhancedPerception):
                if _is_all_senses(equip):
                    n3 += equip.levels
                continue
            
            if isinstance(equip, CompoundPower):
                for sub_power in equip.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if _is_all_senses(sub_power):
                            n3 += sub_power.levels
        
        return n2 + n3
    
    def secondary_per_roll(self, active_hero: Optional['Hero'] = None) -> int:
        """Get secondary PER roll."""
        # CompoundPower is imported under TYPE_CHECKING and used in a
        # runtime isinstance() below — invisible until this method
        # actually runs, which nothing made it do until Detect asked
        # for a PER roll.
        from kirby_cost.objects.powers.compound_power import CompoundPower
        if active_hero is None:
            return 11
        
        n2 = int(9 + round_half_up(self.get_secondary_value(active_hero) / 5.0))
        n3 = 0  # All senses bonus
        # Java accumulates a `secBonus` here for Enhanced Perceptions bought
        # for a SINGLE sense group — and every one of those lines is COMMENTED
        # OUT (Intelligence.java:  `// secBonus += ep.getLevels();`), four
        # times over. This port made the commented code live, so the secondary
        # PER roll came out above the primary and every Detect printed two
        # rolls ("13-/17-") where HD prints one. Kept at zero, as HD keeps it.
        n4 = 0
        
        # Check powers for Enhanced Perception
        for power in active_hero.powers:
            if isinstance(power, EnhancedPerception):
                if _is_all_senses(power):
                    n3 += power.levels
                continue
            
            if isinstance(power, CompoundPower):
                for sub_power in power.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if _is_all_senses(sub_power):
                            n3 += sub_power.levels
        
        # Check equipment for Enhanced Perception
        for equip in active_hero.equipment:
            if isinstance(equip, EnhancedPerception):
                if _is_all_senses(equip):
                    n3 += equip.levels
                continue
            
            if isinstance(equip, CompoundPower):
                for sub_power in equip.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if _is_all_senses(sub_power):
                            n3 += sub_power.levels
        
        return n2 + n3 + n4



def _is_all_senses(power) -> bool:
    """Whether an Enhanced Perception applies to every sense group.

    Java asks `getSelectedOption().getXMLID().equals("ALL")` — the OPTION
    OBJECT, and nothing else. It is tempting to fall back to the document's
    OPTIONID when the object has not been resolved, and that is WRONG: HD does
    not resolve one either, because ENHANCEDPERCEPTION's template lists no
    options at all (it is priced by ALLCOST/GROUPCOST/SENSECOST). So the
    bonus is not applied in HD, and a character with
    `OPTIONID="ALL" OPTION_ALIAS="all Sense Groups except Sight Group"` — a
    file that says ALL and means all-but-one — gets no bonus either.
    Substituting OPTIONID here made every such Detect roll 2 too high.
    """
    option = getattr(power, "selected_option", None)
    return option is not None and (option.xmlid or "").upper() == "ALL"
