"""
Tests for kirby_cost.io.xml_utility.XMLUtility

Verifies XML reading/writing operations used for HDC file I/O.
"""

import pytest
from lxml import etree
from kirby_cost.io.xml_utility import XMLUtility


@pytest.fixture
def sample_element():
    """Create a sample XML element for testing."""
    root = etree.Element("POWER")
    root.set("XMLID", "ENERGYBLAST")
    root.set("BASECOST", "0")
    root.set("LEVELS", "10")
    root.set("LEVELCOST", "5")
    child = etree.SubElement(root, "NAME")
    child.text = "Energy Blast"
    notes = etree.SubElement(root, "NOTES")
    notes.text = "  Some notes  "
    empty = etree.SubElement(root, "EMPTY")
    return root


class TestGetValue:
    """get_value: tries child text first, then attribute."""

    def test_gets_attribute(self):
        elem = etree.Element("POWER")
        elem.set("XMLID", "FLIGHT")
        assert XMLUtility.get_value(elem, "XMLID") == "FLIGHT"

    def test_gets_child_text(self):
        elem = etree.Element("POWER")
        name = etree.SubElement(elem, "NAME")
        name.text = "My Power"
        assert XMLUtility.get_value(elem, "NAME") == "My Power"

    def test_child_text_preferred_over_attribute(self, sample_element):
        """If both child and attribute exist with same name, child wins."""
        # NAME exists as child with text "Energy Blast"
        assert XMLUtility.get_value(sample_element, "NAME") == "Energy Blast"

    def test_strips_whitespace(self, sample_element):
        assert XMLUtility.get_value(sample_element, "NOTES") == "Some notes"

    def test_missing_returns_empty(self, sample_element):
        assert XMLUtility.get_value(sample_element, "NONEXISTENT") == ""

    def test_none_element(self):
        assert XMLUtility.get_value(None, "ANYTHING") == ""

    def test_none_name(self, sample_element):
        assert XMLUtility.get_value(sample_element, None) == ""

    def test_empty_child_falls_through_to_attribute(self):
        """If child exists but has no text, try attribute."""
        elem = etree.Element("POWER")
        elem.set("XMLID", "FLIGHT")
        empty_child = etree.SubElement(elem, "XMLID")
        # Child has no text, so should fall through to attribute
        assert XMLUtility.get_value(elem, "XMLID") == "FLIGHT"


class TestGetChildText:
    """get_child_text: specifically reads child element text."""

    def test_gets_text(self, sample_element):
        assert XMLUtility.child_text(sample_element, "NAME") == "Energy Blast"

    def test_strips_whitespace(self, sample_element):
        assert XMLUtility.child_text(sample_element, "NOTES") == "Some notes"

    def test_missing_child(self, sample_element):
        assert XMLUtility.child_text(sample_element, "MISSING") == ""

    def test_none_element(self):
        assert XMLUtility.child_text(None, "NAME") == ""

    def test_empty_child(self, sample_element):
        assert XMLUtility.child_text(sample_element, "EMPTY") == ""


class TestGetAttribute:
    """get_attribute: reads XML attributes."""

    def test_gets_attribute(self, sample_element):
        assert XMLUtility.get_attribute(sample_element, "XMLID") == "ENERGYBLAST"

    def test_missing_attribute(self, sample_element):
        assert XMLUtility.get_attribute(sample_element, "MISSING") == ""

    def test_none_element(self):
        assert XMLUtility.get_attribute(None, "XMLID") == ""


class TestSetValue:
    """set_value: creates/replaces child element text."""

    def test_creates_child(self):
        elem = etree.Element("ROOT")
        XMLUtility.set_value(elem, "NAME", "Test")
        assert elem.find("NAME").text == "Test"

    def test_replaces_existing(self, sample_element):
        XMLUtility.set_value(sample_element, "NAME", "New Name")
        assert sample_element.find("NAME").text == "New Name"

    def test_none_value(self):
        elem = etree.Element("ROOT")
        XMLUtility.set_value(elem, "NAME", None)
        assert elem.find("NAME").text == ""


class TestSetAttribute:
    """set_attribute: sets XML attributes."""

    def test_sets_attribute(self):
        elem = etree.Element("ROOT")
        XMLUtility.set_attribute(elem, "ID", "123")
        assert elem.get("ID") == "123"

    def test_overwrites_attribute(self, sample_element):
        XMLUtility.set_attribute(sample_element, "XMLID", "FLIGHT")
        assert sample_element.get("XMLID") == "FLIGHT"


class TestGetChildren:
    """get_children: returns child elements, optionally filtered."""

    def test_all_children(self, sample_element):
        children = XMLUtility.children(sample_element)
        assert len(children) == 3  # NAME, NOTES, EMPTY

    def test_filtered_children(self, sample_element):
        children = XMLUtility.children(sample_element, "NAME")
        assert len(children) == 1
        assert children[0].text == "Energy Blast"

    def test_no_matching_children(self, sample_element):
        children = XMLUtility.children(sample_element, "MISSING")
        assert len(children) == 0

    def test_none_element(self):
        assert XMLUtility.children(None) == []


class TestHasChild:
    """has_child: checks for existence of child element."""

    def test_exists(self, sample_element):
        assert XMLUtility.has_child(sample_element, "NAME") is True

    def test_not_exists(self, sample_element):
        assert XMLUtility.has_child(sample_element, "MISSING") is False

    def test_none_element(self):
        assert XMLUtility.has_child(None, "NAME") is False


class TestHasAttribute:
    """has_attribute: checks for existence of XML attribute."""

    def test_exists(self, sample_element):
        assert XMLUtility.has_attribute(sample_element, "XMLID") is True

    def test_not_exists(self, sample_element):
        assert XMLUtility.has_attribute(sample_element, "MISSING") is False

    def test_none_element(self):
        assert XMLUtility.has_attribute(None, "XMLID") is False
