"""
SerializationMixin — XML save/restore for GenericObject.

Extracted from GenericObject to separate serialization from object management.
"""

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from kirby_cost.objects.base import GenericObject


class SerializationMixin:
    """XML serialization support for GenericObject.

    Mixed into GenericObject. Relies on attributes/methods from the host.
    """

    def get_general_save_xml(self):
        """
        Get XML element for saving this object (general attributes).

        Returns:
            lxml.etree.Element representing this object's saved state
        """
        from lxml import etree

        # Use xmlid as tag for frameworks so the loader recognizes them
        _FRAMEWORK_TAGS = {"MULTIPOWER", "VPP", "ELEMENTALCONTROL", "LIST"}
        fw_tag = getattr(self, '_framework_tag', None)
        if fw_tag:
            tag = fw_tag
        elif self.xmlid in _FRAMEWORK_TAGS:
            tag = self.xmlid
        else:
            tag = "GENERIC_OBJECT"
        element = etree.Element(tag)

        element.set("XMLID", self.xmlid or "")
        element.set("ID", str(self._id))
        element.set("BASECOST", str(self.base_cost))
        element.set("LEVELS", str(self._levels))
        element.set("LVLCOST", str(self._level_cost))
        element.set("LVLVAL", str(self._level_value))
        if self.min_set:
            element.set("MINCOST", str(self._minimum_cost))
        if self.max_set:
            element.set("MAXCOST", str(self._max_cost))
        element.set("ALIAS", str(self._alias or ""))

        if self.text_output and self.text_output.strip():
            element.set("TEXT", str(self.text_output))

        element.set("POSITION", str(self.position))
        element.set("MULTIPLIER", str(self.multiplier))

        if self._quantity > 1:
            element.set("QUANTITY", str(self._quantity))

        element.set("GRAPHIC", self.graphic or "")
        element.set("COLOR", self.color or "")
        element.set("SFX", self.sfx or "")

        if self._use_end_reserve:
            element.set("USE_END_RESERVE", "Yes")

        element.set("SHOW_ACTIVE_COST", "Yes" if self.display_active_cost else "No")

        if self._is_equipment:
            element.set("PRICE", str(self.price if hasattr(self, 'price') else 0.0))
            element.set("WEIGHT", str(self._weight if hasattr(self, 'weight') else 0.0))
            element.set("CARRIED", "Yes" if getattr(self, 'carried', True) else "No")

        if self._selected_option:
            option = self._selected_option
            element.set("OPTION", option.xmlid or "")
            element.set("OPTIONID", option.xmlid or "")
            element.set("OPTION_ALIAS", option.alias or "")
        elif hasattr(self, 'option_id') and self.option_id:
            element.set("OPTIONID", str(self.option_id))

        notes_elem = etree.SubElement(element, "NOTES")
        notes_elem.text = self.notes or ""

        element.set("INCLUDE_NOTES_IN_PRINTOUT",
                     "Yes" if self.include_notes_in_printout else "No")

        # Derive effective parent ID from parent_id or _parent object
        effective_parent_id = self.parent_id if self.parent_id and self.parent_id > 0 else 0
        if effective_parent_id == 0 and self._parent is not None and hasattr(self._parent, '_id'):
            effective_parent_id = self._parent._id

        if effective_parent_id > 0:
            element.set("PARENTID", str(effective_parent_id))
            parent_list = self._parent
            if parent_list:
                try:
                    from kirby_cost.objects.frameworks.multipower import Multipower
                    if isinstance(parent_list, Multipower):
                        element.set("ULTRA_SLOT", "Yes" if self.ultra else "No")
                except ImportError:
                    pass
                # Also write ULTRA_SLOT for _FallbackObject multipowers
                if parent_list.xmlid == "MULTIPOWER":
                    element.set("ULTRA_SLOT", "Yes" if self.ultra else "No")

        if self._name:
            element.set("NAME", self._name)

        if self.input and self.input.strip():
            element.set("INPUT", self.input)

        self._get_adder_save_xml(element)
        self._get_modifier_save_xml(element)

        return element

    def _get_adder_save_xml(self, element):
        """Add adder XML to the element."""
        for adder in self.assigned_adders:
            if hasattr(adder, 'get_save_xml'):
                element.append(adder.get_save_xml())

    def _get_modifier_save_xml(self, element):
        """Add modifier XML to the element."""
        for modifier in self.assigned_modifiers:
            if hasattr(modifier, 'get_save_xml'):
                element.append(modifier.get_save_xml())

    def get_save_xml(self):
        """Get XML element for saving this object. Override in subclasses."""
        return self.get_general_save_xml()
