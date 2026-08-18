"""
Skill Enhancer classes for kirby-cost.

Converted from com.hero.objects.enhancers.Enhancer.java

Scholar, Scientist, Linguist, Traveler and Jack of All Trades: the five
objects that discount a family of skills rather than doing anything themselves.

**These serialize as themselves, not as skills.** HD writes an enhancer under
its own tag with exactly one attribute of its own::

    <SCHOLAR XMLID="SCHOLAR" ID="1270862156409" ... INTBASED="NO">

``Skill.getSaveXML`` sets the tag to ``SKILL`` and adds CHARACTERISTIC,
FAMILIARITY and PROFICIENCY, which is right for a skill and wrong for these —
in Java they never reach it, because ``Enhancer extends List``, not ``Skill``.
Here they do reach it, so 84 corpus characters exported their enhancers as
``<SKILL CHARACTERISTIC="GENERAL" FAMILIARITY="No" PROFICIENCY="No">``: three
attributes HD never wrote, in place of the INTBASED it did, under the wrong
tag.

They stay ``Skill`` subclasses on the Python side rather than following Java
onto ``List``. The discount is applied by ``CostMixin._apply_enhancer_savings``,
which scans ``hero.skills`` for these xmlids, and the costs it produces match
the oracle on every character in the corpus. Moving the class would move that
for no gain the document can see: what was wrong here is what gets WRITTEN, and
that is the whole of what this fixes.
"""

from kirby_cost.engine.xml_attrs import XMLAttr
from kirby_cost.objects.skills.skill import Skill


class Enhancer(Skill):
    """A skill enhancer, saved as HD saves it.

    Ported from ``Enhancer.getSaveXML``/``restoreFromSave``: the element takes
    the enhancer's own XMLID as its tag and carries INTBASED, which HD writes
    in upper case ("YES"/"NO") unlike the "Yes"/"No" it uses everywhere else.
    """

    #: Java's Enhancer.restoreFromSave reads INTBASED and nothing else.
    XML_ATTRS = (
        XMLAttr("INTBASED", "int_based", "yesno",
                format_with=lambda v: "YES" if v else "NO"),
    )

    def __init__(self, xmlid: str = None):
        super().__init__(xmlid or type(self).XMLID)
        #: Enhancer.java:46 — `protected boolean intBased = false`.
        self.int_based: bool = False

    def get_save_xml(self):
        """The enhancer's own tag, and INTBASED — not a skill's attributes."""
        element = self.get_general_save_xml()
        element.tag = self.xmlid
        return element


class Scholar(Enhancer, xmlid="SCHOLAR"):
    """Scholar — discounts Knowledge Skills."""


class Scientist(Enhancer, xmlid="SCIENTIST"):
    """Scientist — discounts Sciences."""


class Linguist(Enhancer, xmlid="LINGUIST"):
    """Linguist — discounts Languages."""


class Traveler(Enhancer, xmlid="TRAVELER"):
    """Traveler — discounts Area Knowledges."""


class JackOfAllTrades(Enhancer, xmlid="JACK_OF_ALL_TRADES"):
    """Jack of All Trades — discounts Professional Skills."""
