"""
SerializationMixin — XML save/restore for GenericObject.

Extracted from GenericObject to separate serialization from object management.
"""

from typing import Optional, List, TYPE_CHECKING
from kirby_cost.engine.xml_attrs import _UNSET, XMLField

if TYPE_CHECKING:
    from kirby_cost.objects.base import GenericObject


class SerializationMixin:
    """XML serialization support for GenericObject.

    Mixed into GenericObject. Relies on attributes/methods from the host.
    """

    def _verbatim_or_format(self, descriptor, value) -> str:
        """The document's own text when the value is unchanged; ours otherwise.

        Formatting is not part of the meaning: "YES"/"Yes", "1.0"/"1" and
        "0"/"0.0" all parse identically, and re-rendering them makes a file
        that differs from HD's everywhere while saying exactly the same thing.
        """
        raw = getattr(self, "_source_attr_values", {}).get(descriptor.attr)
        if raw is not None:
            try:
                if descriptor.parse(raw) == value:
                    return raw
            except (ValueError, TypeError):
                pass
        return descriptor.format(value)

    def reorder_to_source(self, element) -> None:
        """Restore the attribute order the document used.

        A set or a dict keyed by name answers "was this attribute present"
        but not "in what order" — and lxml writes attributes in the order they
        were set, so a schema-ordered element is a gratuitous diff against
        every file HD has produced even when every value is identical. Source
        attributes come back in their original order; anything new is appended.
        """
        order = getattr(self, "_source_attr_order", ())
        if not order:
            return
        current = dict(element.attrib)
        ordered = [(k, current.pop(k)) for k in order if k in current]
        ordered.extend(current.items())
        element.attrib.clear()
        for key, value in ordered:
            element.set(key, value)

    def write_xml_attrs(self, element) -> None:
        """Emit every writable declared attribute this object holds.

        Reads through ``getattr``, so a declared field that is a property runs
        its getter. Prefer the plain field where a property's getter has side
        effects — ``CharAffectingObject.affect_total`` writes to
        ``affects_total`` when it is read, and serializing a character is not
        allowed to change it.
        """
        stated = getattr(self, "_source_attrs", None)
        defaults = type(self).default_values()
        for descriptor in self.xml_schema():
            if not descriptor.write:
                continue
            value = getattr(self, descriptor.field, None)
            if value is None:
                continue
            if descriptor.omit_if != "__never__" and value == descriptor.omit_if:
                continue
            if stated and descriptor.attr not in stated:
                # The document did not state it. Write it only if this object
                # has since been changed away from its default — otherwise we
                # would be adding attributes HD never wrote.
                default = defaults.get(descriptor.field, _UNSET)
                if default is not _UNSET and value == default:
                    continue
            element.set(descriptor.attr, self._verbatim_or_format(descriptor, value))

    def get_general_save_xml(self):
        """
        Get XML element for saving this object (general attributes).

        Returns:
            lxml.etree.Element representing this object's saved state
        """
        from lxml import etree

        # The element's tag, in order of authority: the framework tag the
        # loader recorded, then the tag this object was READ from, then the
        # xmlid for a framework, and only then the GENERIC_OBJECT fallback.
        #
        # The source tag matters because HD's tag does not follow from the
        # class: a CompoundPower is <POWER XMLID="COMPOUNDPOWER">. Writing it
        # as <GENERIC_OBJECT> produces a file HD opens without complaint and
        # quietly two powers lighter. Our own loader is more forgiving and
        # reads it back whole, which is precisely why this was invisible.
        _FRAMEWORK_TAGS = {"MULTIPOWER", "VPP", "ELEMENTALCONTROL", "LIST"}
        fw_tag = getattr(self, '_framework_tag', None)
        source_tag = getattr(self, '_source_tag', None)
        if fw_tag:
            tag = fw_tag
        elif source_tag:
            tag = source_tag
        elif self.xmlid in _FRAMEWORK_TAGS:
            tag = self.xmlid
        else:
            tag = "GENERIC_OBJECT"
        element = etree.Element(tag)

        # Likewise the XMLID: the loader rewrites a framework's xmlid from its
        # tag (MULTIPOWER, VPP) for the registry's sake, which discards the
        # GENERIC_OBJECT the file actually carried. Write back what was read.
        element.set("XMLID", getattr(self, '_source_xmlid', '') or self.xmlid or "")
        element.set("ID", str(self._id))
        # Cost parameters are written only when the SOURCE stated them. An
        # HDC carries overrides, not resolved values; echoing a template
        # default back as an attribute turns it into a per-character override.
        # An object built in Python has no source, so everything it holds is
        # its own statement and all of it is written.
        stated = getattr(self, "_source_attrs", None)

        def _from_source(attr: str) -> bool:
            return stated is None or not stated or attr in stated

        element.set("BASECOST", str(self.base_cost))
        element.set("LEVELS", str(self._levels))
        if _from_source("LVLCOST"):
            element.set("LVLCOST", str(self._level_cost))
        if _from_source("LVLVAL"):
            element.set("LVLVAL", str(self._level_value))
        if self.min_set and _from_source("MINCOST"):
            element.set("MINCOST", str(self._minimum_cost))
        if self.max_set and _from_source("MAXCOST"):
            element.set("MAXCOST", str(self._max_cost))
        element.set("ALIAS", str(self._alias or ""))

        if self.text_output and self.text_output.strip():
            element.set("TEXT", str(self.text_output))

        # Everything declared in XML_ATTRS — the same inventory the loader
        # reads. POSITION, MULTIPLIER, GRAPHIC, COLOR, SFX, the two display
        # flags, and whatever the subclass adds (ForceField's PDLEVELS).
        # Emitted here rather than restated, so read and write cannot drift.
        if hasattr(self, "write_xml_attrs"):
            self.write_xml_attrs(element)


        if self._use_end_reserve:
            element.set("USE_END_RESERVE", "Yes")


        if self._is_equipment:
            element.set("PRICE", str(self.price if hasattr(self, 'price') else 0.0))
            element.set("WEIGHT", str(self._weight if hasattr(self, 'weight') else 0.0))
            element.set("CARRIED", "Yes" if getattr(self, 'carried', True) else "No")

        if self._selected_option:
            option = self._selected_option
            element.set("OPTION", option.xmlid or "")
            element.set("OPTIONID", option.xmlid or "")
            # The template's alias is the full canonical phrasing; the file may
            # carry a shorter one the character actually used. The document's
            # text is what HD wrote and what it will show, so it wins.
            stated = getattr(self, "_source_attr_values", {}).get("OPTION_ALIAS")
            element.set("OPTION_ALIAS",
                        stated if stated is not None else (option.alias or ""))
        elif hasattr(self, 'option_id') and self.option_id:
            element.set("OPTIONID", str(self.option_id))

        notes_elem = etree.SubElement(element, "NOTES")
        notes_elem.text = self.notes or ""


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

        # An explicit NAME="" is what HD writes for an unnamed object; omitting
        # it is a different document, even though it reads back the same.
        if self._name or "NAME" in getattr(self, "_source_attrs", ()):
            element.set("NAME", self._name or "")

        if self.input and self.input.strip():
            element.set("INPUT", self.input)

        self._get_adder_save_xml(element)
        self._get_modifier_save_xml(element)

        if hasattr(self, "reorder_to_source"):
            self.reorder_to_source(element)

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