# kirby-cost: Pythonic Refactor Design

## Goal

Transform the Java-to-Python port into idiomatic, DRY, elegant Python. The cost engine becomes a pure library that a database-backed FastAPI character builder calls. It handles characters, equipment, vehicles, and bases — any HERO System 6E entity. The 12,654-object oracle test suite is the safety net — no refactoring changes any cost output.

## Constraints

- **Oracle match rate stays at 99.98%** — players must trust the numbers match HD6
- **Cost engine is stateless** — no caching, no globals. Objects hold references to their containing entity (hero, vehicle, base) for cross-lookups (enhancers, Automaton multipliers, TF discounts), but no timer-based caches or singletons.
- **Database stores inputs, not costs** — costs are always computed fresh
- **No new features** — this is a refactor, not a rewrite

## Architecture

```
FastAPI (champions-campaign-manager)
  │
  ├── Database (PostgreSQL)
  │     ├── Template tables ── mutable reference data (powers, skills, modifiers, adders)
  │     │                      seeded from HDT files, editable by GM for homebrew
  │     └── Entity tables ── character/vehicle/base state (what you've bought)
  │
  └── kirby_cost (this library)
        │
        ├── engine/        ← Pure cost calculation, no I/O, no DB
        │   ├── cost.py        ← CostMixin
        │   ├── modifiers.py   ← ModifierMixin
        │   ├── serialize.py   ← SerializationMixin
        │   └── base.py        ← GenericObject (slim, ~300 lines)
        │
        ├── objects/       ← Domain objects (powers, skills, etc.)
        │   ├── powers/
        │   ├── skills/
        │   ├── characteristics/
        │   ├── perks/
        │   ├── frameworks/
        │   ├── modifiers/
        │   └── talents/
        │
        ├── io/            ← Import/export tools
        │   ├── hdc_loader.py  ← HDC XML → domain objects (import tool)
        │   ├── hdc_writer.py  ← Domain objects → HDC XML (export)
        │   └── hdt_seed.py    ← Parse HDT files → seed data for template tables
        │
        └── tests/
            └── fixtures/      ← Per-character oracle snapshots
                ├── bestiary/
                ├── villains/
                └── characters/
```

### Template Data Flow

Templates are **mutable reference data in the database**, not frozen files. The flow:

1. **Seed:** `hdt_seed.py` parses HDT files (Main6E, Vehicle6E, Automaton6E, etc.) → populates template tables in PostgreSQL. Run once on setup, or re-run to reset to stock.
2. **Customize:** GM edits template data via the API — homebrew powers, adjusted costs, campaign-specific modifiers. The DB is the source of truth.
3. **Calculate:** API layer fetches template data from DB, passes it to the cost engine as plain dicts/dataclasses. The engine never queries the DB or reads files.
4. **Test:** Oracle tests use stock seed data fixtures so they always validate against HD6.

The cost engine's signature is:
```python
# Engine takes data, returns costs. Doesn't care where data came from.
obj.apply_template(template_data)  # dict from DB, fixture, or anywhere
cost = obj.total_cost              # pure calculation
```

### Multiple Templates

Each entity (character, vehicle, base) references a template. The DB stores multiple templates:

| Template | Differences from Main6E |
|----------|------------------------|
| Vehicle6E | PD/ED lc=3/lv=2 (vs 1/1), resistant by default |
| Automaton6E | Different defense handling |
| Base6E | Size-based characteristics |
| Heroic6E | Lower point totals, different NCM |
| Superheroic6E | Standard Champions |

The API fetches the correct template for the entity type and passes it through.

**Multi-entity support:** The cost engine is entity-agnostic. Characters, Vehicles, and Bases all compose from the same `GenericObject` subclasses. The `LoadedEntity` container (currently `LoadedHero`) holds powers, skills, characteristics regardless of entity type. Entity-specific differences (Vehicle PD/ED costs, Base size categories) come from the template, not the engine.

## Caller Inventory

Phase 1 (property conversion) touches every caller. Key packages beyond the core engine:

| Package | Lines | Caller Density | Migration Complexity |
|---------|-------|----------------|---------------------|
| `objects/` | ~8,000 | Heavy — `get_total_cost()`, `get_xmlid()` everywhere | Mechanical find-replace |
| `io/hdc_loader.py` | 1,100 | Heavy — builds objects | Mechanical |
| `database/converter.py` | 771 | Heavy — maps objects to DB | Careful — field name alignment |
| `services/hero_builder.py` | 1,073 | Medium — orchestrates builds | Mechanical |
| `api/` | 2,400 | Light — mostly passes through | Mechanical |
| `behaviors/` | 900 | Light — expression engine | Mechanical |
| `model/` | 900 | Medium — Hero, Rules | Careful — Rules has cost-affecting methods |

