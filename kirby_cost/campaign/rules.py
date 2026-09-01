"""A campaign's rule overrides, as a diff over the template.

kirby-cost is the only thing in the platform that reads a `.hdt`, which makes
it the only place a house rule can enter the model. This holds what a campaign
changed -- four values wide for a campaign that changes four rules -- so that
"what does this campaign change?" stays a question something can answer. A
copy of Main6E cannot answer it.
"""
from __future__ import annotations

import dataclasses
import difflib
from typing import Any, Iterable, Optional

from kirby_cost.template.dataclasses import TemplateData

#: Bookkeeping the provider writes, never a rule a GM sets. Excluded so it
#: cannot be set as an override and then silently clobbered.
_NOT_OVERRIDABLE = frozenset({"campaign_forced"})

#: Fields a campaign may NOT set, and why. Derivation stays the rule so a new
#: template fact is overridable automatically; this names the exceptions.
#:
#: Accepting a field nothing reads would mean a GM writes a rule, gets no
#: error, and the rule silently does nothing -- the exact defect this feature
#: exists to remove.
#:
#: HOW THIS SET WAS ESTABLISHED, field by field, so a later reader knows what
#: is measurement and what is inference. Every `TemplateData` field except
#: `campaign_forced` was accounted for. Each entry listed below was measured
#: INERT -- forced, and the loaded object did not change. Of the rest:
#:
#:   * killing, does_body, does_damage, does_knockback, defense, target,
#:     range, uses_end: wired by `apply_template` and each one locked by a
#:     test in tests/test_campaign_beats_hdc.py that asserts the forced value
#:     reaches the object and outranks a document-stated one.
#:   * level_cost: measured end to end (tests/test_campaign_cost_fields.py:
#:     Ravel's RKA moves 45 -> 30). display, level_value, level_power,
#:     level_multiplier, min_set, max_set: read directly by `apply_template`
#:     (base.py:398, :487-:509, :545, :551) and by `Adder.apply_template`.
#:   * The nine below were the ones the first pass never probed. Each was
#:     then forced through `CampaignRules` and observed changing a loaded
#:     object, on 2026-08-25 (six via real character loads; three via
#:     constructed objects, noted below):
#:   * types      -> forcing ("PROBE",) on RKA gave Ravel's RKA `_types
#:                   == ["PROBE"]` (base.py, the `tmpl.types` loop).
#:   * attributes -> forcing SHOWOPTIONONLY="Yes" on PENETRATING flipped
#:                   that modifier's `show_option_only` to True (base.py:291).
#:   * adders     -> forcing {} emptied `_template_adder_order` on RKA.
#:   * options    -> forcing LARGE's level_cost=77/level_multiplier=9 moved
#:                   Bokor's GROWTH to exactly those (base.py:428).
#:   * option_aliases -> with LARGE removed from `options`, forcing
#:                   {"LARGE": "HUGE"} resolved GROWTH's option to HUGE.
#:   * base_value -> forcing 42.0 on STR moved Ravel's STR `base_level`
#:                   from 10.0 to 42.0 (hdc_loader.py:655).
#:   * all_cost / group_cost / sense_cost -> forcing 55.0 on a sense-rate
#:                   xmlid put 55.0 on all three of a constructed SenseAdder
#:                   (base.py, the sense-rate loop; hdc_loader.py:1615).
#:                   (These three were probed via apply_template on a built
#:                   object, not a real character load, because none of the
#:                   authored characters carries a SenseAdder.)
#:
#:   * characteristic -> forcing "STR" on DEDUCTION moved Ravel's Deduction
#:                   off INT, and its roll with it (skill.py, Skill's own
#:                   apply_template override). Only Skill reads it; every
#:                   other object type ignores it, which is why it is listed
#:                   here as a rule rather than as inert.
#:
#: The one field that is neither wired nor listed as a rule is `class_name`,
#: below: it has ZERO reads off a `TemplateData` anywhere in `kirby_cost/`.
_UNSUPPORTED_FIELDS = {
    # apply_template never assigns tmpl.base_cost to a non-maneuver object
    # (its only base_cost write is from an OPTION, base.py:440), and never
    # reads _base_cost_from_xml. Making the template's price authoritative for
    # every object changes how the engine costs everything and needs its own
    # oracle-gated change. Use level_cost to re-price a power.
    "base_cost": "not applied by apply_template; use level_cost to re-price",
    # apply_template DOES assign these (base.py:546, :552) -- but gated on
    # tmpl.min_set / tmpl.max_set, which are false for a typical power. And
    # forcing min_set/max_set on would surface the TEMPLATE's own
    # minimum_cost/max_cost, never a campaign-forced one, because this field
    # is itself blocked. So the value a GM sets here can never reach an
    # object by either route.
    "minimum_cost": "gated on min_set, and forcing min_set surfaces the template's value, not this one",
    "max_cost": "gated on max_set, and forcing max_set surfaces the template's value, not this one",
    # Gated on the object not already having a duration, which it does by the
    # time a campaign could matter.
    "duration": "the object already holds a duration when the template applies",
    # Not rules. Identity and a derived predicate.
    "xmlid": "identity, not a rule",
    "is_power": "derived from the object, not settable",
    # Parsed by hdt_provider (:323) and dataclasses (:196) and then read by
    # NOTHING: `grep -rn class_name kirby_cost/` finds only unrelated local
    # variables in modifier.py and behaviors/registry.py, never a read off a
    # TemplateData. Forcing it can therefore not change any loaded object.
    "class_name": "carried by TemplateData but read by nothing, so forcing it cannot change a loaded object",
    # LEVELSTART is the prototype's level count. apply_template never assigns
    # it -- a .hdc always states LEVELS, so the load path has no use for it --
    # and the only reader is tests/matrix_support.py, which builds HD's own
    # prototypes for the applicability matrix. Forcing it therefore cannot
    # change any loaded object. Measured: `grep -rn level_start kirby_cost/`
    # finds the parser, the dataclass and this entry, and no read.
    "level_start": "parsed and carried, but apply_template never assigns it; only the matrix harness reads it",
    # exclusive, on the same terms as level_start and continuing_effect:
    # apply_template never assigns it to a loaded object. Measured:
    # `grep -rn "\.exclusive\b" kirby_cost/` finds only
    # `validation.exclusive_conflict`, which reads it straight off the
    # template, and no read off a loaded GenericObject.
    "exclusive": "read by validation.exclusive_conflict; never applied to a loaded object",
}

