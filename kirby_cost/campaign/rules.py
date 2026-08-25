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

#: Every field of TemplateData, DERIVED rather than listed. Adding a template
#: fact makes it overridable automatically. A hand-maintained list here would
#: rebuild the exact trap this work came from -- a fact parsed into one
#: structure and dropped because a second structure had no field for it.
OVERRIDABLE_FIELDS = frozenset(
    f.name for f in dataclasses.fields(TemplateData)
) - _NOT_OVERRIDABLE


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
        if field not in OVERRIDABLE_FIELDS:
            near = difflib.get_close_matches(field, sorted(OVERRIDABLE_FIELDS), n=3)
            hint = f" Did you mean: {', '.join(near)}?" if near else ""
            raise ValueError(
                f"{field!r} is not a template field, so nothing would ever "
                f"read it.{hint}"
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
