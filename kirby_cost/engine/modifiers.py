"""
ModifierMixin — modifier/adder list management for GenericObject.

Handles the null-guard initialization, lookup, and aggregation of
modifiers, adders, and options.
"""

from typing import Optional, List, TYPE_CHECKING

# Framework predicates are lazy-imported inside the methods that need them.
# See the same note in engine/cost.py — circular via base.py.

if TYPE_CHECKING:
    from kirby_cost.objects.adder import Adder
    from kirby_cost.objects.modifier import Modifier
    from kirby_cost.objects.base import GenericObject


class ModifierMixin:
    """Modifier and adder list management.

    Mixed into GenericObject. Relies on these attributes from the host:
    - assigned_modifiers, assigned_adders, available_adders, options,
      selected_option, parent, main_power, types
    """

    @property
    def assigned_modifiers(self) -> List['Modifier']:
        """Get the list of assigned modifiers. Override in subclasses."""
        if self._assigned_modifiers is None:
            self._assigned_modifiers = []
        return self._assigned_modifiers

    @assigned_modifiers.setter
    def assigned_modifiers(self, value: List['Modifier']) -> None:
        self._assigned_modifiers = value

    @property
    def assigned_adders(self) -> List['Adder']:
        """Get the list of assigned adders. Override in subclasses."""
        if self._assigned_adders is None:
            self._assigned_adders = []
        return self._assigned_adders

    @assigned_adders.setter
    def assigned_adders(self, value: List['Adder']) -> None:
        self._assigned_adders = value

    @property
    def available_adders(self) -> List['Adder']:
        """Get the list of available adders. Override in subclasses."""
        if self._available_adders is None:
            self._available_adders = []
        return self._available_adders

    @available_adders.setter
    def available_adders(self, value: List['Adder']) -> None:
        self._available_adders = value

    @property
    def options(self) -> List['Adder']:
        """Get the list of options. Override in subclasses."""
        if self._options is None:
            self._options = []
        return self._options

    @options.setter
    def options(self, value: List['Adder']) -> None:
        self._options = value

    @property
    def selected_option(self) -> Optional['Adder']:
        """Get the currently selected option. Override in subclasses."""
        return self._selected_option

    @selected_option.setter
    def selected_option(self, option: Optional['Adder']) -> None:
        """Set the currently selected option. Override in subclasses."""
        self._selected_option = option

    @property
    def types(self) -> List[str]:
        """Get the list of types for this object, including modifier-derived types."""
        if self._types is None:
            self._types = []
        types_list = list(self._types)

        uoo = self.find_modifier_by_id("UOO")
        if uoo and uoo.selected_option and uoo.selected_option.xmlid == "UAA":
            types_list.append("ATTACK")
        if self.find_modifier_by_id("BOECV"):
            types_list.append("MENTAL")
        if self.find_modifier_by_id("ABSORPTIONASDEFENSE"):
            types_list.append("DEFENSE")

        return types_list

    @types.setter
    def types(self, value: List[str]) -> None:
        self._types = value

    def find_modifier_by_id(self, xmlid: str) -> Optional['Modifier']:
        """Find a modifier by XML ID in assigned modifiers."""
        from kirby_cost.objects.base import GenericObject
        return GenericObject.find_object_by_id(self.assigned_modifiers, xmlid)

    @property
    def all_assigned_modifiers(self) -> List['Modifier']:
        """Get all assigned modifiers, including from parent list if applicable."""
        from kirby_cost.objects.base import GenericObject
        from kirby_cost.objects.frameworks import is_multipower
        from kirby_cost.objects.modifiers.linked import is_linked

        modifiers = list(self.assigned_modifiers)

        parent = self._parent
        if self.main_power:
            parent = self.main_power.parent

        if parent:
            for mod in parent.assigned_modifiers:
                if mod.types and "VPP" in mod.types:
                    continue
                if mod.xmlid == "CHARGES" and is_multipower(parent):
                    continue
                if is_linked(mod):
                    continue
                if GenericObject.find_object_by_id(modifiers, mod.xmlid):
                    continue
                modifiers.append(mod)

        return modifiers
