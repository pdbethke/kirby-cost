"""Scoping the active campaign.

The engine is global by design -- `set_active_hero` is a process-wide
singleton and loading a character mutates it -- so a campaign slot matches the
surrounding shape. What the bare setter does not give you is restoration, and
without it a caller that sets rules and forgets leaks them into everything
that follows in the process.

CONCURRENCY: process-global, exactly as `active_hero` already is. That is a
pre-existing property of this engine, not one this feature introduces, and it
is not solved here. Anyone serving two campaigns from one process needs to
read this note first.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from kirby_cost.core.context import EngineContext


@contextmanager
def use_campaign_rules(rules: Optional["CampaignRules"]):
    """Run a block with *rules* active, restoring the previous value after.

    Named `use_` rather than plainly `campaign_rules` because the latter
    collides with `EngineContext.campaign_rules()`, the GETTER -- and a module
    that needs both (tests/test_campaign_active.py does) ends up importing two
    different things under one name.
    """
    previous = EngineContext.campaign_rules()
    EngineContext.set_campaign_rules(rules)
    try:
        yield rules
    finally:
        EngineContext.set_campaign_rules(previous)
