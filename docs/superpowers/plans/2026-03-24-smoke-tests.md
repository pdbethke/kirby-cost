# Smoke Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add happy-path smoke tests for the 4 untested layers (behaviors, database, services, API) — ~125 new tests across 4 test files.

**Architecture:** TDD approach — write tests first against the existing code, ensuring every public function/endpoint has at least one happy-path test. SQLite in-memory for fast DB tests, optional Postgres marker for integration. FastAPI TestClient for API tests.

**Tech Stack:** Python 3.12, pytest, SQLAlchemy, FastAPI TestClient, httpx

**Spec:** `docs/superpowers/specs/2026-03-24-test-suite-design.md`

---

## File Structure

### New files to create
- `tests/test_behaviors.py` — Behaviors engine tests (~40 tests)
- `tests/test_database.py` — Database schema + service tests (~30 tests)
- `tests/test_hero_builder.py` — HeroBuilder service tests (~15 tests)
- `tests/test_api.py` — FastAPI endpoint smoke tests (~40 tests)

### Files to modify
- `tests/conftest.py` — Add DB fixtures (SQLite engine, session, seeded data, TestClient)

---

## Task 1: Install test dependencies + extend conftest

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Install httpx (required by FastAPI TestClient)**

Run: `.venv/bin/pip install httpx`

- [ ] **Step 2: Add database fixtures to conftest.py**

Add these fixtures after the existing `make_adder` function:

```python
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ── Database fixtures ──────────────────────────────────────────

@pytest.fixture(scope="session")
def sqlite_engine():
    """SQLite in-memory engine for fast tests."""
    from kirby_cost.database.schema import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(sqlite_engine):
    """Per-test DB session with rollback."""
    connection = sqlite_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def postgres_engine():
    """Real PostgreSQL engine. Returns None if unavailable."""
    db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://champions_user:champions_dev_password@localhost:5432/champions_rules"
    )
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None

@pytest.fixture
def pg_session(postgres_engine):
    """Per-test PostgreSQL session with rollback. Skips if unavailable."""
    if postgres_engine is None:
        pytest.skip("PostgreSQL not available")
    connection = postgres_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

- [ ] **Step 3: Run existing tests to verify fixtures don't break anything**

Run: `.venv/bin/python -m pytest tests/ -q --tb=short`
Expected: 968 passed

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add database session fixtures to conftest (SQLite + optional Postgres)"
```

---

## Task 2: Behaviors engine tests

**Files:**
- Create: `tests/test_behaviors.py`

These are all pure Python tests — no DB needed.

- [ ] **Step 1: Write SafeExpressionEvaluator tests**

```python
"""Smoke tests for kirby_cost.behaviors — engine, registry, plugins, power instances."""
import pytest
from kirby_cost.behaviors.engine import SafeExpressionEvaluator


class TestSafeExpressionEvaluator:
    """Happy-path tests for the expression evaluator."""

    def setup_method(self):
        self.eval = SafeExpressionEvaluator()

    def test_addition(self):
        assert self.eval.evaluate("2 + 3", {}) == 5

    def test_multiplication(self):
        assert self.eval.evaluate("10 * 5", {}) == 50

    def test_division(self):
        assert self.eval.evaluate("100 / 4", {}) == 25

    def test_subtraction(self):
        assert self.eval.evaluate("10 - 3", {}) == 7

    def test_variable_substitution(self):
        assert self.eval.evaluate("LEVELS * 5", {"LEVELS": 10}) == 50

    def test_comparison_gt(self):
        assert self.eval.evaluate("LEVELS > 3", {"LEVELS": 5}) is True

    def test_comparison_eq(self):
        assert self.eval.evaluate("BASE_COST == 0", {"BASE_COST": 0}) is True

    def test_parentheses(self):
        assert self.eval.evaluate("(2 + 3) * 4", {}) == 20

    def test_nested_arithmetic(self):
        assert self.eval.evaluate("LEVELS * COST + 5", {"LEVELS": 3, "COST": 10}) == 35

    def test_zero_context(self):
        assert self.eval.evaluate("42", {}) == 42

    def test_float_result(self):
        result = self.eval.evaluate("10 / 3", {})
        assert abs(result - 3.333) < 0.01

    def test_negative_numbers(self):
        assert self.eval.evaluate("-5 + 10", {}) == 5
```

