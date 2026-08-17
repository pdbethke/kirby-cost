"""
EnergyDefense characteristic class.

Converted from com.hero.objects.characteristics.EnergyDefense.java
"""

from kirby_cost.objects.characteristics.defense_characteristic import DefenseCharacteristic
from kirby_cost.util.constants import CharacteristicType


class EnergyDefense(DefenseCharacteristic, xmlid="ED"):
    """Energy Defense (ED) characteristic."""

    _CHAR_TYPE = CharacteristicType.ED
    _DEFENSE_LABEL = "ED"
    _COMBAT_LUCK_INCREASE_ATTR = "ed_increase"
    _COMBAT_LUCK_INCREASE_LEVELS_ATTR = "ed_increase_levels"
    _DAMAGE_RESISTANCE_LEVELS_ATTR = "ed_levels"
    _RESISTANCE_CHECK_INCLUDES_IS_RESISTANT = False

    # Backward-compatible aliases for the unified internal names
    @property
    def ed_resistance(self) -> int:
        return self._defense_resistance

    @ed_resistance.setter
    def ed_resistance(self, value: int) -> None:
        self._defense_resistance = value

    def calc_ed_resistance(self, active_hero=None):
        """Calculate ED resistance (delegates to base)."""
        return self.calc_defense_resistance(active_hero)

    def get_ed_resistance(self, active_hero=None):
        """Get ED resistance (delegates to base)."""
        return self.get_defense_resistance(active_hero)
