#!/usr/bin/env python3
"""Debug DETECT cost calculation in Python."""
import os, sys, json, subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kirby_cost.io.hdc_loader import HDCLoader

HD6CLI = os.path.join(os.path.dirname(__file__), '..', '..', 'kirby-hd-oracle', 'hd6cli.sh')

def debug_file(hdc_path, target_xmlid):
    loader = HDCLoader()
    hero = loader.load_file(hdc_path)

    # Get Java oracle
    r = subprocess.run([HD6CLI, hdc_path], capture_output=True, text=True, timeout=30)
    out = r.stdout
    oracle = json.loads(out[out.find('{'):])
    java_powers = [p for p in oracle['powers'] if p.get('xmlid') == target_xmlid]

    py_idx = 0
    for p in hero.powers:
        if p.get_xmlid() != target_xmlid:
            continue

        java_p = java_powers[py_idx] if py_idx < len(java_powers) else None
        py_idx += 1

        name = p.name or p.alias or p.get_xmlid()
        print(f"\n=== {name} (XMLID={p.get_xmlid()}) ===")
        print(f"  Python class: {type(p).__name__}")
        print(f"  Java class:   {java_p.get('class', '?') if java_p else '?'}")
        print(f"  base_cost:  py={p.base_cost}  java={java_p.get('base_cost', '?') if java_p else '?'}")
        print(f"  levels:     py={p.levels}  java={java_p.get('levels', '?') if java_p else '?'}")
        print(f"  level_cost: py={p.level_cost}  java={java_p.get('level_cost', '?') if java_p else '?'}")
        print(f"  level_value:py={p.level_value}  java={java_p.get('level_value', '?') if java_p else '?'}")
        print(f"  total_cost: py={p.get_total_cost()}  java={java_p.get('total_cost', '?') if java_p else '?'}")
        print(f"  active_cost:py={p.get_active_cost()}  java={java_p.get('active_cost', '?') if java_p else '?'}")
        print(f"  real_cost:  py={p.get_real_cost_pre_list()}  java={java_p.get('real_cost', '?') if java_p else '?'}")

        adders = p.get_assigned_adders()
        java_adders = java_p.get('adders', []) if java_p else []
        print(f"  Adders ({len(adders)} py, {len(java_adders)} java):")
        for i, a in enumerate(adders):
            ja = java_adders[i] if i < len(java_adders) else None
            print(f"    [{i}] {a.get_xmlid()}: base={a.base_cost} selected={a._selected} cost={a.get_total_cost()}", end="")
            if ja:
                print(f"  | java: base={ja.get('base_cost','?')} selected={ja.get('selected','?')} cost={ja.get('total_cost','?')}", end="")
            print()

SHARK = os.path.join(os.path.dirname(__file__), '..', '..',
    'champions-campaign-manager/resources/bestiary/HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/CHAPTER_6/SHARKS/MAKO_SHARK_HSB.hdc')
EAGLE = os.path.join(os.path.dirname(__file__), '..', '..',
    'champions-campaign-manager/resources/bestiary/HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/CHAPTER_6/BIRDS_OF_PREY/EAGLE_HAWK_HSB.hdc')

print("=== DETECT (Mako Shark) ===")
debug_file(SHARK, "DETECT")

print("\n\n=== TELESCOPIC (Eagle/Hawk) ===")
debug_file(EAGLE, "TELESCOPIC")
