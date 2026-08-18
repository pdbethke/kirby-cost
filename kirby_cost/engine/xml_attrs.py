"""One declaration per XML attribute, used by both reading and writing.

Before this, an element's attributes were described in three separate
hand-maintained places:

* ``GenericObject._init`` — the cost-bearing half (BASECOST, LEVELS, LVLCOST…),
  which is what ``HDCLoader`` calls;
* ``GenericObject.restore_from_save`` — POSITION, PARENTID, MULTIPLIER, TEXT,
  USE_END_RESERVE, which the loader never calls at all;
* ``get_general_save_xml`` — a third list, for writing.

None of the three agreed, and nothing made them. An engine built to reach
oracle parity only ever needed the attributes that change a cost, so the rest
were read by whichever path happened to mention them and written by whichever
path happened to remember. The failure only surfaces on the way back out: a
character re-exported through this engine came back with every element at
POSITION 0, and two Resistant Protections stripped of the PDLEVELS/EDLEVELS
that HERO Designer costs them by — 38 points, silently, in a file that opened
without complaint.

So attributes are declared ONCE, here, and both directions consume the
declaration. Adding an attribute is a single line, and a round trip cannot drop
it, because the reader and the writer are the same list.

``read`` exists for the handful whose ingest is genuinely bespoke — MINCOST and
MAXCOST also set ``min_set``/``max_set``, BASECOST records whether the XML
supplied it at all — where ``_init`` keeps the logic but the attribute is still
declared here so the writer stays driven by one inventory.
"""
from __future__ import annotations

from typing import Any

_UNSET = object()


class XMLAttrError(TypeError):
    """A declaration that cannot be honoured — a field that will not take the
    value. Raised rather than skipped: a declared attribute that silently fails
    to load is the exact failure this module exists to end."""


class XMLAttr:
    """One attribute of an HDC element, and the field it lives in."""

    __slots__ = ("attr", "field", "kind", "read", "write", "omit_if",
                 "parse_with", "format_with")

    def __init__(self, attr: str, field: str, kind: str = "str", *,
                 read: bool = True, write: bool = True,
                 omit_if: Any = "__never__",
                 parse_with=None, format_with=None) -> None:
        #: the XML attribute name, e.g. "POSITION"
        self.attr = attr
        #: the attribute on the object, e.g. "position"
        self.field = field
        #: str | int | float | yesno
        self.kind = kind
        #: False when _init owns the read (bespoke side effects)
        self.read = read
        #: False for attributes that are read but must not be echoed back
        self.write = write
        #: skip writing when the value equals this (HD omits some defaults)
        self.omit_if = omit_if
        #: coercions for attributes the four built-in kinds cannot express —
        #: Skill.characteristic is a CharacteristicType int while the document
        #: writes "INT"/"GENERAL", and getting that pair wrong costs 3 vs 2.
        self.parse_with = parse_with
        self.format_with = format_with

    def parse(self, raw: str) -> Any:
        if self.parse_with is not None:
            return self.parse_with(raw)
        if self.kind == "int":
            return int(float(raw))
        if self.kind == "float":
            return float(raw)
        if self.kind == "yesno":
            # HD is not consistent about case: modifiers carry SELECTED="Yes"
            # and adders SELECTED="YES". Matching "Yes" exactly read the latter
            # as False on 60 of Ravel's adders — a silent data change, not a
            # formatting one.
            return raw.strip().upper() == "YES"
        return raw

    def format(self, value: Any) -> str:
        if self.format_with is not None:
            return self.format_with(value)
        if self.kind == "yesno":
            return "Yes" if value else "No"
        if self.kind == "int":
            return str(int(value))
        return str(value)


class XMLField(XMLAttr):
    """An XML attribute declared AS the Python attribute that holds it.

    ``XMLAttr`` keeps the field name as a string, which means the declaration
    and the field are two separate things that can disagree. They did::

        XMLAttr("USESTANDARDEFFECT", "uses_standard_effect", "yesno")

    named the METHOD that gates the field rather than the field, and the read
    replaced it with a bool. Nothing could have caught that: the string is not
    checked against anything until it runs.

    Declared as a descriptor, the field IS the attribute::

        use_standard_effect = XMLField("USESTANDARDEFFECT", "yesno", default=False)

    so the name cannot be wrong, cannot collide with a method, and carries its
    own default — which also retires ``default_values()``, whose only way to
    learn a default was to construct a probe instance of the class.

    The XML name stays explicit and is never derived from the Python name:
    PDLEVELS/pd_levels, SHOW_ACTIVE_COST/display_active_cost and
    USESTANDARDEFFECT/use_standard_effect share no rule between them.
    """

    __slots__ = ("default", "_store")

    def __init__(self, attr: str, kind: str = "str", default: Any = None,
                 **kwargs) -> None:
        super().__init__(attr, "", kind, **kwargs)
        self.default = default
        self._store = ""

    def __set_name__(self, owner, name: str) -> None:
        self.field = name
        self._store = f"_xmlfield_{name}"

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        return getattr(obj, self._store, self.default)

    def __set__(self, obj, value) -> None:
        setattr(obj, self._store, value)


class XMLAttrsMixin:
    """Read and write an object's declared attributes.

    Each class contributes its own ``XML_ATTRS``; the effective schema is the
    merge up the MRO, so a subclass adds what it owns (ForceField's PDLEVELS)
    without restating what it inherits, and can override one entry by
    redeclaring the same attribute name.
    """

    #: Declared per class. Base classes first in effect; see xml_schema().
    XML_ATTRS: tuple = ()

    @classmethod
    def default_values(cls) -> dict:
        """What a freshly built instance holds, per declared field.

        Used to answer "did the caller change this?". An attribute the source
        did not state and the object has not altered must not be written: HD
        omits it, and inventing it is how a template default becomes a
        per-character override. Cached per class; a class that cannot be
        constructed bare simply gets no defaults and writes everything.
        """
        cached = cls.__dict__.get("_xml_defaults_cache")
        if cached is not None:
            return cached
        schema = cls.xml_schema()
        declared = {d.field: d.default for d in schema if isinstance(d, XMLField)}
        rows = [d for d in schema if not isinstance(d, XMLField)]
        if not rows:
            # Every field declares its own default; no probe needed.
            cls._xml_defaults_cache = declared
            return declared
        try:
            probe = cls()
            defaults = {d.field: getattr(probe, d.field, _UNSET) for d in rows}
        except Exception:  # noqa: BLE001 — abstract or arg-taking classes
            defaults = {}
        defaults.update(declared)
        cls._xml_defaults_cache = defaults
        return defaults

    @classmethod
    def xml_schema(cls) -> tuple:
        cached = cls.__dict__.get("_xml_schema_cache")
        if cached is not None:
            return cached
        merged: dict = {}
        for klass in reversed(cls.__mro__):
            # Descriptors declared as class attributes...
            for value in klass.__dict__.values():
                if isinstance(value, XMLField):
                    merged[value.attr] = value
            # ...and rows, for fields whose storage is a private name the
            # class sets in __init__ (Adder._required and friends), where a
            # descriptor would mean renaming the field itself.
            for descriptor in klass.__dict__.get("XML_ATTRS", ()):
                merged[descriptor.attr] = descriptor
        schema = tuple(merged.values())
        cls._xml_schema_cache = schema
        return schema

