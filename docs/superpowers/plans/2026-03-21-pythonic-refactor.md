# Pythonic Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Java-to-Python port into idiomatic, DRY Python with properties, mixins, consolidated skill classes, and a clean loader — while keeping the 99.98% oracle match rate.

**Architecture:** Bottom-up refactor: oracle fixture first (safety net), then properties (surface), then DRY skill consolidation, then base class mixins, then template dataclasses, then loader cleanup. Each phase is independently testable.

**Tech Stack:** Python 3.12, pytest, lxml, dataclasses

**Spec:** `docs/superpowers/specs/2026-03-21-pythonic-refactor-design.md`

---

## File Structure

### New files to create
- `tests/fixtures/oracle/` — per-character JSON oracle snapshots (~200 files)
- `scripts/generate_oracle_fixtures.py` — one-time fixture generation script
- `tests/test_oracle_fixtures.py` — fast oracle comparison using fixtures
- `kirby_cost/engine/cost.py` — CostMixin extracted from base.py
- `kirby_cost/engine/modifiers.py` — ModifierMixin extracted from base.py
- `kirby_cost/engine/serialize.py` — SerializationMixin extracted from base.py
- `kirby_cost/engine/__init__.py`
- `kirby_cost/objects/skills/n_counter_skill.py` — consolidated Group A skills
- `kirby_cost/objects/skills/accumulator_skill.py` — consolidated Group B skills
- `kirby_cost/template/__init__.py`
- `kirby_cost/template/dataclasses.py` — TemplateData, AdderTemplate, etc.

### Files to heavily modify
- `kirby_cost/objects/base.py` — getter/setter removal, mixin extraction
- `kirby_cost/io/hdc_loader.py` — standalone functions → class methods + registry
- `kirby_cost/objects/skills/skill.py` — flag-based overrides
- All files in `kirby_cost/objects/` — caller migration (get_x() → x)

### Files to delete (Phase 2)
- `kirby_cost/objects/skills/navigation.py` — merged into n_counter_skill.py
- `kirby_cost/objects/skills/animal_handler.py` — merged
- `kirby_cost/objects/skills/gambling.py` — merged
- `kirby_cost/objects/skills/weaponsmith.py` — merged
- `kirby_cost/objects/skills/forgery.py` — merged
- `kirby_cost/objects/skills/electronics.py` — merged into accumulator_skill.py
- `kirby_cost/objects/skills/computer_programming.py` — merged
- `kirby_cost/objects/skills/systems_operation.py` — merged

---

## Task 1: Generate Oracle Fixtures

**Files:**
- Create: `scripts/generate_oracle_fixtures.py`
- Create: `tests/fixtures/oracle/` (directory with ~200 JSON files)
- Create: `tests/test_oracle_fixtures.py`

- [ ] **Step 1: Write the fixture generation script**

```python
# scripts/generate_oracle_fixtures.py
"""Generate per-character oracle fixture files from the Java HD6 CLI.

Run once. Output is immutable — the Java oracle never changes.

Usage:
    .venv/bin/python scripts/generate_oracle_fixtures.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

RESOURCE_DIR = Path(__file__).parent.parent.parent / "champions-campaign-manager" / "resources"
HD6CLI = str(Path(__file__).parent.parent.parent / "kirby-hd-oracle" / "hd6cli.sh")
OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "oracle"


def generate():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    errors = 0

    for root, dirs, files in os.walk(RESOURCE_DIR):
        if "__MACOSX" in root:
            continue
        for f in files:
            if not f.endswith(".hdc") or "CV3" in f:
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, RESOURCE_DIR)
            out_name = rel.replace(os.sep, "__").replace(".hdc", ".json")
            out_path = OUTPUT_DIR / out_name

            try:
                result = subprocess.run(
                    [HD6CLI, path], capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0 or not result.stdout.strip():
                    errors += 1
                    continue
                idx = result.stdout.find("{")
                if idx < 0:
                    errors += 1
                    continue
                oracle_data = json.loads(result.stdout[idx:])
                fixture = {
                    "hdc_path": path,
                    "relative_path": rel,
                    **oracle_data,
                }
                out_path.write_text(json.dumps(fixture, indent=2))
                total += 1
                print(f"  [{total}] {out_name}")
            except Exception as e:
                errors += 1
                print(f"  ERROR {f}: {e}", file=sys.stderr)

    print(f"\nGenerated {total} fixtures ({errors} errors)")


if __name__ == "__main__":
    generate()
```

- [ ] **Step 2: Run the generation script**

Run: `.venv/bin/python scripts/generate_oracle_fixtures.py`
Expected: ~200 JSON files created in `tests/fixtures/oracle/`

- [ ] **Step 3: Write the fixture-based oracle test**

