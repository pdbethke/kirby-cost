"""
Size characteristic class.

Converted from com.hero.objects.characteristics.Size.java
"""

from typing import Optional, TYPE_CHECKING
from decimal import Decimal, ROUND_HALF_UP
import math

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up, round_down

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class Size(Characteristic, xmlid="SIZE"):
    """Size characteristic."""
    
    def __init__(self):
        """Initialize Size."""
        super().__init__(self.XMLID)
        self.start_width: float = 0.5
        self.start_length: float = 1.0
        self.start_dcv: int = 0
    
    def _init(self, element=None):
        """Initialize from XML element."""
        super()._init(element)
        self.start_width = 0.5
        self.start_length = 1.0
        self.start_dcv = 0
        
        if element is not None:
            # Parse XML attributes (stub - would use XMLUtility)
            # start_width = XMLUtility.getValue(element, "STARTWIDTH")
            # start_length = XMLUtility.getValue(element, "STARTHEIGHT")
            # start_dcv = XMLUtility.getValue(element, "STARTDCV")
            pass
    
    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(CharacteristicType.SIZE)
    
    def roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Size doesn't have a roll."""
        return ""
    
    @property
    def height_increase_levels(self) -> int:
        """Get height increase levels (defaults to 1)."""
        levels = super().height_increase_levels
        if levels == 0:
            return 1
        return levels
    
    @property
    def width_increase_levels(self) -> int:
        """Get width increase levels (defaults to 1)."""
        levels = super().width_increase_levels
        if levels == 0:
            return 1
        return levels
    
    def dcv_effect(self, primary: bool, active_hero: Optional['Hero'] = None) -> int:
        """Get DCV effect (overrides base class)."""
        if self.dcv_increase_levels != 0:
            n = -1 if self.dcv_increase < 0.0 else 1
            d = 0.0
            d2 = self.get_primary_value(active_hero) if primary else self.get_secondary_value(active_hero)
            d = round_down(abs(d2 * self.dcv_increase / float(self.dcv_increase_levels)))
            d *= float(n)
            d = round_half_up(d)
            return int(d)
        return 0
    
    def pre_increase_value(self, active_hero: Optional['Hero'] = None) -> float:
        """Get PRE increase value (overrides base class)."""
        if (self.increase_levels(CharacteristicType.PRE) > 0 and
            self.increase(CharacteristicType.PRE) != 0.0):
            return self.increase(CharacteristicType.PRE) * math.floor(self.characteristic_value(active_hero) / float(self.increase_levels(CharacteristicType.PRE)))
        return 0.0
    
    @property
    def display_notes(self) -> str:
        """Get display notes with size information."""
        # Calculate dimensions
        d2 = self.start_length
        if self._levels != 0:
            d2 *= math.pow(self.height_increase, float(self._levels) / float(self.height_increase_levels))
        
        d3 = self.start_width
        if self._levels != 0:
            d3 *= math.pow(self.width_increase, float(self._levels) / float(self.width_increase_levels))
        
        d4 = d2 * d3  # Area
        d5 = d2 * d3 * d3  # Volume
        
        # Calculate mass
        l = 100
        if self._levels != 0:
            n3 = self._levels / self.mass_multiplier_levels
            n2 = int(round_half_up(math.pow(self.mass_multiplier, n3)))
            n = int(round_half_up(math.pow(self.mass_multiplier, n3 + 1)))
            n4 = n - n2
            l = int(100 * (round_half_up(math.pow(self.mass_multiplier, n3)) + float(n4) * float(self._levels % self.mass_multiplier_levels) / float(self.mass_multiplier_levels)))
        
        # Calculate DCV/OCV
        n3 = self.start_dcv
        n2 = -1 if self.dcv_increase < 0.0 else 1
        if self.dcv_increase_levels != 0:
            n3 += n2 * int(round_down(abs(self.dcv_increase) * float(self._levels) / float(self.dcv_increase_levels)))
        n = abs(n3)
        
        # Format mass string
        string = ""
        if l / 1000 < 1:
            string = f"{l} kg"
        elif l / 1000 < 1000:
            d = float(l) / 1000.0
            big_decimal = Decimal(str(d))
            big_decimal = big_decimal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            string = f"{big_decimal} ton"
        else:
            d = float(l) / 1000000.0
            big_decimal = Decimal(str(d))
            big_decimal = big_decimal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            string = f"{big_decimal} kton"
        
        # Calculate KB
        n6 = 0
        if self._levels != 0:
            n7 = self._levels / self.kb_increase_levels
            n8 = 1
            n9 = int(round_half_up(self.kb_increase))
            if n9 < 0:
                n8 = -1
                n9 = abs(n9)
            n10 = int(round_half_up(math.pow(n9, n7)))
            n11 = int(round_half_up(math.pow(n9, n7 + 1)))
            n12 = n11 - n10
            n6 = int((float(n9 * n7) + float(n12) * float(self._levels % n9) / float(self.kb_increase_levels)) * n8)
        
        # Format dimensions
        big_decimal2 = Decimal(str(d2))
        big_decimal2 = big_decimal2.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        big_decimal3 = Decimal(str(d3))
        big_decimal3 = big_decimal3.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        big_decimal4 = Decimal(str(d4))
        big_decimal4 = big_decimal4.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        big_decimal5 = Decimal(str(d5))
        big_decimal5 = big_decimal5.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Check if 6E (stub - would need template access)
        is_6e = False  # Default to 5E format
        
        if is_6e:
            string2 = (f"Length {big_decimal2}m,  Width {big_decimal3}m,  Height {big_decimal3}m,  "
                      f"Volume {big_decimal5}m^3  Mass {string},  OCV +{n},  KB {n6}")
        else:
            string2 = (f"Length {big_decimal2}\",  Width {big_decimal3}\",   Area {big_decimal4}\"   "
                      f"Mass {string}   KB {n6}")
        
        return string2
    
    def increase_value(self, char_type: int, primary: bool, active_hero: Optional['Hero'] = None) -> float:
        """Get increase value (overrides base class for PRE)."""
        if char_type == CharacteristicType.PRE:
            if self.increase_levels(char_type) == 0:
                return 0.0
            
            if not ((not primary or (self.affect_primary and self.affect_total))):
                return 0.0
            
            if not ((primary or (not self.affect_primary and self.affect_total))):
                return 0.0
            
            if not self.affect_total:
                return 0.0
            
            return self.increase(char_type) * math.floor(float(self._levels) / float(self.increase_levels(char_type)))
        
        # Use parent class method
        return super().increase_value(char_type, primary, active_hero)

