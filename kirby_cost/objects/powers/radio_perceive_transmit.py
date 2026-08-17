"""
Radio Perceive/Transmit power class for kirby-cost.

Converted from com.hero.objects.powers.RadioPerceiveTransmit.java

Radio perception and transmission sense.
"""

from kirby_cost.objects.powers.sense import Sense


class RadioPerceiveTransmit(Sense, xmlid="RADIOPERCEIVETRANSMIT"):
    """
    Radio Perceive/Transmit power.
    
    Sense for radio wave perception and transmission.
    """
    
    def __init__(self):
        """Initialize a Radio Perceive/Transmit power."""
        super().__init__(RadioPerceiveTransmit.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Radio Perceive/Transmit)."""
        return ""