```python
# tests/test_oracle_fixtures.py
"""Oracle comparison tests using pre-generated fixtures.

These fixtures are immutable — generated once from the Java HD6 CLI.
Tests load each fixture, run the Python HDCLoader, and compare costs.
"""
import json
import pytest
from pathlib import Path

from kirby_cost.io.hdc_loader import HDCLoader

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "oracle"
FW_CLASSES = {"Multipower", "VariablePowerPool", "ElementalControl", "List"}
FW_XMLIDS = {"MULTIPOWER", "VPP", "ELEMENTALCONTROL"}


def _fixture_files():
    """Yield all oracle fixture JSON files."""
    if not FIXTURE_DIR.exists():
        pytest.skip("Oracle fixtures not generated")
    return sorted(FIXTURE_DIR.glob("*.json"))


def _filter_oracle(oracle_list):
    return [j for j in oracle_list if j.get("class") not in FW_CLASSES]


def _filter_python(py_list):
    return [
        p for p in py_list
        if p.get_xmlid() not in FW_XMLIDS
        and not (
            p.get_xmlid() == "GENERIC_OBJECT"
            and p.get_levels() == 0
            and p.get_level_cost() == 0.0
        )
    ]


@pytest.mark.parametrize("fixture_path", _fixture_files(), ids=lambda p: p.stem)
def test_oracle_match(fixture_path):
    """Every object's cost must match the frozen Java oracle."""
    fixture = json.loads(fixture_path.read_text())
    hdc_path = fixture["hdc_path"]

    if not Path(hdc_path).exists():
        pytest.skip(f"HDC file missing: {hdc_path}")

    hero = HDCLoader().load_file(hdc_path)

    mismatches = []
    for section, hero_list in [
        ("powers", hero.powers),
        ("skills", hero.skills),
        ("perks", hero.perks),
        ("talents", hero.talents),
    ]:
        oracle_list = _filter_oracle(fixture.get(section, []))
        py_list = _filter_python(hero_list)

        for i, oracle_obj in enumerate(oracle_list):
            if i >= len(py_list):
                break
            py_obj = py_list[i]
            for field in ("total_cost", "active_cost", "real_cost"):
                py_val = (
                    py_obj.get_total_cost() if field == "total_cost"
                    else py_obj.get_active_cost() if field == "active_cost"
                    else py_obj.get_real_cost_pre_list()
                )
                if abs(py_val - oracle_obj[field]) > 0.01:
                    mismatches.append(
                        f"{section}[{i}] {py_obj.get_xmlid()} "
                        f"{field}: py={py_val} oracle={oracle_obj[field]}"
                    )
                    break

    assert len(mismatches) == 0, (
        f"{fixture_path.stem}: {len(mismatches)} mismatches:\n"
        + "\n".join(mismatches[:10])
    )
```

- [ ] **Step 4: Run fixture tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_oracle_fixtures.py -v --tb=short -q`
Expected: ~200 tests PASS (matching the live oracle results)

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_oracle_fixtures.py tests/test_oracle_fixtures.py tests/fixtures/oracle/
git commit -m "Add frozen oracle fixtures for fast regression testing"
```

---

## Task 2: Property Conversion — GenericObject Plain Attributes

Convert trivial getters/setters on `GenericObject` to direct attribute access. These have no logic — just `return self.x` / `self.x = val`.

**Files:**
- Modify: `kirby_cost/objects/base.py`
- Modify: All files in `kirby_cost/` (caller migration)

- [ ] **Step 1: Add deprecation shims to base.py**

Add these at the end of GenericObject, BEFORE deleting any methods. This keeps everything working during migration:

```python
# ── Deprecation shims (remove after caller migration) ──────────
# These forward old get_/set_/is_ calls to the new attribute names.
# Run: grep -rn "\.get_xmlid\|\.get_levels\|\.set_levels" kirby_cost/
# to find remaining callers. Delete shims when grep returns empty.

def get_id(self): return self._id
def set_id(self, val): self._id = val
def get_xmlid(self): return self.xmlid
def set_xmlid(self, val): self.xmlid = val
def get_levels(self): return self.levels
def set_levels(self, val): self.levels = val
def get_level_cost(self): return self.level_cost
def get_level_value(self): return self.level_value
def get_level_power(self): return self.level_power
def get_level_multiplier(self): return self.level_multiplier
def get_orig_base_cost(self): return self.orig_base_cost
def get_minimum_level(self): return self.minimum_level
def set_minimum_level(self, val): self.minimum_level = val
def set_max_cost(self, val): self.max_cost = val
def get_selected_option(self): return self.selected_option
def set_selected_option(self, val): self.selected_option = val
def get_parent_list(self): return self.parent
def set_parent_list(self, val): self.parent = val
def get_main_power(self): return self.main_power
def get_target(self): return self.target
def get_duration(self): return self.duration
def get_position(self): return self.position
def set_position(self, val): self.position = val
def set_name(self, val): self.name = val
def set_notes(self, val): self.notes = val
def get_parent_id(self): return self.parent_id
def set_parent_id(self, val): self.parent_id = val
def set_is_equipment(self, val): self.is_equipment = val
def set_ultra(self, val): self.ultra = val
def get_use_end_reserve(self): return self.use_end_reserve
def set_use_end_reserve(self, val): self.use_end_reserve = val
def set_graphic(self, val): self.graphic = val
def set_color(self, val): self.color = val
def set_sfx(self, val): self.sfx = val
def set_include_notes_in_printout(self, val): self.include_notes_in_printout = val
def get_minimum_cost(self): return self.minimum_cost
def is_min_set(self): return self.min_set
def get_max_cost(self): return self.max_cost
def is_max_set(self): return self.max_set
def get_multiplier(self): return self.multiplier
def get_quantity(self): return self.quantity
def set_power(self, val): self._is_power = val
def set_alias(self, val): self.alias = val
```

