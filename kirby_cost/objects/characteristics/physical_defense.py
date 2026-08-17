"""
PhysicalDefense characteristic class.

Converted from com.hero.objects.characteristics.PhysicalDefense.java
"""

from kirby_cost.objects.characteristics.defense_characteristic import DefenseCharacteristic
from kirby_cost.util.constants import CharacteristicType


class PhysicalDefense(DefenseCharacteristic, xmlid="PD"):
    """Physical Defense (PD) characteristic."""

    _CHAR_TYPE = CharacteristicType.PD
    _DEFENSE_LABEL = "PD"
    _COMBAT_LUCK_INCREASE_ATTR = "pd_increase"
    _COMBAT_LUCK_INCREASE_LEVELS_ATTR = "pd_increase_levels"
    _DAMAGE_RESISTANCE_LEVELS_ATTR = "pd_levels"
    _RESISTANCE_CHECK_INCLUDES_IS_RESISTANT = True

    # Backward-compatible aliases for the unified internal names
    @property
    def pd_resistance(self) -> int:
        return self._defense_resistance

    @pd_resistance.setter
    def pd_resistance(self, value: int) -> None:
        self._defense_resistance = value

    def calc_pd_resistance(self, active_hero=None):
        """Calculate PD resistance (delegates to base)."""
        return self.calc_defense_resistance(active_hero)

    def get_pd_resistance(self, active_hero=None):
        """Get PD resistance (delegates to base)."""
        return self.get_defense_resistance(active_hero)
