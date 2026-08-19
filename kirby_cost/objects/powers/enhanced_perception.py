"""
Enhanced Perception power class for kirby-cost.

Converted from com.hero.objects.powers.EnhancedPerception.java

Enhanced perception sense adder.
"""

from kirby_cost.objects.base import option_alias
from kirby_cost.objects.powers.sense_adder import SenseAdder


class EnhancedPerception(SenseAdder, xmlid="ENHANCEDPERCEPTION"):
    """
    Enhanced Perception power.
    
    Sense adder that provides PER bonuses.
    """
    
    def __init__(self):
        """Initialize an Enhanced Perception power."""
        super().__init__(EnhancedPerception.XMLID)
        self._duration = "CONSTANT"
    
    @property
    def damage_display(self) -> str:
        """Get damage display (empty for Enhanced Perception)."""
        return ""
    
    @property
    def column2_output(self) -> str:
        """``+4 PER with all Sense Groups`` — the levels, then what they apply to.

        Ported from ``EnhancedPerception.getColumn2Output``. The sense group
        comes from the object's SELECTED OPTION, and this power's template has
        no options at all — it is priced by ALLCOST/GROUPCOST/SENSECOST — so
        `_selected_option` is None on every one of them and 324 of these
        printed "+4 PER" with nothing after it. The document states the option
        outright (`OPTIONID="ALL" OPTION_ALIAS="all Sense Groups"`), which is
        what `option_alias` reads.

        Resolving the option OBJECT in the loader would be the tidier fix and
        is NOT safe: it moved 306 of the 656 oracle fixtures, because several
        cost paths branch on whether a selected option exists. This stays in
        the display layer, where it belongs.
        """
        output = f"+{self._levels} PER"

        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"

        # HD's guard here is `if (!withString.equals(" for"))` against a string
        # initialised to " with ", so it is always true — a leftover from
        # whichever class this was copied from. The suffix is unconditional.
        with_str = " with "
        option = (option_alias(self) or "").strip()
        adder_str = self.adder_string or ""
        if option:
            with_str += option
            if adder_str.strip():
                with_str += ", " + adder_str
                with_str = _last_comma_to_and(with_str)
        elif adder_str.strip():
            with_str += " " + adder_str
            if ", " in with_str:
                with_str = _last_comma_to_and(with_str)
        output += with_str

        if self.input and self.input.strip():
            output += f":  {self.input}"

        output += self.modifier_string
        return output


def _last_comma_to_and(text: str) -> str:
    """"a, b, c" -> "a, b and c". HD writes lists the way prose does."""
    i = text.rfind(",")
    if i < 0:
        return text
    return text[:i] + " and" + text[i + 1:]
