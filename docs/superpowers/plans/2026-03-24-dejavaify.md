# De-Java-ify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate all 1,017 Java-style `get_`/`set_`/`is_` methods from the hero-designer-python codebase, replacing them with `@property` or bare method names.

**Architecture:** A `libcst` transformation script runs in three phases: (1) non-conflicting parameterless methods → `@property`, (2) attribute-conflicting methods → rename attribute + `@property`, (3) parameterized methods → drop prefix. Oracle test suite (968 tests, 655 oracle fixtures) validates each phase.

**Tech Stack:** Python 3.12, libcst, pytest

---

## File Structure

### New files to create
- `scripts/dejavaify.py` — The CST transformation script (all three phases)
- `scripts/dejavaify_config.py` — Exclude list + attribute-conflict mappings

### Files to heavily modify
- Every `.py` file under `kirby_cost/` (~257 files, mechanical changes)
- `tests/` — Call-site updates in test files

---

## Exclusion List

These methods keep their current names:

| Method | Reason |
|--------|--------|
| `get_save_xml` | Serialization interface, called by lxml pipeline |
| `get_general_save_xml` | SerializationMixin XML generation |
| `get_instance` | Static factory pattern (Modifier, Disadvantage) |

---

## Phase 1: Non-Conflicting Properties (754 methods)

Methods where the property name does NOT collide with an existing `__init__` attribute.

Examples: `get_column2_output()` → `column2_output`, `get_damage_display()` → `damage_display`, `is_limitation_modifier()` → `limitation_modifier`, `get_roll()` → `roll`.

## Phase 2: Attribute-Conflicting Properties (89 methods, 25 unique names)

Methods whose stripped name matches an existing `self.X` attribute. Strategy: rename the attribute to `self._X`, convert the getter to `@property def X`, and if a `set_X` exists convert it to `@X.setter`.

**Trivial (16 methods):** The getter just returns the attribute — after renaming the attribute, the property is the sole public interface. e.g. `get_base_cost()` returns `self.base_cost` → rename `self.base_cost` to `self._base_cost`, add `@property def base_cost`.

**Computed (73 methods):** The getter has real logic (null guards, list cloning, modifier checks). Same approach — rename attribute, make property. e.g. `get_types()` clones the list and adds modifier-derived types.

Attribute rename map (applied to `__init__` + all `self.X` assignments/reads):

| Attribute | Renamed to | Getter → Property | Setter → @setter |
|-----------|-----------|-------------------|-------------------|
| `base_cost` | `_base_cost` | `get_base_cost()` → `base_cost` | `set_base_cost()` → `base_cost.setter` |
| `levels` | `_levels` | `get_levels()` → `levels` | — |
| `level_cost` | `_level_cost` | `get_level_cost()` → `level_cost` | — |
| `level_value` | `_level_value` | `get_level_value()` → `level_value` | — |
| `minimum_level` | `_minimum_level` | `get_minimum_level()` → `minimum_level` | — |
| `minimum_cost` | `_minimum_cost` | `get_minimum_cost()` → `minimum_cost` | — |
| `max_cost` | `_max_cost` | `get_max_cost()` → `max_cost` | — |
| `max_level` | `_max_level` | `get_max_level()` → `max_level` | — |
| `assigned_modifiers` | `_assigned_modifiers` | `get_assigned_modifiers()` → `assigned_modifiers` | — |
| `assigned_adders` | `_assigned_adders` | `get_assigned_adders()` → `assigned_adders` | — |
| `available_adders` | `_available_adders` | `get_available_adders()` → `available_adders` | — |
| `available_modifiers` | `_available_modifiers` | `get_available_modifiers()` → `available_modifiers` | — |
| `options` | `_options` | `get_options()` → `options` | — |
| `selected_option` | `_selected_option` | `get_selected_option()` → `selected_option` | `set_selected_option()` → `selected_option.setter` |
| `types` | `_types` | `get_types()` → `types` | — |
| `display` | `_display` | `get_display()` → `display` | — |
| `name` | `_name` | `get_name()` → `name` | — |
| `alias` | `_alias` | `get_alias()` → `alias` | — |
| `defense` | `_defense` | `get_defense()` → `defense` | — |
| `duration` | `_duration` | `get_duration()` → `duration` | — |
| `parent` | `_parent` | `get_parent()` → `parent` | `set_parent()` → `parent.setter` |
| `quantity` | `_quantity` | `get_quantity()` → `quantity` | — |
| `sources` | `_sources` | `get_sources()` → `sources` | — |
| `use_end_reserve` | `_use_end_reserve` | `get_use_end_reserve()` → `use_end_reserve` | — |
| `weight` | `_weight` | `get_weight()` → `weight` | — |

