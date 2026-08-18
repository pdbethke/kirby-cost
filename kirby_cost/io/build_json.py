"""Build doc (JSON) <-> build engine. The build doc is the canonical, complete,
HDC-structured-but-not-XML description of any point-built entity. This module
turns it into BuildNode trees the loader's construct-and-cost core consumes."""
from __future__ import annotations
from typing import Any
from kirby_cost.io.hdc_loader import HDCLoader, BuildNode, LoadedHero

class BuildDocError(ValueError):
    """Malformed build doc."""

_SECTION_TAG = {
    "characteristics": "CHARACTERISTICS", "powers": "POWERS", "skills": "SKILLS",
    "perks": "PERKS", "talents": "TALENTS", "martial_arts": "MARTIALARTS",
    "disadvantages": "DISADVANTAGES",
}
# Cost-driving fields the loader's _init() reads off every element (power,
# modifier, adder). Emitting the EFFECTIVE values back as their HDC attributes
# makes the build doc fully self-describing so the rebuild reproduces the cost
# regardless of which template defaults would otherwise apply. (loader: base.py
# _init reads BASECOST/LVLCOST/LVLVAL/LEVELS/MINCOST/MAXCOST; for XML-supplied
# values these override template defaults — see _base_cost_from_xml at base.py:569.)
_ATTR = {"levels": "LEVELS", "alias": "ALIAS",
         # "name"→NAME now round-trips: to_build_json emits it (see
         # _obj_to_dict). "notes"→NOTES is still input-only — accepted so
         # hand-authored docs are not rejected, but not emitted.
         "name": "NAME",
         "option_id": "OPTIONID", "input": "INPUT",
         "notes": "NOTES",
         "id": "ID", "parent": "PARENTID", "base_cost": "BASECOST",
         "level_cost": "LVLCOST", "level_value": "LVLVAL",
         "min_cost": "MINCOST", "max_cost": "MAXCOST",
         "characteristic": "CHARACTERISTIC"}
_BOOL = {"ultra_slot": "ULTRA_SLOT", "add_modifiers_to_base": "ADD_MODIFIERS_TO_BASE",
         # "is_power"→ISPOWER is accepted on input but NOT emitted by to_build_json
         # (is_power is derived from the element tag at load time, not stored as an
         # attribute). Does not survive a round-trip; keep for hand-authored docs.
         "is_power": "ISPOWER",
         "selected": "SELECTED", "private": "PRIVATE",
         "required": "REQUIRED"}
# Power-type-specific cost fields the loader reads in a subclass _init and that
# drive cost but are NOT generic LEVELS/BASECOST:
#   - ForceWall dimension levels (force_wall.py:42-48): length/height/body/width
#     levels + per-inch/per-body unit costs feed total_cost.
#   - Sense GROUP (hdc_loader.py:918-920): membership in an existing sense group
#     gives a cost discount, so it must round-trip.
_TYPED_ATTR = {
    "length_levels": "LENGTHLEVELS", "height_levels": "HEIGHTLEVELS",
    "body_levels": "BODYLEVELS", "width_levels": "WIDTHLEVELS",
    "cost_per_inch": "COSTPERINCH", "cost_per_body": "COSTPERBODY",
    "group": "GROUP",
}
# Skill cost-mode flags the Skill loader reads in _init (skill.py:654-668). These
# decide the base cost (familiarity=1 / proficiency=N / 3) and the adder-cost
# discount path (AdderBasedSkill.total_cost). Without them a skill that defaulted
# off in the HDC re-defaults ON (set_familiarity(True) at adder_based_skill.py:43),
# dropping adder cost. Emit the EFFECTIVE flag (Yes/No) so the mode is preserved.
_SKILL_FLAG = {"familiarity": "FAMILIARITY", "proficiency": "PROFICIENCY",
               "levels_only": "LEVELSONLY", "everyman": "EVERYMAN"}
