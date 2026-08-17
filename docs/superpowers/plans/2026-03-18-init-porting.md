# HD6 Init Porting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining 4.2% oracle gap (2,196 issues across 28,593 cost calculations) by porting Java init(Element) cost-resolution logic to Python in a DRY, data-driven way.

**Architecture:** Three categories of fix address all issues: (1) option alias resolution in template JSON + loader for sense powers, (2) reuse Survival's adder-based cost for all similar skills, (3) thin _init() overrides and class mapping for powers/perks with unique cost logic. Each fix is independent and oracle-verifiable.

**Tech Stack:** Python 3.12, lxml, pytest, oracle_compare_v2.py (Java HD6 CLI comparison)

**Key Insight:** Analysis shows the oracle_compare_v2.py uses positional alignment between Java and Python lists. Many reported issues (e.g., 309 KnowledgeSkill) are actually alignment phantoms — when one skill's cost is wrong, all subsequent skills at that index get flagged. Real skill issues total 87 (all adder-based), not 573. Fixing the root causes will cascade-fix the phantom issues.

**Verification command:** `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | grep "^TOTAL\|^PERFECT\|^ISSUES"`

**Baseline:** 27,380/28,593 matched (95.8%), 376 perfect characters

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `kirby_cost/data/template_6e.json` | Modify | Add `option_aliases` for sense powers |
| `kirby_cost/io/hdc_loader.py` | Modify | Option alias resolution, class maps for perks/powers, EndRes recovery loading |
| `kirby_cost/objects/skills/adder_based_skill.py` | Create | Extract adder-based skill cost pattern from Survival |
| `kirby_cost/objects/skills/survival.py` | Modify | Thin re-export of AdderBasedSkill |
| `kirby_cost/objects/powers/force_wall.py` | Modify | Read dimension levels in _init() |
| `kirby_cost/objects/perks/follower.py` | Modify | Read BASEPOINTS/DISADPOINTS/MULTIPLES in _init() |
| `tests/test_init_porting.py` | Create | Oracle-driven integration tests |

**Note:** Tests require the Java HD6 CLI (`kirby-hd-oracle/hd6cli.sh`) and HDC resource files (`champions-campaign-manager/resources/`). Tests use `pytest.skip()` when unavailable.

---

### Task 1: Option Alias Resolution (EnhancedPerception 237 + Telescopic 108 = 345 issues)

**Files:**
- Modify: `kirby_cost/data/template_6e.json` — add `option_aliases` to ENHANCEDPERCEPTION, TELESCOPIC
- Modify: `kirby_cost/io/hdc_loader.py:72-137` — resolve aliases before option lookup
- Create: `tests/test_init_porting.py`

The template has options keyed `ALL`, `SENSEGROUP`, `SINGLE`. HDC files use specific group names like `HEARINGGROUP`, `SMELLGROUP`. The loader does exact match, never finds them, falls back to wrong default.

- [ ] **Step 1: Write failing test**