**Migration approach:** Add temporary deprecation shims on `GenericObject` during Phase 1. Migrate callers package-by-package. Remove shims once `grep` confirms zero remaining callers. This keeps the oracle green at every commit.

## Phase 0: Oracle Fixture (Do First)

Generate per-character oracle snapshots, commit to git. One JSON file per HDC character for easy debugging:

```
tests/fixtures/bestiary/ETTIN_HSB.json
tests/fixtures/villains/DOCTOR_DESTROYER-CV1.json
tests/fixtures/characters/Wipeout_100percent.json
```

Each file contains the Java oracle's cost outputs for all objects in that character. The oracle comparison test loads the fixture + runs HDCLoader, compares. Runs in ~10 seconds instead of ~3 minutes.

**Impact:** Fast CI feedback, no JVM dependency, immutable (Java oracle never changes).

## Phase 1: Properties & Naming (Mechanical, High Impact)

### What changes

Replace 81 getter/setter methods in `GenericObject` with direct attribute access or `@property` decorators.

**Three categories:**

1. **Plain attributes** — `name`, `alias`, `input`, `xmlid`, `display`, `position`, etc. Delete the getter/setter, callers use the attribute directly.

2. **Computed read-only properties** — `total_cost`, `real_cost`, `real_cost_pre_list`. These become `@property` with the calculation logic. No setter.

3. **Mutable properties with logic** — `base_cost` on `Skill` (checks familiarity), `levels` on `Skill` (returns 0 for familiarity/proficiency). These become `@property` with both getter and setter.

### active_cost special case

`active_cost` currently takes an optional `exclude_xmlid` parameter. Properties cannot accept arguments. Solution:

```python
@property
def active_cost(self) -> float:
    """total_cost * (1 + advantage_sum)."""
    return self._compute_active_cost()

def _compute_active_cost(self, exclude_xmlid: str = None) -> float:
    """Parameterized version for internal use."""
    ...
```

### Caller migration

Add temporary shims, migrate incrementally, remove shims:

```python
# Step 1: Add shims (keeps everything working)
def get_xmlid(self): return self.xmlid  # DEPRECATED
def get_base_cost(self): return self.base_cost  # DEPRECATED

# Step 2: Migrate callers package by package
# Step 3: grep -r "get_xmlid\|get_base_cost" → confirm zero hits
# Step 4: Delete shims
```

### __init_subclass__ registry

```python
def __init_subclass__(cls, xmlid: str = None, **kwargs):
    super().__init_subclass__(**kwargs)
    if xmlid:
        cls._registry[xmlid] = cls
        cls.XMLID = xmlid  # Backward compat with existing cls.XMLID references
```

### Naming cleanup

- `usesEND()` → `uses_end` property
- `doesDamage()` → `does_damage` property
- Any remaining `camelCase` → `snake_case`

### Impact

- Deletes ~350 lines from `base.py`
- Touches every file (with shim safety net)
- Zero logic changes

## Phase 2: DRY Skill Consolidation

### Pre-work: Diff matrix

Before writing any consolidated class, generate a line-by-line diff matrix of all 8 skill files. The review identified two distinct groups:

**Group A — Base-first n-counter:** Navigation, AnimalHandler, Gambling, Weaponsmith, Forgery. Start with `d = base_cost`, use counter `n = -1` to discount adders beyond the first.

**Group B — Accumulator pattern:** Electronics, ComputerProgramming, SystemsOperation. Start with `d = 0`, accumulate adder costs with `has_adder` flag, fall back to `d += base_cost` when no adders found. Override `minimum_cost` to return 2.0 when adders present.

### Consolidation

Two classes, not one:

```python
class NCounterSkill(AdderBasedSkill):
    """First adder pays full cost, subsequent pay minimum.
    Used by: Navigation, AnimalHandler, Gambling, Weaponsmith, Forgery.
    """

    @property
    def total_cost(self) -> float:
        # n-counter discount logic (~80 lines, single implementation)
        ...

class AccumulatorSkill(AdderBasedSkill):
    """Adders accumulate; falls back to base when none present.
    Used by: Electronics, ComputerProgramming, SystemsOperation.
    """

    @property
    def total_cost(self) -> float:
        # Accumulator pattern (~60 lines, single implementation)
        ...
```