# Maneuver fields: get_save_xml (maneuver.py:795-822) is the attr authority.
# Plain string/int attrs:
_MANEUVER_ATTR = {
    "category": "CATEGORY", "display": "DISPLAY", "ocv": "OCV", "dcv": "DCV",
    "dc": "DC", "phase": "PHASE", "effect": "EFFECT",
    "maneuver_active_cost": "ACTIVECOST", "damage_type": "DAMAGETYPE",
    "max_str": "MAXSTR", "str_multiplier": "STRMULT",
    "weapon_effect": "WEAPONEFFECT", "ranged": "RANGE",
}
# Bool attrs (emit "Yes"/"No"):
_MANEUVER_BOOL = {"add_str": "ADDSTR", "use_weapon": "USEWEAPON", "custom": "CUSTOM"}
# Characteristic sub-power tags the loader types as "char" (hdc_loader.py:751-754,
# 964-968) — a CompoundPower/sub-power emitted under one of these tags must keep
# that tag so the loader rebuilds it as a Characteristic, not a generic POWER.
_CHAR_TAGS = {"STR", "DEX", "CON", "BODY", "INT", "EGO", "PRE", "COM",
              "PD", "ED", "SPD", "REC", "END", "STUN",
              "OCV", "DCV", "OMCV", "DMCV",
              "RUNNING", "SWIMMING", "LEAPING", "SIZE"}

def _yn(v: bool) -> str:
    return "Yes" if v else "No"

def _obj_node(o: dict, child_tag: str | None = None) -> BuildNode:
    if "xmlid" not in o:
        raise BuildDocError(f"build-doc object missing 'xmlid': {o!r}")
    attrs: dict[str, str] = {"XMLID": str(o["xmlid"])}
    for field_name, hdc in _ATTR.items():
        if o.get(field_name) is not None:
            attrs[hdc] = str(o[field_name])
    for field_name, hdc in _BOOL.items():
        if field_name in o:
            attrs[hdc] = _yn(bool(o[field_name]))
    for field_name, hdc in _SKILL_FLAG.items():
        if field_name in o:
            attrs[hdc] = _yn(bool(o[field_name]))
    if o.get("maneuver"):
        for f, hdc in _MANEUVER_ATTR.items():
            if o.get(f) is not None:
                attrs[hdc] = str(o[f])
        for f, hdc in _MANEUVER_BOOL.items():
            if f in o:
                attrs[hdc] = _yn(bool(o[f]))
    for field_name, hdc in _TYPED_ATTR.items():
        if o.get(field_name) is not None:
            attrs[hdc] = str(o[field_name])
    if o.get("sense_active"):
        attrs["ACTIVE"] = "Yes"
    kids = [_obj_node(m, "MODIFIER") for m in o.get("modifiers", [])]
    # Sense PROVIDES children (sense.py:925-928): capabilities the sense grants.
    for prov in o.get("provides", []):
        kids.append(BuildNode("PROVIDES", {}, [], text=str(prov)))
    kids += [_obj_node(a, "ADDER") for a in o.get("adders", [])]
    # CompoundPower sub-powers: the loader rebuilds each child of a CompoundPower
    # by iterating raw element children and typing on the child's tag
    # (hdc_loader.py:957-973). Reconstruct each as a child node tagged by its own
    # xmlid (so PD/ED etc. type as Characteristics), NOT "POWER".
    for sp in o.get("sub_powers", []):
        sp_xmlid = str(sp.get("xmlid", ""))
        if sp_xmlid in _CHAR_TAGS:
            sp_tag = sp_xmlid
        elif sp.get("skill"):
            # A SKILL nested inside a power (Bullet's CompoundPower carries
            # COMBAT_LEVELS; Duplication grants Teamwork / Cramming / a KS).
            # The loader types these on the child's tag, so emitting <POWER>
            # here lost the skill fields — characteristic/familiarity/
            # proficiency/levels_only/everyman — on the way back in. Same
            # reason _CHAR_TAGS is handled above: the tag is what makes the
            # loader rebuild the right class.
            sp_tag = "SKILL"
        else:
            sp_tag = "POWER"
        kids.append(_obj_node(sp, sp_tag))
    # EnduranceReserve REC sub-element (hdc_loader.py:977-985): the loader looks
    # for a child whose XMLID == "ENDURANCERESERVEREC" and builds it as a power.
    rec = o.get("endurance_reserve_rec")
    if rec is not None:
        kids.append(_obj_node(rec, "POWER"))
    fw = {"MULTIPOWER", "VPP", "LIST", "ELEMENTALCONTROL"}
    # framework_tag allows a LIST/MULTIPOWER tag to differ from xmlid (e.g. separator)
    framework_tag = o.get("framework_tag", "")
    xmlid = str(o["xmlid"])
    if child_tag:
        tag = child_tag
    elif framework_tag in fw:
        tag = framework_tag
    elif xmlid in fw:
        tag = xmlid
    elif xmlid in _CHAR_TAGS:
        # Characteristic in the POWERS section: the loader keys char-vs-power
        # detection on the element TAG (hdc_loader.py:751-756). It must be the
        # char xmlid (PD/ED/STR...), not "POWER", so the loader flags _is_power
        # and builds it as a power-based Characteristic with the right cost path.
        tag = xmlid
    elif o.get("skill"):
        # Skill bought in the POWERS section (e.g. Weaponsmith on a vehicle):
        # the loader keys skill-vs-power dispatch on the element TAG
        # (hdc_loader.py:854-855 — `elif tag == "SKILL": obj_type = "skill"`).
        # Without the SKILL tag the rebuilt object goes through the power
        # registry, misses (Skill subclasses are excluded there), and falls
        # back to _FallbackObject with the wrong cost.
        tag = "SKILL"
    elif o.get("maneuver"):
        # Maneuver in MARTIALARTS section: the loader dispatches on the element
        # TAG (hdc_loader.py ~707: `_load_section(root, "MARTIALARTS", None, "power")`
        # with XMLID-keyed registry — Maneuver is registered as "MANEUVER").
        # The explicit MANEUVER tag ensures the correct Maneuver class is
        # reconstructed rather than falling back to a generic power object.
        tag = "MANEUVER"
    else:
        tag = "POWER"
    return BuildNode(tag, attrs, kids)

