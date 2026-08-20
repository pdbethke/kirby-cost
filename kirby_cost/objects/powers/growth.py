"""
Growth power class for kirby-cost.

Converted from com.hero.objects.powers.Growth.java

Power to increase character size.
"""

from kirby_cost.objects.powers.power import Power
from kirby_cost.util.rounder import round_half_up, round_down
import math



#: What each Growth size confers. In 6E these are FIXED per size rather than
#: scaled per level, so the whole line is a table lookup — HD's own
#: getPlainDamageDisplay is a chain of `else if` on the option's xmlid, and
#: this is that chain as data. Order matters only for readability.
_GROWTH_SIZES = {
    "LARGE":      dict(STR=15, CON=5,  PRE=5,  PD=3,  ED=3,  BODY=3,  STUN=6,
                       reach=1,  running=12, kb=6,  radius=0, ocv=2,  per=2,
                       weight="101-800 kg", size="2-4m tall, 1-2m wide"),
    "ENORMOUS":   dict(STR=30, CON=10, PRE=10, PD=6,  ED=6,  BODY=6,  STUN=12,
                       reach=3,  running=24, kb=12, radius=0, ocv=4,  per=4,
                       weight="801-6,400 kg", size="5-8m tall, 3-4m wide"),
    "HUGE":       dict(STR=45, CON=15, PRE=15, PD=9,  ED=9,  BODY=9,  STUN=18,
                       reach=7,  running=36, kb=18, radius=1, ocv=6,  per=6,
                       weight="6,401-50,000 kg", size="9-16m tall, 5-8m wide"),
    "GIGANTIC":   dict(STR=60, CON=20, PRE=20, PD=12, ED=12, BODY=12, STUN=24,
                       reach=15, running=48, kb=24, radius=2, ocv=8,  per=8,
                       weight="50,001-400,000 kg", size="17-32m tall, 9-16m wide"),
    "GARGANTUAN": dict(STR=75, CON=25, PRE=25, PD=15, ED=15, BODY=15, STUN=30,
                       reach=31, running=60, kb=30, radius=3, ocv=10, per=10,
                       weight="40,001-3.2 mil kg", size="33-64m tall, 17-32m wide"),
    "COLOSSAL":   dict(STR=90, CON=30, PRE=30, PD=18, ED=18, BODY=18, STUN=36,
                       reach=63, running=72, kb=36, radius=4, ocv=12, per=12,
                       weight="3.3-25.6 mil kg", size="65-125m tall, 33-64m wide"),
}

class Growth(Power, xmlid="GROWTH"):
    """
    Growth power.
    
    Increases character size, affecting mass, height, and various characteristics.
    """
    
    def __init__(self):
        """Initialize a Growth power."""
        super().__init__()
        self.xmlid = Growth.XMLID
        self._duration = "CONSTANT"
        # Stub: would initialize mass/height multipliers and characteristic increases
    
    @property
    def damage_display(self) -> str:
        """``+60 STR, +20 CON, +20 PRE, +12 PD, ... 17-32m tall, 9-16m wide``.

        Ported from ``Growth.getPlainDamageDisplay`` (6E branch). A Growth is
        a SIZE, not a number of levels, and the size confers a fixed list —
        strength, constitution, presence, defences, body, stun, reach,
        running, knockback resistance, the weight and height ranges, and how
        much easier the character is to hit and to see. "(Gigantic size)" named
        the size and said none of what it means.

        The Area Of Effect clause appears only from Huge upward, where the
        character's hands are large enough to be an area attack in themselves.
        """
        from kirby_cost.objects.base import option_alias
        option = self._selected_option
        key = (getattr(option, "xmlid", "") or "").upper()
        if not key:
            key = (getattr(self, "option_id", "") or "").upper()
        row = _GROWTH_SIZES.get(key)
        if row is None:
            return ""
        area = (f"hands/feet are Area Of Effect ({row['radius']}m Radius) attacks, "
                if row["radius"] > 0 else "")
        return (f"+{row['STR']} STR, +{row['CON']} CON, +{row['PRE']} PRE, "
                f"+{row['PD']} PD, +{row['ED']} ED, +{row['BODY']} BODY, "
                f"+{row['STUN']} STUN, +{row['reach']}m Reach, "
                f"+{row['running']}m Running, -{row['kb']}m KB, "
                f"{area}{row['weight']}, +{row['ocv']} to OCV to hit, "
                f"+{row['per']} to PER Rolls to perceive character, {row['size']}")
    @property
    def plain_damage_display(self) -> str:
        """Get plain growth display string."""
        # Stub: would calculate mass, height, STR, CON, PRE, PD, ED, BODY, STUN, reach, running, KB, OCV, PER
        # For 6E with selected option, would use predefined size categories
        # For now, return simplified version
        if self._selected_option:
            # Stub: would use size category values
            return f"{self._selected_option.alias} size"
        return f"{self._levels} levels"
    
    @property
    def column2_output(self) -> str:
        """``Growth (+60 STR, +20 CON, ... 17-32m tall, 9-16m wide)``.

        Ported from ``Growth.getColumn2Output``. The bracket holds what the
        size CONFERS, and in 6E the option is not printed separately at all —
        HD's `getSelectedOption()` branch is guarded on `!is6E()`, because in
        6E the list inside the bracket already says which size it is.
        """
        from kirby_cost.objects.base import is_6e, option_alias
        ret = f"{self.alias or ''} ({self.damage_display})"
        if self._name and self._name.strip():
            ret = f"<i>{self._name}:</i>  {ret}"
        if self.input and self.input.strip():
            ret += f":  {self.input}"
        option = (option_alias(self) or "").strip()
        adders = self.adder_string
        if option and not is_6e():
            ret += f" ({option}"
            if adders.strip():
                ret += f"; {adders}"
            ret += ")"
        elif adders.strip():
            ret += f" ({adders})"
        ret += self.modifier_string
        ret += self._end_reserve_note()
        return ret
