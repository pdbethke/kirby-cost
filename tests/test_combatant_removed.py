import pytest

def test_to_combatant_no_longer_exported():
    import kirby_cost.io as io
    assert not hasattr(io, "to_combatant")
    assert not hasattr(io, "Combatant")
    with pytest.raises(ImportError):
        from kirby_cost.io import to_combatant  # noqa

def test_front_door_still_exports_build_doc_api():
    from kirby_cost.io import (build_from_json, to_build_json, cost_build,
                                  extract_costs, BuildNode, CostResult, BuildDocError)  # noqa
