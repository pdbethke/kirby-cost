"""
CharacteristicChoice class for kirby-cost.

Converted from com.hero.objects.skills.CharacteristicChoice.java

Represents a characteristic choice for skills that can be based on different characteristics.
"""

from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType, characteristic_integer, characteristic_string


class CharacteristicChoice(GenericObject):
    """
    Represents a characteristic choice for skills.
    
    Some skills can be based on different characteristics (e.g., INT, EGO, PRE).
    This class represents one of those choices.
    """
    
    def __init__(self, xmlid: str = "CHARACTERISTIC_CHOICE"):
        """Initialize a CharacteristicChoice."""
        super().__init__()
        self.xmlid = xmlid
        self.characteristic: int = 0
    
    def __eq__(self, other) -> bool:
        """Check equality based on characteristic."""
        if isinstance(other, CharacteristicChoice):
            return other.characteristic == self.characteristic
        return False
    
    def __hash__(self) -> int:
        """Hash based on characteristic."""
        return self.characteristic
    
    def __str__(self) -> str:
        """String representation."""
        return characteristic_string(self.characteristic)
    
    def _init(self, element) -> None:
        """Initialize from XML element."""
        self.characteristic = 0
        super()._init(element)
        
        # Parse CHARACTERISTIC attribute
        char_str = element.get("CHARACTERISTIC", "")
        if char_str and char_str.strip():
            self.characteristic = characteristic_integer(char_str)
        else:
            self.characteristic = 0