```python
# tests/test_init_porting.py
"""Oracle-driven integration tests for init porting fixes.

Requires:
- Java HD6 CLI at kirby-hd-oracle/hd6cli.sh
- HDC resource files at champions-campaign-manager/resources/
Tests skip gracefully when unavailable.
"""
import json
import os
import subprocess
import pytest
from pathlib import Path

RESOURCE_DIR = Path(__file__).parent.parent.parent / "champions-campaign-manager" / "resources"
HD6CLI = str(Path(__file__).parent.parent.parent / "kirby-hd-oracle" / "hd6cli.sh")


def _hdc_files():
    """Yield all HDC file paths."""
    for root, dirs, files in os.walk(RESOURCE_DIR):
        if "__MACOSX" in root:
            continue
        for f in files:
            if f.endswith(".hdc") and "CV3" not in f:
                yield os.path.join(root, f)


def _oracle(hdc_path: str) -> dict:
    """Run Java oracle on an HDC file, return parsed JSON."""
    result = subprocess.run(
        [HD6CLI, hdc_path], capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip(f"Oracle failed for {hdc_path}")
    output = result.stdout
    idx = output.find("{")
    if idx < 0:
        pytest.skip(f"No JSON in oracle output for {hdc_path}")
    return json.loads(output[idx:])


def _find_hdc_with(xmlid: str) -> str:
    """Find first HDC file containing a given XMLID."""
    for path in _hdc_files():
        with open(path, "rb") as fh:
            if xmlid.encode() in fh.read():
                return path
    pytest.skip(f"No HDC with {xmlid} found")


def _compare_section(hero_list, oracle_list, section="powers"):
    """Compare Python objects against Java oracle, return list of (py, java) mismatches."""
    FW = {"Multipower", "VariablePowerPool", "ElementalControl", "List"}
    java_filtered = [j for j in oracle_list if j.get("class") not in FW]
    py_filtered = [p for p in hero_list
                   if p.get_xmlid() not in ("MULTIPOWER", "VPP", "ELEMENTALCONTROL")
                   and not (p.get_xmlid() == "GENERIC_OBJECT"
                            and p.get_levels() == 0
                            and p.get_level_cost() == 0.0)]
    mismatches = []
    for i, java_obj in enumerate(java_filtered):
        if i >= len(py_filtered):
            break
        py_obj = py_filtered[i]
        for field in ("total_cost", "active_cost", "real_cost"):
            py_val = (py_obj.get_total_cost() if field == "total_cost"
                      else py_obj.get_active_cost() if field == "active_cost"
                      else py_obj.get_real_cost_pre_list())
            if abs(py_val - java_obj[field]) > 0.01:
                mismatches.append((py_obj, java_obj, field))
                break  # one mismatch per object is enough
    return mismatches


class TestSensePowerCosts:
    """EnhancedPerception/Telescopic option alias resolution."""

    def test_enhanced_perception_costs_match_oracle(self):
        """All EP objects in a character should match Java costs."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("ENHANCEDPERCEPTION")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        ep_mismatches = [m for m in mismatches if m[1]["xmlid"] == "ENHANCEDPERCEPTION"]
        assert len(ep_mismatches) == 0, \
            f"EP mismatches: {[(m[1]['xmlid'], m[2], m[1][m[2]]) for m in ep_mismatches]}"

    def test_telescopic_costs_match_oracle(self):
        """All Telescopic objects in a character should match Java costs."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("TELESCOPIC")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        tel_mismatches = [m for m in mismatches if m[1]["xmlid"] == "TELESCOPIC"]
        assert len(tel_mismatches) == 0, \
            f"Telescopic mismatches: {[(m[1]['xmlid'], m[2], m[1][m[2]]) for m in tel_mismatches]}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestSensePowerCosts -v`
Expected: FAIL — Python uses wrong level_cost for sense group options

- [ ] **Step 3: Add option_aliases to template JSON**

In `kirby_cost/data/template_6e.json`, add `option_aliases` field to ENHANCEDPERCEPTION and TELESCOPIC:

For ENHANCEDPERCEPTION, add after the existing fields (before `"options"`):
```json
"option_aliases": {
    "ALL": "ALL",
    "*GROUP": "SENSEGROUP",
    "*": "SINGLE"
},
```

Same `option_aliases` for TELESCOPIC.

- [ ] **Step 4: Implement alias resolution in loader**

In `hdc_loader.py`, add `_resolve_option_alias` function before `_apply_template_defaults`:

```python
def _resolve_option_alias(tmpl: dict, option_id: str) -> str:
    """Resolve an HDC OPTIONID to a template option key via aliases.

    Alias patterns:
      "EXACT"    — exact match
      "*SUFFIX"  — suffix match (e.g. *GROUP matches HEARINGGROUP)
      "*"        — fallback (matches anything)
    """
    if not option_id:
        return option_id
    aliases = tmpl.get("option_aliases")
    if not aliases:
        return option_id
    # Direct match in options — no alias needed
    if option_id in tmpl.get("options", {}):
        return option_id
    # Pattern matching
    for pattern, target in aliases.items():
        if pattern == option_id:
            return target
        if pattern.startswith("*") and option_id.endswith(pattern[1:]):
            return target
    # Wildcard fallback
    return aliases.get("*", option_id)
```

Modify `_apply_template_defaults` (line 132) to resolve aliases:

```python
def _apply_template_defaults(obj: GenericObject, xmlid: str, option_id: str = None) -> None:
    """Apply template defaults from the pre-resolved JSON template."""
    tmpl = _template_lookup(xmlid)
    if tmpl is None:
        return
    resolved = _resolve_option_alias(tmpl, option_id) if option_id else None
    _apply_obj_from_tmpl(obj, tmpl, resolved)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestSensePowerCosts -v`
