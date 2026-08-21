"""
Adder class stub.

This is a placeholder for the full Adder implementation.
Adder extends GenericObject and represents adders that can be added to powers.
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.base import option_alias, GenericObject
from kirby_cost.engine.xml_attrs import XMLAttr

if TYPE_CHECKING:
    from kirby_cost.template.dataclasses import AdderTemplate


class Adder(GenericObject):
    """Adder class - extends GenericObject."""

    def to_build_dict(self) -> dict:
        """An adder exports less than a power: no alias, name or input."""
        d = self._build_dict_core()
        if getattr(self, "_selected", False):
            d["selected"] = True
        # REQUIRED gates whether some skills/perks count an adder's cost at
        # all (Reputation skips required HOWWELL/HOWWIDE).
        if getattr(self, "_required", False):
            d["required"] = True
        nested = [a.to_build_dict() for a in self.assigned_adders]
        if nested:
            d["adders"] = nested
        return d


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
        self._template_has_sub_adders = False
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

        # Display-only, and neither is ever stated by an HDC file: REQUIRED is
        # a property of the template, and ALIAS is what the template says to
        # PRINT as opposed to what it calls the adder. Both were parsed out of
        # the .hdt and then dropped, so a required adder rendered as though it
        # were optional (printing its own name alongside its option) and an
        # adder whose alias deliberately opens an unclosed bracket printed its
        # display text instead.
        if tmpl.required:
            self._required = True
        if tmpl.alias and not (self._alias or '').strip():
            self._alias = tmpl.alias
        # The template's DISPLAY, which an HDC file never writes for an adder.
        # It carries the [LVL] marker — `DISPLAY="x[LVL] Shots"` — and
        # addAliasToVector suppresses the level suffix when it is present,
        # because the alias already says the number. Without it every such
        # adder printed its count twice: "x8 Noncombat:  x8".
        if tmpl.display and not (self._display or "").strip():
            self._display = tmpl.display
        # Whether this adder heads a group. HD keeps group adders ahead of the
        # plain ones in an adder string, and the only place that is stated is
        # the template.
        if tmpl.has_sub_adders:
            self._template_has_sub_adders = True

    @property
    def column2_output(self) -> str:
        """``Eating: Character only has to eat once per week`` — what an adder
        contributes to the line above it.

        Ported from ``Adder.getColumn2Output`` (Adder.java). Adder inherited
        GenericObject's default, which knows nothing about `showAlias`, the
        selected option, or the level suffix, so Life Support rendered as
        "(Eating:; Immunity; Immunity:; Self-Contained)" — every adder reduced
        to its own name and a colon.

        An unselected adder contributes only what its children contribute: it
        is a GROUP, and the group heading is not itself a thing the character
        bought.
        """
        adders = self.adder_string
        ret = ""
        if self.is_selected:
            if self.show_alias:
                ret += self.alias or ""
            ret = ret.strip()
            option = (option_alias(self) or "").strip()
            if option:
                if ret.strip():
                    ret += " "
                ret += option
            if self.input and self.input.strip():
                if ret.strip():
                    ret += " "
                ret += self.input
        if adders.strip():
            if ret.strip():
                ret += ", "
            ret += adders
        if self._levels > 0 and "[LVL]" not in (self._display or ""):
            ret += f":  +{self._levels}"
        return ret

    def __str__(self) -> str:
        """Java ``Adder.toString()``: the alias once the adder is selected.

        This matters only in one place, and it is not obvious: sorting.
        ``getSortingValue()`` is ``toString()``, and Sense.getAdderString sorts
        on it — so a Detect's adders order by what they are CALLED, not by
        their xmlid. Ours returned the xmlid, so ANALYZESENSE sorted before
        DISCRIMINATORY and the comparator's special case (which rewrites
        "ANALYZE" to "DISCRIMINATORYANALYZE" so Analyze follows
        Discriminatory) never matched anything.
        """
        if self.is_selected:
            return self.alias or ""
        return super().__str__()

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
        """``Adder.includeInBase`` (Adder.java:95).

        Not a stub: the template's INCLUDEINBASE flag, OR required. A 6E
        power's range is its total cost times ten with every adder that is
        NOT in the base subtracted first, so answering False for everything
        made every adder count toward range.
        """
        return bool(self.included_in_base or self.is_required)
    
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

