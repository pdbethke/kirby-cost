"""Temporary copies of the maintainer's own characters, with objects added.

Tests that need a feature none of Ravel, Bokor or PowerLad has build it on a
copy: parse the bundled .hdc, change the header or append XML, write to
``tmp_path`` and load that. The bundled files are never modified. Same pattern
as the ``slotted`` / ``blasts`` fixtures in ``test_allocation.py``; this module
is where the helper lives so every test does it the same way.
"""
from pathlib import Path
from typing import Iterable, Optional

from lxml import etree

from tests.corpus import require_authored_hdc


def own_copy(
    tmp_path: Path,
    character: str = "PowerLad",
    *,
    template: Optional[str] = None,
    section_xml: Iterable[tuple[str, str]] = (),
    filename: Optional[str] = None,
) -> str:
    """Write a modified copy of an own character; return its path.

    ``template`` replaces the ``TEMPLATE`` attribute (``"builtIn.Vehicle6E.hdt"``).
    ``section_xml`` is ``(section, xml)`` pairs: each ``xml`` string is parsed
    and appended to the character's ``section`` element (``"POWERS"``,
    ``"CHARACTERISTICS"``, ``"SKILLS"``, ...).
    """
    root = etree.parse(str(require_authored_hdc(character))).getroot()
    if template is not None:
        root.set("TEMPLATE", template)
    for section, xml in section_xml:
        root.find(section).append(etree.fromstring(xml))
    out = tmp_path / (filename or f"{character}-copy.hdc")
    out.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    return str(out)


SIZE_4 = ('<SIZE XMLID="SIZE" ID="9000000000001" BASECOST="0.0" LEVELS="4" '
          'ALIAS="Size" POSITION="0" MULTIPLIER="1.0" />')
FLIGHT_10 = ('<POWER XMLID="FLIGHT" ID="9000000000002" BASECOST="0.0" LEVELS="10" '
             'ALIAS="Flight" POSITION="99" MULTIPLIER="1.0" QUANTITY="1" '
             'AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes" />')


def vehicle_copy(tmp_path: Path, template: str = "builtIn.Vehicle6E.hdt") -> str:
    """PowerLad re-declared on ``template`` with SIZE 4 and Flight 10" added.

    The corpus has no vehicle among the maintainer's own characters, and a
    vehicle is what the template-resolution tests need: Vehicle6E defines SIZE
    (5/level), prices PD/ED at 3 per 2 and states ``USESEND="No"`` on FLIGHT.
    Pass another ``template`` for the same character costed against the
    maintainer's own template instead.
    """
    return own_copy(
        tmp_path,
        template=template,
        section_xml=[("CHARACTERISTICS", SIZE_4), ("POWERS", FLIGHT_10)],
        filename=f"PowerLad-{template.split('.')[1]}.hdc",
    )


# ── martial arts ────────────────────────────────────────────────────────────
MARTIAL_DODGE = (
    '<MANEUVER XMLID="MANEUVER" ID="9000000000070" BASECOST="4.0" LEVELS="0" '
    'ALIAS="Martial Dodge" POSITION="2" MULTIPLIER="1.0" NAME="" CATEGORY="Hand To Hand" '
    'DISPLAY="Martial Dodge" OCV="--" DCV="+5" DC="0" PHASE="1/2" '
    'EFFECT="Dodge all attacks, Abort" ADDSTR="No" ACTIVECOST="-20" DAMAGETYPE="0" '
    'MAXSTR="0" STRMULT="1" USEWEAPON="No" />')
EXTRA_DC_2 = (
    '<EXTRADC XMLID="EXTRADC" ID="9000000000071" BASECOST="0.0" LEVELS="2" '
    'ALIAS="+2 HTH Damage Class(es)" POSITION="3" MULTIPLIER="1.0" NAME="" />')


def ravel_with_martial_dodge(tmp_path: Path) -> str:
    """Ravel (who owns Grappling Block and Joint Lock/Throw) plus Martial Dodge
    and +2 HTH damage classes -- the martial-arts section the build-doc
    round-trip tests need: three maneuvers, one with a '--' OCV, and an EXTRADC.
    """
    return own_copy(
        tmp_path, "Ravel",
        section_xml=[("MARTIALARTS", MARTIAL_DODGE), ("MARTIALARTS", EXTRA_DC_2)],
        filename="Ravel-martial-dodge.hdc",
    )


# ── a Trigger whose Reset adder carries an explicit BASECOST="0.0" ──────────
TRIGGERED_TELEPORT = (
    '<POWER XMLID="TELEPORTATION" ID="9000000000080" BASECOST="0.0" LEVELS="10" '
    'ALIAS="Teleportation" POSITION="99" MULTIPLIER="1.0" NAME="Staying Out Of Reach" '
    'QUANTITY="1" AFFECTS_PRIMARY="Yes" AFFECTS_TOTAL="Yes">'
    '<MODIFIER XMLID="TRIGGER" ID="9000000000081" BASECOST="0.25" LEVELS="0" ALIAS="Trigger" '
    'POSITION="-1" MULTIPLIER="1.0" OPTION="SET" OPTIONID="SET" OPTION_ALIAS="Set Trigger" '
    'PRIVATE="No" FORCEALLOW="No">'
    '<ADDER XMLID="ACTIVATION" ID="9000000000082" BASECOST="0.0" LEVELS="0" '
    'ALIAS="Activation Modifiers" POSITION="-1" MULTIPLIER="1.0" OPTION="ZEROPHASE" '
    'OPTIONID="ZEROPHASE" SHOWALIAS="Yes" PRIVATE="No" REQUIRED="Yes" INCLUDEINBASE="No" '
    'DISPLAYINSTRING="Yes" GROUP="No" SELECTED="YES" />'
    '<ADDER XMLID="RESET" ID="9000000000083" BASECOST="0.0" LEVELS="0" '
    'ALIAS="Reset Parameters" POSITION="-1" MULTIPLIER="1.0" OPTION="HALFPHASE" '
    'OPTIONID="HALFPHASE" SHOWALIAS="Yes" PRIVATE="No" REQUIRED="Yes" INCLUDEINBASE="No" '
    'DISPLAYINSTRING="Yes" GROUP="No" SELECTED="YES" />'
    '</MODIFIER></POWER>')


def powerlad_with_triggered_teleport(tmp_path: Path) -> str:
    """PowerLad plus a Teleportation whose Trigger resets on a Half Phase --
    the one Reset option that costs nothing, so its BASECOST="0.0" is explicit
    and differs from the template's default for RESET."""
    return own_copy(
        tmp_path, section_xml=[("POWERS", TRIGGERED_TELEPORT)],
        filename="PowerLad-triggered-teleport.hdc",
    )