- [ ] **Step 2: Write BehaviorSchema tests**

```python
from kirby_cost.behaviors.schema import BehaviorSchema, FormulaExpression


class TestBehaviorSchema:
    """Smoke tests for behavior schema dataclasses."""

    def test_formula_expression_roundtrip(self):
        fe = FormulaExpression(expression="LEVELS * 5", description="damage calc")
        d = fe.to_dict()
        fe2 = FormulaExpression.from_dict(d)
        assert fe2.expression == "LEVELS * 5"
        assert fe2.description == "damage calc"

    def test_behavior_schema_from_dict(self):
        data = {
            "xmlid": "ENERGYBLAST",
            "version": 1,
            "display_template": "{LEVELS}d6 Energy Blast",
            "is_attack": True,
        }
        bs = BehaviorSchema.from_dict(data)
        assert bs.xmlid == "ENERGYBLAST"
        assert bs.is_attack is True
        assert bs.display_template == "{LEVELS}d6 Energy Blast"

    def test_behavior_schema_defaults(self):
        data = {"xmlid": "TEST", "version": 1}
        bs = BehaviorSchema.from_dict(data)
        assert bs.is_attack is False
        assert bs.is_defense is False
        assert bs.damage_calculation is None
```

- [ ] **Step 3: Write BehaviorEngine tests**

```python
from kirby_cost.behaviors.engine import BehaviorEngine
from kirby_cost.behaviors.schema import BehaviorSchema


class TestBehaviorEngine:
    """Smoke tests for the behavior engine."""

    def _make_engine(self, **schema_overrides):
        data = {"xmlid": "TEST", "version": 1, "display_template": "Test Power"}
        data.update(schema_overrides)
        schema = BehaviorSchema.from_dict(data)
        return BehaviorEngine(schema)

    def test_build_context(self):
        engine = self._make_engine()
        ctx = engine.build_context({"levels": 10, "base_cost": 5})
        assert ctx["LEVELS"] == 10
        assert ctx["BASE_COST"] == 5

    def test_evaluate_formula(self):
        engine = self._make_engine()
        ctx = {"LEVELS": 10, "LEVEL_COST": 5}
        result = engine.evaluate_formula("LEVELS * LEVEL_COST", ctx)
        assert result == 50

    def test_display(self):
        engine = self._make_engine(display_template="{LEVELS}d6 Blast")
        result = engine.display({"levels": 10})
        assert "10" in result

    def test_calculate_endurance(self):
        engine = self._make_engine()
        result = engine.calculate_endurance({"levels": 10, "active_cost": 50})
        assert isinstance(result, (int, float))
```

- [ ] **Step 4: Write Registry and PluginLoader tests**

```python
from kirby_cost.behaviors.registry import BehaviorRegistry
from kirby_cost.behaviors.plugins import PluginLoader


class TestBehaviorRegistry:
    """Smoke tests for the behavior registry."""

    def test_singleton(self):
        r1 = BehaviorRegistry()
        r2 = BehaviorRegistry()
        assert r1 is r2

    def test_register_and_lookup_json_behavior(self):
        registry = BehaviorRegistry()
        data = {"xmlid": "TEST_SMOKE", "version": 1, "display_template": "Test"}
        schema = BehaviorSchema.from_dict(data)
        registry.register_json_behavior("TEST_SMOKE", schema)
        assert registry.has_behavior("TEST_SMOKE")

    def test_lookup_missing_returns_none(self):
        registry = BehaviorRegistry()
        result = registry.behavior("NONEXISTENT_XMLID_12345")
        assert result is None

    def test_list_behaviors(self):
        registry = BehaviorRegistry()
        result = registry.list_json_behaviors()
        assert isinstance(result, list)


class TestPluginLoader:
    """Smoke tests for the plugin loader."""

    def test_create_loader(self):
        loader = PluginLoader()
        assert loader is not None

    def test_list_plugins_empty(self):
        loader = PluginLoader()
        plugins = loader.list_plugins()
        assert isinstance(plugins, list)

    def test_load_plugin_from_code(self):
        loader = PluginLoader()
        code = '''
from kirby_cost.objects.powers.power import Power
class TestSmokePlugin(Power):
    """Test plugin for smoke tests."""
    pass
'''
        result = loader.load_plugin_from_code(code, "test_smoke_plugin")
        assert isinstance(result, bool)

    def test_list_power_classes(self):
        loader = PluginLoader()
        result = loader.list_power_classes()
        assert isinstance(result, list)
```