**Critical:** The attribute rename must happen in ALL files, not just `base.py`. Subclasses and the loader directly assign `obj.base_cost = X`, `obj.levels = 5`, etc. All of those become `obj._base_cost = X` (or use the setter if one exists).

## Phase 3: Parameterized Method Renames (215 methods)

Methods that take parameters beyond `self` — keep as methods but drop the `get_`/`set_`/`is_` prefix.

Examples: `get_double_total(check_selected)` → `double_total(check_selected)`, `get_characteristic_value(active_hero)` → `characteristic_value(active_hero)`, `set_familiarity(value)` → just use property setter if appropriate.

Exclude `set_` methods that have side effects and already serve as the `@setter` for a Phase 2 property.

---

## Task 1: Write the CST transformation script

**Files:**
- Create: `scripts/dejavaify_config.py`
- Create: `scripts/dejavaify.py`

- [ ] **Step 1: Write the config module**

```python
# scripts/dejavaify_config.py
"""Configuration for the de-Java-ify transformation."""

# Methods that keep their exact current names
EXCLUDE_METHODS = {
    "get_save_xml",
    "get_general_save_xml",
    "get_instance",
}

# Attribute renames: old_attr → new_attr
# Applied in Phase 2 to resolve property/attribute name collisions
ATTRIBUTE_RENAMES = {
    "base_cost": "_base_cost",
    "levels": "_levels",
    "level_cost": "_level_cost",
    "level_value": "_level_value",
    "minimum_level": "_minimum_level",
    "minimum_cost": "_minimum_cost",
    "max_cost": "_max_cost",
    "max_level": "_max_level",
    "assigned_modifiers": "_assigned_modifiers",
    "assigned_adders": "_assigned_adders",
    "available_adders": "_available_adders",
    "available_modifiers": "_available_modifiers",
    "options": "_options",
    "selected_option": "_selected_option",
    "types": "_types",
    "display": "_display",
    "name": "_name",
    "alias": "_alias",
    "defense": "_defense",
    "duration": "_duration",
    "parent": "_parent",
    "quantity": "_quantity",
    "sources": "_sources",
    "use_end_reserve": "_use_end_reserve",
    "weight": "_weight",
}

# Setter methods that should become @property.setter (not standalone renames)
# Maps get_X → set_X pairs for Phase 2
SETTER_PAIRS = {
    "get_base_cost": "set_base_cost",
    "get_selected_option": "set_selected_option",
    "get_parent": "set_parent",
}
```

- [ ] **Step 2: Write the CST transformation script**

The script uses `libcst` to:
1. **Categorize** all `get_`/`set_`/`is_` methods into Phase 1/2/3
2. **Transform definitions:** add `@property`, rename method, optionally rename attribute
3. **Transform call sites:** `.get_foo()` → `.foo` (property) or `.foo()` (renamed method)
4. **Transform attribute access:** `self.base_cost` → `self._base_cost` (Phase 2 only)

The script operates on a single phase at a time (passed as CLI arg).

```bash
# Usage:
python scripts/dejavaify.py --phase 1 --dry-run  # Preview changes
python scripts/dejavaify.py --phase 1             # Apply Phase 1
python scripts/dejavaify.py --phase 2             # Apply Phase 2
python scripts/dejavaify.py --phase 3             # Apply Phase 3
```

- [ ] **Step 3: Verify script loads and --dry-run works**

Run: `.venv/bin/python scripts/dejavaify.py --phase 1 --dry-run 2>&1 | tail -20`
Expected: Summary of changes to be made, no files modified

- [ ] **Step 4: Commit**

```bash
git add scripts/dejavaify.py scripts/dejavaify_config.py
git commit -m "feat: add CST-based de-Java-ify transformation script"
```

---

## Task 2: Run Phase 1 — Non-Conflicting Properties

- [ ] **Step 1: Run Phase 1 transformation**

Run: `.venv/bin/python scripts/dejavaify.py --phase 1`
Expected: ~754 method definitions converted, ~2000+ call sites updated

- [ ] **Step 2: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -q --tb=short`
Expected: 968 passed, 0 failed

- [ ] **Step 3: Fix any failures**

If tests fail, the script missed a call site or made an incorrect conversion.
Fix manually, re-run tests until green.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: Phase 1 — convert 754 non-conflicting methods to @property"
```

---

## Task 3: Run Phase 2 — Attribute-Conflicting Properties

- [ ] **Step 1: Run Phase 2 transformation**

