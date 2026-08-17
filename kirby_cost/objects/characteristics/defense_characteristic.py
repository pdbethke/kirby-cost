"""
DefenseCharacteristic base class shared by PhysicalDefense and EnergyDefense.

Extracted from the nearly-identical PD/ED implementations to eliminate ~600 lines
of duplication. Subclasses parameterize defense type via class attributes.
"""

from typing import Iterator, Optional, TYPE_CHECKING

from kirby_cost.objects.characteristics.characteristic import Characteristic
from kirby_cost.objects.char_affecting import CharAffectingObject
from kirby_cost.objects.base import GenericObject
from kirby_cost.util.constants import CharacteristicType
from kirby_cost.util.rounder import round_half_up

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero
    from kirby_cost.objects.powers.compound_power import CompoundPower
    from kirby_cost.objects.powers.power import Power
    from kirby_cost.objects.powers.damage_resistance import DamageResistance
    from kirby_cost.objects.talents.combat_luck import CombatLuck


class DefenseCharacteristic(Characteristic):
    """
    Base class for PD and ED characteristics.

    Subclasses must set:
        _CHAR_TYPE: CharacteristicType enum member (e.g. CharacteristicType.PD)
        _DEFENSE_LABEL: short label for display_notes (e.g. "PD")
        _COMBAT_LUCK_INCREASE_ATTR: CombatLuck attribute for increase (e.g. "pd_increase")
        _COMBAT_LUCK_INCREASE_LEVELS_ATTR: CombatLuck attribute for increase_levels
        _DAMAGE_RESISTANCE_LEVELS_ATTR: DamageResistance attribute (e.g. "pd_levels")
        _RESISTANCE_CHECK_INCLUDES_IS_RESISTANT: bool - PD checks `and not self.is_resistant`
            in calc_resistance, ED does not.
    """

    # Subclass must define these
    _CHAR_TYPE: CharacteristicType
    _DEFENSE_LABEL: str
    _COMBAT_LUCK_INCREASE_ATTR: str
    _COMBAT_LUCK_INCREASE_LEVELS_ATTR: str
    _DAMAGE_RESISTANCE_LEVELS_ATTR: str
    _RESISTANCE_CHECK_INCLUDES_IS_RESISTANT: bool = True

    def __init_subclass__(cls, xmlid: str = "", **kwargs):
        """Pass xmlid through to Characteristic's __init_subclass__."""
        super().__init_subclass__(xmlid=xmlid, **kwargs)

    def __init__(self):
        """Initialize defense characteristic."""
        super().__init__(self.XMLID)
        self.is_resistant: bool = False
        self._defense_resistance: int = 0
        self.primary_resistant_total: int = 0
        self.secondary_resistant_total: int = 0

    def _init(self, element=None):
        """Initialize from XML element."""
        super()._init(element)
        if element is not None:
            pass

    @property
    def type(self) -> int:
        """Get characteristic type."""
        return int(self._CHAR_TYPE)

    # ------------------------------------------------------------------
    # CombatLuck helpers
    # ------------------------------------------------------------------

    def _combat_luck_increase(self, combat_luck: 'CombatLuck') -> int:
        """Get the defense-specific increase from a CombatLuck instance."""
        return getattr(combat_luck, self._COMBAT_LUCK_INCREASE_ATTR)

    def _combat_luck_increase_levels(self, combat_luck: 'CombatLuck') -> int:
        """Get the defense-specific increase_levels from a CombatLuck instance."""
        return getattr(combat_luck, self._COMBAT_LUCK_INCREASE_LEVELS_ATTR)

    def _damage_resistance_levels(self, dr: 'DamageResistance') -> int:
        """Get the defense-specific levels from a DamageResistance instance."""
        return getattr(dr, self._DAMAGE_RESISTANCE_LEVELS_ATTR)

    # ------------------------------------------------------------------
    # Iteration helper
    # ------------------------------------------------------------------

    def _iter_powers_and_equipment(self, hero: 'Hero') -> Iterator[GenericObject]:
        """Yield each power and equipment item, expanding CompoundPower children.

        For each item in hero.powers and hero.equipment: if the item is a
        CompoundPower, yield its children; otherwise yield the item itself.
        CompoundPower containers are never yielded directly.
        """
        from kirby_cost.objects.powers.compound_power import CompoundPower
        for source in (hero.powers, getattr(hero, 'equipment', [])):
            for obj in source:
                if isinstance(obj, CompoundPower):
                    yield from obj.powers
                else:
                    yield obj

    # ------------------------------------------------------------------
    # calc_base_value  (identical in PD and ED)
    # ------------------------------------------------------------------

    def calc_base_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate base value (overrides base class)."""
        d = 0.0
        d2 = 1.0  # Automaton denominator

        # Check for Automaton
        if active_hero is not None:
            automaton = GenericObject.find_object_by_id(active_hero.powers, "AUTOMATON")
            if automaton is not None:
                if automaton.selected_option is not None:
                    option_xmlid = automaton.selected_option.xmlid.upper()
                    if option_xmlid.startswith("NOSTUN"):
                        d2 = float(automaton.base_pded_denominator)

        if active_hero is not None:
            self.base_level = self.orig_base_level / d2
            self.double_base = self.orig_base_level / d2

            # Check characteristics
            for char_obj in active_hero.characteristics:
                if (char_obj.xmlid == self.xmlid or
                    char_obj.increase_levels(self.type) <= 0 or
                    char_obj.increase(self.type) == 0.0 or
                    not CharAffectingObject.check_figured(char_obj, self.type)):
                    continue

                if isinstance(char_obj, Characteristic):
                    char_value = char_obj.characteristic_value(active_hero)
                    increase = char_obj.increase(self.type)
                    increase_levels = char_obj.increase_levels(self.type)
                    d4 = char_value * increase / float(increase_levels)
                    if "DEFENSE" not in (char_obj.types or []):
                        d4 /= d2
                    self.double_base += d4
                    d += round_half_up(d4)

            # Check powers and equipment (CompoundPower children are expanded)
            for item in self._iter_powers_and_equipment(active_hero):
                if item.xmlid == self.xmlid or not isinstance(item, Characteristic):
                    continue

                char_obj = item
                if (char_obj.increase_levels(self.type) <= 0 or
                    char_obj.increase(self.type) == 0.0 or
                    not char_obj.affect_primary or
                    not CharAffectingObject.check_figured(char_obj, self.type) or
                    not char_obj.affect_total):
                    continue

                d3 = char_obj.increase_value(self.type, True)
                self.double_base += d3 / d2
                d += round_half_up(d3 / d2)

        self.base_value = min(self.base_level + d, float(self.max_val))

    # ------------------------------------------------------------------
    # calc_defense_resistance  (PD adds `and not self.is_resistant`, ED does not)
    # ------------------------------------------------------------------

    def calc_defense_resistance(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate defense resistance."""
        from kirby_cost.objects.powers.compound_power import CompoundPower
        from kirby_cost.objects.powers.damage_resistance import DamageResistance

        n3 = 0

        if self.is_resistant:
            n3 = int(n3 + self.get_value(self.figured(active_hero), self.type, active_hero))

        if active_hero is not None:
            # Check powers and equipment; for CompoundPower, process sub-powers directly
            for source in (active_hero.powers, getattr(active_hero, 'equipment', [])):
                for item in source:
                    if isinstance(item, DamageResistance):
                        n3 += self._damage_resistance_levels(item)
                        continue

                    if item.xmlid == self.xmlid:
                        def_char = item
                        if self.is_resistant:
                            n3 += def_char.levels
                            continue

                        if GenericObject.find_object_by_id(def_char.assigned_modifiers, "RESISTANT") is None:
                            continue

                        if self._RESISTANCE_CHECK_INCLUDES_IS_RESISTANT:
                            if def_char.add_modifiers_to_base and not self.is_resistant:
                                n3 = int(float(n3) + self.get_value(self.figured(active_hero), self.type, active_hero))
                        else:
                            if def_char.add_modifiers_to_base:
                                n3 = int(float(n3) + self.get_value(self.figured(active_hero), self.type, active_hero))

                        if not def_char.affect_total:
                            continue
                        n3 += def_char.levels
                        continue

                    if isinstance(item, CompoundPower):
                        for sub_power in item.powers:
                            if isinstance(sub_power, DamageResistance):
                                n3 += self._damage_resistance_levels(sub_power)
                                continue

                            if sub_power.xmlid != self.xmlid:
                                continue

                            def_char = sub_power
                            if self.is_resistant:
                                n3 += def_char.levels
                                continue

                            if GenericObject.find_object_by_id(def_char.assigned_modifiers, "RESISTANT") is None:
                                continue

                            if self._RESISTANCE_CHECK_INCLUDES_IS_RESISTANT:
                                if def_char.add_modifiers_to_base and not self.is_resistant:
                                    n3 = int(float(n3) + self.get_value(self.figured(active_hero), self.type, active_hero))
                            else:
                                if def_char.add_modifiers_to_base:
                                    n3 = int(float(n3) + self.get_value(self.figured(active_hero), self.type, active_hero))

                            if not def_char.affect_total:
                                continue
                            n3 += def_char.levels

        self._defense_resistance = n3

    # ------------------------------------------------------------------
    # _calc_primary_value  (identical in PD and ED, modulo attribute names)
    # ------------------------------------------------------------------

    def _calc_primary_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate primary value (overrides base class)."""
        from kirby_cost.objects.talents.combat_luck import CombatLuck

        d2 = self.characteristic_value(active_hero)
        d3 = 1.0  # Automaton denominator

        # Check for Automaton
        if active_hero is not None:
            automaton = GenericObject.find_object_by_id(active_hero.powers, "AUTOMATON")
            if automaton is not None:
                if automaton.selected_option is not None:
                    option_xmlid = automaton.selected_option.xmlid.upper()
                    if option_xmlid.startswith("NOSTUN"):
                        d3 = float(automaton.base_pded_denominator)

        if active_hero is not None:
            # Check powers and equipment (CompoundPower children are expanded)
            for item in self._iter_powers_and_equipment(active_hero):
                if item.xmlid == self.xmlid:
                    char_obj = item
                    if not char_obj.affect_primary or not char_obj.affect_total:
                        continue
                    d2 += float(char_obj.levels)
                    self.double_base += float(char_obj.levels)
                    continue

                if isinstance(item, CombatLuck):
                    combat_luck = item
                    if (self._combat_luck_increase_levels(combat_luck) <= 0 or
                        not combat_luck.affect_primary or
                        not combat_luck.affect_total):
                        continue
                    d2 += round_half_up(float(self._combat_luck_increase(combat_luck)) * float(combat_luck.levels) / float(self._combat_luck_increase_levels(combat_luck)))
                    continue

                if (isinstance(item, CharAffectingObject) and
                    not isinstance(item, Characteristic) and
                    item.increase_levels(self.type) > 0 and
                    item.increase(self.type) != 0.0 and
                    item.affect_primary and
                    CharAffectingObject.check_figured(item, self.type) and
                    item.affect_total):
                    d4 = item.increase_value(self.type, True)
                    self.double_base += d4
                    d2 += round_half_up(d4)

            # Check talents for CombatLuck
            for talent in active_hero.talents:
                if isinstance(talent, CombatLuck):
                    combat_luck = talent
                    if (not combat_luck.affect_primary or
                        not combat_luck.affect_total):
                        continue
                    d2 = round_half_up(d2 + float(self._combat_luck_increase(combat_luck)) * float(combat_luck.levels) / float(self._combat_luck_increase_levels(combat_luck)))

        self.primary_value = d2

    # ------------------------------------------------------------------
    # calc_resistant_total  (identical modulo attribute names)
    # ------------------------------------------------------------------

    def calc_resistant_total(self, primary: bool, active_hero: Optional['Hero'] = None) -> None:
        """Calculate resistant total."""
        from kirby_cost.objects.powers.power import Power
        from kirby_cost.objects.talents.combat_luck import CombatLuck

        d = 0.0
        char_type = self._CHAR_TYPE

        if active_hero is not None:
            # Check powers and equipment (CompoundPower children are expanded)
            for item in self._iter_powers_and_equipment(active_hero):
                if isinstance(item, Power):
                    char_obj = item
                    if (char_obj.increase_levels(char_type) <= 0 or
                        not char_obj.resistant_defenses() or
                        (not char_obj.affect_primary and primary) or
                        not char_obj.affect_total):
                        continue
                    d += round_half_up(char_obj.increase(char_type) * float(char_obj.levels) / float(char_obj.increase_levels(char_type)))
                    continue

                if isinstance(item, CombatLuck):
                    combat_luck = item
                    if (self._combat_luck_increase_levels(combat_luck) <= 0 or
                        (not combat_luck.affect_primary and primary) or
                        not combat_luck.affect_total):
                        continue
                    d += round_half_up(float(self._combat_luck_increase(combat_luck)) * float(combat_luck.levels) / float(self._combat_luck_increase_levels(combat_luck)))

            # Check talents
            for talent in active_hero.talents:
                if isinstance(talent, CombatLuck):
                    combat_luck = talent
                    if ((not combat_luck.affect_primary and primary) or
                        not combat_luck.affect_total):
                        continue
                    d = round_half_up(d + float(self._combat_luck_increase(combat_luck)) * float(combat_luck.levels) / float(self._combat_luck_increase_levels(combat_luck)))

            # Add resistance (up to nonresistant total)
            n3 = self.get_defense_resistance(active_hero)
            n = self.nonresistant_total(primary, active_hero)
            if n3 <= n:
                d += float(n3)
            elif n > 0:
                d += float(n)

        if primary:
            self.primary_resistant_total = int(round_half_up(d))
        else:
            self.secondary_resistant_total = int(round_half_up(d))

    # ------------------------------------------------------------------
    # _calc_secondary_value  (identical modulo attribute names)
    # ------------------------------------------------------------------

    def _calc_secondary_value(self, active_hero: Optional['Hero'] = None) -> None:
        """Calculate secondary value (overrides base class)."""
        from kirby_cost.objects.talents.combat_luck import CombatLuck

        super()._calc_secondary_value(active_hero)
        d = self.get_secondary_value()

        if active_hero is not None:
            # Check talents for CombatLuck (secondary)
            for talent in active_hero.talents:
                if isinstance(talent, CombatLuck):
                    combat_luck = talent
                    if (combat_luck.affect_primary or
                        not combat_luck.affect_total):
                        continue
                    d += float(self._combat_luck_increase(combat_luck)) * float(combat_luck.levels) / float(self._combat_luck_increase_levels(combat_luck))

            # Check powers and equipment for CombatLuck (secondary;
            # CompoundPower children are expanded)
            for item in self._iter_powers_and_equipment(active_hero):
                if isinstance(item, CombatLuck):
                    combat_luck = item
                    if (combat_luck.affect_primary or
                        not combat_luck.affect_total):
                        continue
                    d += float(self._combat_luck_increase(combat_luck)) * float(combat_luck.levels) / float(self._combat_luck_increase_levels(combat_luck))

        self.secondary_value = d

    # ------------------------------------------------------------------
    # display_notes, nonresistant_total, resistance caching, roll
    # ------------------------------------------------------------------

    def display_notes(self, active_hero: Optional['Hero'] = None) -> str:
        """Get display notes with defense label."""
        label = self._DEFENSE_LABEL
        n = self.resistant_total(True, active_hero)
        n2 = self.resistant_total(False, active_hero)
        n3 = self.nonresistant_total(True, active_hero)
        n4 = self.nonresistant_total(False, active_hero)

        string = str(n3)
        if n3 != n4:
            string = f"{string}/{n4}"

        string = f"{string} {label} ({n}"
        if n != n2:
            string = f"{string}/{n2}"

        string = f"{string} r{label})"
        return string

    def nonresistant_total(self, primary: bool, active_hero: Optional['Hero'] = None) -> int:
        """Get nonresistant total."""
        d2 = 0.0
        if primary:
            d2 += self.get_primary_value(active_hero)
        else:
            d2 += self.get_secondary_value(active_hero)

        if d2 < float(self.max_val):
            return int(round_half_up(d2))
        return self.max_val

    def get_defense_resistance(self, active_hero: Optional['Hero'] = None) -> int:
        """Get defense resistance."""
        self.calc_defense_resistance(active_hero)
        return self._defense_resistance

    def resistant_total(self, primary: bool, active_hero: Optional['Hero'] = None) -> int:
        """Get resistant total."""
        self.calc_resistant_total(primary, active_hero)
        if primary:
            return self.primary_resistant_total
        else:
            return self.secondary_resistant_total

    def roll(self, active_hero: Optional['Hero'] = None) -> str:
        """Defense characteristics don't have a roll."""
        return ""