- [ ] **Step 5: Write PowerInstance tests**

```python
from kirby_cost.behaviors.power_instance import PowerInstance, create_power


class TestPowerInstance:
    """Smoke tests for PowerInstance."""

    def test_create_power_instance(self):
        pi = create_power("ENERGYBLAST", levels=10, name="Energy Blast")
        assert pi.xmlid == "ENERGYBLAST"
        assert pi.levels == 10
        assert pi.name == "Energy Blast"

    def test_power_instance_properties(self):
        pi = create_power("ENERGYBLAST", levels=10)
        assert isinstance(pi.active_cost, (int, float))
        assert isinstance(pi.real_cost, (int, float))

    def test_power_instance_to_dict(self):
        pi = create_power("ENERGYBLAST", levels=10)
        d = pi.to_dict()
        assert "xmlid" in d
        assert d["xmlid"] == "ENERGYBLAST"

    def test_power_instance_repr(self):
        pi = create_power("ENERGYBLAST", levels=10)
        r = repr(pi)
        assert "ENERGYBLAST" in r

    def test_power_instance_display(self):
        pi = create_power("ENERGYBLAST", levels=10)
        d = pi.display
        assert isinstance(d, str)

    def test_power_instance_has_extension(self):
        pi = create_power("ENERGYBLAST", levels=10)
        assert isinstance(pi.has_extension("nonexistent"), bool)
```

- [ ] **Step 6: Run all behavior tests**

Run: `.venv/bin/python -m pytest tests/test_behaviors.py -v --tb=short`
Expected: ~35 passed

- [ ] **Step 7: Commit**

```bash
git add tests/test_behaviors.py
git commit -m "test: add behavior engine smoke tests (expression eval, registry, plugins, power instance)"
```

---

## Task 3: Database smoke tests

**Files:**
- Create: `tests/test_database.py`

- [ ] **Step 1: Write schema smoke tests**

```python
"""Smoke tests for kirby_cost.database — schema, template service, converter."""
import pytest
from kirby_cost.database.schema import (
    Base, Character, CharacterObject, Template,
    TemplateObject, Campaign, Team, Rules,
)


class TestSchemaCreation:
    """Verify all key models can be created and persisted."""

    def test_create_character(self, db_session):
        char = Character(
            character_name="Test Hero",
            player_name="Player 1",
            campaign_name="Test Campaign",
        )
        db_session.add(char)
        db_session.flush()
        assert char.id is not None

    def test_create_character_object(self, db_session):
        char = Character(character_name="Test")
        db_session.add(char)
        db_session.flush()
        obj = CharacterObject(
            character_id=char.id,
            xmlid="ENERGYBLAST",
            tag="POWER",
            alias="Energy Blast",
            base_cost=0.0,
            levels=10,
        )
        db_session.add(obj)
        db_session.flush()
        assert obj.id is not None
        assert obj.character_id == char.id

    def test_create_template(self, db_session):
        tmpl = Template(
            template_id="Main6E",
            display="Main 6th Edition",
        )
        db_session.add(tmpl)
        db_session.flush()
        assert tmpl.id is not None

    def test_create_campaign(self, db_session):
        camp = Campaign(
            name="Champions Universe",
            description="Standard Champions setting",
        )
        db_session.add(camp)
        db_session.flush()
        assert camp.id is not None

    def test_create_template_object(self, db_session):
        tmpl = Template(template_id="Test", display="Test Template")
        db_session.add(tmpl)
        db_session.flush()
        tobj = TemplateObject(
            template_id=tmpl.id,
            xmlid="ENERGYBLAST",
            display="Energy Blast",
            base_cost=0.0,
            level_cost=5.0,
        )
        db_session.add(tobj)
        db_session.flush()
        assert tobj.id is not None

    def test_character_object_relationship(self, db_session):
        char = Character(character_name="Test")
        db_session.add(char)
        db_session.flush()
        obj = CharacterObject(
            character_id=char.id,
            xmlid="STR",
            tag="STR",
            alias="Strength",
            levels=5,
        )
        db_session.add(obj)
        db_session.flush()
        # Query back
        result = db_session.query(CharacterObject).filter_by(character_id=char.id).all()
        assert len(result) == 1
        assert result[0].xmlid == "STR"

    def test_rules_creation(self, db_session):
        rules = Rules(
            base_points=400,
            disad_points=75,
        )
        db_session.add(rules)
        db_session.flush()
        assert rules.id is not None
```

