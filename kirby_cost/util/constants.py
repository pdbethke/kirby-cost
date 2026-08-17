"""
Constants for kirby-cost.

Converted from com.hero.util.Constants.java
"""

from enum import IntEnum
from typing import Optional


class CharacteristicType(IntEnum):
    """Characteristic type constants."""
    GENERAL = 0
    STR = 1
    DEX = 2
    CON = 3
    BODY = 4
    INT = 5
    EGO = 6
    PRE = 7
    COM = 8
    PD = 9
    ED = 10
    SPD = 11
    REC = 12
    END = 13
    STUN = 14
    SIZE = 15
    DEF = 16
    RUNNING = 17
    SWIMMING = 18
    LEAPING = 19
    CUSTOM1 = 20
    CUSTOM2 = 21
    CUSTOM3 = 22
    CUSTOM4 = 23
    CUSTOM5 = 24
    CUSTOM6 = 25
    CUSTOM7 = 26
    CUSTOM8 = 27
    CUSTOM9 = 28
    CUSTOM10 = 29
    OCV = 30
    DCV = 31
    OMCV = 32
    DMCV = 33


# UI Constants
IMAGE_WIDTH = 300
COL_1_WIDTH = 60
COL_2_WIDTH = 300
COL_3_WIDTH = 40


# Characteristic name mapping
_CHARACTERISTIC_NAMES = {
    CharacteristicType.GENERAL: "GENERAL",
    CharacteristicType.STR: "STR",
    CharacteristicType.DEX: "DEX",
    CharacteristicType.CON: "CON",
    CharacteristicType.BODY: "BODY",
    CharacteristicType.INT: "INT",
    CharacteristicType.EGO: "EGO",
    CharacteristicType.PRE: "PRE",
    CharacteristicType.COM: "COM",
    CharacteristicType.PD: "PD",
    CharacteristicType.ED: "ED",
    CharacteristicType.SPD: "SPD",
    CharacteristicType.REC: "REC",
    CharacteristicType.END: "END",
    CharacteristicType.STUN: "STUN",
    CharacteristicType.SIZE: "SIZE",
    CharacteristicType.DEF: "DEF",
    CharacteristicType.RUNNING: "RUNNING",
    CharacteristicType.SWIMMING: "SWIMMING",
    CharacteristicType.LEAPING: "LEAPING",
    CharacteristicType.CUSTOM1: "CUSTOM1",
    CharacteristicType.CUSTOM2: "CUSTOM2",
    CharacteristicType.CUSTOM3: "CUSTOM3",
    CharacteristicType.CUSTOM4: "CUSTOM4",
    CharacteristicType.CUSTOM5: "CUSTOM5",
    CharacteristicType.CUSTOM6: "CUSTOM6",
    CharacteristicType.CUSTOM7: "CUSTOM7",
    CharacteristicType.CUSTOM8: "CUSTOM8",
    CharacteristicType.CUSTOM9: "CUSTOM9",
    CharacteristicType.CUSTOM10: "CUSTOM10",
    CharacteristicType.OCV: "OCV",
    CharacteristicType.DCV: "DCV",
    CharacteristicType.OMCV: "OMCV",
    CharacteristicType.DMCV: "DMCV",
}


def characteristic_integer(name: str, active_hero: Optional[object] = None) -> int:
    """
    Get characteristic integer value from name.
    
    Args:
        name: Characteristic name (e.g., "STR", "DEX")
        active_hero: Optional active hero object to check custom characteristics
        
    Returns:
        Characteristic type integer, or 0 (GENERAL) if not found
    """
    name = name.strip().upper()
    
    # Check active hero for custom characteristics first
    # (This would require Hero model to be implemented)
    # if active_hero is not None:
    #     for char in active_hero.get_characteristics():
    #         if char.display.strip().upper() == name:
    #             return char.get_type()
    
    # Check standard characteristics
    for char_type, char_name in _CHARACTERISTIC_NAMES.items():
        if char_name == name:
            return int(char_type)
    
    return int(CharacteristicType.GENERAL)


def characteristic_string(char_type: int, active_hero: Optional[object] = None) -> str:
    """
    Get characteristic name string from integer type.
    
    Args:
        char_type: Characteristic type integer
        active_hero: Optional active hero object to check custom characteristics
        
    Returns:
        Characteristic name string, or "GENERAL" if not found
    """
    # Check active hero for custom characteristics first
    # (This would require Hero model to be implemented)
    # if active_hero is not None:
    #     char = active_hero.get_characteristic(char_type)
    #     if char is not None:
    #         return char.display
    
    # Check standard characteristics
    try:
        char_enum = CharacteristicType(char_type)
        return _CHARACTERISTIC_NAMES.get(char_enum, "GENERAL")
    except ValueError:
        return "GENERAL"

