"""
CharAffectingObject class for kirby-cost.

Converted from com.hero.objects.CharAffectingObject.java

This is an intermediate class between GenericObject and Power/Skill classes.
It handles objects that can affect characteristics.
"""

from typing import Optional
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType


class CharAffectingObject(GenericObject):
    """
    Base class for objects that can affect characteristics.
    
    Extends GenericObject with characteristic increase tracking.
    """
    
    def __init__(self):
        """Initialize a CharAffectingObject."""
        super().__init__()
        
        # Characteristic affecting flags
        self.affects_primary: bool = True
        self.affects_total: bool = True
        
        # Characteristic increases (value per level)
        self.str_increase: float = 0.0
        self.dex_increase: float = 0.0
        self.con_increase: float = 0.0
        self.body_increase: float = 0.0
        self.int_increase: float = 0.0
        self.ego_increase: float = 0.0
        self.pre_increase: float = 0.0
        self.com_increase: float = 0.0
        self.pd_increase: float = 0.0
        self.ed_increase: float = 0.0
        self.spd_increase: float = 0.0
        self.rec_increase: float = 0.0
        self.end_increase: float = 0.0
        self.stun_increase: float = 0.0
        self.def_increase: float = 0.0
        self.size_increase: float = 0.0
        self.running_increase: float = 0.0
        self.swimming_increase: float = 0.0
        self.leaping_increase: float = 0.0
        self.ocv_increase: float = 0.0
        self.dcv_increase: float = 0.0
        self.omcv_increase: float = 0.0
        self.dmcv_increase: float = 0.0
        
        # Custom characteristic increases
        self.custom1_increase: float = 0.0
        self.custom2_increase: float = 0.0
        self.custom3_increase: float = 0.0
        self.custom4_increase: float = 0.0
        self.custom5_increase: float = 0.0
        self.custom6_increase: float = 0.0
        self.custom7_increase: float = 0.0
        self.custom8_increase: float = 0.0
        self.custom9_increase: float = 0.0
        self.custom10_increase: float = 0.0
        
        # Characteristic increase levels (levels per unit)
        self.str_increase_levels: int = 1
        self.dex_increase_levels: int = 1
        self.con_increase_levels: int = 1
        self.body_increase_levels: int = 1
        self.int_increase_levels: int = 1
        self.ego_increase_levels: int = 1
        self.pre_increase_levels: int = 1
        self.com_increase_levels: int = 1
        self.pd_increase_levels: int = 1
        self.ed_increase_levels: int = 1
        self.spd_increase_levels: int = 1
        self.rec_increase_levels: int = 1
        self.end_increase_levels: int = 1
        self.stun_increase_levels: int = 1
        self.def_increase_levels: int = 1
        self.size_increase_levels: int = 1
        self.running_increase_levels: int = 1
        self.swimming_increase_levels: int = 1
        self.leaping_increase_levels: int = 1
        self.ocv_increase_levels: int = 1
        self.dcv_increase_levels: int = 1
        self.omcv_increase_levels: int = 1
        self.dmcv_increase_levels: int = 1
        
        # Custom characteristic increase levels
        self.custom1_increase_levels: int = 1
        self.custom2_increase_levels: int = 1
        self.custom3_increase_levels: int = 1
        self.custom4_increase_levels: int = 1
        self.custom5_increase_levels: int = 1
        self.custom6_increase_levels: int = 1
        self.custom7_increase_levels: int = 1
        self.custom8_increase_levels: int = 1
        self.custom9_increase_levels: int = 1
        self.custom10_increase_levels: int = 1
        
        # Other increases
        self.kb_increase: float = 0.0
        self.kb_increase_levels: int = 1
        self.md_increase: float = 0.0
        self.md_increase_levels: int = 1
        self.mass_multiplier: float = 0.0
        self.mass_multiplier_levels: int = 1
        self.reach_increase: float = 0.0
        self.reach_increase_levels: int = 1
        self.height_increase: float = 0.0
        self.height_increase_levels: int = 1
        self.width_increase: float = 0.0
        self.width_increase_levels: int = 1
        self.per_increase: float = 0.0
        self.per_increase_levels: int = 1
        self.ecv_increase: float = 0.0
        self.ecv_increase_levels: int = 1
    
    @property
    def affect_primary(self) -> bool:
        """Get whether this affects primary characteristics."""
        return self.affects_primary
    
    @affect_primary.setter
    def affect_primary(self, value: bool) -> None:
        """Set whether this affects primary characteristics."""
        self.affects_primary = value
    
    @property
    def affect_total(self) -> bool:
        """Get whether this affects total characteristics."""
        if self.affects_primary:
            self.affects_total = True
        return self.affects_total
    
    @affect_total.setter
    def affect_total(self, value: bool) -> None:
        """Set whether this affects total characteristics."""
        self.affects_total = value
    
    def affects_characteristics(self) -> bool:
        """Check if this object affects any characteristics."""
        # Check all characteristic increases
        increases = [
            self.str_increase, self.dex_increase, self.con_increase, self.body_increase,
            self.int_increase, self.ego_increase, self.pre_increase, self.com_increase,
            self.pd_increase, self.ed_increase, self.spd_increase, self.rec_increase,
            self.end_increase, self.stun_increase, self.def_increase, self.size_increase,
            self.running_increase, self.swimming_increase, self.leaping_increase,
            self.ocv_increase, self.dcv_increase, self.omcv_increase, self.dmcv_increase,
            self.custom1_increase, self.custom2_increase, self.custom3_increase,
            self.custom4_increase, self.custom5_increase, self.custom6_increase,
            self.custom7_increase, self.custom8_increase, self.custom9_increase,
            self.custom10_increase,
        ]
        return any(inc != 0.0 for inc in increases)
    
    def increase(self, char_type: int) -> float:
        """Get the increase value for a characteristic type."""
        char_enum = CharacteristicType(char_type)
        if char_enum == CharacteristicType.STR:
            return self.str_increase
        elif char_enum == CharacteristicType.DEX:
            return self.dex_increase
        elif char_enum == CharacteristicType.CON:
            return self.con_increase
        elif char_enum == CharacteristicType.BODY:
            return self.body_increase
        elif char_enum == CharacteristicType.INT:
            return self.int_increase
        elif char_enum == CharacteristicType.EGO:
            return self.ego_increase
        elif char_enum == CharacteristicType.PRE:
            return self.pre_increase
        elif char_enum == CharacteristicType.COM:
            return self.com_increase
        elif char_enum == CharacteristicType.PD:
            return self.pd_increase
        elif char_enum == CharacteristicType.ED:
            return self.ed_increase
        elif char_enum == CharacteristicType.SPD:
            return self.spd_increase
        elif char_enum == CharacteristicType.REC:
            return self.rec_increase
        elif char_enum == CharacteristicType.END:
            return self.end_increase
        elif char_enum == CharacteristicType.STUN:
            return self.stun_increase
        elif char_enum == CharacteristicType.DEF:
            return self.def_increase
        elif char_enum == CharacteristicType.SIZE:
            return self.size_increase
        elif char_enum == CharacteristicType.RUNNING:
            return self.running_increase
        elif char_enum == CharacteristicType.SWIMMING:
            return self.swimming_increase
        elif char_enum == CharacteristicType.LEAPING:
            return self.leaping_increase
        elif char_enum == CharacteristicType.OCV:
            return self.ocv_increase
        elif char_enum == CharacteristicType.DCV:
            return self.dcv_increase
        elif char_enum == CharacteristicType.OMCV:
            return self.omcv_increase
        elif char_enum == CharacteristicType.DMCV:
            return self.dmcv_increase
        elif char_enum == CharacteristicType.CUSTOM1:
            return self.custom1_increase
        elif char_enum == CharacteristicType.CUSTOM2:
            return self.custom2_increase
        elif char_enum == CharacteristicType.CUSTOM3:
            return self.custom3_increase
        elif char_enum == CharacteristicType.CUSTOM4:
            return self.custom4_increase
        elif char_enum == CharacteristicType.CUSTOM5:
            return self.custom5_increase
        elif char_enum == CharacteristicType.CUSTOM6:
            return self.custom6_increase
        elif char_enum == CharacteristicType.CUSTOM7:
            return self.custom7_increase
        elif char_enum == CharacteristicType.CUSTOM8:
            return self.custom8_increase
        elif char_enum == CharacteristicType.CUSTOM9:
            return self.custom9_increase
        elif char_enum == CharacteristicType.CUSTOM10:
            return self.custom10_increase
        return 0.0
    
    def increase_levels(self, char_type: int) -> int:
        """Get the increase levels for a characteristic type."""
        char_enum = CharacteristicType(char_type)
        if char_enum == CharacteristicType.STR:
            return self.str_increase_levels
        elif char_enum == CharacteristicType.DEX:
            return self.dex_increase_levels
        elif char_enum == CharacteristicType.CON:
            return self.con_increase_levels
        elif char_enum == CharacteristicType.BODY:
            return self.body_increase_levels
        elif char_enum == CharacteristicType.INT:
            return self.int_increase_levels
        elif char_enum == CharacteristicType.EGO:
            return self.ego_increase_levels
        elif char_enum == CharacteristicType.PRE:
            return self.pre_increase_levels
        elif char_enum == CharacteristicType.COM:
            return self.com_increase_levels
        elif char_enum == CharacteristicType.PD:
            return self.pd_increase_levels
        elif char_enum == CharacteristicType.ED:
            return self.ed_increase_levels
        elif char_enum == CharacteristicType.SPD:
            return self.spd_increase_levels
        elif char_enum == CharacteristicType.REC:
            return self.rec_increase_levels
        elif char_enum == CharacteristicType.END:
            return self.end_increase_levels
        elif char_enum == CharacteristicType.STUN:
            return self.stun_increase_levels
        elif char_enum == CharacteristicType.DEF:
            return self.def_increase_levels
        elif char_enum == CharacteristicType.SIZE:
            return self.size_increase_levels
        elif char_enum == CharacteristicType.RUNNING:
            return self.running_increase_levels
        elif char_enum == CharacteristicType.SWIMMING:
            return self.swimming_increase_levels
        elif char_enum == CharacteristicType.LEAPING:
            return self.leaping_increase_levels
        elif char_enum == CharacteristicType.OCV:
            return self.ocv_increase_levels
        elif char_enum == CharacteristicType.DCV:
            return self.dcv_increase_levels
        elif char_enum == CharacteristicType.OMCV:
            return self.omcv_increase_levels
        elif char_enum == CharacteristicType.DMCV:
            return self.dmcv_increase_levels
        elif char_enum == CharacteristicType.CUSTOM1:
            return self.custom1_increase_levels
        elif char_enum == CharacteristicType.CUSTOM2:
            return self.custom2_increase_levels
        elif char_enum == CharacteristicType.CUSTOM3:
            return self.custom3_increase_levels
        elif char_enum == CharacteristicType.CUSTOM4:
            return self.custom4_increase_levels
        elif char_enum == CharacteristicType.CUSTOM5:
            return self.custom5_increase_levels
        elif char_enum == CharacteristicType.CUSTOM6:
            return self.custom6_increase_levels
        elif char_enum == CharacteristicType.CUSTOM7:
            return self.custom7_increase_levels
        elif char_enum == CharacteristicType.CUSTOM8:
            return self.custom8_increase_levels
        elif char_enum == CharacteristicType.CUSTOM9:
            return self.custom9_increase_levels
        elif char_enum == CharacteristicType.CUSTOM10:
            return self.custom10_increase_levels
        return 0
    
    def increase_value(self, char_type: int, primary: bool) -> float:
        """
        Get the increase value for a characteristic type.
        
        Args:
            char_type: Characteristic type
            primary: Whether to get primary or secondary value
            
        Returns:
            Increase value
        """
        increase = self.increase(char_type)
        increase_levels = self.increase_levels(char_type)
        
        if increase_levels <= 0:
            return 0.0
        
        # This is a simplified version - subclasses may override
        if primary:
            # For primary, use levels directly
            return (float(self._levels) / float(increase_levels)) * increase
        else:
            # For secondary, same calculation
            return (float(self._levels) / float(increase_levels)) * increase
    
    @staticmethod
    def check_figured(obj: 'GenericObject', char_type: int) -> bool:
        """
        Check if a characteristic can be figured.
        
        Args:
            obj: The object to check
            char_type: Characteristic type
            
        Returns:
            True if the characteristic can be figured
        """
        from kirby_cost.util.constants import CharacteristicType
        
        # Special handling for movement characteristics (LEAPING=19, RUNNING=17, SWIMMING=18)
        if char_type in (CharacteristicType.LEAPING, CharacteristicType.RUNNING, CharacteristicType.SWIMMING):
            # Check if it's a Characteristic and has negative values
            if hasattr(obj, 'get_primary_value') and hasattr(obj, 'get_secondary_value'):
                primary = obj.primary_value()
                secondary = obj.secondary_value()
                # Can be figured if either primary or secondary is not negative
                return not (primary < 0.0) or not (secondary < 0.0)
            return True
        
        # Check for NOFIGURED modifier
        from kirby_cost.objects.base import GenericObject
        if GenericObject.find_object_by_id(obj.assigned_modifiers, "NOFIGURED") is not None:
            return False
        
        # Check parent list for NOFIGURED modifier
        parent = obj.parent
        if parent is not None:
            if GenericObject.find_object_by_id(parent.assigned_modifiers, "NOFIGURED") is not None:
                return False
        
        return True