Expected: PASS

- [ ] **Step 6: Run oracle to measure improvement**

Run: `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | grep "^TOTAL\|^PERFECT\|^ISSUES"`
Expected: EnhancedPerception (237) + Telescopic (108) issues substantially reduced

- [ ] **Step 7: Commit**

```bash
git add kirby_cost/data/template_6e.json kirby_cost/io/hdc_loader.py tests/test_init_porting.py
git commit -m "feat: option alias resolution for sense power costs"
```

---

### Task 2: Adder-Based Skill Cost (Navigation 24 + TF 22 + AnimalHandler 14 + Gambling 12 + Weaponsmith 10 + Forgery 1 = 87 real issues, cascading to ~573 oracle-reported)

**Files:**
- Create: `kirby_cost/objects/skills/adder_based_skill.py` — extract from Survival
- Modify: `kirby_cost/objects/skills/survival.py` — re-export AdderBasedSkill
- Modify: `kirby_cost/io/hdc_loader.py:258-280` — map skills to AdderBasedSkill
- Modify: `tests/test_init_porting.py`

Navigation, AnimalHandler, Gambling, Weaponsmith, Forgery, and TransportFamiliarity all use the same adder-based getTotalCost as Survival. DRY: extract to AdderBasedSkill, map all to it. Fixing these 87 objects also eliminates ~486 phantom alignment issues in the oracle.

- [ ] **Step 1: Write failing test**

Add to `tests/test_init_porting.py`:

```python
class TestAdderBasedSkillCosts:
    """Skills that use adder-based cost (Navigation, AnimalHandler, etc.)."""

    @pytest.mark.parametrize("xmlid", [
        "NAVIGATION", "ANIMAL_HANDLER", "GAMBLING", "WEAPONSMITH",
        "TRANSPORT_FAMILIARITY", "FORGERY",
    ])
    def test_adder_skill_costs_match_oracle(self, xmlid):
        """Adder-based skill cost should match Java oracle."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with(xmlid)
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.skills, oracle.get("skills", []))
        skill_mismatches = [m for m in mismatches if m[1]["xmlid"] == xmlid]
        assert len(skill_mismatches) == 0, \
            f"{xmlid} mismatches: {[(m[2], m[0].get_total_cost(), m[1][m[2]]) for m in skill_mismatches]}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestAdderBasedSkillCosts -v`
Expected: FAIL for Navigation, etc. — wrong cost from base Skill

- [ ] **Step 3: Create AdderBasedSkill**

Create `kirby_cost/objects/skills/adder_based_skill.py`:

