"""Campaign rules are scoped, and the scope is restored -- including on error.

Without restoration a test that sets rules and forgets leaks them into every
later test in the process. That is silent cross-contamination and it is very
hard to trace, which is why the `with` form exists alongside the setter.
"""
from __future__ import annotations

import pytest

from kirby_cost.campaign import CampaignRules, campaign_rules
from kirby_cost.core.context import EngineContext


def test_the_slot_starts_empty():
    assert EngineContext.campaign_rules() is None


def test_the_block_sets_and_restores(provider):
    rules = CampaignRules(provider=provider)
    assert EngineContext.campaign_rules() is None
    with campaign_rules(rules):
        assert EngineContext.campaign_rules() is rules
    assert EngineContext.campaign_rules() is None


def test_the_block_restores_even_when_the_body_raises(provider):
    rules = CampaignRules(provider=provider)
    with pytest.raises(RuntimeError):
        with campaign_rules(rules):
            raise RuntimeError("boom")
    assert EngineContext.campaign_rules() is None


def test_blocks_nest_and_restore_the_outer_value(provider):
    outer, inner = CampaignRules(provider=provider), CampaignRules(provider=provider)
    with campaign_rules(outer):
        with campaign_rules(inner):
            assert EngineContext.campaign_rules() is inner
        assert EngineContext.campaign_rules() is outer
    assert EngineContext.campaign_rules() is None


def test_the_active_template_slot_is_left_alone(provider):
    """active_template has nine readers whose branches are unfinished stubs
    (`if template: # Would check if template is 6E; return True`). Setting it
    would flip all nine on at once. This feature must not touch it."""
    rules = CampaignRules(provider=provider)
    with campaign_rules(rules):
        assert EngineContext.active_template() is None