def _root_from_doc(doc: dict[str, Any]) -> BuildNode:
    if not isinstance(doc, dict):
        raise BuildDocError("build doc must be a dict")
    children = [
        BuildNode("CHARACTER_INFO", {"CHARACTER_NAME": str(doc.get("name", ""))}),
        BuildNode("BASIC_CONFIGURATION", {
            "BASE_POINTS": str(doc.get("base_points", 400)),
            "DISAD_POINTS": str(doc.get("disad_points", 75)),
            "EXPERIENCE": str(doc.get("experience", 0)),
        }),
    ]
    for key, sec_tag in _SECTION_TAG.items():
        items = doc.get(key, [])
        if not isinstance(items, list):
            raise BuildDocError(f"build-doc '{key}' must be a list")
        children.append(BuildNode(sec_tag, {}, [_obj_node(o) for o in items]))
    return BuildNode("CHARACTER", {"TEMPLATE": str(doc.get("template", ""))}, children)

def build_from_json(doc: dict[str, Any]) -> LoadedHero:
    """Build doc -> loaded build (live cost properties)."""
    return HDCLoader()._build_hero_from_root(_root_from_doc(doc))


def _obj_to_dict(o, idx: int, parent_id: str | None) -> dict[str, Any]:
    """Document placement around the object's own export.

    Everything about WHAT an object is now comes from the object
    (``SerializationMixin.to_build_dict``, overridden by the classes that have
    more to say). What is left here is where it sits in the document: the
    synthetic id and the parent link, which no object can know about itself.

    This function used to be 120 lines that branched on isinstance for
    ForceWall, Sense, Skill and Maneuver — so adding a subclass with anything
    extra to export meant editing this module, and forgetting to was silent.
    """
    d: dict[str, Any] = {"id": f"O{idx}"}
    d.update(o.to_build_dict())
    if parent_id:
        d["parent"] = parent_id
    return d


def to_build_json(hero: LoadedHero) -> dict[str, Any]:
    """Loaded build -> canonical build doc. Reads the loaded build (full structure:
    frameworks, all modifiers, adders), so the doc is complete + round-trippable."""
    doc: dict[str, Any] = {
        "name": getattr(hero, "name", ""),
        "template": getattr(hero, "template_name", "") or "",
        "base_points": getattr(hero, "base_points", 400),
        "disad_points": getattr(hero, "disad_points", 75),
        "experience": getattr(hero, "experience", 0),
    }
    ids: dict[int, str] = {}
    counter = 0
    for key in _SECTION_TAG:
        attr = {"disadvantages": "complications"}.get(key, key)
        for o in getattr(hero, attr, []):
            counter += 1
            ids[id(o)] = f"O{counter}"
    out_counter = 0
    for key in _SECTION_TAG:
        attr = {"disadvantages": "complications"}.get(key, key)
        section = []
        for o in getattr(hero, attr, []):
            out_counter += 1
            parent = getattr(o, "parent", None)
            pid = ids.get(id(parent)) if parent is not None else None
            section.append(_obj_to_dict(o, out_counter, pid))
        doc[key] = section
    return doc