```python
"""
Adder-based skill cost for kirby-cost.

Skills where cost = base (familiarity/proficiency/3) + adder costs,
with special first-adder handling for familiarity/proficiency.

Used by: Survival, Navigation, AnimalHandler, Gambling, Weaponsmith,
TransportFamiliarity, Forgery.

Ported from Survival.java — same cost pattern shared by all the above
Java classes (Navigation.java, AnimalHandler.java, Gambling.java, etc.).
"""

from typing import Optional, TYPE_CHECKING
from kirby_cost.objects.skills.skill import Skill
from kirby_cost.objects.base import GenericObject

if TYPE_CHECKING:
    from kirby_cost.model.hero import Hero


class AdderBasedSkill(Skill):
    """Skill whose cost derives from adders rather than a flat base."""

    def __init__(self, xmlid: str = "SURVIVAL"):
        super().__init__(xmlid)

    def get_total_cost(self) -> float:
        """Adder-based cost calculation.

        1. Base = familiarity(1) / proficiency(profCost) / levelsOnly(0) / 3
        2. + level costs (with skill maxima)
        3. + positive adders (familiarity/proficiency get minimum cost)
        4. Clamp to min/max
        5. + negative adders
        6. - enhancer savings
        """
        active_hero = self._get_active_hero()
        self.enhancer_applied = None

        d = self.get_base_cost()
        if self.is_everyman():
            return 0.0

        # Determine if we have real (non-custom) adders
        all_custom = all(a.is_custom() for a in self.get_assigned_adders())
        if len(self.get_assigned_adders()) == 0 or all_custom:
            if self.is_familiarity():
                d = 1.0
            elif self.is_proficiency():
                d = float(self.proficiency_cost)
            elif self.is_levels_only():
                d = 0.0
            else:
                d = 3.0

        # Level cost
        if self.get_level_value() != 0.0:
            d += float(self.get_levels()) / self.get_level_value() * self.get_level_cost()

            # Skill maxima
            if (self.get_levels() > 0
                    and active_hero is not None
                    and active_hero.get_rules().get_use_skill_maxima()
                    and self.roll_based):
                maxima_limit = active_hero.get_rules().get_skill_maxima_limit()
                roll_value = self.get_roll_value()
                secondary = self.get_secondary_roll_value()
                if secondary > roll_value:
                    roll_value = secondary
                if roll_value > maxima_limit:
                    excess = min(roll_value - maxima_limit, self.get_levels())
                    d += float(excess) / self.get_level_value() * self.get_level_cost()

        # Positive adders (special handling for familiarity/proficiency)
        for adder in self.get_assigned_adders():
            if adder.get_real_cost() <= 0.0:
                continue
            if adder.is_custom():
                d += adder.get_real_cost()
                continue
            if not (self.is_familiarity() or self.is_everyman() or self.is_proficiency()):
                d += adder.get_real_cost()
                continue
            # Familiarity/proficiency: use minimum of adder cost vs minimum_cost
            if adder.get_minimum_cost() < adder.get_real_cost():
                d += adder.get_minimum_cost()
            else:
                d += adder.get_real_cost()

        # Min/max clamp
        if (d < self.get_minimum_cost()
                and self.is_min_set()
                and not self.is_everyman()
                and not self.is_levels_only()):
            d = self.get_minimum_cost()
        elif d > self.get_max_cost() and self.is_max_set():
            d = self.get_max_cost()

        # Negative adders
        for adder in self.get_assigned_adders():
            if adder.get_real_cost() >= 0.0:
                continue
            d += adder.get_real_cost()

        # Enhancer savings
        if (self.get_types() is not None
                and len(self.get_types()) > 0
                and not self.is_levels_only()
                and active_hero is not None):
            for skill in active_hero.get_skills():
                if hasattr(skill, 'applies_to_type') and hasattr(skill, 'get_cost_savings'):
                    for skill_type in self.get_types():
                        if not skill.applies_to_type(skill_type):
                            continue
                        self.enhancer_applied = skill
                        if d > float(skill.get_cost_savings()):
                            d -= float(skill.get_cost_savings())
                            return d
                        if d > 0.0:
                            d = 1.0
                        return d

        return d

    def include_familiarity(self) -> bool:
        return True


# Backward compatibility alias
Survival = AdderBasedSkill
```

- [ ] **Step 4: Update survival.py as thin re-export**

Replace `kirby_cost/objects/skills/survival.py` contents:

```python
"""Backward compatibility — Survival is now AdderBasedSkill."""
from kirby_cost.objects.skills.adder_based_skill import AdderBasedSkill, AdderBasedSkill as Survival

__all__ = ["Survival", "AdderBasedSkill"]
```

- [ ] **Step 5: Wire Skill._init() to parse FAMILIARITY/PROFICIENCY from XML**

The adder-based cost depends on `is_familiarity()` and `is_proficiency()` which require these flags to be parsed from the HDC XML. Currently Skill._init() doesn't parse them. Add to the end of `Skill._init()` in `skill.py` (after line 613):

```python
    # Parse skill-specific XML attributes
    if element is None:
        return

    char_str = element.get("CHARACTERISTIC", "")
    if char_str and char_str.strip():
        from kirby_cost.util.constants import get_characteristic_integer
        self.characteristic = get_characteristic_integer(char_str)

    fam_str = element.get("FAMILIARITY", "")
    if fam_str and fam_str.strip():
        self.set_familiarity(fam_str.upper().startswith("Y"))

    prof_str = element.get("PROFICIENCY", "")
    if prof_str and prof_str.strip():
        self.set_proficiency(prof_str.upper().startswith("Y"))

    levels_only_str = element.get("LEVELSONLY", "")
    if levels_only_str and levels_only_str.strip():
        self.set_levels_only(levels_only_str.upper().startswith("Y"))

    everyman_str = element.get("EVERYMAN", "")
    if everyman_str and everyman_str.strip():
        self.set_everyman(everyman_str.upper().startswith("Y"))
```

**Note:** We set `self.characteristic` directly (not via `set_characteristic()`) because `characteristic_choices` is not populated from HDC XML. The characteristic integer is still useful for display and roll calculations. Cost fields (base_cost, level_cost) come from the HDC's BASECOST attribute and template defaults, not from characteristic choices.

