"""
Smoke tests for the behavior engine layer.

Tests SafeExpressionEvaluator, BehaviorSchema, BehaviorEngine,
BehaviorRegistry, PluginLoader, and PowerInstance at a happy-path level.
"""

import uuid
import pytest

from kirby_cost.behaviors.engine import SafeExpressionEvaluator, BehaviorEngine
from kirby_cost.behaviors.schema import (
    BehaviorSchema, FormulaExpression, EnduranceCalculation, RoundingMode,
    DamageCalculation, CalculationType,
)
from kirby_cost.behaviors.registry import BehaviorRegistry, get_registry
from kirby_cost.behaviors.plugins import PluginLoader
from kirby_cost.behaviors.power_instance import PowerInstance, create_power


# =========================================================================
# SafeExpressionEvaluator
# =========================================================================

class TestSafeExpressionEvaluator:

    @pytest.fixture()
    def evaluator(self):
        return SafeExpressionEvaluator()

    def test_addition(self, evaluator):
        assert evaluator.evaluate("3 + 4", {}) == 7

    def test_subtraction(self, evaluator):
        assert evaluator.evaluate("10 - 3", {}) == 7

    def test_multiplication(self, evaluator):
        assert evaluator.evaluate("6 * 7", {}) == 42

    def test_division(self, evaluator):
        result = evaluator.evaluate("10 / 4", {})
        assert result == 2.5

    def test_variable_substitution(self, evaluator):
        assert evaluator.evaluate("levels * 5", {"levels": 8}) == 40

    def test_comparison_less_than(self, evaluator):
        assert evaluator.evaluate("3 < 5", {}) is True

    def test_comparison_greater_equal(self, evaluator):
        assert evaluator.evaluate("5 >= 5", {}) is True

    def test_comparison_equal(self, evaluator):
        assert evaluator.evaluate("4 == 4", {}) is True

    def test_comparison_equal_false(self, evaluator):
        assert evaluator.evaluate("4 == 5", {}) is False

    def test_comparison_not_equal(self, evaluator):
        assert evaluator.evaluate("4 != 5", {}) is True

    def test_comparison_not_equal_false(self, evaluator):
        assert evaluator.evaluate("4 != 4", {}) is False

    def test_comparison_less_equal(self, evaluator):
        assert evaluator.evaluate("5 <= 5", {}) is True
        assert evaluator.evaluate("4 <= 5", {}) is True
        assert evaluator.evaluate("6 <= 5", {}) is False

    def test_comparison_greater_equal_false(self, evaluator):
        assert evaluator.evaluate("4 >= 5", {}) is False

    def test_parentheses(self, evaluator):
        assert evaluator.evaluate("(2 + 3) * 4", {}) == 20

    def test_negative_number(self, evaluator):
        assert evaluator.evaluate("-5 + 10", {}) == 5

    def test_float_result(self, evaluator):
        result = evaluator.evaluate("7 / 2", {})
        assert result == 3.5

    def test_empty_expression_returns_zero(self, evaluator):
        assert evaluator.evaluate("", {}) == 0

    def test_unknown_variable_returns_zero(self, evaluator):
        assert evaluator.evaluate("nonexistent", {}) == 0

    def test_function_max(self, evaluator):
        assert evaluator.evaluate("max(3, 7)", {}) == 7

    def test_function_min(self, evaluator):
        assert evaluator.evaluate("min(3, 7)", {}) == 3

    def test_integer_division(self, evaluator):
        assert evaluator.evaluate("7 // 2", {}) == 3

    def test_integer_division_exact(self, evaluator):
        assert evaluator.evaluate("10 // 5", {}) == 2

    def test_equality_with_variable(self, evaluator):
        assert evaluator.evaluate("LEVELS == 5", {"LEVELS": 5}) is True
        assert evaluator.evaluate("LEVELS == 5", {"LEVELS": 3}) is False


# =========================================================================
# BehaviorSchema / FormulaExpression
# =========================================================================

class TestFormulaExpression:

    def test_round_trip(self):
        expr = FormulaExpression(expression="levels * 5", description="Base damage")
        d = expr.to_dict()
        restored = FormulaExpression.from_dict(d)
        assert restored.expression == "levels * 5"
        assert restored.description == "Base damage"

    def test_from_dict_string_shorthand(self):
        restored = FormulaExpression.from_dict("levels + 1")
        assert restored.expression == "levels + 1"
        assert restored.description is None


