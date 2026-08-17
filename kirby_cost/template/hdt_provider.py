"""HDTTemplateProvider — templates read from a HERO Designer ``.hdt``.

Like HERO Designer itself, kirby-cost relies on template files: the user points
it at a ``.hdt`` from their own licensed HD installation, and every cost
parameter comes from there. The package carries no template data and supplies no
catalogue of its own.

**Presence, not value.** Several template fields are three-state — set, set to
zero, or absent — and ``apply_template`` distinguishes them: ``min_set`` and
``max_set`` say whether the template constrains cost at all, and a missing
``LVLVAL`` means the template is silent about per-level value rather than
asserting one. So each field is read from the element's raw attributes by
presence. An absent attribute yields the dataclass default; it never yields a
plausible-looking number.
"""
from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional

from kirby_cost.template.dataclasses import (
    AdderTemplate,
    OptionTemplate,
    TemplateData,
)

# Sections of a parsed HDT that define purchasable objects, and whether the
# things in them are powers (``is_power`` drives power-specific cost paths).
_SECTIONS: tuple[tuple[str, bool], ...] = (
    ("characteristics", False),
    ("skills", False),
    ("skill_enhancers", False),
    ("martial_arts", False),
    ("perks", False),
    ("talents", False),
    ("powers", True),
    ("modifiers", False),
    ("disadvantages", False),
)

# Parsing a template is ~1MB of XML, and a provider is built per load, so the
# parse is cached by path and mtime. Editing a .hdt therefore takes effect
# without restarting anything.
_PARSE_CACHE: dict[tuple[str, float], dict[str, Any]] = {}


def _parse_cached(path: Path) -> dict[str, Any]:
    from kirby_cost.io.hdt_parser import HDTParser

    key = (str(path), path.stat().st_mtime)
    cached = _PARSE_CACHE.get(key)
    if cached is None:
        cached = HDTParser().parse_file(str(path))
        _PARSE_CACHE[key] = cached
    return cached


# Child tags that describe an element rather than define a new object.
_NOT_DEFINITIONS = frozenset({
    "TYPE", "DEFINITION", "OPTION", "ADDER", "MODIFIER", "EXCLUDES",
    "CHARACTERISTIC_CHOICE", "GROUPS", "PROVIDES", "NOTES", "ITEM",
})


def _attrs(entry: dict[str, Any]) -> dict[str, str]:
    return entry.get("attributes") or {}