**Do NOT modify `restore_from_save()`** — it may have callers outside the loader that depend on the full `set_characteristic()` path with populated `characteristic_choices`. The double-parse is harmless (idempotent).

**Pre-existing bug note:** `Skill.__init__` line 60 sets `self.include_familiarity: bool = False` which shadows the method `def include_familiarity(self)` at line 168. This is a pre-existing issue — do not fix it in this task, but be aware that calling `obj.include_familiarity()` as a method would raise `TypeError`. The `AdderBasedSkill` method override has the same collision. If this causes issues during testing, rename the attribute to `_include_familiarity` in a separate commit.

- [ ] **Step 6: Update skill map in loader**

In `hdc_loader.py`, `_get_skill_map()`, replace the imports and mapping:

```python
from kirby_cost.objects.skills.adder_based_skill import AdderBasedSkill
_SKILL_MAP.update({
    "KNOWLEDGE_SKILL": KnowledgeSkill,
    "LANGUAGES": Language,
    "SURVIVAL": AdderBasedSkill,
    "NAVIGATION": AdderBasedSkill,
    "ANIMAL_HANDLER": AdderBasedSkill,
    "GAMBLING": AdderBasedSkill,
    "WEAPONSMITH": AdderBasedSkill,
    "FORGERY": AdderBasedSkill,
    "TRANSPORT_FAMILIARITY": AdderBasedSkill,
})
```

Remove the old `Survival` import line.

- [ ] **Step 7: Run test to verify it passes**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestAdderBasedSkillCosts -v`
Expected: PASS for all 6 parametrized XMLIDs

- [ ] **Step 8: Run full test suite for regressions**

Run: `.venv/bin/python3 -m pytest tests/ -v`
Expected: All existing tests pass

- [ ] **Step 9: Run oracle to measure improvement**

Run: `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | grep "^TOTAL\|^PERFECT\|^ISSUES"`
Expected: Large reduction — fixing 87 real issues eliminates ~573 reported oracle issues (including alignment phantoms)

- [ ] **Step 10: Commit**

```bash
git add kirby_cost/objects/skills/adder_based_skill.py kirby_cost/objects/skills/survival.py kirby_cost/objects/skills/skill.py kirby_cost/io/hdc_loader.py tests/test_init_porting.py
git commit -m "feat: adder-based skill cost for Navigation, AnimalHandler, Gambling, Weaponsmith, TF, Forgery"
```

---

### Task 3: ForceWall Dimension Levels (120 issues)

**Files:**
- Modify: `kirby_cost/objects/powers/force_wall.py` — add _init() to read dimension XML attrs
- Modify: `tests/test_init_porting.py`

ForceWall._init() doesn't read LENGTHLEVELS, HEIGHTLEVELS, WIDTHLEVELS, BODYLEVELS from HDC XML. The existing get_total_cost() already uses these fields but they default to 0.

- [ ] **Step 1: Write failing test**

Add to `tests/test_init_porting.py`:

```python
class TestForceWallCosts:
    """ForceWall dimension level costs."""

    def test_force_wall_costs_match_oracle(self):
        """ForceWall with dimension levels should include their cost."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("FORCEWALL")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        fw_mismatches = [m for m in mismatches if m[1]["xmlid"] == "FORCEWALL"]
        assert len(fw_mismatches) == 0, \
            f"ForceWall mismatches: {[(m[2], m[0].get_total_cost(), m[1][m[2]]) for m in fw_mismatches]}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestForceWallCosts -v`
Expected: FAIL — dimension levels all zero

- [ ] **Step 3: Add _init() to ForceWall**

In `force_wall.py`, add after `__init__`:

```python
def _init(self, element) -> None:
    """Initialize from XML, including dimension levels."""
    super()._init(element)
    if element is None:
        return
    from kirby_cost.io.xml_utility import XMLUtility

    for attr, field, conv in [
        ("LENGTHLEVELS", "length_levels", int),
        ("HEIGHTLEVELS", "height_levels", int),
        ("BODYLEVELS", "body_levels", int),
        ("WIDTHLEVELS", "width_levels", float),
    ]:
        val = XMLUtility.get_value(element, attr)
        if val:
            try:
                setattr(self, field, conv(val))
            except (ValueError, TypeError):
                pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestForceWallCosts -v`
Expected: PASS

- [ ] **Step 5: Run oracle, commit**

Run: `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | grep "^TOTAL\|^PERFECT\|^ISSUES"`

```bash
git add kirby_cost/objects/powers/force_wall.py tests/test_init_porting.py
git commit -m "feat: load ForceWall dimension levels from HDC XML"
```

---

### Task 4: EnduranceReserve Recovery Component (84 issues)

**Files:**
- Modify: `kirby_cost/io/hdc_loader.py` — build recovery sub-object for EnduranceReserve
- Modify: `tests/test_init_porting.py`

EnduranceReserve needs its recovery component loaded from HDC XML. Recovery is a child `<POWER XMLID="ENDURANCERESERVEREC">` element within the EnduranceReserve element.

- [ ] **Step 1: Write failing test**

Add to `tests/test_init_porting.py`:

```python
class TestEnduranceReserveCosts:
    """EnduranceReserve with recovery component."""

    def test_endurance_reserve_costs_match_oracle(self):
        """END Reserve should include recovery component cost."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with("ENDURANCERESERVE")
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        mismatches = _compare_section(hero.powers, oracle.get("powers", []))
        er_mismatches = [m for m in mismatches if m[1]["xmlid"] == "ENDURANCERESERVE"]
        assert len(er_mismatches) == 0, \
            f"EndRes mismatches: {[(m[2], m[0].get_total_cost(), m[1][m[2]]) for m in er_mismatches]}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestEnduranceReserveCosts -v`

- [ ] **Step 3: Load recovery component in loader**

In `hdc_loader.py`, in `_build_object()`, after the CompoundPower sub-power handling block (after line 546), add:

```python
# Handle EnduranceReserve recovery component
from kirby_cost.objects.powers.endurance_reserve import EnduranceReserve
if isinstance(obj, EnduranceReserve):
    for sub_elem in elem:
        if sub_elem.tag in ("NOTES", "MODIFIER", "ADDER"):
            continue
        if sub_elem.get("XMLID", sub_elem.tag) == "ENDURANCERESERVEREC":
            rec = self._build_object(sub_elem, "power")
            if rec is not None:
                obj.rec = rec
            break
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestEnduranceReserveCosts -v`
Expected: PASS

- [ ] **Step 5: Run oracle, commit**

```bash
git add kirby_cost/io/hdc_loader.py tests/test_init_porting.py
git commit -m "feat: load EnduranceReserve recovery component from HDC XML"
```

---

### Task 5: Map Perk and Power Classes in Loader (Follower 50 + Reputation 33 + Money 18 + DamageReduction 15 + KBResistance 15 + Vehicle 24 = 155 issues)

**Files:**
- Modify: `kirby_cost/io/hdc_loader.py:226-255` — add classes to power map
- Modify: `kirby_cost/objects/perks/follower.py` — add _init() for BASEPOINTS
- Modify: `tests/test_init_porting.py`

These classes exist with correct getTotalCost() but aren't registered in `_get_power_map()`. All fall through to `_FallbackObject` which uses GenericObject's base cost logic.

- [ ] **Step 1: Write failing test**

Add to `tests/test_init_porting.py`:

```python
class TestPerkAndPowerMapping:
    """Perk/power class mapping for correct cost calculation."""

    @pytest.mark.parametrize("xmlid,section", [
        ("FOLLOWER", "perks"),
        ("REPUTATION", "perks"),
        ("MONEY", "perks"),
        ("DAMAGEREDUCTION", "powers"),
    ])
    def test_class_costs_match_oracle(self, xmlid, section):
        """Mapped class should produce correct costs."""
        from kirby_cost.io.hdc_loader import HDCLoader
        path = _find_hdc_with(xmlid)
        hero = HDCLoader().load_file(path)
        oracle = _oracle(path)
        hero_list = getattr(hero, section)
        mismatches = _compare_section(hero_list, oracle.get(section, []))
        target_mismatches = [m for m in mismatches if m[1]["xmlid"] == xmlid]
        assert len(target_mismatches) == 0, \
            f"{xmlid} mismatches: {[(m[2], m[0].get_total_cost(), m[1][m[2]]) for m in target_mismatches]}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestPerkAndPowerMapping -v`

- [ ] **Step 3: Add classes to power map**

In `hdc_loader.py`, `_get_power_map()`, add after existing imports:

