"""
Detect power class for kirby-cost.

Converted from com.hero.objects.powers.Detect.java

Power to detect things.
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.powers.sense import Sense

#: Java's Constants.INT — hero.characteristic() keys on this ordinal.
_INT = 4


class Detect(Sense, xmlid="DETECT"):
    """
    Detect power.
    
    Power to detect specific things.
    """

    #: Whether the Detect is an ACTIVE sense — Java reads and writes it
    #: (Detect.java:145, :152) and this port did neither, so 17 characters
    #: exported a Detect that had lost the distinction entirely.
    XML_ATTRS = (
        XMLAttr("ACTIVE", "active", "yesno"),
    )

    def __init__(self):
        """Initialize a Detect power."""
        super().__init__(Detect.XMLID)
        self._duration = "CONSTANT"
        self.active: bool = False
    
    def _is_focus(self) -> bool:
        """Whether this Detect is done by a focus rather than by the character.

        Java's `isFocus()` is on GenericObject; only Skill has it here, so
        this mirrors Skill's — the FOCUS modifier on the object itself or on
        the framework it sits in.
        """
        from kirby_cost.objects.base import GenericObject
        if GenericObject.find_object_by_id(self.assigned_modifiers, "FOCUS") is not None:
            return True
        parent = self._parent
        if parent is not None:
            return GenericObject.find_object_by_id(
                parent.assigned_modifiers, "FOCUS") is not None
        return False

    @property
    def damage_display(self) -> str:
        """``18-`` — the roll to notice something, not a distance.

        Ported from ``Detect.getDamageDisplay``. This returned
        "{levels}m range", which is a different quantity entirely: a Detect's
        levels buy the ROLL, and range is a separate adder. HD prints
        "Detect Magic 18- (no Sense Group)"; this printed
        "Detect Magic 3m range (no Sense Group)".

        A Detect through a focus rolls 9 + levels flat, since the focus does
        the perceiving rather than the character.
        """
        hero = _active_hero()
        if self._is_focus() and hero is not None:
            return f"{9 + self._levels}-"
        if hero is None:
            return f"{9 + self._levels}-"
        intel = hero.characteristic(_INT)
        if intel is None:
            return f"{9 + self._levels}-"
        # The loader maps only RUNNING, SWIMMING and LEAPING to their own
        # classes, so INT arrives as a plain Characteristic and does not carry
        # Intelligence's PER-roll methods. They read nothing but the value and
        # the hero's powers, so they are called unbound rather than changing
        # what the loader constructs — that mapping is a cost decision and
        # this is a display one.
        from kirby_cost.objects.characteristics.intelligence import Intelligence
        base1 = Intelligence.primary_per_roll(intel, hero) + self._levels
        base2 = Intelligence.secondary_per_roll(intel, hero) + self._levels
        ret = f"{base1}-"
        if base1 != base2:
            ret += f"/{base2}-"
        return ret
    
    @property
    def column2_output(self) -> str:
        """Get column 2 output string."""
        output = self._alias
        
        if self._name and self._name.strip():
            output = f"<i>{self._name}:</i>  {output}"
        
        # Get selected option display
        if self._selected_option:
            option_display = self._selected_option.alias
            # Check for EXTRA adders
            extra_adders = []
            for adder in self.assigned_adders:
                if adder.xmlid == "EXTRA":
                    extra_adders.append(adder.alias)
                    adder.display_in_string = False
            
            if extra_adders:
                option_display += ", " + ", ".join(extra_adders)
                # Replace last comma with "and"
                if ", " in option_display:
                    last_comma = option_display.rfind(", ")
                    option_display = (option_display[:last_comma] + 
                                    " and" + 
                                    option_display[last_comma+1:])
            
            output += " " + option_display
        
        output += " " + self.damage_display
        
        # Add group if multiple groups available
        group = self.group
        available_groups = self.available_groups
        if group and len(available_groups) > 1:
            output += f" ({group.alias})"
        elif group is None and len(available_groups) > 1:
            output += " (Unusual Group)"
        
        adder_str = self.adder_string
        if adder_str and adder_str.strip():
            output += ", " + adder_str
        
        modifier_str = self.modifier_string
        output += modifier_str
        
        return output
    



def _active_hero():
    """The character whose PER roll this Detect is measured against."""
    try:
        from kirby_cost.core.context import EngineContext
        return EngineContext.active_hero()
    except Exception:  # noqa: BLE001
        return None