def _f(attrs: dict[str, str], key: str, default: float = 0.0) -> float:
    """Read a float attribute, treating absence as *default*."""
    raw = attrs.get(key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _i(attrs: dict[str, str], key: str, default: int = 1) -> int:
    raw = attrs.get(key)
    if raw is None or raw == "":
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def _level_value(attrs: dict[str, str]) -> float:
    """``LVLVAL`` if the element sets it, else nothing.

    ``apply_template`` reads 0 / -1 / -1.0 alike as "the template says nothing
    about per-level value", so an absent attribute maps to 0.0. It must not map
    to a per-level value the template never stated.
    """
    return _f(attrs, "LVLVAL", 0.0)


def _option(entry: dict[str, Any]) -> OptionTemplate:
    a = _attrs(entry)
    return OptionTemplate(
        xmlid=entry.get("xmlid") or "",
        display=entry.get("display") or "",
        base_cost=_f(a, "BASECOST"),
        level_cost=_f(a, "LVLCOST"),
        level_value=_level_value(a),
        level_power=_i(a, "LVLPOWER"),
        level_multiplier=_i(a, "LVLMULTIPLIER"),
    )


def _adder(entry: dict[str, Any]) -> AdderTemplate:
    a = _attrs(entry)
    return AdderTemplate(
        xmlid=entry.get("xmlid") or "",
        display=entry.get("display") or "",
        base_cost=_f(a, "BASECOST"),
        level_cost=_f(a, "LVLCOST"),
        level_value=_level_value(a),
        level_power=_i(a, "LVLPOWER"),
        level_multiplier=_i(a, "LVLMULTIPLIER"),
        types=tuple(entry.get("types") or ()),
    )


def _all_adders(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """The element's adders, plus those nested inside its options."""
    found = list(entry.get("adders") or [])
    for opt in entry.get("options") or []:
        found.extend(opt.get("adders") or [])
    return found


def _identity(entry: dict[str, Any]) -> str:
    """The xmlid an object is known by.

    Most template elements are tagged with their own xmlid (``<STR>``,
    ``<FLASH>``), and the parser reads it off the tag. Senses and sense groups
    are not: they share a tag and name themselves with an attribute
    (``<SENSEGROUP XMLID="SIGHTGROUP">``). Taking the tag there would file all
    six sight/hearing/… groups under one key and lose five of them.
    """
    return _attrs(entry).get("XMLID") or entry.get("xmlid") or ""


def _sense_groups(parsed: dict[str, Any]) -> list[tuple[str, str, tuple[str, ...]]]:
    """The template's sense groups, in template order, with what each provides.

    ``<SENSEGROUP XMLID="SIGHTGROUP"><PROVIDES>TARGETINGSENSE</PROVIDES>`` —
    the PROVIDES list is what Java reads as ``getDefaultSenseAdders()``, and
    whether it names ``TARGETINGSENSE`` is what separates a targeting group
    from a non-targeting one.
    """
    found: list[tuple[str, str, tuple[str, ...]]] = []
    for entry in parsed.get("powers") or []:
        if entry.get("xmlid") != "SENSEGROUP":
            continue
        xmlid = _attrs(entry).get("XMLID")
        if not xmlid:
            continue
        provides = tuple(
            (child.get("text") or "").strip()
            for child in entry.get("child_elements") or []
            if child.get("tag") == "PROVIDES"
        )
        found.append((xmlid, entry.get("display") or "", provides))
    return found


# Sense-affecting powers are bought against a sense group, and the group is
# what sets the price — Sight costs more than Hearing. The template says so
# once, on the power (TARGETINGCOST / NONTARGETINGCOST), and HD turns that into
# one selectable option per sense group at load time rather than the template
# listing them: SenseAffectingPower.getOptions(). Two groups never appear.
_EXCLUDED_SENSE_GROUPS = frozenset({"UNUSUALGROUP", "NOGROUP"})

# Shapeshift prices the groups its own way — Shapeshift.java:196, 6E only.
# Sight is targeting, Hearing and Touch are not, and the remaining three are
# charged the group rate instead of either.
_SHAPESHIFT_RATES = {
    "SIGHTGROUP": "TARGETINGCOST",
    "HEARINGGROUP": "NONTARGETINGCOST",
    "TOUCHGROUP": "NONTARGETINGCOST",
    "SMELLGROUP": "TARGETINGGROUPCOST",
    "MENTALGROUP": "TARGETINGGROUPCOST",
    "RADIOGROUP": "TARGETINGGROUPCOST",
}


def _sense_group_options(
    xmlid: str,
    entry: dict[str, Any],
    groups: list[tuple[str, str, tuple[str, ...]]],
) -> dict[str, OptionTemplate]:
    """One option per sense group for a sense-affecting power.

    Ported from ``SenseAffectingPower.getOptions()`` (and ``Shapeshift`` for
    that one power). The rate lands on levels where the power is bought by the
    level and on the base cost where it is not, which is the same three-state
    reading of ``LVLVAL`` used everywhere else: ``levelValue <= 0`` means the
    power has no levels, so the whole rate is the base cost.
    """
    attrs = _attrs(entry)
    if "TARGETINGCOST" not in attrs and "NONTARGETINGCOST" not in attrs:
        return {}
    if not groups:
        return {}
    level_value = _level_value(attrs)
    options: dict[str, OptionTemplate] = {}
    for group, display, provides in groups:
        if group in _EXCLUDED_SENSE_GROUPS:
            continue
        if xmlid == "SHAPESHIFT":
            rate_attr = _SHAPESHIFT_RATES.get(group)
            if rate_attr is None:
                continue
        elif "TARGETINGSENSE" in provides:
            rate_attr = "TARGETINGCOST"
        else:
            rate_attr = "NONTARGETINGCOST"
        if rate_attr not in attrs:
            continue
        rate = _f(attrs, rate_attr, -1.0)
        if rate < 0:
            continue
        if level_value <= 0:
            options[group] = OptionTemplate(
                xmlid=group, display=display, base_cost=rate,
                level_cost=-1.0, level_value=-1.0,
            )
        else:
            options[group] = OptionTemplate(
                xmlid=group, display=display, base_cost=0.0,
                level_cost=rate, level_value=level_value,
            )
    return options


def _template_data(entry: dict[str, Any], *, is_power: bool) -> TemplateData:
    a = _attrs(entry)
    xmlid = _identity(entry)
    # A skill states its cost through CHARACTERISTIC_CHOICE rather than on the
    # element: <ITEM CHARACTERISTIC="DEX" BASECOST="3" LVLCOST="2" LVLVAL="1"/>.
    # HD offers the character a choice where there is more than one (Knowledge
    # Skill: GENERAL 2/1 or INT 3/1); the first item is what it presents by
    # default, and is what the element means when nothing else selects one.
    choice = (entry.get("characteristic_choice") or [None])[0]
    base_cost = _f(a, "BASECOST")
    level_cost = _f(a, "LVLCOST")
    level_value = _level_value(a)
    # An element that states no cost of its own but offers options is priced by
    # its first option — what HD offers as the default selection. Reduced
    # Endurance is written that way: no BASECOST on the MODIFIER, then
    # <OPTION XMLID="HALFEND" BASECOST=".25"> and <OPTION XMLID="ZERO"
    # BASECOST=".5">. A character that names no option still pays the +1/4.
    options = entry.get("options") or []
    if options and "BASECOST" not in a:
        base_cost = _f(_attrs(options[0]), "BASECOST")
    if isinstance(choice, dict):
        if "BASECOST" not in a:
            base_cost = float(choice.get("base_cost") or 0.0)
        if "LVLCOST" not in a:
            level_cost = float(choice.get("level_cost") or 0.0)
        if "LVLVAL" not in a:
            level_value = float(choice.get("level_value") or 0.0)
    return TemplateData(
        xmlid=xmlid,
        display=entry.get("display") or "",
        base_cost=base_cost,
        level_cost=level_cost,
        level_value=level_value,
        level_power=_i(a, "LVLPOWER"),
        level_multiplier=_i(a, "LVLMULTIPLIER"),
        minimum_cost=_f(a, "MINCOST"),
        min_set="MINCOST" in a,
        max_cost=_f(a, "MAXCOST"),
        max_set="MAXCOST" in a,
        duration=entry.get("duration") or "",
        target=entry.get("target") or "",
        uses_end=bool(entry.get("uses_end")),
        is_power=is_power,
        # The engine resolves classes through its own xmlid registry; the
        # template has no say in it, so this stays empty.
        class_name="",
        base_value=_f(a, "BASE"),
        all_cost=_f(a, "ALLCOST", -1.0),
        group_cost=_f(a, "GROUPCOST", -1.0),
        sense_cost=_f(a, "SENSECOST", -1.0),
        # Adders live both on the element and inside its options — Area Of
        # Effect keeps ACCURATE under RADIUS, THINCONE under CONE, FIXEDSHAPE
        # under ANY. They are all buyable on the object, so they are collected
        # together; an option's own adder wins if the names collide.
        adders={
            (ad.get("xmlid") or ""): _adder(ad)
            for ad in _all_adders(entry)
            if ad.get("xmlid")
        },
        options={
            (op.get("xmlid") or ""): _option(op)
            for op in (entry.get("options") or [])
            if op.get("xmlid")
        },
        types=tuple(entry.get("types") or ()),
        attributes=dict(a),
    )


class HDTTemplateProvider:
    """Serve ``TemplateData`` from a HERO Designer ``.hdt`` file.

    Construct with an explicit path, or leave it out to resolve from the
    ``KIRBY_COST_HDT`` environment variable. There is no bundled fallback: the
    package ships no template data, so an unresolvable path is an error with a
    message saying what to provide.
    """

    ENV_VAR = "KIRBY_COST_HDT"

    def __init__(self, path: Optional[str | Path] = None,
                 fallbacks: Optional[list[str | Path]] = None) -> None:
        resolved = Path(path) if path else self._from_env()
        if not resolved.is_file():
            raise FileNotFoundError(
                f"HERO Designer template not found: {resolved}. kirby-cost ships "
                f"no template data — point it at a .hdt from your own HERO "
                f"Designer installation, either by passing a path or by setting "
                f"{self.ENV_VAR}."
            )
        self.path = resolved
        self._index: dict[str, TemplateData] = {}
        self._adder_types: dict[str, list[str]] = {}
        self._maneuvers: dict[str, TemplateData] = {}
        # Providers for sibling templates, shared across the family — see
        # for_template().
        self._peers: dict[str, "HDTTemplateProvider"] = {}
        # Load order is child-before-parent throughout, because indexing is
        # first-wins: whatever is loaded first owns the xmlid.
        #
        #   1. the template itself
        #   2. its ancestors, via <TEMPLATE extends="builtIn.Main6E.hdt">
        #   3. the earlier-edition fallback beside each of those
        #
        # (2) is HD's own inheritance. A specialised template — Vehicle6E,
        # Computer6E, Automaton6E, Superheroic6E — is a thin override layer
        # over Main6E: Vehicle6E restates FLIGHT as USESEND="No" and defines
        # SIZE, Automaton6E prices EGO at 2/level, and everything they do not
        # restate comes from the parent. Without the chain a vehicle would
        # resolve only the ~47 objects its own file lists.
        chain = [resolved] + self._ancestors(resolved)
        for path in chain:
            self._load(path)
        # (3) HD falls back to the earlier-edition template for objects the 6E
        # one does not define — ARMOR, SUPPRESS, TRANSFER, SUCCOR,
        # DAMAGERESISTANCE and ENDURANCERESERVEREC are defined there and
        # nowhere else, and characters in the wild still carry them. The
        # fallback sits beside its 6E counterpart in the same directory, so it
        # is found the same way HD finds it rather than configured separately.
        if fallbacks is not None:
            extras = [Path(f) for f in fallbacks]
        else:
            extras = [s for p in chain for s in self._siblings(p)]
        for extra in extras:
            if extra.is_file():
                self._load(extra)

    @staticmethod
    def _resolve_builtin(name: str, beside: Path) -> Optional[Path]:
        """Resolve a template reference to a file next to *beside*.

        ``builtIn.`` is HD's marker for "one of the templates that ship with
        the app" — not a path. The application resolved it off its own
        classpath; here the shipped templates sit together in one directory, so
        the reference resolves to the file of that name beside the template
        doing the referencing.
        """
        if not name:
            return None
        if name.startswith("builtIn."):
            name = name[len("builtIn."):]
        # Defend against a template naming a path; only the basename is ours.
        candidate = beside.with_name(Path(name).name)
        return candidate if candidate.is_file() else None

    def _ancestors(self, primary: Path) -> list[Path]:
        """The extends chain above *primary*, nearest parent first."""
        seen = {primary.resolve()}
        out: list[Path] = []
        current = primary
        while True:
            parsed = _parse_cached(current)
            parent = self._resolve_builtin(parsed.get("extends") or "", current)
            # A cycle would hang the loader; a template that extends itself, or
            # a pair that extend each other, simply stops the walk.
            if parent is None or parent.resolve() in seen:
                return out
            seen.add(parent.resolve())
            out.append(parent)
            current = parent

    @classmethod
    def _from_env(cls) -> Path:
        raw = os.environ.get(cls.ENV_VAR)
        if not raw:
            raise FileNotFoundError(
                f"No HERO Designer template configured. kirby-cost ships no "
                f"template data — set {cls.ENV_VAR} to a .hdt from your own "
                f"HERO Designer installation, or pass a path explicitly."
            )
        return Path(raw)

    @staticmethod
    def _siblings(primary: Path) -> list[Path]:
        """The earlier-edition template beside *primary*, if there is one.

        ``Main6E.hdt`` -> ``Main.hdt``. A template with no ``6E`` in its name is
        already the fallback, so it has none of its own.
        """
        if "6E" not in primary.stem:
            return []
        return [primary.with_name(primary.stem.replace("6E", "") + primary.suffix)]

    def _load(self, path: Path) -> None:
        parsed = _parse_cached(path)
        groups = _sense_groups(parsed)
        self._index_maneuvers(parsed.get("martial_arts") or [])
        # Senses and sense groups are indexed last. HD keeps them in registries
        # of their own (Sense.getAllSenses, SenseGroup.getAllGroups) rather than
        # among purchasable objects, and a name can appear in both: Mind Scan is
        # a <SENSE> in the Mental Group *and* a power costing 5 per level. The
        # power is the definition a character buys, so it must win.
        for pass_senses in (False, True):
            for section, is_power in _SECTIONS:
                for entry in parsed.get(section) or []:
                    if (entry.get("xmlid") in ("SENSE", "SENSEGROUP")) != pass_senses:
                        continue
                    xmlid = _identity(entry)
                    if not xmlid or xmlid in self._index:
                        continue
                    data = _template_data(entry, is_power=is_power)
                    synthetic = _sense_group_options(xmlid, entry, groups)
                    if synthetic:
                        data = replace(data, options=synthetic)
                    self._index[xmlid] = data
                    self._index_nested(entry, is_power=is_power)
                    self._index_adder_types(_all_adders(entry))

    def _index_nested(self, entry: dict[str, Any], *, is_power: bool) -> None:
        """Index definitions written inside another element.

        A template defines some objects in place rather than at section level:
        Endurance Reserve holds the whole <ENDURANCERESERVEREC> definition and a
        <MODIFIER XMLID="RESTRICTEDUSE"> inside itself. They are ordinary
        definitions that characters reference by xmlid, so they have to be
        findable — otherwise the lookup misses and falls through to whatever an
        earlier-edition template happens to say, at that edition's rates.
        """
        for mod in entry.get("modifiers") or []:
            xmlid = mod.get("xmlid")
            if xmlid and xmlid not in self._index:
                self._index[xmlid] = _template_data(mod, is_power=False)
        for child in entry.get("child_elements") or []:
            tag = child.get("tag")
            attrs = child.get("attributes") or {}
            if not tag or tag in _NOT_DEFINITIONS or tag in self._index:
                continue
            # A nested definition is one that prices itself.
            if not any(k in attrs for k in ("BASECOST", "LVLCOST", "MINCOST")):
                continue
            self._index[tag] = _template_data(
                {"xmlid": tag, "display": attrs.get("DISPLAY", ""),
                 "attributes": attrs, "duration": attrs.get("DURATION", ""),
                 "target": attrs.get("TARGET", ""),
                 "uses_end": attrs.get("USESEND", "No") == "Yes"},
                is_power=is_power,
            )

    def _index_maneuvers(self, entries: list[dict[str, Any]]) -> None:
        """Index the martial-arts section's maneuvers by DISPLAY.

        A ``<MANEUVER>`` element carries no ``XMLID`` attribute — its DISPLAY is
        the whole of its identity, and every HDC maneuver is written
        ``<MANEUVER XMLID="MANEUVER" DISPLAY="Killing Strike">``. Keying them by
        xmlid like every other element files all 53 under ``MANEUVER`` and the
        first (Basic Strike) wins.

        Java matches on display, and searches maneuvers nested in a ``LIST``
        container as well as top-level ones (``Hero.java:2706-2731``);
        ``Main6E.hdt`` states them flat, but a house template may not. The other
        martial-arts entries — EXTRADC, RANGEDDC, WEAPON_ELEMENT — name
        themselves properly and are looked up by xmlid, exactly as Java's
        ``getXMLID().equals(...)`` scans above do.
        """
        for entry in entries:
            tag = entry.get("tag")
            if tag == "LIST":
                self._index_maneuvers(entry.get("child_elements") or [])
                continue
            if tag != "MANEUVER":
                continue
            display = entry.get("display") or ""
            if display and display not in self._maneuvers:
                self._maneuvers[display] = _template_data(entry, is_power=False)

    def _index_adder_types(self, adders: list[dict[str, Any]]) -> None:
        """Record the types of every adder, however deeply nested.

        An element's own adders reach a character through its ``TemplateData``,
        but adders nest — Transport Familiarity's ``RIDINGANIMALS`` holds
        ``CAMELS``, ``DOGS``, ``EQUINES`` — and only the outermost layer is
        indexed there. The types still have to arrive: ``TRANSPORT_FAMILIARITY``
        discounts itself by 1 when a ``RIDING``-typed adder costs 1 and the
        character also has the Riding skill, so a sub-adder that loses its type
        silently overcharges the character.
        """
        for entry in adders:
            xmlid = entry.get("xmlid")
            types = entry.get("types") or []
            if xmlid and types and xmlid not in self._adder_types:
                self._adder_types[xmlid] = list(types)
            nested = entry.get("adders") or []
            if nested:
                self._index_adder_types(nested)

    def get_adder_type_map(self) -> dict[str, list[str]]:
        """xmlid -> types for every adder in the template, nested included."""
        return self._adder_types

    def for_template(self, name: str) -> "HDTTemplateProvider":
        """A provider for the template *name*, resolved beside this one.

        A character declares the template it was built on
        (``TEMPLATE="builtIn.Vehicle6E.hdt"``) and HD costs it against that,
        not against whatever the application last had open. The loader asks for
        it here rather than reaching for files itself.

        Returns ``self`` when the name is empty, names this same template, or
        cannot be resolved — the last case matching HD, which keeps the active
        template when a named one cannot be found. Instances are cached, so a
        roster of 40 vehicles parses Vehicle6E once.
        """
        if not name:
            return self
        resolved = self._resolve_builtin(name, self.path)
        if resolved is None or resolved.resolve() == self.path.resolve():
            return self
        key = str(resolved.resolve())
        cached = self._peers.get(key)
        if cached is None:
            cached = HDTTemplateProvider(resolved)
            # Share one cache across the family so siblings resolve each other
            # without rebuilding, and so this provider is reachable from them.
            cached._peers = self._peers
            self._peers[key] = cached
            self._peers.setdefault(str(self.path.resolve()), self)
        return cached

    def get_maneuver(self, display: str) -> Optional[TemplateData]:
        """The template's maneuver named *display*, or None if it defines none.

        None means "custom maneuver": Java builds one from the HDC element
        alone when no template maneuver matches the display.
        """
        return self._maneuvers.get(display)

    def get_maneuver_map(self) -> dict[str, TemplateData]:
        """display -> TemplateData for every maneuver the template defines."""
        return self._maneuvers

    def get_template_data(self, xmlid: str) -> Optional[TemplateData]:
        return self._index.get(xmlid)

    def __len__(self) -> int:
        return len(self._index)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"HDTTemplateProvider({self.path!s}, {len(self._index)} objects)"
