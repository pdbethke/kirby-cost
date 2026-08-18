"""Reading an HDC element into an object — the twin of SerializationMixin.

Writing was always a mixin (``SerializationMixin.get_save_xml``). Reading was
not: it was ``_init`` plus a loose ``read_element`` on ``GenericObject``, so
the two directions did not look like the pair they are, and nothing made them
symmetric. They diverged accordingly — for years the read side and the write
side described the same element with different, hand-maintained lists.

The three pieces now line up:

* ``XMLAttrsMixin`` (xml_attrs.py) — the DECLARATIONS, shared vocabulary;
* ``DeserializationMixin`` (here) — element in, object out;
* ``SerializationMixin`` (serialize.py) — object in, element out.

Per-class reading that cannot be declared stays where it belongs, in that
class's ``_init``. What lives here is what every object does identically:
apply the declared attributes, remember what the document said, and descend
into the children an element contains.
"""
from __future__ import annotations

from kirby_cost.engine.xml_attrs import XMLAttrError


class DeserializationMixin:
    """Element in, object out."""

    def read_xml_attrs(self, element) -> None:
        """Apply every readable declared attribute the element carries.

        An absent attribute leaves the field at its default: absent and
        present-but-empty are different statements, and HD makes both.
        """
        for descriptor in self.xml_schema():
            if not descriptor.read:
                continue
            raw = element.get(descriptor.attr)
            if raw is None:
                continue
            try:
                value = descriptor.parse(raw)
            except (ValueError, TypeError):
                # The document said something this attribute's type cannot
                # express (LEVELS="" and friends). HD tolerates it; so do we.
                continue
            existing = getattr(self, descriptor.field, None)
            if callable(existing):
                raise XMLAttrError(
                    f"{type(self).__name__}.{descriptor.field} is a method; "
                    f"{descriptor.attr} must name the field it gates, not the "
                    f"accessor (e.g. use_standard_effect, not uses_...)"
                )
            try:
                setattr(self, descriptor.field, value)
            except AttributeError as exc:
                # Fields are looked up by NAME, so Python's descriptor protocol
                # applies: a property is invoked transparently, and a read-only
                # one raises here. That is a declaration bug, not bad input.
                raise XMLAttrError(
                    f"{type(self).__name__}.{descriptor.field} cannot be set "
                    f"from {descriptor.attr} (read-only property?)"
                ) from exc

    def read_element(self, element) -> None:
        """Read this element and the children it contains.

        Was ``restore_from_save`` — a name that promised the file-loading
        path while HDCLoader used ``_init``, so the two drifted for years:
        adders and modifiers came through here and got POSITION, TEXT and
        USE_END_RESERVE, while powers and skills came through ``_init``
        and did not. Everything scalar now lives in ``_init`` (declared
        once in XML_ATTRS); this adds only what ``_init`` cannot do
        without double-parsing — descending into ADDER and MODIFIER
        children, which the loader handles itself for powers.
        """
        if element is None:
            return
        self._init(element)
        # Parse adders
        for adder_elem in XMLUtility.children(element, "ADDER"):
            adder = self._create_adder_from_xml(adder_elem)
            if adder:
                adder.parent = self
                adder.read_element(adder_elem)
                self._assigned_adders.append(adder)
        
        # Parse modifiers
        for mod_elem in XMLUtility.children(element, "MODIFIER"):
            modifier = self._create_modifier_from_xml(mod_elem)
            if modifier:
                modifier.parent = self
                modifier.read_element(mod_elem)
                if not modifier.display:
                    modifier.display = modifier.alias if modifier.alias else ""
                self._assigned_modifiers.append(modifier)
        
        # Ensure all modifiers have parent set
        for modifier in self._assigned_modifiers:
            modifier.parent = self
        
        input_val = XMLUtility.get_value(element, "INPUT")
        if input_val is not None:
            self.input = input_val
        
        # Set abbreviation from alias
        if self._alias:
            self.abbreviation = self._alias
