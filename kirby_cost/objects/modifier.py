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
        self._duration: str = ""
        # Applicability, from the template (apply_template).
        self._excludes: tuple = ()
        self._requires: tuple = ()
        self._requires_all: bool = False
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
    def levels(self) -> int:
        """Java's getLevels() clamp (GenericObject.java:1996-2001), scoped to
        modifiers: the template's MINVAL floors the raw field. NOTELEPORT
        declares MINVAL=1 LVLCOST=.25, so a stated LEVELS=0 still prices one
        level -- HD's +1/4 on the sink's Naked Advantage."""
        if self._levels < self._minimum_level:
            return self._minimum_level
        return self._levels

    @levels.setter
    def levels(self, value: int) -> None:
        self._levels = value

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
        
        # Add level costs. Java reads getLevels() -- the MINVAL-clamped
        # accessor -- not the raw field (Modifier.getTotalValue), so a stated
        # LEVELS below the template's MINVAL still prices at the floor:
        # NOTELEPORT (MINVAL=1, LVLCOST=.25) is +1/4 even when the document
        # writes no LEVELS at all.
        if self._level_value > 0.0:
            level_units = float(self.levels) / self._level_value
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
        """May this modifier go on ``obj``? ``""`` if so, else HD's reason.

        A line-by-line port of ``Modifier.java:763`` (``included``), in the
        Java's order, messages verbatim -- ``tests/test_included_matrix.py``
        compares every template modifier against every template power with
        what HD itself returns, so the text is part of the contract (HD's
        typo "abilties" included).  The book pages behind the generic rules
        are cited per block; where HD's code and the book differ, HD wins
        (PeterB, 2026-08-29: "if Steve Long says so, it's canon").

        Note the martial-arts "10 point style" rule is NOT here: it is
        commented out in the Java (``Modifier.java:807-825``, "removed per
        phone conversation with Steve Long -- 04/28/2010").
        """
        # Modifier.java:764-769 -- a null power is always allowed.
        if obj is None:
            return ""

        # Modifier.java:770-778 -- a modifier on a modifier is judged against
        # the progenitor: the first non-Modifier ancestor.
        modifier_parent = False
        if isinstance(obj, Modifier):
            modifier_parent = True
            node = obj.parent
            while isinstance(node, Modifier):
                node = node.parent
            if node is None:
                return ""
            obj = node

        # Modifier.java:779-781 -- forceAllow() outranks every rule below.
        if self.force_allow:
            return ""

        # Modifier.java:782-806 -- 6E1 p.129: every Power has one of three
        # durations (Instant, Constant, Persistent) and may be made Inherent;
        # a modifier declaring DURATION needs at least that much.
        if self._duration and self._duration.strip():
            d = getattr(obj, "duration", "") or ""
            mine = self._duration.upper()
            if mine == "INSTANT":
                if d != "INSTANT":
                    return f"{self.display} can only be applied to Instant Powers."
            elif mine == "CONSTANT":
                if d == "INSTANT":
                    return f"{self.display} can only be applied to Constant Powers."
            elif mine == "PERSISTENT":
                if d in ("INSTANT", "CONSTANT"):
                    return f"{self.display} can only be applied to Persistent Powers."
            elif mine == "INHERENT":
                if d in ("INSTANT", "CONSTANT", "PERSISTENT"):
                    return f"{self.display} can only be applied to Inherent Powers."

        from kirby_cost.objects.list import List as HeroList
        from kirby_cost.objects.frameworks.elemental_control import ElementalControl
        from kirby_cost.objects.frameworks.multipower import Multipower
        from kirby_cost.objects.frameworks.vpp import VariablePowerPool

        # Modifier.java:826-831 -- Advantages go on the slots, not the pool.
        # 6E1 p.23 records that 6E removed Elemental Controls outright; the
        # rule lives on in HD for 5E-era builds, so it is an HD rule now.
        if (isinstance(obj, ElementalControl) and not self.is_limitation
                and not modifier_parent):
            return (f"{self.display} cannot be applied to an Elemental Control.  "
                    "Advantages should be applied to each slot individually.")

        # Modifier.java:832-874 -- framework typing, then type matching.
        # TYPE=VPP/MP/EC/LIST names a Power Framework (6E1 p.398) rather than
        # an ability type; anything else is matched against the power's own
        # TYPE list.  Both lists come from the HD template, not the book.
        ret = ""
        types = list(self._types or [])
        if not types or isinstance(obj, HeroList):
            if not types:
                ret = ""
            elif not isinstance(obj, VariablePowerPool) and "VPP" in types:
                ret = f"{self.display} can only be applied to a Variable Power Pool."
            elif not isinstance(obj, Multipower) and "MP" in types:
                ret = f"{self.display} can only be applied to a Multipower."
            elif not isinstance(obj, ElementalControl) and "EC" in types:
                ret = f"{self.display} can only be applied to an Elemental Control."
            elif not isinstance(obj, HeroList) and "LIST" in types:
                ret = f"{self.display} can only be applied to a List."
            else:
                ret = ""
        else:
            # Modifier.java:854-865: ", " between, "or " before the last, and
            # nothing appended after -- the message has NO trailing period.
            ret = f"{self.display} can only be applied to abilities of type "
            for i, t in enumerate(types):
                if i > 0:
                    ret += ", "
                if i == len(types) - 1 and i > 0:
                    ret += "or "
                ret += str(t).lower()
            # Modifier.java:866-873: only a MATCHING power type clears the
            # message, so a power with no types at all stays refused.
            for s in (getattr(obj, "types", None) or []):
                if self.contains_type(s):
                    ret = ""

        if ret.strip():
            return ret

        # Modifier.java:875-899 -- EXCLUDES, checked against the modifiers
        # already on the power, the power's own xmlid, and its selected
        # adders.  HD template rule, no page.
        assigned = list(getattr(obj, "assigned_modifiers", None) or [])
        adders = list(getattr(obj, "assigned_adders", None) or [])
        for xmlid in (self._excludes or ()):
            xmlid = xmlid.upper().strip()
            for mod in assigned:
                if (mod.xmlid or "").upper().strip() == xmlid:
                    return (f"{self.display} cannot be applied to abilties "
                            f"which have {mod.display}")
            if (obj.xmlid or "").upper().strip() == xmlid:
                return f"{self.display} cannot be applied to {obj.display}"
            for add in adders:
                if ((add.xmlid or "").upper().strip() == xmlid
                        and getattr(add, "is_selected", False)):
                    return (f"{self.display} cannot be applied to abilties "
                            f"which have {add.display}")

        # Modifier.java:900-965 -- REQUIRES, any-of or (REQUIRESALL) all-of.
        # Each entry is an xmlid, optionally narrowed to a chosen option as
        # XMLID.OPTIONID, matched against the power, its modifiers or its
        # adders.  HD template rule, no page.
        requires = list(self._requires or ())
        if not requires:
            return ""

        # The message is built BEFORE the check (Java:903-925) and cleared if
        # the requirement turns out to be met.  For a single requirement the
        # Java names it once in the prefix and again in the loop; that
        # duplication is HD's output and the matrix holds us to it.
        if len(requires) > 1:
            ret = (f"{self.display} requires the following modifiers:  "
                   if self._requires_all
                   else f"{self.display} requires at least one of the following: ")
        else:
            ret = f"{self.display} requires {requires[0]}"
        for i, r in enumerate(requires):
            if i > 0:
                ret += ", "
            if i == len(requires) - 1:
                ret += "and " if self._requires_all else "or "
            ret += r

        def _has(entry: str, option: Optional[str]) -> bool:
            candidates = [obj] + assigned + adders
            for o in candidates:
                if (getattr(o, "xmlid", "") or "").upper().strip() != entry:
                    continue
                if option is None:
                    return True
                sel = getattr(o, "selected_option", None)
                if sel is not None and (sel.xmlid or "").upper() == option:
                    return True
            return False

        missed_one = False
        for entry in requires:
            entry = entry.upper().strip()
            option = None
            dot = entry.find(".")
            if 0 < dot < len(entry) - 1:
                option = entry[dot + 1:].strip() or None
                entry = entry[:dot]
            if _has(entry, option):
                if self._requires_all:
                    continue
                ret = ""
                break
            missed_one = True
            if self._requires_all:
                break
        if not missed_one:
            ret = ""
        return ret


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
        
        # Resolve through the registry that ``__init_subclass__`` already
        # maintains (GenericObject._registry, xmlid -> class).
        #
        # This used to be a hand-written ``modifier_map`` of xmlid -> class
        # NAME, resolved by importing ``kirby_cost.objects.modifiers.<name
        # .lower()>`` inside a bare try/except. Four classes live in
        # underscored modules -- self_only.py, no_kb.py, does_body.py,
        # does_kb.py -- so that import raised ModuleNotFoundError, the
        # except swallowed it, and the loader silently built a generic
        # Modifier for SELFONLY, NOKB, DOESBODY and DOESKB. Those are on
        # 13 / 24 / 72 / 3 corpus characters. Their cost and display were
        # still right (the subclasses override neither), but their
        # ``included()`` validation was unreachable, and nothing noticed
        # because nothing calls ``included()``.
        #
        # Measured 2026-08-29 before this change: the map and the registry
        # agreed on all 77 entries that resolved, and the registry held no
        # modifier the map lacked. The map was a second registry that could
        # only ever drift; it is gone.
        import kirby_cost.objects._registry_imports  # noqa: F401 -- populate
        from kirby_cost.objects.base import GenericObject
        cls = GenericObject._registry.get(xmlid)
        if cls is not None and cls is not Modifier and issubclass(cls, Modifier):
            return cls(element)

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
        # Java is getSelectedOption(), and subclasses override it. Alternate
        # Combat Value drops an option that does not match the kind of power
        # it is on (AlternateCombatValue.java:73): Arthon's Entangle is not
        # MENTAL, so its MENTALOCV option is not HD's to print and the line
        # reads "Alternate Combat Value (+1/4)". Reading the private field
        # went behind every such override.
        option = self.selected_option

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