- [ ] **Step 2: Write Postgres integration tests**

```python
class TestPostgresSmoke:
    """Verify schema works against real PostgreSQL."""

    def test_tables_exist(self, pg_session):
        """Verify key tables exist in the real database."""
        from sqlalchemy import inspect
        inspector = inspect(pg_session.bind)
        tables = inspector.get_table_names()
        assert "characters" in tables or "character" in tables

    def test_query_templates(self, pg_session):
        """Verify templates table has data."""
        result = pg_session.query(Template).first()
        # May or may not have data — just shouldn't error
        assert result is None or result.template_id is not None

    def test_query_template_objects(self, pg_session):
        """Verify template_objects table is queryable."""
        count = pg_session.query(TemplateObject).count()
        assert isinstance(count, int)
```

- [ ] **Step 3: Run database tests**

Run: `.venv/bin/python -m pytest tests/test_database.py -v --tb=short`
Expected: ~10 passed (Postgres tests may skip)

- [ ] **Step 4: Commit**

```bash
git add tests/test_database.py
git commit -m "test: add database schema and Postgres smoke tests"
```

---

## Task 4: HeroBuilder service tests

**Files:**
- Create: `tests/test_hero_builder.py`

These tests need a populated database. They use the Postgres fixture since HeroBuilder queries real character data.

- [ ] **Step 1: Write HeroBuilder tests**

```python
"""Smoke tests for kirby_cost.services.hero_builder."""
import pytest
from kirby_cost.services.hero_builder import HeroBuilder
from kirby_cost.database.schema import Character, CharacterObject


class TestHeroBuilderSQLite:
    """HeroBuilder tests using SQLite (minimal, seed our own data)."""

    def _seed_character(self, session):
        """Create a minimal character with one characteristic."""
        char = Character(character_name="Test Hero", player_name="Tester")
        session.add(char)
        session.flush()
        # Add STR characteristic
        obj = CharacterObject(
            character_id=char.id,
            xmlid="STR",
            tag="STR",
            alias="Strength",
            base_cost=0.0,
            levels=10,
            level_cost=1.0,
            level_value=1.0,
        )
        session.add(obj)
        session.flush()
        return char.id

    def test_build_hero_returns_hero(self, db_session):
        char_id = self._seed_character(db_session)
        builder = HeroBuilder(db_session)
        hero = builder.build_hero(char_id)
        assert hero is not None
        assert hero.name == "Test Hero"

    def test_build_hero_loads_characteristics(self, db_session):
        char_id = self._seed_character(db_session)
        builder = HeroBuilder(db_session)
        hero = builder.build_hero(char_id)
        assert len(hero.characteristics) >= 1

    def test_build_hero_missing_character(self, db_session):
        builder = HeroBuilder(db_session)
        with pytest.raises((ValueError, AttributeError, TypeError)):
            builder.build_hero(999999)


class TestHeroBuilderPostgres:
    """HeroBuilder tests using real PostgreSQL data."""

    def test_build_first_character(self, pg_session):
        """Build the first character in the database."""
        first = pg_session.query(Character).first()
        if first is None:
            pytest.skip("No characters in database")
        builder = HeroBuilder(pg_session)
        hero = builder.build_hero(first.id)
        assert hero is not None
        assert hero.name != ""

    def test_build_hero_has_powers(self, pg_session):
        """Find a character with powers and verify they load."""
        from sqlalchemy import func
        char_with_powers = (
            pg_session.query(Character)
            .join(CharacterObject, Character.id == CharacterObject.character_id)
            .filter(CharacterObject.tag == "POWER")
            .first()
        )
        if char_with_powers is None:
            pytest.skip("No characters with powers in database")
        builder = HeroBuilder(pg_session)
        hero = builder.build_hero(char_with_powers.id)
        assert len(hero.powers) >= 1
```

- [ ] **Step 2: Run hero builder tests**

Run: `.venv/bin/python -m pytest tests/test_hero_builder.py -v --tb=short`
Expected: ~3 passed (SQLite tests), Postgres may skip

