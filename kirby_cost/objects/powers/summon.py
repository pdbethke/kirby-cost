"""
Summon power class for kirby-cost.

Converted from com.hero.objects.powers.Summon.java

Power to summon beings.
"""

from kirby_cost.objects.powers.power import Power
from pathlib import Path
from typing import Optional


class Summon(Power, xmlid="SUMMON"):
    """
    Summon power.
    
    Summons beings to serve the character.
    """
    
    def __init__(self):
        """Initialize a Summon power."""
        super().__init__()
        self.xmlid = Summon.XMLID
        self._duration = "INSTANT"
        self.file_path: Optional[str] = None
        self.file_association_last_check: Optional[int] = None
    
    @property
    def damage_display(self) -> str:
        """Get summon display."""
        # Calculate total from base and INCREASETOTAL adder
        total = 1.0
        for adder in self.assigned_adders:
            if adder.xmlid == "INCREASETOTAL":
                adder.display_in_string = False
                total += adder.levels * adder.level_multiplier
        
        return f"{int(total)}x {self.input or 'Base Points'}"
    
    def clear_file_path(self) -> None:
        """Clear associated file path."""
        self.file_path = None
        self.file_association_last_check = None

