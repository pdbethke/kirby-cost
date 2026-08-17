"""
Tests for kirby_cost.util.constants

Verifies characteristic type mappings and lookups.
"""

import pytest
from kirby_cost.util.constants import (
    CharacteristicType,
    characteristic_integer,
    characteristic_string,
)


class TestCharacteristicType:
    """CharacteristicType enum covers all Champions 6E characteristics."""

    def test_primary_characteristics(self):
        assert CharacteristicType.STR == 1
        assert CharacteristicType.DEX == 2
        assert CharacteristicType.CON == 3
        assert CharacteristicType.BODY == 4
        assert CharacteristicType.INT == 5
        assert CharacteristicType.EGO == 6
        assert CharacteristicType.PRE == 7

    def test_combat_values(self):
        assert CharacteristicType.OCV == 30
        assert CharacteristicType.DCV == 31
        assert CharacteristicType.OMCV == 32
        assert CharacteristicType.DMCV == 33

    def test_derived_stats(self):
        assert CharacteristicType.PD == 9
        assert CharacteristicType.ED == 10
        assert CharacteristicType.SPD == 11
        assert CharacteristicType.REC == 12
        assert CharacteristicType.END == 13
        assert CharacteristicType.STUN == 14

    def test_movement(self):
        assert CharacteristicType.RUNNING == 17
        assert CharacteristicType.SWIMMING == 18
        assert CharacteristicType.LEAPING == 19

    def test_general(self):
        assert CharacteristicType.GENERAL == 0


class TestGetCharacteristicInteger:
    """characteristic_integer: name -> int lookup."""

    def test_standard_lookup(self):
        assert characteristic_integer("STR") == 1
        assert characteristic_integer("DEX") == 2

    def test_case_insensitive(self):
        assert characteristic_integer("str") == 1
        assert characteristic_integer("Str") == 1

    def test_whitespace_stripped(self):
        assert characteristic_integer("  STR  ") == 1

    def test_unknown_returns_general(self):
        assert characteristic_integer("NONEXISTENT") == 0

    def test_empty_returns_general(self):
        assert characteristic_integer("") == 0


class TestGetCharacteristicString:
    """characteristic_string: int -> name lookup."""

    def test_standard_lookup(self):
        assert characteristic_string(1) == "STR"
        assert characteristic_string(2) == "DEX"

    def test_general(self):
        assert characteristic_string(0) == "GENERAL"

    def test_invalid_returns_general(self):
        assert characteristic_string(999) == "GENERAL"

    def test_combat_values(self):
        assert characteristic_string(30) == "OCV"
        assert characteristic_string(31) == "DCV"
