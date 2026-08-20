"""
Modifier class for kirby-cost.

Converted from com.hero.objects.modifiers.Modifier.java

Modifiers represent advantages and limitations that can be applied to powers.
"""

from typing import Optional, List, TYPE_CHECKING
from kirby_cost.objects.base import GenericObject
from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.util.rounder import round_half_up, round_down

if TYPE_CHECKING:
    from kirby_cost.objects.adder import Adder


class Modifier(GenericObject):
    """
    Base class for all modifiers (advantages and limitations).
    
    Modifiers can have:
    - Base cost/value
    - Level-based costs
    - Adders
    - Nested modifiers (advantages on limitations, etc.)
    - Minimum/maximum value limits
    """

    def to_build_dict(self) -> dict:
        """A modifier, with the adders and sub-modifiers it carries."""
        d = self._build_dict_core()
        if getattr(self, "private_mod", False):
            d["private"] = True
        nested = [a.to_build_dict()
                  for a in getattr(self, "_assigned_adders", [])]
        if nested:
            d["adders"] = nested
        submods = [s.to_build_dict()
                   for s in getattr(self, "assigned_modifiers", [])]
        if submods:
            d["modifiers"] = submods
        return d


    XML_ATTRS = (
        XMLAttr("DISPLAYINSTRING", "_display_in_string", "yesno"),
    )

    
    def __init__(self):
        """Initialize a Modifier."""
        super().__init__()
        self._parent_object: Optional[GenericObject] = None
        self._is_limitation: bool = False
        self.is_limitation_set: bool = False
        #: (base_cost, level_cost) for each option the template offers.
        self._template_option_costs: list = []
        self.available_check: bool = False
        self.is_multiplier: bool = False
        self.excludes: List[str] = []
        self.requires: List[str] = []
        self._duration: str = ""
        self.requires_all: bool = False
        self.full_display: bool = False
        self.show_option_only: bool = False
        self.show_option_in_parens: bool = False
        self.show_input_in_parens: bool = False
        self.private_mod: bool = False
        self._display_in_string: bool = True
        self.comments: str = ""
        self._force_allow: bool = False
        
        # Modifiers default to -10 to +10 range
        self._minimum_cost = -10.0
        self._max_cost = 10.0
        self.min_set = True
        self.max_set = True
        self.fixed_value = True
    
    @property
    def parent(self) -> Optional[GenericObject]:
        """Get the parent object."""
        return self._parent_object

    @parent.setter
    def parent(self, parent: GenericObject) -> None:
        """Set the parent object for this modifier."""
        self._parent_object = parent
    
    @property
    def progenitor(self) -> Optional[GenericObject]:
        """Get the progenitor (original parent) of this modifier."""
        # This would track the original parent before nesting
        # For now, just return parent
        return self._parent_object
    
    @property
    def total_value(self) -> float:
        """
        Calculate the total value of this modifier.
        
        Formula:
        1. Start with base cost
        2. Add adder costs (using getDoubleTotal)
        3. Add level costs
        4. Apply advantages (positive nested modifiers): multiply by (1 + sum)
        5. Apply limitations (negative nested modifiers): divide by (1 + sum)
        6. Multiply by 4, round, divide by 4 (for quarter precision)
        7. Apply min/max limits
        
        Returns:
            Modifier value (positive for advantages, negative for limitations)
        """
        # Start with base cost
        total = self.base_cost
        
        # Add adder costs
        for adder in self.assigned_adders:
            # Use getDoubleTotal() for modifier calculations
            total += adder.double_total()
        
        # Add level costs
        if self._level_value > 0.0:
            level_units = float(self._levels) / self._level_value
            total += level_units * self._level_cost
        
        # Apply advantages (positive nested modifiers)
        advantage_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value > 0.0:
                advantage_sum += modifier.total_value
        
        if advantage_sum > 0.0:
            total = total * (1.0 + advantage_sum)
        
        # Apply limitations (negative nested modifiers)
        limitation_sum = 0.0
        for modifier in self.assigned_modifiers:
            if modifier.total_value < 0.0:
                limitation_sum += abs(modifier.total_value)
        
        if limitation_sum > 0.0:
            total = total / (1.0 + limitation_sum)
        
        # Multiply by 4, round to quarter, then divide by 4
        # This gives us quarter precision (0.25, 0.5, 0.75, etc.)
        sign = 1
        if total < 0.0:
            sign = -1
        
        total = abs(total) * 4.0
        total = round_half_up(total)
        total = (total / 4.0) * sign
        
        # Apply min/max limits
        if total < self._minimum_cost and self.min_set:
            total = self._minimum_cost
        elif total > self._max_cost and self.max_set:
            total = self._max_cost
        
        return total
    
    @property
    def limitation_modifier(self) -> bool:
        """
        Check if this modifier is a limitation (negative value).
        
        A modifier is a limitation if:
        - It has negative adders and no positive adders, OR
        - Its total value is negative
        """
        # Check for negative adders
        has_positive_adder = False
        has_negative_adder = False
        
        for adder in self.assigned_adders:
            if adder.base_cost > 0.0:
                has_positive_adder = True
            if adder.base_cost < 0.0:
                has_negative_adder = True
            if adder.level_cost > 0.0:
                has_positive_adder = True
            if adder.level_cost < 0.0:
                has_negative_adder = True
        
        # If has both positive and negative adders, check total value
        if has_positive_adder and has_negative_adder:
            return self.total_value < 0.0
        
        # If only has positive adders, it's not a limitation
        if has_positive_adder:
            return False
        
        # If only has negative adders, it's a limitation
        if has_negative_adder:
            return True
        
        # Default: check total value
        return self.total_value < 0.0
    
    @property
    def private(self) -> bool:
        """
        Check if this modifier is private.

        Ported from Modifier.java isPrivate():
        - If progenitor exists and is NOT a List and NOT a NakedModifier → false
        - Otherwise → return privateMod field
        """
        progenitor = self.progenitor
        if progenitor is not None:
            progenitor_name = type(progenitor).__name__
            is_list = progenitor_name in ("List", "Multipower", "VariablePowerPool", "ElementalControl")
            is_naked = progenitor_name == "NakedModifier"
            if not is_list and not is_naked:
                return False
        return self.private_mod
    
    @private.setter
    def private(self, value: bool) -> None:
        """Set whether this modifier is private."""
        self.private_mod = value
    
    @property
    def is_limitation(self) -> bool:
        """Whether this modifier makes the power WORSE.

        Ported from ``Modifier.isLimitation`` (Modifier.java:1065). This was a
        plain bool field defaulting to False and set from nowhere, so a
        modifier worth exactly zero — "Doesn't Protect Hit Location 18 (+0)" —
        sorted with the advantages and printed before the active-point note
        instead of after it.

        The decision has three stages and they are not interchangeable. A
        template that states ISLIMITATION settles it outright. Failing that,
        the OPTIONS decide: if they run in both directions the value does; if
        they only ever cost, it is an advantage; and if they only ever save —
        or if they are all free — it is a limitation, because a modifier that
        cannot cost anything is not being bought for benefit. Only with no
        options at all does it come down to the value.
        """
        if self.is_limitation_set:
            return self._is_limitation
        costs = self._template_option_costs
        if costs:
            has_positive = any(b > 0 or l > 0 for b, l in costs)
            has_negative = any(b < 0 or l < 0 for b, l in costs)
            if has_positive and has_negative:
                return self.total_value < 0
            if has_positive:
                return False
            return True
        return self.total_value < 0

    @is_limitation.setter
    def is_limitation(self, value: bool) -> None:
        self.is_limitation_set = True
        self._is_limitation = bool(value)

    @property
    def display_in_string(self) -> bool:
        """Whether this modifier should be displayed in the string."""
        return self._display_in_string

    @display_in_string.setter
    def display_in_string(self, value: bool) -> None:
        self._display_in_string = value
    
    @property
    def selected_option(self) -> Optional['Adder']:
        """Get the selected option for this modifier."""
        return self._selected_option
    
    @property
    def force_allow(self) -> bool:
        """Whether this modifier should be force-allowed."""
        return self._force_allow

    @force_allow.setter
    def force_allow(self, value: bool) -> None:
        self._force_allow = value
    
    def use_multiplier(self) -> bool:
        """Check if this modifier uses multiplier mode."""
        if self.is_multiplier:
            return True
        if self._parent_object is None:
            return False
        # If parent is a Modifier or Disadvantage, use multiplier
        # Use string check to avoid circular import
        parent_type = type(self._parent_object).__name__
        if parent_type == "Modifier":
            return True
        if parent_type == "Disadvantage":
            return True
        return False
    
    def contains_type(self, type_name: str) -> bool:
        """Check if this modifier can be applied to objects of the given type."""
        if not self._types or len(self._types) == 0:
            return True  # No type restriction
        return type_name in self._types
    
    def included(self, obj: Optional[GenericObject]) -> str:
        """
        Check if this modifier can be included with the given object.
        
        Returns:
            Empty string if allowed, error message if not allowed
        """
        if obj is None:
            return ""
        
        if self.force_allow:
            return ""
        
        # Check duration restrictions
        if self._duration and self._duration.strip():
            obj_duration = obj.duration if hasattr(obj, 'duration') else ""
            if self._duration.upper() == "INSTANT":
                if obj_duration != "INSTANT":
                    return f"{self._display} can only be applied to Instant Powers."
            elif self._duration.upper() == "CONSTANT":
                if obj_duration == "INSTANT":
                    return f"{self._display} can only be applied to Constant Powers."
            elif self._duration.upper() == "PERSISTENT":
                if obj_duration in ("INSTANT", "CONSTANT"):
                    return f"{self._display} can only be applied to Persistent Powers."
            elif self._duration.upper() == "INHERENT":
                if obj_duration in ("INSTANT", "CONSTANT", "PERSISTENT"):
                    return f"{self._display} can only be applied to Inherent Powers."
        
        # Check type restrictions
        if self._types and len(self._types) > 0:
            obj_types = obj.types if hasattr(obj, 'types') else []
            
            # Check for framework-specific types
            if "VPP" in self._types:
                # Would check if obj is VariablePowerPool
                pass
            if "MP" in self._types:
                # Would check if obj is Multipower
                pass
            if "EC" in self._types:
                # Would check if obj is ElementalControl
                pass
            if "LIST" in self._types:
                # Would check if obj is List
                pass
            
            # Check if object types match modifier types
            if obj_types:
                type_match = any(t in obj_types for t in self._types)
                if not type_match:
                    type_list = ", ".join(t.lower() for t in self._types)
                    return f"{self._display} can only be applied to abilities of type {type_list}."
        
        return ""
    
    def __str__(self) -> str:
        """String representation."""
        if self.full_display:
            # Would return HTML column output
            return self._display
        return self._display
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"<{self.__class__.__name__}(xmlid={self.xmlid}, value={self.total_value:.2f})>"
    
    def get_save_xml(self):
        """Get XML element for saving this modifier."""
        from lxml import etree
        from kirby_cost.io.xml_utility import XMLUtility
        
        element = super().get_save_xml()
        element.tag = "MODIFIER"
        
        # Modifier-specific attributes.
        #
        # Only when the DOCUMENT said so. `is_limitation` used to be a field
        # that nothing set, so writing it back on truthiness was harmless;
        # it is a computed decision now, and writing that decision out would
        # turn HD's own inference into a per-character override on every
        # modifier that happens to be a limitation. Same rule as DURATION
        # below, and for the same reason.
        if self.is_limitation and "IS_LIMITATION" in getattr(self, "_source_attrs", ()):
            element.set("IS_LIMITATION", "Yes")
        if self.private_mod:
            element.set("PRIVATE", "Yes")
        # Only when the document said so: DURATION is template-derived on most
        # modifiers, and writing it back makes it a per-character override.
        if self._duration and "DURATION" in getattr(self, "_source_attrs", ()) :
            element.set("DURATION", self._duration)
        
        return element
    
    @staticmethod
    def get_instance(element):
        """
        Factory method to create the appropriate Modifier subclass based on XMLID.
        
        Args:
            element: XML element (lxml.etree.Element) containing modifier data
            
        Returns:
            Appropriate Modifier subclass instance
        """
        from kirby_cost.io.xml_utility import XMLUtility
        
        xmlid = XMLUtility.get_value(element, "XMLID")
        if not xmlid or not xmlid.strip():
            xmlid = "GENERIC_OBJECT"
        
        xmlid = xmlid.strip().upper()
        
        # Map XMLID to class
        modifier_map = {
            "ONLYTOACTIVATE": "OnlyToActivate",
            "TIMELIMIT": "TimeLimit",
            "HALFRANGEMODIFIER": "HalfRangeModifier",
            "DAMAGEOVERTIME": "DamageOverTime",
            "AVAD": "AVAD",
            "DOUBLEENDCOST": "DoubleEnduranceCost",
            "PHYSICALMANIFESTATION": "PhysicalManifestation",
            "TRANSPARENT": "Transparent",
            "SEMIARMORPIERCING": "SemiArmorPiercing",
            "PARTIALCOVERAGE": "PartialCoverage",
            "NOTELEPORT": "CannotEscapeWithTeleport",
            "LIMITEDARCOFFIRE": "LimitedArcOfFire",
            "REQUIREDHANDS": "RequiredHands",
            "REALWEAPON": "RealWeapon",
            "MOBILE": "Mobile",
            "LINGERING": "Lingering",
            "VARIABLETARGETS": "VariableTarget",
            "FEEDBACK": "Feedback",
            "ONLYONAPPROPRIATETERRAIN": "OnlyOnAppropriateTerrain",
            "DROPPED": "Dropped",
            "DELAYEDRETURNRATE": "DelayedReturnRate",
            "VARIABLEEFFECT": "VariableEffect",
            "ONLYTOSTARTING": "OnlyToStarting",
            "SELFONLY": "SelfOnly",
            "OTHERSONLY": "OthersOnly",
            "BEAM": "Beam",
            "CANBEMISSILEDEFLECTED": "CanBeMissileDeflected",
            "NOKB": "NoKB",
            "COSTSENDONLYTOACTIVATE": "CostsENDOnlyToActivate",
            "HARDENED": "Hardened",
            "DOESNOTPROVIDEMENTALAWARENESS": "DoesNotProvideMentalAwareness",
            "NOTTHROUGHMINDLINK": "NotThroughMindLink",
            "COSTSENDTOMAINTAIN": "CostsENDToMaintain",
            "NORMALRANGE": "NormalRange",
            "TURNMODE": "TurnMode",
            "AFFECTSDESOLID": "AffectsDesolid",
            "AOE": "AreaEffect",
            "ARMORPIERCING": "ArmorPiercing",
            "AVLD": "AVLD",
            "AUTOFIRE": "Autofire",
            "BOECV": "BasedOnECV",
            "CUMULATIVE": "Cumulative",
            "DAMAGESHIELD": "DamageShield",
            "DELAYEDEFFECT": "DelayedEffect",
            "DIFFICULTTODISPEL": "DifficultToDispel",
            "DOESBODY": "DoesBODY",
            "DOESKB": "DoesKB",
            "DOUBLEKB": "DoubleKB",
            "CONTINUOUS": "Continuous",
            "PERSISTENT": "Persistent",
            "INHERENT": "Inherent",
            "EXPLOSION": "Explosion",
            "HOLEINTHEMIDDLE": "HoleInTheMiddle",
            "INDIRECT": "Indirect",
            "INVISIBLE": "Invisible",
            "MEGASCALE": "Megascale",
            "NND": "NND",
            "PENETRATING": "Penetrating",
            "PERSONALIMMUNITY": "PersonalImmunity",
            "INCREASEDMAXRANGE": "IncreasedMaxRange",
            "LOS": "LineOfSight",
            "NORANGEMODIFIER": "NoRangeModifier",
            "RANGED": "Ranged",
            "REDUCEDEND": "ReducedEND",
            "DELAYEDEND": "DelayedEND",
            "STICKY": "Sticky",
            "TRANSDIMENSIONAL": "Transdimensional",
            "TRIGGER": "Trigger",
            "UNCONTROLLED": "Uncontrolled",
            "UOO": "UsableOnOthers",
            "VARIABLEADVANTAGE": "VariableAdvantage",
            "VARIABLELIMITATIONS": "VariableLimitations",
            "VISIBLE": "Visible",
            "AFFECTSPHYSICALWORLD": "AffectsPhysicalWorld",
            "ENDRESERVEOREND": "ENDReserveOrEND",
            "ACV": "AlternateCombatValue",
            "ACTIVATIONROLL": "ActivationRoll",
            "ALWAYSON": "AlwaysOn",
            "CHARGES": "Charges",
            "CONCENTRATION": "Concentration",
            "INSTANT": "Instant",
            "NONPERSISTENT": "Nonpersistent",
            "COSTSEND": "CostsEND",
            "INCREASEDEND": "IncreasedEND",
            "EXTRATIME": "ExtraTime",
            "FOCUS": "Focus",
            "GESTURES": "Gestures",
            "INCANTATIONS": "Incantations",
            "LINKED": "Linked",
            "NORANGE": "NoRange",
            "LIMITEDRANGE": "LimitedRange",
            "RANGEBASEDONSTR": "RangeBasedOnSTR",
            "REDUCEDBYRANGE": "ReducedByRange",
            "SUBJECTTORANGEMODIFIER": "SubjectToRangeModifier",
            "REQUIRESASKILLROLL": "RequiresSkillRoll",
            "RESTRAINABLE": "Restrainable",
            "SIDEEFFECTS": "SideEffects",
        }
        
        class_name = modifier_map.get(xmlid)
        if class_name:
            # Import and instantiate the specific modifier class
            module_name = f"kirby_cost.objects.modifiers.{class_name.lower()}"
            try:
                module = __import__(module_name, fromlist=[class_name])
                modifier_class = getattr(module, class_name)
                return modifier_class(element)
            except (ImportError, AttributeError):
                # Fall back to base Modifier if class not found
                pass
        
        # Default to base Modifier
        modifier = Modifier()
        modifier._init(element)
        return modifier

    def get_fraction(self, val: float) -> str:
        """The value HD prints inside a modifier's brackets.

        Ported from ``Modifier.getFraction`` (Modifier.java:532). Not a general
        decimal-to-fraction helper — ``GenericObject.fraction`` is that, and is
        not a substitute. This always carries an explicit sign, snaps to
        quarters by NEAREST match rather than exact equality, rolls a value
        within a quarter of the next whole number up into it, and has a
        separate multiplier form.
        """
        flag = "*" if (_flag_forced_modifiers() and self.force_allow) else ""
        use_mult = self.use_multiplier()

        if val == 0:
            if use_mult:
                return "x1" + flag
            return ("-0" if self.is_limitation else "+0") + flag

        if use_mult:
            ret = "x"
            is_neg = val < 0
            val = abs(val)
            frac = ""
            check = round_down(val + 0.0000001)
            if check < val:
                # HD detaches the parent before recursing so the nested call
                # cannot pick up a multiplier from it.
                holder, self._parent = self._parent, None
                frac = self._fraction_plain(val - check)
                self._parent = holder
                if frac.startswith("+"):
                    frac = frac[1:]
            if frac.strip():
                frac = " " + frac
            check += 1
            ret += (f"1/{check}{frac}" if is_neg else f"{check}{frac}")
            return ret + flag

        return self._fraction_plain(val) + flag

    def _fraction_plain(self, val: float) -> str:
        """The non-multiplier half of getFraction, split out so the multiplier
        branch can recurse into it without re-testing use_multiplier()."""
        ret = "-" if val < 0 else "+"
        val = abs(val)
        if val > 1:
            ret += str(int(round_down(val + 1) if self.use_multiplier()
                           else round_down(val)))
            val = val - round_down(val)
        if val == 0:
            return ret

        closest_match = ""
        closest = 1.0
        for candidate, text in ((0.25, "1/4"), (0.5, "1/2"), (0.75, "3/4")):
            if abs(candidate - val) < closest:
                closest = abs(candidate - val)
                closest_match = text
        if abs(1 - val) < closest:
            # Nearer the next whole number than to three quarters: absorb it.
            closest_match = ""
            if len(ret) > 1:
                ret = ret[0] + str(int(ret[1:]) + 1)
            elif ret not in ("+", "-", "x") and len(ret) == 1:
                ret = str(int(ret) + 1)
            elif not ret.strip() or ret.strip() == "+":
                ret = "+1"
            else:
                ret = "-1"
        if len(ret) > 1:
            ret += " "
        return (ret + closest_match).strip()

    @property
    def column2_output(self) -> str:
        """``Resistant (+1/2)`` — the alias, then everything in brackets.

        Ported from ``Modifier.getColumn2Output`` (Modifier.java:415). This
        class inherited GenericObject's default, which is the alias and the
        input and nothing else, so every modifier printed without the value
        that makes it mean anything.
        """
        ret = "" if self.show_option_only else (self.alias or "")
        val = self.total_value
        option = self._selected_option

        if (not self.show_option_in_parens and option is not None
                and getattr(option, "display_in_string", True)
                and (option.alias or "").strip()):
            ret = f"{ret} {option.alias}".strip()
        if not self.show_input_in_parens and self.input and self.input.strip():
            if ret.strip():
                ret += " "
            ret += self.input
        ret = ret.strip()
        for nested in self.assigned_modifiers:
            ret += f", {nested.alias}"

        # An alias may open a bracket of its own — "Reduced Endurance (0 END".
        # HD continues that one rather than opening a second.
        paren_count = ret.count("(") - ret.count(")")
        ret += " (" if paren_count <= 0 else "; "

        if (self.show_option_in_parens and option is not None
                and getattr(option, "display_in_string", True)
                and (option.alias or "").strip()):
            ret += option.alias.strip() + "; "
        if self.show_input_in_parens and self.input and self.input.strip():
            ret += self.input + "; "
        for adder in self.assigned_adders:
            if not getattr(adder, "is_selected", True):
                continue
            text = (adder.column2_output or "").strip()
            if text:
                ret += text + "; "
        if (self.comments or "").strip():
            ret += self.comments + "; "

        if val > self._max_cost and self.max_set:
            val = self._max_cost
        if val < self._minimum_cost and self.min_set:
            val = self._minimum_cost

        ret += self.get_fraction(val) + ")"
        paren_count -= 1
        while paren_count > 0:
            ret += ")"
            paren_count -= 1
        return ret


def _flag_forced_modifiers() -> bool:
    """The preference that marks force-allowed modifiers with an asterisk."""
    try:
        from kirby_cost.core.context import EngineContext
        return bool(EngineContext.prefs().flag_forced_modifiers)
    except Exception:  # noqa: BLE001 — a missing preference is not an error
        return False