Run: `.venv/bin/python scripts/dejavaify.py --phase 2`
Expected: ~89 method definitions converted, attribute renames across all files

- [ ] **Step 2: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -q --tb=short`
Expected: 968 passed, 0 failed

- [ ] **Step 3: Fix any failures**

Phase 2 is the riskiest — attribute renames touch `__init__`, assignments, and reads everywhere.
Fix manually, re-run tests until green.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: Phase 2 — convert 89 attribute-conflicting methods to @property"
```

---

## Task 4: Run Phase 3 — Parameterized Method Renames

- [ ] **Step 1: Run Phase 3 transformation**

Run: `.venv/bin/python scripts/dejavaify.py --phase 3`
Expected: ~215 method definitions renamed, call sites updated

- [ ] **Step 2: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -q --tb=short`
Expected: 968 passed, 0 failed

- [ ] **Step 3: Fix any failures**

Fix manually, re-run tests until green.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: Phase 3 — rename 215 parameterized methods, drop get_/set_ prefix"
```

---

## Task 5: Final Validation

- [ ] **Step 1: Verify zero remaining Java-isms**

Run: `grep -rn "def get_\|def set_\|def is_" kirby_cost/ --include="*.py" | grep -v "__pycache__\|get_save_xml\|get_general_save_xml\|get_instance" | wc -l`
Expected: 0

- [ ] **Step 2: Verify no stale call sites**

Run: `grep -rn "\.get_\|\.set_\|\.is_" kirby_cost/ --include="*.py" | grep -v "__pycache__\|get_save_xml\|get_general_save_xml\|get_instance\|\.get(\|\.set(\|\.is_power\b\|\.is_equipment\b\|_is_\|\.items()\|\.setdefault\|\.isinstance\|\.isdigit\|\.isalpha\|\.isupper\|\.islower\|\.isspace\|\.startswith\|\.strip\|\.split\|\.set(" | wc -l`
Expected: Near 0 (may have some false positives from unrelated dict/set/string methods)

- [ ] **Step 3: Run oracle fixtures specifically**

Run: `.venv/bin/python -m pytest tests/test_oracle_fixtures.py -q --tb=short`
Expected: 655 passed, 0 failed

- [ ] **Step 4: Line count check**

Run: `find kirby_cost -name "*.py" -exec cat {} + | wc -l`
Expected: Reduction from 51,399 (less boilerplate)

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "refactor: de-Java-ify complete — 1017 methods converted to Pythonic style"
```

---

## Review Errata — READ BEFORE IMPLEMENTING

### Critical: Phase 2 attribute renames touch the ENTIRE codebase

The attributes being renamed (`base_cost`, `levels`, `level_cost`, etc.) are used in:
- `__init__` of GenericObject and all subclasses
- `hdc_loader.py` (assigns `obj.base_cost = X` during loading)
- `engine/cost.py` (reads `self.base_cost` in cost calculations)
- `template/dataclasses.py` (field names — NOT renamed)
- `apply_template` methods
- Every subclass that overrides cost behavior

The CST script must transform ALL of these consistently. After Phase 2, there should be ZERO bare `self.base_cost` references — only `self._base_cost` (internal) and `self.base_cost` (via @property).

**Exception:** `TemplateData` and `AdderTemplate` dataclass fields keep their names (`base_cost`, `level_cost`, etc.) because they model external data, not internal state.

### Critical: `get_types()` has side effects

`get_types()` in `engine/modifiers.py` mutates `self.types` (initializes to `[]` if None) AND dynamically adds modifier-derived types. Converting to `@property def types` is correct but the implementation must still handle the mutation. After Phase 2, `self.types` becomes `self._types`, and the property is:

```python
@property
def types(self) -> list[str]:
    if self._types is None:
        self._types = []
    types_list = list(self._types)
    # ... modifier checks ...
    return types_list
```

### Important: `set_selected_option` has side effects in AreaEffect

`AreaEffect.set_selected_option()` removes shape-specific adders when the shape changes. This MUST become the `@selected_option.setter` with the side-effect logic preserved.

### Important: `is_power` is already a @property in some classes

`Adder.is_required`, `Adder.is_selected`, `Adder.is_group` are already `@property`. The script must not double-decorate them. Check for existing `@property` before adding.

### Important: External callers in behaviors/ and services/

`kirby_cost/behaviors/power_instance.py` and `kirby_cost/services/hero_builder.py` call many of these methods. The script must process these files too (they're under `kirby_cost/`).

### Important: Test files must also be updated

Tests call `obj.get_foo()` extensively. The script should process `tests/` as well.
