# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Python reimplementation of Hero Designer 6 (HD6), a character builder for the HERO System tabletop RPG. The code is ported from the **licensed** HERO Designer Java source (purchased from Hero Games 2026-04-07 — see the Provenance section of `README.md`) and must produce **identical cost calculations** to the original Java application. The Java reference lives in a sibling repo (`kirby-hd-oracle/`).

Current state: 99.6% match across 28,593 cost calculations (532/656 characters at 100%).

## Build and Development Commands

```bash
# Virtual environment (use .venv, not venv)
python3 -m venv .venv
source .venv/bin/activate

# Install as editable
pip install -e .
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/ -q --tb=short

# Run a single test file
python -m pytest tests/test_cost_calculations.py -v --tb=short

# Run a single test by name
python -m pytest tests/test_oracle_fixtures.py -k "SCORPION" -q --tb=line

# Run tests excluding slow roundtrip tests
python -m pytest tests/ --ignore=tests/test_hdc_roundtrip.py -q --tb=short

# Oracle comparison (requires Java HD6 CLI in sibling repo)
python scripts/oracle_compare_v2.py --all --summary

# Lint and type check
black hero_designer/ tests/
flake8 hero_designer/ tests/
mypy hero_designer/
```

## Architecture

### Origin: Java Port

Every class traces back to a Java original. Docstrings reference the Java source class (e.g. `Converted from com.hero.objects.GenericObject.java`). When the Python cost result doesn't match Java, the Java CLI oracle (`kirby-hd-oracle/hd6cli.sh`) is the source of truth. The oracle outputs JSON with `total_cost`, `active_cost`, and `real_cost` per object.

### Core Class Hierarchy

```
GenericObject (ABC)  ← CostMixin + ModifierMixin + SerializationMixin
├── Power (via CharAffectingObject)
│   ├── EnergyBlast, Armor, Flight, ... (100+ power subclasses)
│   └── Sense powers (Detect, ActiveSonar, etc.)
├── Skill
│   ├── NCounterSkill, AccumulatorSkill, AdderBasedSkill
│   ├── KnowledgeSkill, Language, CombatLevels, ...
│   └── WeaponFamiliarity, TransportFamiliarity
├── Modifier (advantages & limitations)
│   └── AreaEffect, Charges, Focus, ... (90+ modifier subclasses)
├── Adder (purchasable add-ons within powers/modifiers)
├── Characteristic (STR, DEX, CON, ...)
├── List (framework base)
│   ├── Multipower, VariablePowerPool, ElementalControl
│   └── CompoundPower
├── Perk, Talent, Disadvantage subclasses
└── Maneuver subclasses
```

### Cost Calculation Chain

The HERO System cost formula is: `Total Cost → Active Cost → Real Cost`.

- **Total Cost** = base_cost + (levels / level_value × level_cost) + adder costs
- **Active Cost** = Total Cost × (1 + sum of advantage values)
- **Real Cost** = Active Cost / (1 + |sum of limitation values|) − enhancer savings

These are implemented in `hero_designer/engine/cost.py` (CostMixin). Framework containers (Multipower, VPP) override `real_cost_for_child()` to apply slot-specific rules.

### Subclass Registry (`__init_subclass__`)

Power/modifier/skill subclasses register via `__init_subclass__(xmlid="ENERGYBLAST")`. The HDC loader looks up `GenericObject._registry[xmlid]` to instantiate the correct class. All subclasses must be imported in `hero_designer/objects/_registry_imports.py` to trigger registration.

When adding a new power or modifier subclass:
1. Define the class with `class MyPower(Power, xmlid="MYPOWERID")`
2. Add the import to `_registry_imports.py`

### Template System

Cost parameters (base_cost, level_cost, level_value, min/max, options, adders) come from the user's own HD6 template file (`Main6E.hdt`), read by `HDTTemplateProvider` and resolved from `KIRBY_COST_HDT`. No template data ships with the package. Template data is modeled as frozen dataclasses in `hero_designer/template/dataclasses.py` (`TemplateData`, `OptionTemplate`, `AdderTemplate`). Objects call `apply_template()` during loading to set cost parameters.

HDC files (UTF-16 XML) store only overrides — the loader must merge template defaults with XML-supplied values. XML-supplied values (`_base_cost_from_xml`) take precedence over template defaults.

### HDC Loader

`hero_designer/io/hdc_loader.py` is the primary entry point for loading characters. It:
1. Parses HDC XML (UTF-16 encoded)
2. Looks up each object's class via the `_registry`
3. Applies template defaults from the configured `TemplateProvider`
4. Sets up parent-child relationships (framework slots)
5. Returns a `LoadedHero` with typed lists (characteristics, powers, skills, etc.)

Supplemental data a `TemplateData` does not carry (types, modifier types, sense template provides, adder option costs) is defined as module-level dicts in `hdc_loader.py` (e.g. `_HDT_TYPES`, `_SENSE_TEMPLATE_PROVIDES`).

### Mixin Pattern

`GenericObject` composes behavior from three mixins defined in `hero_designer/engine/`:
- **CostMixin** (`cost.py`): `total_cost`, `active_cost`, `real_cost` properties
- **ModifierMixin** (`modifiers.py`): modifier/adder list management, type aggregation
- **SerializationMixin** (`serialize.py`): XML save/restore

### Behavior System (Experimental)

`hero_designer/behaviors/` defines a hybrid JSON + Python class system for power mechanics (damage, END cost, display). See `behaviors/README.md`. Powers can have JSON-defined behaviors stored in the database, with Python class fallback.

### Database Layer

SQLAlchemy models in `hero_designer/database/schema.py`. Supports SQLite (testing) and PostgreSQL (production). Migrations in `migrations/` (numbered SQL/Python files). The `HeroBuilder` service reconstructs Hero objects from database records for cost calculation.

**Important convention**: Never use JSON blob columns for structured data. Always model as relational tables with proper foreign keys and typed columns.

### API Layer

FastAPI endpoints in `hero_designer/api/` for characters, power types, power attributes, and templates.

## Testing Approach

- **Unit tests** in `tests/` use pytest with factory fixtures (`make_object`, `make_modifier`, `make_adder` in `conftest.py`). `ConcreteObject` is required to instantiate `GenericObject` (it's ABC).
- **Oracle fixture tests** (`test_oracle_fixtures.py`) compare Python cost calculations against pre-generated JSON fixtures from the Java HD6 CLI. These are the definitive correctness tests.
- **Oracle comparison script** (`scripts/oracle_compare_v2.py`) runs the full comparison against all 656 HDC files.
- **Database tests** use SQLite in-memory (`db_session` fixture) or PostgreSQL (`pg_session`, skips if unavailable).

## Key Conventions

- Properties replace Java-style `get_/set_/is_` accessors. Internal state uses underscore-prefixed attributes (`_levels`, `_base_cost`).
- `round_half_down` and `round_half_up` from `hero_designer/util/rounder.py` replicate Java's rounding behavior exactly — do not substitute Python's built-in `round()`.
- XMLID strings are always uppercase (e.g. `"ENERGYBLAST"`, `"REDUCEDEND"`).
- HDC files are UTF-16 XML. The parser auto-detects encoding and preserves BOM/line-ending style for roundtrip fidelity.
- The `HeroDesigner` singleton (`core/hero_designer.py`) provides global access to the active hero, template, and preferences, mirroring the Java `HeroDesigner.getInstance()` pattern.
