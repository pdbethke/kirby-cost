"""
BaseSize characteristic class.

Converted from com.hero.objects.characteristics.BaseSize.java
"""

from typing import Optional, TYPE_CHECKING
from decimal import Decimal, ROUND_HALF_UP
import math

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up, round_down

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class BaseSize(Characteristic, xmlid="BASESIZE"):
    """BaseSize characteristic."""
    
    def __init__(self):
        """Initialize BaseSize."""
        super().__init__(self.XMLID)
        self.start_width: float = 0.5
        self.start_length: float = 1.0
        self.start_dcv: int = -4
    
    def _init(self, element=None):
        """Initialize from XML element."""
        super()._init(element)
        self.start_width = 0.5
        self.start_length = 1.0
        self.start_dcv = -4
        
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
        """BaseSize doesn't have a roll."""
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
    
    @property
    def display_notes(self) -> str:
        """Get display notes with size information."""
        # Calculate dimensions
        d = self.start_length
        if self._levels != 0:
            d *= math.pow(self.height_increase, float(self._levels) / float(self.height_increase_levels))
        
        d2 = self.start_width
        if self._levels != 0:
            d2 *= math.pow(self.width_increase, float(self._levels) / float(self.width_increase_levels))
        
        d3 = d * d2  # Area
        d4 = d * d2 * d2  # Volume
        
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
        
        # Format dimensions
        big_decimal = Decimal(str(d))
        big_decimal = big_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        big_decimal2 = Decimal(str(d2))
        big_decimal2 = big_decimal2.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        big_decimal3 = Decimal(str(d3))
        big_decimal3 = big_decimal3.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        big_decimal4 = Decimal(str(d4))
        big_decimal4 = big_decimal4.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Check if 6E (stub - would need template access)
        is_6e = False  # Default to 5E format
        
        if is_6e:
            string = (f"Length {big_decimal}m,  Width {big_decimal2}m,  Height {big_decimal2}m,  "
                     f"Volume {big_decimal4}m^3   OCV +{n}")
        else:
            string = (f"Length {big_decimal}\",  Width {big_decimal2}\",   Area {big_decimal3}\"   "
                     f"DCV {n3}")
        
        return string