- [ ] **Step 3: Commit**

```bash
git add tests/test_hero_builder.py
git commit -m "test: add HeroBuilder service smoke tests (SQLite + Postgres)"
```

---

## Task 5: API endpoint smoke tests

**Files:**
- Create: `tests/test_api.py`
- Modify: `tests/conftest.py` (add TestClient fixture)

- [ ] **Step 1: Add TestClient fixture to conftest.py**

Add after the database fixtures:

```python
@pytest.fixture(scope="session")
def api_client(sqlite_engine):
    """FastAPI TestClient with SQLite backend."""
    from fastapi.testclient import TestClient
    from kirby_cost.api.main import app
    # Override the DB dependency if possible
    client = TestClient(app)
    return client

@pytest.fixture
def pg_api_client(postgres_engine):
    """FastAPI TestClient with real PostgreSQL backend."""
    if postgres_engine is None:
        pytest.skip("PostgreSQL not available")
    from fastapi.testclient import TestClient
    from kirby_cost.api.main import app
    return TestClient(app)
```

- [ ] **Step 2: Write API smoke tests**

```python
"""Smoke tests for kirby_cost.api endpoints."""
import pytest


class TestHealthEndpoints:
    """Verify the app starts and health checks work."""

    def test_root(self, pg_api_client):
        response = pg_api_client.get("/")
        assert response.status_code == 200

    def test_health(self, pg_api_client):
        response = pg_api_client.get("/health")
        assert response.status_code == 200


class TestCharacterEndpoints:
    """Smoke tests for character endpoints (require Postgres with data)."""

    def test_list_characters(self, pg_api_client):
        response = pg_api_client.get("/api/v1/characters/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_campaigns(self, pg_api_client):
        response = pg_api_client.get("/api/v1/characters/campaigns")
        assert response.status_code == 200

    def test_list_players(self, pg_api_client):
        response = pg_api_client.get("/api/v1/characters/players")
        assert response.status_code == 200

    def test_get_character_not_found(self, pg_api_client):
        response = pg_api_client.get("/api/v1/characters/999999")
        assert response.status_code in (404, 422)

    def test_get_first_character(self, pg_api_client):
        chars = pg_api_client.get("/api/v1/characters/").json()
        if not chars:
            pytest.skip("No characters in database")
        char_id = chars[0]["id"]
        response = pg_api_client.get(f"/api/v1/characters/{char_id}")
        assert response.status_code == 200

    def test_character_characteristics(self, pg_api_client):
        chars = pg_api_client.get("/api/v1/characters/").json()
        if not chars:
            pytest.skip("No characters in database")
        char_id = chars[0]["id"]
        response = pg_api_client.get(f"/api/v1/characters/{char_id}/characteristics")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_character_powers(self, pg_api_client):
        chars = pg_api_client.get("/api/v1/characters/").json()
        if not chars:
            pytest.skip("No characters in database")
        char_id = chars[0]["id"]
        response = pg_api_client.get(f"/api/v1/characters/{char_id}/powers")
        assert response.status_code == 200

    def test_character_skills(self, pg_api_client):
        chars = pg_api_client.get("/api/v1/characters/").json()
        if not chars:
            pytest.skip("No characters in database")
        char_id = chars[0]["id"]
        response = pg_api_client.get(f"/api/v1/characters/{char_id}/skills")
        assert response.status_code == 200


class TestTemplateEndpoints:
    """Smoke tests for template endpoints."""

    def test_list_templates(self, pg_api_client):
        response = pg_api_client.get("/api/v1/templates/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_template(self, pg_api_client):
        templates = pg_api_client.get("/api/v1/templates/").json()
        if not templates:
            pytest.skip("No templates in database")
        tmpl_id = templates[0]["template_id"]
        response = pg_api_client.get(f"/api/v1/templates/{tmpl_id}")
        assert response.status_code == 200

    def test_template_powers(self, pg_api_client):
        templates = pg_api_client.get("/api/v1/templates/").json()
        if not templates:
            pytest.skip("No templates in database")
        tmpl_id = templates[0]["template_id"]
        response = pg_api_client.get(f"/api/v1/templates/{tmpl_id}/powers")
        assert response.status_code == 200

    def test_template_skills(self, pg_api_client):
        templates = pg_api_client.get("/api/v1/templates/").json()
        if not templates:
            pytest.skip("No templates in database")
        tmpl_id = templates[0]["template_id"]
        response = pg_api_client.get(f"/api/v1/templates/{tmpl_id}/skills")
        assert response.status_code == 200

    def test_template_modifiers(self, pg_api_client):
        templates = pg_api_client.get("/api/v1/templates/").json()
        if not templates:
            pytest.skip("No templates in database")
        tmpl_id = templates[0]["template_id"]
        response = pg_api_client.get(f"/api/v1/templates/{tmpl_id}/modifiers")
        assert response.status_code == 200

    def test_search_powers(self, pg_api_client):
        templates = pg_api_client.get("/api/v1/templates/").json()
        if not templates:
            pytest.skip("No templates in database")
        tmpl_id = templates[0]["template_id"]
        response = pg_api_client.get(f"/api/v1/templates/{tmpl_id}/search/powers?q=blast")
        assert response.status_code == 200

    def test_search_all(self, pg_api_client):
        templates = pg_api_client.get("/api/v1/templates/").json()
        if not templates:
            pytest.skip("No templates in database")
        tmpl_id = templates[0]["template_id"]
        response = pg_api_client.get(f"/api/v1/templates/{tmpl_id}/search?q=energy")
        assert response.status_code == 200


class TestPowerAttributeEndpoints:
    """Smoke tests for power attribute endpoints."""

    def test_list_attributes(self, pg_api_client):
        response = pg_api_client.get("/api/v1/power-attributes/")
        assert response.status_code == 200

    def test_list_categories(self, pg_api_client):
        response = pg_api_client.get("/api/v1/power-attributes/categories/list")
        assert response.status_code == 200


class TestPowerTypeEndpoints:
    """Smoke tests for power type endpoints."""

    def test_list_power_types(self, pg_api_client):
        response = pg_api_client.get("/api/v1/power-types/")
        assert response.status_code == 200
```