class TestBehaviorSchema:

    def test_from_dict_minimal(self):
        schema = BehaviorSchema.from_dict({"xmlid": "TESTPOWER"})
        assert schema.xmlid == "TESTPOWER"
        assert schema.version == 1

    def test_defaults(self):
        schema = BehaviorSchema(xmlid="TEST")
        assert schema.is_attack is False
        assert schema.is_defense is False
        assert schema.is_movement is False
        assert schema.display_template == "{alias}"
        assert schema.does_body is True
        assert schema.custom_calculations == {}
        assert schema.validation_rules == []

    def test_to_dict_round_trip(self):
        original = BehaviorSchema(
            xmlid="ROUNDTRIP",
            is_attack=True,
            does_knockback=True,
            description="A test power",
        )
        d = original.to_dict()
        restored = BehaviorSchema.from_dict(d)
        assert restored.xmlid == "ROUNDTRIP"
        assert restored.is_attack is True
        assert restored.does_knockback is True


# =========================================================================
# BehaviorEngine
# =========================================================================

class TestBehaviorEngine:

    @pytest.fixture()
    def engine(self):
        schema = BehaviorSchema(
            xmlid="TESTBLAST",
            display_template="{alias}",
            endurance_calculation=EnduranceCalculation(
                formula="active_cost / 10",
                round=RoundingMode.UP,
                minimum=1,
                costs_end=True,
            ),
        )
        return BehaviorEngine(schema)

    @pytest.fixture()
    def power_data(self):
        return {
            "levels": 8,
            "name": "Energy Blast",
            "alias": "Energy Blast",
            "active_cost": 40,
            "real_cost": 40,
            "base_cost": 5,
        }

    def test_build_context(self, engine, power_data):
        ctx = engine.build_context(power_data)
        assert ctx["levels"] == 8
        assert ctx["active_cost"] == 40
        assert ctx["name"] == "Energy Blast"
        assert ctx["is_6e"] is True

    def test_evaluate_formula(self, engine):
        result = engine.evaluate_formula("levels * 5", {"levels": 8})
        assert result == 40

    def test_display(self, engine, power_data):
        result = engine.display(power_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_endurance(self, engine, power_data):
        end = engine.calculate_endurance(power_data)
        # active_cost=40 / 10 = 4, ceil(4) = 4, max(1, 4) = 4
        assert end == 4

    def test_calculate_endurance_rounds_up(self):
        schema = BehaviorSchema(
            xmlid="TESTEND",
            endurance_calculation=EnduranceCalculation(
                formula="active_cost / 10",
                round=RoundingMode.UP,
                minimum=1,
                costs_end=True,
            ),
        )
        engine = BehaviorEngine(schema)
        # active_cost=15 / 10 = 1.5, ceil = 2
        end = engine.calculate_endurance({"active_cost": 15, "levels": 3})
        assert end == 2

    def test_calculate_endurance_no_end(self):
        schema = BehaviorSchema(
            xmlid="NOEND",
            endurance_calculation=EnduranceCalculation(costs_end=False),
        )
        engine = BehaviorEngine(schema)
        assert engine.calculate_endurance({"active_cost": 40, "levels": 8}) == 0

    def test_calculate_endurance_none(self):
        schema = BehaviorSchema(xmlid="NOENDCALC")
        engine = BehaviorEngine(schema)
        assert engine.calculate_endurance({"active_cost": 40, "levels": 8}) == 0


# =========================================================================
# BehaviorRegistry
# =========================================================================

class TestBehaviorRegistry:

    def test_singleton(self):
        a = BehaviorRegistry()
        b = BehaviorRegistry()
        assert a is b

    def test_register_and_lookup(self):
        registry = BehaviorRegistry()
        uid = f"SMOKETEST_{uuid.uuid4().hex[:8].upper()}"
        schema = BehaviorSchema(xmlid=uid)
        registry.register_json_behavior(uid, schema)
        engine = registry.behavior(uid)
        assert engine is not None
        assert isinstance(engine, BehaviorEngine)

    def test_missing_lookup_returns_none(self):
        registry = BehaviorRegistry()
        uid = f"MISSING_{uuid.uuid4().hex[:8].upper()}"
        assert registry.behavior(uid) is None

    def test_list_json_behaviors(self):
        registry = BehaviorRegistry()
        result = registry.list_json_behaviors()
        assert isinstance(result, list)

    def test_has_behavior_false_for_unknown(self):
        registry = BehaviorRegistry()
        uid = f"NOPE_{uuid.uuid4().hex[:8].upper()}"
        assert registry.has_behavior(uid) is False

    def test_register_makes_has_behavior_true(self):
        registry = BehaviorRegistry()
        uid = f"HASBHV_{uuid.uuid4().hex[:8].upper()}"
        schema = BehaviorSchema(xmlid=uid)
        registry.register_json_behavior(uid, schema)
        assert registry.has_behavior(uid) is True


# =========================================================================
# PluginLoader
# =========================================================================

class TestPluginLoader:

    def test_create_loader(self):
        loader = PluginLoader()
        assert loader is not None

    def test_list_plugins_empty(self):
        loader = PluginLoader()
        result = loader.list_plugins()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_load_plugin_from_code(self):
        loader = PluginLoader()
        code = """
PLUGIN_NAME = "test_plugin"
PLUGIN_VERSION = "0.1"
"""
        uid = f"code_{uuid.uuid4().hex[:8]}"
        ok = loader.load_plugin_from_code(code, uid)
        assert ok is True
        plugins = loader.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]['name'] == 'test_plugin'
        assert plugins[0]['source'] == 'database'

    def test_list_power_classes_empty(self):
        loader = PluginLoader()
        result = loader.list_power_classes()
        assert isinstance(result, list)

    def test_load_bad_code_returns_false(self):
        loader = PluginLoader()
        ok = loader.load_plugin_from_code("def broken(:", f"bad_{uuid.uuid4().hex[:8]}")
        assert ok is False


