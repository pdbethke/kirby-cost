# Test Suite Design — Smoke Tests for Untested Layers

## Goal

Add happy-path smoke tests for the 4 untested layers: behaviors engine, database, services, and API. Every public function/endpoint gets at least one test. ~125 new tests across 4 files.

## Layers

### Layer 1: Behaviors Engine (~40 tests, pure Python)

**`SafeExpressionEvaluator`** (`behaviors/engine.py`):
- Arithmetic: `2 + 3`, `10 * 5`, `100 / 4`
- Variable substitution: `{LEVELS} * 5` with context dict
- Comparison: `{LEVELS} > 3`, `{BASE_COST} == 0`
- Conditional: `{LEVELS} if {LEVELS} > 0 else 1`
- Safety: rejects `__import__`, `eval`, `exec`, `os.system`
- Edge cases: empty expression, unknown variable

**`BehaviorRegistry`** (`behaviors/registry.py`):
- Register a behavior definition, retrieve by xmlid
- Lookup missing xmlid returns None
- Register overwrites existing

**`PluginLoader`** (`behaviors/plugins.py`):
- Load plugin from a Python file
- Plugin registers power class in registry
- Invalid plugin file doesn't crash

**`PowerInstance`** (`behaviors/power_instance.py`):
- Wrap a GenericObject, access display/damage/active_cost
- Wrap with behavior override
- Access levels, xmlid, cost properties

### Layer 2: Database (~30 tests, SQLite + optional Postgres)

**Test infrastructure:**
- SQLite in-memory engine as default (`sqlite:///:memory:`)
- Postgres tests use `champions_rules` DB, skip if unavailable (`@pytest.mark.postgres`)
- Session fixture with `BEGIN`/`ROLLBACK` per test (no persistent state)

**Schema smoke tests** (`database/schema.py`):
- Create and read each of the key models: Character, Power, Skill, Modifier, Adder, Template, Characteristic, Perk, Talent, Disadvantage
- Verify foreign key relationships (Power → Character)
- Verify nullable/required fields

**`TemplateService`** (`database/template_service.py`):
- Load template data from DB
- Cache hit on second load
- Lookup by xmlid returns correct record

**`Converter`** (`database/converter.py`):
- Convert a simple GenericObject to DB model
- Convert DB model back to GenericObject
- Round-trip preserves cost fields

**`CharacterExporter`** (`database/character_exporter.py`):
- Export a minimal Hero (name + 1 characteristic) to DB
- Verify rows created in Character + related tables

### Layer 3: Services (~15 tests, needs DB)

**`HeroBuilder`** (`services/hero_builder.py`):
- Build Hero from DB character ID
- Verify characteristics loaded
- Verify powers loaded
- Verify skills loaded
- Verify cost totals match expected
- Missing character ID raises appropriate error

### Layer 4: API (~40 tests, FastAPI TestClient)

**Test infrastructure:**
- FastAPI `TestClient` with dependency override for DB session (SQLite)
- Seed minimal test data in fixture

**Character endpoints** (`api/characters.py`):
- `GET /characters` — list, returns 200
- `POST /characters` — create, returns 201
- `GET /characters/{id}` — read, returns 200
- `PUT /characters/{id}` — update, returns 200
- `GET /characters/{id}/powers` — powers list
- `GET /characters/{id}/skills` — skills list
- `GET /characters/{id}/characteristics` — characteristics
- `GET /characters/999` — not found, returns 404
- `POST /characters` with bad data — returns 422

**Template endpoints** (`api/templates.py`):
- `GET /templates` — list
- `GET /templates/{id}` — get specific
- `GET /templates/{id}/powers` — powers in template
- `GET /templates/{id}/skills` — skills in template

**Power attribute/type endpoints** (`api/power_attributes.py`, `api/power_types.py`):
- `GET /power-attributes` — list
- `GET /power-types` — list

## File Structure

### New files
- `tests/test_behaviors.py` — Layer 1 tests
- `tests/test_database.py` — Layer 2 tests
- `tests/test_hero_builder.py` — Layer 3 tests
- `tests/test_api.py` — Layer 4 tests

### Modified files
- `tests/conftest.py` — Add DB session fixtures, TestClient fixture, seed data helpers

## Dependencies

May need to add to dev dependencies:
- `httpx` — required by FastAPI TestClient
- `pytest-asyncio` — if any async endpoints

## Test Markers

- `@pytest.mark.postgres` — tests requiring real PostgreSQL (skip if unavailable)
- No marker needed for SQLite tests (always run)
