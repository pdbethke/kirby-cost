"""
CustomSkill skill class for kirby-cost.

Converted from com.hero.objects.skills.CustomSkill.java
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill

if TYPE_CHECKING:
    from kirby_cost.io.hdc_loader import LoadedHero as Hero  # the live hero type
    from kirby_cost.ui.dialog.generic_dialog import GenericDialog


class CustomSkill(Skill, xmlid="CUSTOMSKILL"):
    """Custom Skill."""
    
    def __init__(self, xmlid: str = None):
        """Initialize CustomSkill."""
        super().__init__(xmlid or CustomSkill.XMLID)
        self._minimum_level = -999
        # CustomSkill carries an explicit numeric roll from the HDC ``ROLL``
        # attribute.  Skill.roll is a *computed display string* used by the
        # cost engine (levels_only, etc.), so we MUST NOT shadow it with an
        # int — store the numeric roll separately and expose it via
        # roll_value, leaving the inherited string ``roll`` property intact.
        self._custom_roll: int = 0

    def dialog(self, bl: bool, bl2: bool) -> 'GenericDialog':
        """Get dialog (stub - would need CustomSkillDialog)."""
        # Would need: from kirby_cost.ui.dialog.custom_skill_dialog import CustomSkillDialog
        # return CustomSkillDialog(self, bl, bl2)
        raise NotImplementedError("CustomSkillDialog not yet implemented")

    @property
    def roll_value(self) -> int:
        """Get the explicit numeric roll value from the HDC ``ROLL`` attribute."""
        return self._custom_roll

    @property
    def roll(self) -> str:
        """``CustomSkill.getRoll`` (CustomSkill.java:48).

        The stated roll, and nothing else. Skill.roll compares the primary
        roll against the secondary and prints both when they differ --
        "15- (14-)" -- but a custom skill's roll is a number the player typed,
        so there is no secondary to disagree with it. Inheriting Skill's
        version printed a computed 14- beside Necrull's stated 15-.

        An unstated roll (0) prints nothing at all.
        """
        if not self._custom_roll:
            return ""
        return f"{self.roll_value}-"

    def get_save_xml(self) -> 'Element':
        """Get save XML."""
        element = super().get_save_xml()
        element.set("ROLL", str(self._custom_roll))
        return element

    def _init(self, element) -> None:
        """Read this element. Was restore_from_save."""
        super()._init(element)
        # Folded in from restore_from_save, which ran after _init.
        # One ingest per class; see engine/xml_attrs.py.
        roll_str = element.get("ROLL")
        if roll_str and roll_str.strip():
            try:
                self._custom_roll = int(roll_str)
            except (ValueError, TypeError):
                self._custom_roll = 0
        else:
            self._custom_roll = 0
    



