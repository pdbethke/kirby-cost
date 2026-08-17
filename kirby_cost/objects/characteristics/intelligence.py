"""
Intelligence characteristic class.

Converted from com.hero.objects.characteristics.Intelligence.java
"""

from typing import Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
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
    
    def display_notes(self, active_hero: Optional['Hero'] = None) -> str:
        """Get display notes with PER roll."""
        return f"PER Roll {self.per_roll(active_hero)}"
    
    def per_roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Get PER roll string."""
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
                if power.selected_option is not None and power.selected_option.xmlid == "ALL":
                    n2 += power.levels
                else:
                    n5 += power.levels
                continue
            
            if isinstance(power, CompoundPower):
                for sub_power in power.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if sub_power.selected_option is not None and sub_power.selected_option.xmlid == "ALL":
                            n2 += sub_power.levels
                        elif sub_power.selected_option is not None:
                            n5 += sub_power.levels
        
        # Check equipment for Enhanced Perception
        for equip in active_hero.equipment:
            if isinstance(equip, EnhancedPerception):
                if equip.selected_option is not None and equip.selected_option.xmlid == "ALL":
                    n2 += equip.levels
                else:
                    n5 += equip.levels
                continue
            
            if isinstance(equip, CompoundPower):
                for sub_power in equip.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if sub_power.selected_option is not None and sub_power.selected_option.xmlid == "ALL":
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
        if active_hero is None:
            return 11
        
        n2 = int(9 + round_half_up(self.get_primary_value(active_hero) / 5.0))
        n3 = 0  # All senses bonus
        
        # Check powers for Enhanced Perception with ALL option
        if EnhancedPerception is None:
            return 11
        
        for power in active_hero.powers:
            if EnhancedPerception and isinstance(power, EnhancedPerception):
                if power.selected_option is not None and power.selected_option.xmlid == "ALL":
                    n3 += power.levels
                continue
            
            if isinstance(power, CompoundPower):
                for sub_power in power.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if sub_power.selected_option is not None and sub_power.selected_option.xmlid == "ALL":
                            n3 += sub_power.levels
        
        # Check equipment for Enhanced Perception with ALL option
        for equip in active_hero.equipment:
            if isinstance(equip, EnhancedPerception):
                if equip.selected_option is not None and equip.selected_option.xmlid == "ALL":
                    n3 += equip.levels
                continue
            
            if isinstance(equip, CompoundPower):
                for sub_power in equip.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if sub_power.selected_option is not None and sub_power.selected_option.xmlid == "ALL":
                            n3 += sub_power.levels
        
        return n2 + n3
    
    def secondary_per_roll(self, active_hero: Optional['Hero'] = None) -> int:
        """Get secondary PER roll."""
        if active_hero is None:
            return 11
        
        n2 = int(9 + round_half_up(self.get_secondary_value(active_hero) / 5.0))
        n3 = 0  # All senses bonus
        n4 = 0  # Other senses bonus
        
        # Check powers for Enhanced Perception
        for power in active_hero.powers:
            if isinstance(power, EnhancedPerception):
                if power.selected_option is not None and power.selected_option.xmlid == "ALL":
                    n3 += power.levels
                elif power.selected_option is not None:
                    n4 += power.levels
                continue
            
            if isinstance(power, CompoundPower):
                for sub_power in power.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if sub_power.selected_option is not None and sub_power.selected_option.xmlid == "ALL":
                            n3 += sub_power.levels
                        elif sub_power.selected_option is not None:
                            n4 += sub_power.levels
        
        # Check equipment for Enhanced Perception
        for equip in active_hero.equipment:
            if isinstance(equip, EnhancedPerception):
                if equip.selected_option is not None and equip.selected_option.xmlid == "ALL":
                    n3 += equip.levels
                elif equip.selected_option is not None:
                    n4 += equip.levels
                continue
            
            if isinstance(equip, CompoundPower):
                for sub_power in equip.powers:
                    if EnhancedPerception and isinstance(sub_power, EnhancedPerception):
                        if sub_power.selected_option is not None and sub_power.selected_option.xmlid == "ALL":
                            n3 += sub_power.levels
                        elif sub_power.selected_option is not None:
                            n4 += sub_power.levels
        
        return n2 + n3 + n4

