"""Export belongs to the object, in every shape it is exported to.

The XML side always worked this way: each class contributes its own
``get_save_xml``. The build-doc side did not — ``io/build_json.py`` held a
120-line ``_obj_to_dict`` that branched on ``isinstance`` for ForceWall, Sense,
Skill and Maneuver, so one module had to know every class with anything extra
to say. A new subclass exported wrongly until somebody remembered to edit a
file nowhere near it, and nothing failed in the meantime.

Both directions now run through the export mixin. These tests are what keeps
that true, because the old shape works fine right up until the day it doesn't.
"""
import ast
import inspect
from pathlib import Path

import pytest

from kirby_cost.engine.serialize import SerializationMixin
from kirby_cost.io import build_json


BUILD_JSON = Path(inspect.getfile(build_json))


class TestTheDocumentModuleKnowsNoClasses:
    def test_no_isinstance_branching_on_object_classes(self):
        """The document places objects; it does not classify them."""
        # Validating the shape of an incoming doc (isinstance(doc, dict)) is
        # this module's job. Classifying an ENGINE object is not.
        builtins = {"dict", "list", "str", "int", "float", "bool", "tuple"}
        tree = ast.parse(BUILD_JSON.read_text())
        offenders = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "isinstance"):
                continue
            checked = node.args[1] if len(node.args) > 1 else None
            names = ([checked.id] if isinstance(checked, ast.Name)
                     else [e.id for e in getattr(checked, "elts", [])
                           if isinstance(e, ast.Name)])
            if any(n not in builtins for n in names):
                offenders.append(node.lineno)
        assert not offenders, (
            f"isinstance branching returned to build_json.py at lines "
            f"{offenders} — that export belongs on the class"
        )

    def test_it_does_not_import_power_or_skill_classes(self):
        source = BUILD_JSON.read_text()
        for leaked in ("force_wall", "ForceWall", "Sense", "Maneuver"):
            assert f"import {leaked}" not in source and \
                   f"import {leaked}," not in source, \
                   f"build_json.py imports {leaked}; it should not know it exists"


class TestTheMixinOwnsExport:
    def test_the_mixin_provides_the_entry_point(self):
        assert hasattr(SerializationMixin, "to_build_dict")
        assert hasattr(SerializationMixin, "get_save_xml"), \
            "both shapes come off the same mixin, or it does not own export"

    @pytest.mark.parametrize("module,cls,key", [
        ("kirby_cost.objects.skills.skill", "Skill", "skill"),
        ("kirby_cost.objects.martial_arts.maneuver", "Maneuver", "maneuver"),
        ("kirby_cost.objects.powers.force_wall", "ForceWall", "cost_per_inch"),
    ])
    def test_each_class_contributes_its_own_fields(self, module, cls, key):
        """Declared on the class, not enumerated by the exporter."""
        import importlib
        klass = getattr(importlib.import_module(module), cls)
        assert "to_build_dict" in vars(klass), \
            f"{cls} should export its own fields"
        assert key in klass().to_build_dict()

    def test_a_new_subclass_inherits_export_without_touching_the_exporter(self):
        """The property the isinstance chain could never have."""
        from kirby_cost.objects.powers.power import Power

        class InventedPower(Power, xmlid="INVENTED_FOR_A_TEST"):
            pass

        invented = InventedPower()
        invented.xmlid = "INVENTED_FOR_A_TEST"
        invented._name = "Something Nobody Enumerated"
        exported = invented.to_build_dict()
        assert exported["xmlid"] == "INVENTED_FOR_A_TEST"
        assert exported["name"] == "Something Nobody Enumerated"