#: Every field of TemplateData, DERIVED rather than listed. Adding a template
#: fact makes it overridable automatically. A hand-maintained list here would
#: rebuild the exact trap this work came from -- a fact parsed into one
#: structure and dropped because a second structure had no field for it.
OVERRIDABLE_FIELDS = frozenset(
    f.name for f in dataclasses.fields(TemplateData)
) - _NOT_OVERRIDABLE - frozenset(_UNSUPPORTED_FIELDS)


class CampaignRules:
    """What one campaign changes about the template.

    Validates at `set()` time against a real template, so a typo raises at the
    line that wrote it rather than silently matching nothing all session.
    """

    def __init__(self, provider: Optional[Any] = None) -> None:
        if provider is None:
            from kirby_cost.template.hdt_provider import HDTTemplateProvider
            # Raises FileNotFoundError with the provider's own message when no
            # template is configured -- authoring rules that cannot be checked
            # is the failure this class exists to prevent.
            provider = HDTTemplateProvider()
        self._provider = provider
        self._overrides: dict[tuple[str, str], Any] = {}

    def set(self, xmlid: str, field: str, value: Any) -> None:
        # Checked before the OVERRIDABLE_FIELDS membership test below, and
        # given its own message: an unsupported field IS a template field
        # (it's a name a GM typed correctly), so the near-miss/typo message
        # for an unknown field would be actively misleading here.
        if field in _UNSUPPORTED_FIELDS:
            raise ValueError(
                f"{field!r} is a template field, but apply_template does not "
                f"wire it into a loaded object, so a campaign rule on it "
                f"would never take effect: {_UNSUPPORTED_FIELDS[field]}."
            )
        if field not in OVERRIDABLE_FIELDS:
            near = difflib.get_close_matches(field, sorted(OVERRIDABLE_FIELDS), n=3)
            hint = f" Did you mean: {', '.join(near)}?" if near else ""
            raise ValueError(
                f"{field!r} is not a template field, so nothing would ever "
                f"read it.{hint}"
            )
        # A rule that sets None cannot do anything. `apply_template` skips a
        # tri-state field whose template value is None (`if stated_value is
        # None ... continue`), which is how "the template says nothing" is
        # spelled -- so None means ABSENCE, not "revert to the class
        # default". That second meaning is not a capability this engine has,
        # and accepting None would only add another accepted-and-inert path.
        if value is None:
            raise ValueError(
                f"a campaign rule cannot set {field!r} to None: None means "
                f"'the template says nothing', so the rule would be skipped "
                f"and do nothing. Set the value you want instead. (Reverting "
                f"a field to its class default is not a capability that "
                f"exists today.)"
            )
        # Template maneuvers carry no XMLID — DISPLAY is their sole identity.
        # So `hdc_loader` routes them to `get_maneuver` (keyed by display), not
        # to `get_template_data`. If allowed here, this rule would find nothing
        # on the template side and do nothing. Moreover, patching here by xmlid
        # would rewrite all 53 maneuvers at once (they all parse with the same
        # XMLID="MANEUVER" in HDC). Refused here instead, before the check.
        if xmlid.upper() == "MANEUVER":
            raise ValueError(
                "'MANEUVER' cannot be the subject of a campaign rule: template "
                "maneuvers carry no XMLID (DISPLAY is their identity), so this "
                "rule would find nothing on the template side. Moreover, all 53 "
                "HDC maneuvers are written XMLID=\"MANEUVER\", so patching by "
                "xmlid would rewrite all 53 at once. Overriding one maneuver "
                "needs a rule keyed by display, which does not exist yet."
            )
        if self._provider.get_template_data(xmlid) is None:
            raise ValueError(
                f"{xmlid!r} is not in the loaded template, so this rule would "
                f"never match anything. (An xmlid that EXISTS but that no "
                f"character owns is fine -- this is about a name the template "
                f"has never heard of.)"
            )
        self._overrides[(xmlid, field)] = value

    def get(self, xmlid: str, field: str, default: Any = None) -> Any:
        return self._overrides.get((xmlid, field), default)

    def items(self) -> Iterable[tuple[str, str, Any]]:
        return [(x, f, v) for (x, f), v in self._overrides.items()]

    def fields_for(self, xmlid: str) -> frozenset:
        """Field names this campaign forces for *xmlid*."""
        return frozenset(f for (x, f) in self._overrides if x == xmlid)

    def __bool__(self) -> bool:
        return bool(self._overrides)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"CampaignRules({len(self._overrides)} overrides)"
