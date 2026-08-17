"""Round-trip validation: load HDC -> save -> reload -> compare costs."""
from tests.corpus import corpus_root
import sys, tempfile, os
from pathlib import Path
from kirby_cost.io.hdc_loader import HDCLoader
from lxml import etree

def snapshot(hero):
    costs = {}
    for section_name, section in [
        ('chars', hero.characteristics), ('powers', hero.powers),
        ('skills', hero.skills), ('perks', hero.perks),
        ('talents', hero.talents), ('complications', hero.complications)
    ]:
        for i, obj in enumerate(section):
            key = f"{section_name}[{i}] {obj.xmlid}"
            try: tc = obj.total_cost
            except: tc = -999
            try: ac = obj.active_cost
            except: ac = -999
            try: rc = obj.real_cost
            except: rc = -999
            costs[key] = (tc, ac, rc)
    return costs

def export_hero(hero):
    """Export hero to HDC XML string using get_save_xml()."""
    root = etree.Element("CHARACTER")
    root.set("TEMPLATE", getattr(hero, 'template_name', 'Main6E.hdt') or 'Main6E.hdt')
    root.set("version", "6.0")

    # Basic configuration
    basic_config = etree.SubElement(root, "BASIC_CONFIGURATION")
    basic_config.set("BASE_POINTS", str(getattr(hero, 'base_points', 400)))
    basic_config.set("DISAD_POINTS", str(getattr(hero, 'disad_points', 75)))
    basic_config.set("EXPERIENCE", str(getattr(hero, 'experience', 0)))
    basic_config.set("RULES", "Default")

    # Character info
    info = etree.SubElement(root, "CHARACTER_INFO")
    info.set("CHARACTER_NAME", hero.name or "")
    info.set("ALTERNATE_IDENTITIES", getattr(hero, 'alternate_identities', '') or "")
    info.set("PLAYER_NAME", getattr(hero, 'player_name', '') or "")
    info.set("HEIGHT", str(getattr(hero, 'height', 0.0)))
    info.set("WEIGHT", str(getattr(hero, 'weight', 0.0)))
    info.set("HAIR_COLOR", getattr(hero, 'hair_color', '') or "")
    info.set("EYE_COLOR", getattr(hero, 'eye_color', '') or "")
    info.set("CAMPAIGN_NAME", getattr(hero, 'campaign_name', '') or "")
    info.set("GENRE", getattr(hero, 'genre', '') or "")
    info.set("GM", getattr(hero, 'gm', '') or "")

    # Biography text fields
    for field in ("BACKGROUND", "PERSONALITY", "QUOTE", "TACTICS",
                  "CAMPAIGN_USE", "APPEARANCE",
                  "NOTES1", "NOTES2", "NOTES3", "NOTES4", "NOTES5"):
        child = etree.SubElement(info, field)
        val = getattr(hero, field.lower(), '')
        if val:
            child.text = val

    # Image
    image_data = getattr(hero, 'image_data', '')
    if image_data:
        image_elem = etree.SubElement(root, "IMAGE")
        image_elem.set("FILENAME", getattr(hero, 'image_filename', '') or "")
        image_elem.text = image_data

    # Rules
    rules_elem = etree.SubElement(root, "RULES")
    if hero.rules and hero.rules._language_similarities_used:
        rules_elem.set("LANGUAGESIMILARITIESUSED", "Yes")

    sections = [
        ("CHARACTERISTICS", hero.characteristics),
        ("POWERS", hero.powers),
        ("SKILLS", hero.skills),
        ("PERKS", hero.perks),
        ("TALENTS", hero.talents),
        ("DISADVANTAGES", hero.complications),
    ]
    for tag, objects in sections:
        section = etree.SubElement(root, tag)
        for obj in objects:
            try:
                elem = obj.get_save_xml()
                if elem is not None:
                    section.append(elem)
            except Exception as e:
                print(f"  WARN: {obj.xmlid} save failed: {e}")

    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True)

def roundtrip_test(hdc_path):
    loader = HDCLoader()
    hero1 = loader.load_file(str(hdc_path))
    orig = snapshot(hero1)

    xml_bytes = export_hero(hero1)

    tmp = tempfile.NamedTemporaryFile(suffix=".hdc", delete=False, mode='wb')
    tmp.write(xml_bytes)
    tmp.close()

    try:
        loader2 = HDCLoader()
        hero2 = loader2.load_file(tmp.name)
        reloaded = snapshot(hero2)
    finally:
        os.unlink(tmp.name)

    mismatches = []
    matched = 0
    for key in orig:
        if key not in reloaded:
            mismatches.append(f"  {key}: MISSING")
            continue
        o_tc, o_ac, o_rc = orig[key]
        r_tc, r_ac, r_rc = reloaded[key]
        if o_tc == -999 or r_tc == -999:
            continue
        if abs(o_tc - r_tc) > 0.5 or abs(o_ac - r_ac) > 0.5 or abs(o_rc - r_rc) > 0.5:
            mismatches.append(f"  {key}: tc={o_tc}->{r_tc}, ac={o_ac}->{r_ac}, rc={o_rc}->{r_rc}")
        else:
            matched += 1

    return hero1.name, len(orig), matched, mismatches

# Test against all oracle fixture characters
resource_dir = (corpus_root() or Path("/nonexistent"))
hdcs = sorted(resource_dir.rglob("*.hdc"))
total_chars = 0
total_matched = 0
total_mismatched = 0
failed_chars = []

for hdc in hdcs:
    if "__MACOSX" in str(hdc):
        continue
    try:
        name, count, matched, mismatches = roundtrip_test(hdc)
        total_chars += 1
        total_matched += matched
        total_mismatched += len(mismatches)
        if mismatches:
            failed_chars.append((name, count, matched, mismatches))
    except Exception as e:
        pass

print(f"\n=== ROUND-TRIP RESULTS ===")
print(f"Characters tested: {total_chars}")
print(f"Objects matched:   {total_matched}")
print(f"Objects mismatched: {total_mismatched}")
print(f"Characters with issues: {len(failed_chars)}")
if failed_chars:
    for name, count, matched, mismatches in failed_chars[:10]:
        print(f"\n  {name} ({matched}/{count} matched, {len(mismatches)} issues):")
        for m in mismatches[:5]:
            print(f"    {m}")
        if len(mismatches) > 5:
            print(f"    ... and {len(mismatches) - 5} more")