- [ ] **Step 2: Run tests to verify shims work**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: 292 PASS (shims are transparent)

- [ ] **Step 3: Delete the original trivial getter/setter methods from base.py**

Remove lines containing these method definitions (the originals, not the shims). The shims now handle all calls. Delete the methods at these approximate locations:
- `get_id` / `set_id` (~180-186)
- `get_xmlid` / `set_xmlid` (~188-197) — NOTE: `get_xmlid` has translation logic, keep as property
- `get_levels` / `set_levels` (~209-215)
- `get_level_cost` / `get_level_value` / `get_level_power` / `get_level_multiplier` (~217-231)
- All other trivial getters/setters identified in the audit

For `get_xmlid` (has ID translation logic) and `get_name` / `get_notes` / `get_input` (have fallback logic), convert to `@property`:

```python
@property
def effective_xmlid(self) -> str:
    """XMLID with translation for legacy IDs."""
    translated = self._ID_TRANSLATIONS.get(self.xmlid)
    return translated if translated else self.xmlid
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: 292 PASS

- [ ] **Step 5: Migrate callers — objects/ package**

Find-and-replace across `kirby_cost/objects/`:
```
.get_levels()       →  .levels
.set_levels(        →  .levels =
.get_level_cost()   →  .level_cost
.get_level_value()  →  .level_value
.get_position()     →  .position
.set_position(      →  .position =
.get_parent_list()  →  .parent
.set_parent_list(   →  .parent =
.is_min_set()       →  .min_set
.is_max_set()       →  .max_set
.get_minimum_cost() →  .minimum_cost
.get_max_cost()     →  .max_cost
.get_multiplier()   →  .multiplier
.get_quantity()     →  .quantity
.get_duration()     →  .duration
.get_target()       →  .target
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: 292 PASS

- [ ] **Step 7: Migrate callers — io/, model/, database/, services/, api/, behaviors/**

Same find-and-replace across the remaining packages.

- [ ] **Step 8: Run full test suite + oracle fixtures**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS (292 unit + ~200 oracle fixtures)

- [ ] **Step 9: Verify no remaining old-style calls**

Run: `grep -rn "\.get_levels()\|\.set_levels(\|\.get_level_cost()\|\.get_position()\|\.get_duration()\|\.get_target()\|\.is_min_set()\|\.is_max_set()\|\.get_minimum_cost()\|\.get_max_cost()" kirby_cost/`
Expected: Zero hits (only test files and shims)

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "refactor: convert trivial getters/setters to direct attribute access"
```

---

## Task 3: Property Conversion — Computed Properties

Convert getter methods that have logic (fallbacks, calculations) to `@property`.

**Files:**
- Modify: `kirby_cost/objects/base.py`
- Modify: All caller files

- [ ] **Step 1: Convert computed getters to properties on GenericObject**

```python
@property
def display(self) -> str:
    """Display name with fallback to name."""
    return self._display if self._display else (self.name or "")

@property
def name(self) -> str:
    return self._name or ""

@property
def notes(self) -> str:
    return getattr(self, '_notes', '') or ""

@property
def input(self) -> str:
    return getattr(self, '_input', '') or ""

@property
def alias(self) -> str:
    """Alias with fallback chain: alias → display → name."""
    if self._alias:
        return self._alias
    if self._display:
        return self._display
    return self._name or ""

@property
def graphic(self) -> str:
    return getattr(self, '_graphic', '') or ""

@property
def color(self) -> str:
    return getattr(self, '_color', '') or ""

@property
def sfx(self) -> str:
    return getattr(self, '_sfx', '') or ""

@property
def end_usage(self) -> int:
    return getattr(self, '_end_usage', 0)

@property
def is_power(self) -> bool:
    """Check if this object is a power (not a base characteristic)."""
    if self.is_equipment:
        return True
    if self.main_power is not None:
        return self.main_power.is_power
    return getattr(self, '_is_power', False)

@property
def does_damage(self) -> bool:
    return self._does_damage

@property
def uses_end(self) -> bool:
    return self._uses_end
```

NOTE: Rename internal storage attributes to `_name`, `_alias`, `_display`, etc. to avoid property/attribute name collision. Update `__init__` and `_init` accordingly.

- [ ] **Step 2: Migrate callers for computed properties**

```
.get_display()  →  .display
.get_name()     →  .name
.get_notes()    →  .notes
.get_input()    →  .input
.get_alias()    →  .alias
.get_graphic()  →  .graphic
.get_color()    →  .color
.get_sfx()      →  .sfx
.get_end_usage() → .end_usage
.is_power()     →  .is_power (already property-style call, just remove parens)
.does_damage()  →  .does_damage
.usesEND()      →  .uses_end
```

- [ ] **Step 3: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: convert computed getters to @property"
```

---

## Task 4: Property Conversion — Cost Chain

Convert the cost calculation methods to read-only properties. These are the most important — the player-facing API surface.

**Files:**
- Modify: `kirby_cost/objects/base.py`
- Modify: All subclass overrides of get_total_cost, get_active_cost, get_real_cost
- Modify: All caller files

- [ ] **Step 1: Convert cost methods to properties on GenericObject**

```python
@property
def total_cost(self) -> float:
    """Base + levels + adders, clamped to min/max."""
    # ... existing get_total_cost() logic unchanged ...

@property
def active_cost(self) -> float:
    """total_cost * (1 + advantage_sum)."""
    return self._compute_active_cost()

def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
    """Parameterized active cost (used internally for exclude logic)."""
    # ... existing get_active_cost() logic unchanged ...

@property
def real_cost(self) -> float:
    """Real cost with framework discount."""
    # ... existing get_real_cost() logic unchanged ...

@property
def real_cost_pre_list(self) -> float:
    """Real cost before framework discount."""
    # ... existing get_real_cost_pre_list() logic unchanged ...
```

- [ ] **Step 2: Convert ALL subclass overrides**

Every file that overrides `get_total_cost()` must change to `@property def total_cost`. Key files:

**Skills:** skill.py, adder_based_skill.py, language.py, transport_familiarity.py, weapon_familiarity.py, defense_maneuver.py, combat_levels.py, skill_levels.py, mental_combat_levels.py, penalty_skill_levels.py, autofire_skills.py, rapid_attack_hth.py, rapid_attack_ranged.py, two_weapon_fighting_hth.py, two_weapon_fighting_ranged.py, navigation.py, animal_handler.py, gambling.py, weaponsmith.py, forgery.py, electronics.py, computer_programming.py, systems_operation.py

**Powers:** sense.py, force_field.py, force_wall.py, duplication.py, compound_power.py, custom_power.py, endurance_reserve.py, naked_modifier.py

**Perks:** follower.py, reputation.py, vehicle.py, money.py

**Other:** characteristic.py, speed.py, comliness.py, disadvantage.py, maneuver.py, list.py, adder.py, modifier.py

For each: `def get_total_cost(self)` → `@property` + `def total_cost(self)`. Internal `super().get_total_cost()` calls → `super().total_cost`. Internal `self.get_total_cost()` calls → `self.total_cost`.

Similarly for active_cost, real_cost, real_cost_pre_list overrides.

- [ ] **Step 3: Migrate all callers**

```
.get_total_cost()          →  .total_cost
.get_active_cost()         →  .active_cost
.get_active_cost(exclude=  →  ._compute_active_cost(exclude_xmlid=
.get_real_cost()           →  .real_cost
.get_real_cost_pre_list()  →  .real_cost_pre_list
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 5: Run oracle fixtures**

Run: `.venv/bin/python -m pytest tests/test_oracle_fixtures.py -v --tb=short -q`
Expected: All PASS (~200 tests)

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: convert cost chain to @property (total_cost, active_cost, real_cost)"
```

---

## Task 5: Property Conversion — Adder and Modifier Properties

Convert getter/setter methods on `Adder` and `Modifier` classes.

**Files:**
- Modify: `kirby_cost/objects/adder.py`
- Modify: `kirby_cost/objects/modifier.py`
- Modify: All caller files

- [ ] **Step 1: Convert Adder methods**

On `Adder`: `is_selected()` → `@property is_selected`, `is_required()` → `@property is_required`, `is_group()` → `@property is_group`. These are trivial returns.

Convert `get_total_cost()` / `get_real_cost()` to `@property`.

- [ ] **Step 2: Convert Modifier methods**

On `Modifier`: convert trivial getters/setters to properties. Convert `get_total_value()` to `@property total_value`.

- [ ] **Step 3: Migrate callers**

```
adder.is_selected()   →  adder.is_selected
adder.is_required()   →  adder.is_required
adder.get_real_cost() →  adder.real_cost
adder.get_total_cost() → adder.total_cost
modifier.get_total_value() → modifier.total_value
```

- [ ] **Step 4: Run full test suite + oracle**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: convert Adder and Modifier to @property"
```

---

## Task 6: Property Conversion — Skill Overrides

Convert Skill-specific getter overrides (`get_base_cost`, `get_levels`, `get_minimum_cost`) to `@property`.

**Files:**
- Modify: `kirby_cost/objects/skills/skill.py`
- Modify: Skill subclass files

- [ ] **Step 1: Convert Skill.get_base_cost() to @property**

```python
class Skill:
    @property
    def base_cost(self) -> float:
        if self.is_familiarity and self.is_everyman:
            return 0.0
        if self.is_familiarity and float(self.familiarity_cost) < super().base_cost:
            return float(self.familiarity_cost)
        # ... rest of logic
```

NOTE: `is_familiarity` is now a property (no parens) after Task 3.

- [ ] **Step 2: Convert Skill.get_levels() to @property**

- [ ] **Step 3: Migrate callers in skill files**

- [ ] **Step 4: Run tests + oracle**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: convert Skill getter overrides to @property"
```

---

## Task 7: Remove Deprecation Shims

All callers are migrated. Remove the shim methods.

**Files:**
- Modify: `kirby_cost/objects/base.py`

- [ ] **Step 1: Verify zero remaining old-style calls**

Run: `grep -rn "\.get_xmlid()\|\.get_base_cost()\|\.set_base_cost(\|\.get_levels()\|\.get_total_cost()\|\.get_active_cost()\|\.get_real_cost()\|\.get_assigned_modifiers()\|\.get_assigned_adders()\|\.is_familiarity()\|\.is_selected()\|\.is_required()\|\.get_name()\|\.get_display()" kirby_cost/ | grep -v "def get_\|def is_\|def set_\|#.*DEPRECATED\|shim\|__pycache__"`
Expected: Zero hits from non-definition lines

- [ ] **Step 2: Delete all shim methods from base.py**

Remove the entire `# ── Deprecation shims` block.

- [ ] **Step 3: Run tests + oracle**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove deprecation shims — property migration complete"
```

---

## Task 8: DRY Skills — NCounterSkill (Group A)

Consolidate Navigation, AnimalHandler, Gambling, Weaponsmith, Forgery into a single class.

**Files:**
- Create: `kirby_cost/objects/skills/n_counter_skill.py`
- Delete: `kirby_cost/objects/skills/navigation.py`
- Delete: `kirby_cost/objects/skills/animal_handler.py`
- Delete: `kirby_cost/objects/skills/gambling.py`
- Delete: `kirby_cost/objects/skills/weaponsmith.py`
- Delete: `kirby_cost/objects/skills/forgery.py`
- Modify: `kirby_cost/io/hdc_loader.py` (update skill map)
- Create: `tests/test_n_counter_skill.py`

- [ ] **Step 1: Write tests for NCounterSkill**

Write parametrized tests that load each of the 5 skill XMLIDs from HDC files and verify costs match the oracle fixtures. This ensures the consolidated class produces identical results.

```python
@pytest.mark.parametrize("xmlid", [
    "NAVIGATION", "ANIMAL_HANDLER", "GAMBLING", "WEAPONSMITH", "FORGERY",
])
def test_n_counter_skill_matches_oracle(xmlid):
    """NCounterSkill must produce identical costs to the original classes."""
    # Load a character with this skill, compare against oracle fixture
    ...
```

- [ ] **Step 2: Run tests to verify they pass with current code**

Run: `.venv/bin/python -m pytest tests/test_n_counter_skill.py -v`
Expected: All PASS (proves the test itself is correct)

- [ ] **Step 3: Create NCounterSkill**

Write `n_counter_skill.py` with the canonical implementation. Use Navigation's logic as the base (it has the most complete negative adder handling). Preserve ALL behavioral differences found in the diff matrix:
- Consistent `roll_based` check in skill maxima (fix AnimalHandler's missing check)
- Consistent `has_non_custom_adder` logic
- Navigation's negative adder n-counter pattern

```python
class NCounterSkill(AdderBasedSkill):
    """Skill where first adder pays full cost, subsequent pay minimum.

    Used by: NAVIGATION, ANIMAL_HANDLER, GAMBLING, WEAPONSMITH, FORGERY.
    """

    @property
    def total_cost(self) -> float:
        # Single canonical implementation
        ...

    def include_familiarity(self) -> bool:
        return True
```

- [ ] **Step 4: Update loader skill map**

```python
_SKILL_MAP.update({
    "NAVIGATION": NCounterSkill,
    "ANIMAL_HANDLER": NCounterSkill,
    "GAMBLING": NCounterSkill,
    "WEAPONSMITH": NCounterSkill,
    "FORGERY": NCounterSkill,
})
```

- [ ] **Step 5: Run tests + oracle**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 6: Delete old files**

Delete navigation.py, animal_handler.py, gambling.py, weaponsmith.py, forgery.py. Update any imports.

- [ ] **Step 7: Run tests again**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: consolidate 5 skill classes into NCounterSkill"
```

---

## Task 9: DRY Skills — AccumulatorSkill (Group B)

Consolidate Electronics, ComputerProgramming, SystemsOperation into a single class.

**Files:**
- Create: `kirby_cost/objects/skills/accumulator_skill.py`
- Delete: `kirby_cost/objects/skills/electronics.py`
- Delete: `kirby_cost/objects/skills/computer_programming.py`
- Delete: `kirby_cost/objects/skills/systems_operation.py`
- Modify: `kirby_cost/io/hdc_loader.py`
- Create: `tests/test_accumulator_skill.py`

- [ ] **Step 1: Write tests**

Same pattern as Task 8 but for the 3 Group B XMLIDs.

- [ ] **Step 2: Create AccumulatorSkill**

Include the shared `get_minimum_cost` override (returns 2.0 when adders present). Include SystemsOperation's custom adder handling. Fix ComputerProgramming's missing `roll_based` check.

- [ ] **Step 3: Update loader, run tests, delete old files**

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: consolidate 3 skill classes into AccumulatorSkill"
```

---

## Task 10: DRY Skills — Flag-Based Overrides

Eliminate ~10 skill subclasses that only set `self.roll_based = False`.

**Files:**
- Modify: `kirby_cost/objects/skills/skill.py`
- Modify: Various skill files (autofire_skills.py, combat_levels.py, etc.)

- [ ] **Step 1: Add _roll_based_default class variable to Skill**

```python
class Skill:
    _roll_based_default: ClassVar[bool] = True
```

Set `self.roll_based = self._roll_based_default` in `_init()`.

- [ ] **Step 2: Convert flag-only subclasses**

For each class that ONLY overrides `get_total_cost` to set `roll_based = False`:

```python
# Before
class AutofireSkills(Skill):
    def get_total_cost(self):
        self.roll_based = False
        return super().get_total_cost()

# After
class AutofireSkills(Skill, xmlid="AUTOFIRE_SKILLS"):
    _roll_based_default: ClassVar[bool] = False
```

Identify which classes qualify by checking if their `get_total_cost` does ONLY `self.roll_based = False; return super()`.

- [ ] **Step 3: Run tests + oracle**

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: replace flag-only skill overrides with class variables"
```

---

## Task 11: Extract CostMixin

Extract cost calculation logic from `base.py` into `engine/cost.py`.

**Files:**
- Create: `kirby_cost/engine/__init__.py`
- Create: `kirby_cost/engine/cost.py`
- Modify: `kirby_cost/objects/base.py`

- [ ] **Step 1: Create engine/cost.py with CostMixin**

Move these properties from GenericObject into CostMixin:
- `total_cost` (the base implementation, ~80 lines)
- `active_cost` / `_compute_active_cost` (~70 lines)
- `real_cost` (~15 lines)
- `real_cost_pre_list` (~65 lines)
- Related helper methods (enhancer logic, AP per END, etc.)

```python
# kirby_cost/engine/cost.py
class CostMixin:
    """HERO System cost chain: base → total → active → real."""

    @property
    def total_cost(self) -> float:
        # ... moved from GenericObject ...

    @property
    def active_cost(self) -> float:
        return self._compute_active_cost()

    def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
        # ... moved from GenericObject ...

    @property
    def real_cost(self) -> float:
        # ... moved from GenericObject ...

    @property
    def real_cost_pre_list(self) -> float:
        # ... moved from GenericObject ...
```

- [ ] **Step 2: Update GenericObject to inherit from CostMixin**

```python
from kirby_cost.engine.cost import CostMixin

class GenericObject(CostMixin):
    # Remove cost methods — they're in CostMixin now
    ...
```

- [ ] **Step 3: Run tests + oracle**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short -q`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract CostMixin from GenericObject"
```

---

## Task 12: Extract ModifierMixin

Extract modifier/adder management into `engine/modifiers.py`.

**Files:**
- Create: `kirby_cost/engine/modifiers.py`
- Modify: `kirby_cost/objects/base.py`

- [ ] **Step 1: Create ModifierMixin**

Move modifier and adder list management, lookup methods, and string rendering:
- `assigned_modifiers` / `assigned_adders` / `available_adders` initialization
- `find_object_by_id` (static)
- `get_modifier_string` / `get_adder_string`
- `get_all_assigned_modifiers`

- [ ] **Step 2: Update GenericObject**

```python
from kirby_cost.engine.cost import CostMixin
from kirby_cost.engine.modifiers import ModifierMixin

class GenericObject(CostMixin, ModifierMixin):
    ...
```

- [ ] **Step 3: Run tests + oracle**

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract ModifierMixin from GenericObject"
```

---

## Task 13: Extract SerializationMixin

Extract XML serialization into `engine/serialize.py`.

**Files:**
- Create: `kirby_cost/engine/serialize.py`
- Modify: `kirby_cost/objects/base.py`

- [ ] **Step 1: Create SerializationMixin**

Move:
- `get_save_xml` / `get_general_save_xml`
- `_init` (XML parsing)
- `apply_template` (template data application)
- `from_xml` (class method for construction)

- [ ] **Step 2: Update GenericObject**

```python
class GenericObject(CostMixin, ModifierMixin, SerializationMixin):
    ...
```

- [ ] **Step 3: Run tests + oracle**

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract SerializationMixin from GenericObject"
```

---

## Task 14: __init_subclass__ Registry

Replace the loader's _POWER_MAP, _SKILL_MAP, _CHAR_MAP globals with an automatic class registry.

**Files:**
- Modify: `kirby_cost/objects/base.py`
- Modify: All subclass files (add `xmlid=` parameter)
- Modify: `kirby_cost/io/hdc_loader.py`

- [ ] **Step 1: Add __init_subclass__ to GenericObject**

```python
class GenericObject(CostMixin, ModifierMixin, SerializationMixin):
    _registry: ClassVar[dict[str, type['GenericObject']]] = {}

    def __init_subclass__(cls, xmlid: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if xmlid:
            cls._registry[xmlid] = cls
            cls.XMLID = xmlid
```

- [ ] **Step 2: Add xmlid= to all subclasses**

```python
# Before
class ForceWall(Power):
    XMLID = "FORCEWALL"

# After
class ForceWall(Power, xmlid="FORCEWALL"):
    pass  # XMLID set automatically by __init_subclass__
```

Do this for ALL classes that have `XMLID = "..."` class attributes.

- [ ] **Step 3: Update loader to use registry**

```python
# Before
cls = _get_power_map().get(xmlid, GenericObject)

# After
cls = GenericObject._registry.get(xmlid, GenericObject)
```

Delete `_get_power_map()`, `_get_skill_map()`, `_get_char_map()` and their globals.

- [ ] **Step 4: Run tests + oracle**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: replace loader maps with __init_subclass__ registry"
```

---

## Task 15: Template Dataclasses

Define the dataclass contracts for template data. This doesn't touch the database — it defines what shape data the engine expects.

**Files:**
- Create: `kirby_cost/template/__init__.py`
- Create: `kirby_cost/template/dataclasses.py`

- [ ] **Step 1: Define template dataclasses**

```python
# kirby_cost/template/dataclasses.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class OptionTemplate:
    xmlid: str
    display: str
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0

@dataclass(frozen=True)
class AdderTemplate:
    xmlid: str
    display: str
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0
    min_cost: float = 0.0
    max_cost: float = 0.0
    types: tuple[str, ...] = ()
    options: tuple[OptionTemplate, ...] = ()

@dataclass(frozen=True)
class TemplateData:
    xmlid: str
    display: str
    base_cost: float = 0.0
    level_cost: float = 0.0
    level_value: float = 0.0
    level_power: int = 1
    level_multiplier: int = 1
    minimum_cost: float = 0.0
    min_set: bool = False
    max_cost: float = 0.0
    max_set: bool = False
    duration: str = "INSTANT"
    target: str = "N/A"
    uses_end: bool = False
    is_power: bool = False
    class_name: str = ""
    adders: tuple[AdderTemplate, ...] = ()
    options: tuple[OptionTemplate, ...] = ()
    types: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
```

- [ ] **Step 2: Add apply_template methods to domain objects**

```python
class GenericObject:
    def apply_template(self, tmpl: TemplateData) -> None:
        """Apply template defaults. Source-agnostic — works with DB, fixtures, or seed data."""
        if not self._base_cost_from_xml and tmpl.base_cost:
            self.base_cost = tmpl.base_cost
        if not self.level_cost and tmpl.level_cost:
            self.level_cost = tmpl.level_cost
        ...

class Adder(GenericObject):
    def apply_template(self, tmpl: AdderTemplate) -> None:
        if not self._base_cost_from_xml and tmpl.base_cost:
            self.base_cost = tmpl.base_cost
        if tmpl.types:
            self.types = list(tmpl.types)
        ...
```

- [ ] **Step 3: Write tests for template application**

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add template dataclasses and apply_template methods"
```

---

## Task 16: Loader Cleanup

Slim down HDCLoader using the registry and apply_template methods.

**Files:**
- Modify: `kirby_cost/io/hdc_loader.py`

- [ ] **Step 1: Replace standalone functions with object methods**

The 12 standalone functions (`_apply_template_defaults`, `_apply_template_to_modifier`, `_apply_template_to_adder`, etc.) are now handled by each class's `apply_template()`. Remove them.

- [ ] **Step 2: Replace map lookups with registry**

```python
# Before
power_map = _get_power_map()
cls = power_map.get(xmlid, GenericObject)

# After
cls = GenericObject._registry.get(xmlid, GenericObject)
```

- [ ] **Step 3: Simplify _build_object, _build_modifier, _build_adder**

These now delegate to the class's `from_xml()` and `apply_template()`.

- [ ] **Step 4: Run tests + oracle**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: slim HDCLoader — registry + apply_template replaces standalone functions"
```

---

## Task 17: Final Cleanup and Validation

- [ ] **Step 1: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short`
Expected: All PASS

- [ ] **Step 2: Run oracle fixtures**

Run: `.venv/bin/python -m pytest tests/test_oracle_fixtures.py -v --tb=short -q`
Expected: All PASS

- [ ] **Step 3: Verify line count reduction**

Run: `find kirby_cost -name "*.py" -exec cat {} + | wc -l`
Expected: Significant reduction from 52,598

- [ ] **Step 4: Verify no remaining Java-isms**

Run: `grep -rn "def get_\|def set_\|def is_" kirby_cost/objects/base.py | wc -l`
Expected: Near zero (only legitimate methods like `get_save_xml`)

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "refactor: Pythonic refactor complete — properties, DRY skills, mixins, registry"
```

---

## Review Errata — READ BEFORE IMPLEMENTING

The following issues were found during spec review and must be addressed during the relevant tasks.

### Critical: Speed/Comliness parameter on get_total_cost (Task 4)

`Speed.get_total_cost(self, active_hero)` and `Comliness.get_total_cost(self, active_hero)` accept a parameter. Properties cannot accept arguments. **Before converting to `@property`**, refactor these two classes to use `self._entity` (or `self._get_active_hero()`) internally instead of the parameter, and update their callers to not pass the argument. Then convert to `@property` like the rest.

### Critical: is_equipment name collision (Task 2)

`base.py` line 117 sets `self.is_equipment: bool = False` as an attribute, but line 355 defines `def is_equipment(self)` as a method returning `self.is_equipment`. This is a latent bug — some callers use `obj.is_equipment` (attribute) and others use `obj.is_equipment()` (method call). **Resolution:** During Task 2, rename the attribute to `self._is_equipment` and convert the method to a `@property` that returns `self._is_equipment`. Update callers to drop the parentheses.

### Critical: Group A skill variations (Task 8)

The 5 Group A skills are NOT identical. Key differences the implementer must handle:

1. **Positive adder handling:** Navigation/AnimalHandler/Weaponsmith use n-counter discount for all non-first adders. Gambling/Forgery only apply minimum_cost discount when `is_familiarity or is_proficiency` AND it's the first adder — subsequent adders get full cost.
2. **Negative adder handling:** Navigation has a 15-line n-counter for negative adders. The other 4 use a simple 4-line sum.
3. **Everyman guard:** Navigation/AnimalHandler check `is_familiarity and is_everyman`. Gambling/Weaponsmith/Forgery check only `is_everyman`.
4. **roll_based check:** AnimalHandler is missing the `self.roll_based` guard in skill maxima. The others have it.

**Action:** Before writing NCounterSkill, run each of the 5 skill implementations against ALL oracle fixtures to identify which behavioral variant each character actually exercises. If a difference is never hit by any oracle character, use the most conservative implementation (Navigation's). If a difference IS hit, you need to parameterize NCounterSkill or keep separate subclasses for the divergent skills.

### Important: include_familiarity collision in Skill (Task 6)

`skill.py` line 60 sets `self.include_familiarity: bool = False` as an attribute. Line 168 defines `def include_familiarity(self) -> bool` which `return self.include_familiarity` — a recursive call, not an attribute read. Subclasses override the method. **Resolution:** Rename the attribute to `self._include_familiarity` and keep the method (or convert to property).

### Important: Missing override files in Task 4

Task 4's subclass override list is incomplete. Additional files with `get_active_cost` or `get_real_cost_pre_list` overrides:
- `powers/mental_defense.py`, `powers/missile_deflection.py`, `powers/differing_modifier.py`
- `frameworks/vpp.py`, `frameworks/multipower.py`, `frameworks/elemental_control.py`
- `perks/favor.py`, `perks/resource_pool.py`
- `martial_arts/maneuver.py`
- `skills/skill.py`, `skills/language.py` (real_cost_pre_list overrides)

### Important: get_types() and list properties (Tasks 2-3)

`get_types()` (base.py:289) has significant logic (clones list, checks modifiers for UOO/BOECV/ABSORPTIONASDEFENSE). This should remain a method or become a complex `@property`. It is NOT a trivial getter.

`get_assigned_modifiers()`, `get_assigned_adders()`, `get_available_adders()` have null-guard initialization logic. Convert to properties in Task 3 (computed), not Task 2 (trivial).

### Important: Task 10 uses xmlid= syntax before Task 14

Task 10 shows `class AutofireSkills(Skill, xmlid="AUTOFIRE_SKILLS")` but `__init_subclass__` isn't added until Task 14. Use the existing `XMLID = "AUTOFIRE_SKILLS"` class attribute pattern in Task 10. Task 14 converts all to `xmlid=` parameter syntax.

### Important: Registry population (Task 14)

The `__init_subclass__` registry only works if all subclass modules are imported. The plan should specify a `kirby_cost/objects/_registry_imports.py` module that eagerly imports all subclass modules. The loader imports this module once to populate the registry.

### Important: AdderBasedSkill/Survival relationship (Task 8)

`adder_based_skill.py` already exists as a partial consolidation (handles Survival's pattern). NCounterSkill should either extend AdderBasedSkill or replace it. The `Survival = AdderBasedSkill` alias at line 147 needs to be maintained or migrated. Clarify the class hierarchy: `NCounterSkill(AdderBasedSkill)` with AdderBasedSkill continuing to handle Survival, or merge Survival into NCounterSkill.

### Suggestion: GenericObject stays in objects/base.py

The spec shows `engine/base.py` for GenericObject, but moving it would touch every import in the project for a pure file move. Keep GenericObject in `objects/base.py` and update the spec to match. The mixins live in `engine/` but GenericObject stays put.