```python
from kirby_cost.objects.perks.follower import Follower
from kirby_cost.objects.perks.reputation import Reputation
from kirby_cost.objects.perks.money import Money
from kirby_cost.objects.powers.damage_reduction import DamageReduction
_POWER_MAP.update({
    # ... existing entries ...
    "FOLLOWER": Follower,
    "REPUTATION": Reputation,
    "MONEY": Money,
    "DAMAGEREDUCTION": DamageReduction,
})
```

- [ ] **Step 4: Add _init() to Follower for BASEPOINTS**

In `follower.py`, add `_init()` override:

```python
def _init(self, element) -> None:
    """Initialize from XML, including follower-specific fields."""
    super()._init(element)
    if element is None:
        return
    from kirby_cost.io.xml_utility import XMLUtility

    for attr, field, conv in [
        ("BASEPOINTS", "_base_points", lambda v: int(float(v))),
        ("DISADPOINTS", "_disad_points", lambda v: int(float(v))),
        ("MULTIPLES", "multiples", int),
    ]:
        val = XMLUtility.get_value(element, attr)
        if val:
            try:
                setattr(self, field, conv(val))
            except (ValueError, TypeError):
                pass
```

- [ ] **Step 5: Handle Perk constructor in _create_instance**

Perk subclasses take `(element=None)` as first arg. The existing `_create_instance` tries `cls()` which passes `element=None` by default — this should work. Verify by checking that `Follower()` doesn't crash.

If it does crash, add to the power section of `_create_instance`:

```python
try:
    return cls()
except TypeError:
    try:
        return cls(None)
    except Exception:
        pass
```

- [ ] **Step 6: Run tests, oracle, commit**

Run: `.venv/bin/python3 -m pytest tests/test_init_porting.py::TestPerkAndPowerMapping -v`
Run: `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | grep "^TOTAL\|^PERFECT\|^ISSUES"`

```bash
git add kirby_cost/io/hdc_loader.py kirby_cost/objects/perks/follower.py tests/test_init_porting.py
git commit -m "feat: map Follower, Reputation, Money, DamageReduction in loader"
```

---

### Task 6: Full Oracle Verification & Long-Tail Fixes

**Files:**
- Various — depends on remaining issues after Tasks 1-5

- [ ] **Step 1: Run full oracle comparison**

Run: `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | tail -80`

Document remaining issue counts by class.

- [ ] **Step 2: Analyze remaining issues**

For each remaining class with >5 issues, debug one character:

```bash
.venv/bin/python3 -c "
from kirby_cost.io.hdc_loader import HDCLoader
loader = HDCLoader()
hero = loader.load_file('<path>')
for p in hero.powers:
    if p.get_xmlid() == '<XMLID>':
        print(f'class={type(p).__name__} base={p.base_cost} lc={p.level_cost} total={p.get_total_cost()}')
        break
"
```

Likely remaining issues:
- **CompoundPower (183)**: Many sub-powers use now-fixed classes — expect significant reduction as cascade effect
- **PD/ED (196)**: addModifiersToBase needs hero characteristic values — already partially implemented in Characteristic class, may need debugging
- **Language (93)**: Option costs — template has BASIC/FLUENT/ACCENT/IDIOMATIC options, check if OPTIONID mapping works
- **KBResistance (15)**, **Vehicle (24)**: May need class mapping
- Small counts (<10): Likely downstream of above fixes

- [ ] **Step 3: Apply targeted fixes**

For each remaining class, apply the minimal fix:
- If it's a mapping issue → add to `_get_power_map()`
- If it's an option alias issue → add `option_aliases` to template
- If it's a missing XML attribute → add `_init()` override

- [ ] **Step 4: Run final oracle, commit**

Run: `.venv/bin/python3 scripts/oracle_compare_v2.py --all 2>&1 | grep "^TOTAL\|^PERFECT\|^ISSUES"`
Target: >98% match

```bash
git add -A
git commit -m "fix: long-tail oracle fixes for remaining cost mismatches"
```

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/python3 -m pytest tests/ -v`
Expected: All tests pass (278+ with new tests)

---

## Success Criteria

| Metric | Baseline | Target |
|--------|----------|--------|
| Oracle match | 95.8% (27,380/28,593) | >98% |
| Perfect characters | 376/656 | >500/656 |
| Issue count | 2,196 | <500 |
| Test suite | 278 passing | 278+ passing (no regressions) |
