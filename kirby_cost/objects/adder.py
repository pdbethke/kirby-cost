"""
Adder class stub.

This is a placeholder for the full Adder implementation.
Adder extends GenericObject and represents adders that can be added to powers.
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.base import GenericObject
from kirby_cost.engine.xml_attrs import XMLAttr

if TYPE_CHECKING:
    from kirby_cost.template.dataclasses import AdderTemplate


class Adder(GenericObject):
    """Adder class - extends GenericObject."""

    #: HD states these on every adder, as Yes/No. They were written only when
    #: true, so "SELECTED=No" came back as no attribute at all — a different
    #: statement, on 60 of Ravel's elements.
    XML_ATTRS = (
        XMLAttr("REQUIRED", "_required", "yesno"),
        XMLAttr("SELECTED", "_selected", "yesno"),
        XMLAttr("GROUP", "_group", "yesno"),
        XMLAttr("DISPLAYINSTRING", "_display_in_string", "yesno"),
    )

    
    def __init__(self):
        """Initialize an Adder."""
        super().__init__()
        self._required = False
        self._selected = False
        self._group = False
        self._display_in_string = True
        self._is_private = False
        self._parent_object: Optional[GenericObject] = None
    
    def apply_adder_template(self, tmpl: "AdderTemplate") -> None:
        """Apply adder-specific template defaults.

        Unlike ``apply_template`` (which handles full TemplateData), this
        accepts an ``AdderTemplate`` — the per-adder entry found inside a
        parent template's ``adders`` dict.

        XML-supplied values (``_base_cost_from_xml``) are preserved.
        """
        if not self._base_cost_from_xml and self._base_cost == 0.0 and tmpl.base_cost != 0:
            self._base_cost = tmpl.base_cost
        if self._level_cost == 0.0 and tmpl.level_cost != 0:
            self._level_cost = tmpl.level_cost
        if self._level_value == 0.0 and tmpl.level_value != 0:
            self._level_value = tmpl.level_value
        if self.level_power == 0 and tmpl.level_power not in (0, 1):
            self.level_power = tmpl.level_power
        if self.level_multiplier == 1 and tmpl.level_multiplier != 1:
            self.level_multiplier = tmpl.level_multiplier
        if not self._types and tmpl.types:
            self._types = list(tmpl.types)

    @property
    def is_required(self) -> bool:
        """Check if this adder is required."""
        return self._required
    
    @property
    def is_selected(self) -> bool:
        """Check if this adder is selected."""
        return self._selected
    
    @property
    def is_group(self) -> bool:
        """Check if this adder is a group."""
        return self._group
    
    @property
    def real_cost(self) -> float:
        """Get the real cost of this adder."""
        return self.total_cost
    
    @property
    def total_cost(self) -> float:
        """
        Get the total cost of this adder.

        Unlike GenericObject, Adder uses simple division (no floor/ceil)
        for level calculations: levels / levelValue * levelCost.

        Ported from Adder.java getTotalCost().
        """
        d = 0.0
        if self.is_selected:
            d += self.base_cost
            if self._level_value != 0.0:
                d += float(self._levels) / self._level_value * self._level_cost
        else:
            for adder in self.assigned_adders:
                d += adder.real_cost

        if d < self._minimum_cost and d < 0.0 and self.min_set:
            d = self._minimum_cost
        elif d > self._max_cost and d > 0.0 and self.max_set:
            d = self._max_cost
        return d
    
    def double_total(self, check_selected: bool = False) -> float:
        """
        Get the total cost as a double (for modifier calculations).
        
        Args:
            check_selected: If True, only include cost if selected
        
        Returns:
            Total cost as float
        """
        total = 0.0
        
        if self.is_selected or not check_selected:
            total += self.base_cost
            if self._level_value != 0.0:
                level_units = float(self._levels) / self._level_value
                total += level_units * self._level_cost
        else:
            # If not selected, only count assigned adders
            for adder in self.assigned_adders:
                total += adder.real_cost
        
        # Apply min/max limits
        if total < self._minimum_cost and total < 0.0 and self.min_set:
            total = self._minimum_cost
        elif total > self._max_cost and total > 0.0 and self.max_set:
            total = self._max_cost
        
        return total
    
    def contains_type(self, type_name: str) -> bool:
        """Check if this adder contains the given type.

        Overrides GenericObject.containsType() — ported from Adder.java:
        If selected, check own types.  If NOT selected, recurse into sub-adders.
        """
        if self.is_selected:
            return type_name in self.types
        for adder in self.assigned_adders:
            if adder.contains_type(type_name):
                return True
        return False

    def include_in_base(self) -> bool:
        """Check if this adder should be included in base cost calculation."""
        return False
    
    @property
    def custom(self) -> bool:
        """Check if this is a custom adder."""
        return self.xmlid in ("GENERIC_OBJECT", "CUSTOM_ADDER")
    
    @property
    def display_in_string(self) -> bool:
        """Whether this adder should be displayed in the string."""
        return self._display_in_string

    @display_in_string.setter
    def display_in_string(self, value: bool) -> None:
        self._display_in_string = value
    
    @property
    def parent(self) -> Optional['GenericObject']:
        """Get the parent object."""
        return getattr(self, '_parent_object', None)

    @parent.setter
    def parent(self, parent: 'GenericObject') -> None:
        """Set the parent object for this adder."""
        self._parent_object = parent
    
    def get_save_xml(self):
        """Get XML element for saving this adder."""
        from lxml import etree
        
        element = super().get_save_xml()
        element.tag = "ADDER"
        
        # REQUIRED/SELECTED/GROUP are declared in XML_ATTRS and written by the
        # table. They used to be re-set here, AFTER it, which overwrote the
        # document's own "YES" with "Yes" on every adder — the fourth
        # hand-maintained list of the same three facts.
        return element