- [ ] **Step 3: Run API tests**

Run: `.venv/bin/python -m pytest tests/test_api.py -v --tb=short`
Expected: Postgres-dependent tests pass if DB is available, skip otherwise

- [ ] **Step 4: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -q --tb=short`
Expected: 968 + new tests passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_api.py tests/conftest.py
git commit -m "test: add API endpoint smoke tests (FastAPI TestClient + Postgres)"
```

---

## Task 6: Final validation

- [ ] **Step 1: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v --tb=short`
Expected: 968 existing + ~125 new tests passed, 0 failed

- [ ] **Step 2: Run only new tests**

Run: `.venv/bin/python -m pytest tests/test_behaviors.py tests/test_database.py tests/test_hero_builder.py tests/test_api.py -v --tb=short`
Expected: All new tests pass (some may skip if Postgres unavailable)

- [ ] **Step 3: Verify oracle fixtures still pass**

Run: `.venv/bin/python -m pytest tests/test_oracle_fixtures.py -q`
Expected: 655 passed

- [ ] **Step 4: Commit**

```bash
git commit --allow-empty -m "test: smoke test suite complete — behaviors, database, services, API"
```

---

## Review Errata — READ BEFORE IMPLEMENTING

### The API endpoints use raw SessionLocal, not dependency injection

Most API endpoints in `characters.py`, `power_attributes.py`, `power_types.py` create their own DB sessions via `SessionLocal()`. The TestClient won't override these — tests need a real database. This is why API tests use `pg_api_client` (Postgres) rather than `api_client` (SQLite).

The `templates.py` endpoints use `Depends(get_service)` which CAN be overridden, but for smoke tests just hitting the real DB is simpler.

### SQLAlchemy model column names may differ from constructor kwargs

Check the actual `Column()` definitions in `schema.py` — some models may use different column names than the constructor kwargs in the test code. Read the model before writing the test.

### BehaviorRegistry is a singleton

Tests that register behaviors in the registry will persist across test functions within the same session. Use unique XMLIDs (e.g., `TEST_SMOKE_123`) to avoid collisions with other tests.

### Some behavior methods may raise on missing data

`BehaviorEngine.calculate_damage()` etc. may raise if the schema doesn't define a damage calculation. Tests should catch this gracefully or provide minimal schema data.

### httpx is needed

FastAPI's `TestClient` requires `httpx`. Install it before running API tests.