# =========================================================================
# PowerInstance
# =========================================================================

class TestPowerInstance:

    @pytest.fixture(autouse=True)
    def _register_test_behavior(self):
        """Register a JSON behavior so PowerInstance can use it."""
        self.uid = f"SMOKE_PI_{uuid.uuid4().hex[:8].upper()}"
        schema = BehaviorSchema(
            xmlid=self.uid,
            display_template="{alias}",
            endurance_calculation=EnduranceCalculation(
                formula="active_cost / 10",
                round=RoundingMode.UP,
                minimum=1,
                costs_end=True,
            ),
        )
        registry = BehaviorRegistry()
        registry.register_json_behavior(self.uid, schema)

    def _make_instance(self, **overrides):
        data = {
            "levels": 6,
            "name": "Test Blast",
            "alias": "Test Blast",
            "active_cost": 30,
            "real_cost": 30,
            "base_cost": 5,
        }
        data.update(overrides)
        return PowerInstance(self.uid, data)

    def test_create_power_factory(self):
        pi = create_power(self.uid, levels=4, name="Factory Blast", active_cost=20, real_cost=20)
        assert pi.xmlid == self.uid

    def test_xmlid_property(self):
        pi = self._make_instance()
        assert pi.xmlid == self.uid

    def test_levels_property(self):
        pi = self._make_instance(levels=6)
        assert pi.levels == 6

    def test_levels_setter(self):
        pi = self._make_instance(levels=6)
        pi.levels = 10
        assert pi.levels == 10
        assert pi.character_data["levels"] == 10

    def test_name_property(self):
        pi = self._make_instance()
        assert pi.name == "Test Blast"

    def test_name_setter(self):
        pi = self._make_instance()
        pi.name = "Fire Blast"
        assert pi.name == "Fire Blast"
        assert pi.character_data["name"] == "Fire Blast"

    def test_active_cost_property(self):
        pi = self._make_instance(active_cost=30)
        assert pi.active_cost == 30

    def test_real_cost_property(self):
        pi = self._make_instance(real_cost=25)
        assert pi.real_cost == 25

    def test_display_property(self):
        pi = self._make_instance()
        result = pi.display
        assert isinstance(result, str)
        assert len(result) > 0

    def test_has_extension_false(self):
        pi = self._make_instance()
        assert pi.has_extension("nonexistent_method") is False

    def test_using_json_behavior_flag(self):
        pi = self._make_instance()
        assert pi.using_json_behavior is True

    def test_end_cost(self):
        pi = self._make_instance(active_cost=30)
        # 30/10 = 3, ceil = 3, max(1,3) = 3
        assert pi.end_cost == 3

    def test_to_dict(self):
        pi = self._make_instance(levels=6, active_cost=30, real_cost=30)
        d = pi.to_dict()
        assert d['xmlid'] == self.uid
        assert d['using_json_behavior'] is True
        assert isinstance(d['display'], str)
        assert d['active_cost'] == 30
        assert d['real_cost'] == 30

    def test_repr(self):
        pi = self._make_instance(levels=6)
        r = repr(pi)
        assert self.uid in r
        assert "JSON" in r
        assert "levels=6" in r