Delete 6 files (keep NCounterSkill and AccumulatorSkill).

### Flag-based overrides

~10 skill subclasses that just set flags become configuration:

```python
class AutofireSkills(Skill, xmlid="AUTOFIRE_SKILLS"):
    _roll_based_default: ClassVar[bool] = False
    # No total_cost override needed
```

### Impact

- Deletes ~6 skill files (~500 lines)
- Consolidates ~1,000 lines of duplicated logic into ~200 lines
- Eliminates ~10 trivial overrides

## Phase 3: Base Class Mixins

Split `GenericObject` (1,481 lines) into focused mixins:

### CostMixin (~300 lines)

```python
class CostMixin:
    """HERO System cost chain: base → total → active → real."""

    @property
    def total_cost(self) -> float: ...

    @property
    def active_cost(self) -> float: ...

    def _compute_active_cost(self, exclude_xmlid: str = None) -> float: ...

    @property
    def real_cost(self) -> float: ...

    @property
    def real_cost_pre_list(self) -> float: ...
```

### ModifierMixin (~200 lines)

Modifier/adder assignment, lookup, string rendering.

### SerializationMixin (~200 lines)

HDC XML round-trip. `to_xml()`, `from_xml()`, `apply_template()`.

### GenericObject (~300 lines)

```python
class GenericObject(CostMixin, ModifierMixin, SerializationMixin):
    """Core HERO System object — identity, levels, types, and composition."""

    _registry: ClassVar[dict[str, type['GenericObject']]] = {}

    def __init_subclass__(cls, xmlid: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if xmlid:
            cls._registry[xmlid] = cls
            cls.XMLID = xmlid
```

### Hero/entity coupling

Objects hold a reference to their containing entity (`self._entity`) for cross-lookups. This is not global state — it's a back-reference in the object graph, set during loading. Cost methods that need hero context (enhancer savings, Automaton multiplier, TF discounts) access it through `self._entity`. No timer-based caches.

### Impact

- `base.py` goes from 1,481 lines to ~300 lines
- Each mixin is independently testable
- Cost logic is isolated and readable

## Phase 4: Relational Template Schema & Object Methods

### Template tables (PostgreSQL)

Templates are fully normalized relational data. JSON files become seed scripts only.

```sql
-- One row per template file (Main6E, Vehicle6E, Automaton6E, etc.)
templates
  id, name, display, is_6e, description

-- Power/skill/perk/talent definitions — one row per entry in the template
template_objects
  id, template_id, xmlid, category (power/skill/perk/talent/complication),
  display, alias, base_cost, level_cost, level_value, level_power,
  level_multiplier, minimum_cost, min_set, max_cost, max_set,
  duration, target, range_type, uses_end, is_power,
  class_name  -- Python class to instantiate (e.g. "ForceWall", "Detect")

-- Adders on powers/skills/modifiers — nested via parent_id
template_adders
  id, template_object_id, parent_adder_id (self-ref for nesting),
  xmlid, display, base_cost, level_cost, level_value,
  min_cost, max_cost

-- Options on powers/adders (SINGLE/CLASS/LARGECLASS, sense group selections, etc.)
template_options
  id, parent_id, parent_type (object/adder/modifier),
  xmlid, display, base_cost, level_cost, level_value

-- Modifier definitions (advantages and limitations)
template_modifiers
  id, template_id, xmlid, display, base_cost, level_cost, level_value,
  min_cost, max_cost, is_advantage

-- TYPE associations (ATTACK, DEFENSE, SENSORY, MENTAL, etc.)
template_types
  id, parent_id, parent_type (object/adder/modifier), type_name

-- Characteristic definitions — per-template costs (Vehicle PD ≠ Main PD)
template_characteristics
  id, template_id, xmlid, display, base_value, level_cost, level_value,
  min_val, max_val, position

-- PROVIDES associations (Detect PROVIDES ENHANCEDPERCEPTION, etc.)
template_provides
  id, template_object_id, provides_xmlid

-- EXCLUDES associations (mutually exclusive modifiers)
template_excludes
  id, parent_id, parent_type, excludes_xmlid
```

### Seed pipeline

```
HDT files (Main6E.hdt, Vehicle6E.hdt, ...)
    │
    └── hdt_seed.py ── parses XML → INSERT INTO template_* tables
```

Run once on setup. Re-run to reset to stock. GM edits via API after that.

### Cost engine input

The engine receives template data as **dataclasses**, not raw dicts or DB rows. The API layer handles the DB→dataclass conversion:

```python
@dataclass(frozen=True)
class TemplateData:
    """Template data for a single power/skill/modifier."""
    xmlid: str
    base_cost: float
    level_cost: float
    level_value: float
    adders: dict[str, 'AdderTemplate']
    options: dict[str, 'OptionTemplate']
    types: list[str]
    provides: list[str]
    ...

@dataclass(frozen=True)
class AdderTemplate:
    xmlid: str
    display: str
    base_cost: float
    min_cost: float
    types: list[str]
    ...
```

Objects apply template data via methods on themselves:

```python
class Adder(GenericObject):
    def apply_template(self, tmpl: AdderTemplate) -> None:
        """Apply template defaults from DB/fixture/seed data."""
        if not self._base_cost_from_xml and tmpl.base_cost:
            self.base_cost = tmpl.base_cost
        if tmpl.types:
            self.types = list(tmpl.types)
```

### Oracle tests

Oracle tests use stock seed data loaded into dataclasses directly (no DB needed for tests):

```python
# tests/conftest.py
STOCK_TEMPLATE = load_seed_as_dataclasses("main_6e")  # from fixture files
```

This ensures oracle results always validate against HD6 regardless of any DB customizations.

### Impact

- Eliminates JSON as a runtime data source — it's a seed format only
- Template data is queryable (`SELECT * FROM template_objects WHERE category = 'power' AND types @> '{ATTACK}'`)
- GM can customize via API — homebrew, house rules, campaign variants
- Engine is input-source agnostic — works with DB data, test fixtures, or anything that produces the dataclasses
- Eliminates 12 standalone loader functions and 4 module-level globals
- Bridges this project to the campaign manager's PostgreSQL schema

### Note

The full template schema design (migrations, indexes, seed script, API endpoints) will be detailed in a separate design doc since it touches the campaign manager project. This phase in the refactor focuses on: (1) defining the dataclass contracts, (2) moving `apply_template()` onto the objects, (3) removing the JSON-as-runtime-source pattern from the engine.

## Phase 5: Loader Cleanup

`HDCLoader` becomes pure orchestration (~300 lines):

```python
class HDCLoader:
    def load_file(self, path: Path) -> LoadedEntity:
        root = self._parse_xml(path)
        entity = LoadedEntity()
        entity.powers = self._load_section(root, "POWERS")
        entity.skills = self._load_section(root, "SKILLS")
        ...
        self._wire_relationships(entity)
        return entity
```

Object construction uses the class registry:

```python
cls = GenericObject._registry.get(xmlid, GenericObject)
obj = cls.from_xml(element)
obj.apply_template(POWERS.get(xmlid, {}))
```

### Impact

- `hdc_loader.py` goes from 1,100 lines to ~300 lines
- No global state
- Each class owns its construction and template application

## Phase Order & Testing Strategy

| Phase | What | Lines Saved | Risk | Gate |
|-------|------|-------------|------|------|
| 0 | Oracle fixture | 0 | None | Verify fixture matches live oracle |
| 1 | Properties & naming | ~350 | Low | Unit tests + oracle fixture |
| 2 | DRY skills | ~500 | Medium | Unit tests + oracle fixture |
| 3 | Base class mixins | ~200 | Medium | Unit tests + oracle fixture |
| 4 | Template constant | ~200 | Low | Unit tests + oracle fixture |
| 5 | Loader cleanup | ~300 | Medium | Unit tests + oracle fixture |

**Phase 0 first** — build the safety net before touching anything.

**Realistic total reduction: ~1,550 lines** from the affected files. Phase 3 is primarily reorganization (logic moves, doesn't delete), so the savings there are modest. The real wins are Phase 1 (boilerplate) and Phase 2 (duplication).

## What This Enables

After the refactor, the cost engine is a clean Python library:
- **Entity-agnostic** — Characters, Vehicles, Bases all use the same engine
- **No I/O dependencies** — no XML, no JSON files, no database in the engine
- **Clear API surface** — `obj.total_cost`, `obj.active_cost`, `obj.real_cost`
- **Class registry** — `GenericObject._registry["ENERGYBLAST"]` returns `EnergyBlast`
- **Testable in isolation** — construct objects in code, verify costs
- **Database-ready** — the FastAPI layer reads entity state from PostgreSQL, hydrates engine objects, computes costs, returns results. No stale caches, no sync issues.
