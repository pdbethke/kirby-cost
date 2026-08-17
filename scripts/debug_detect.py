#!/usr/bin/env python3
"""Debug script to investigate DETECT and TELESCOPIC issues."""
import subprocess, json, os, sys

sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), '..')))

HD6CLI = os.path.join(os.path.dirname(__file__), '..', '..', 'kirby-hd-oracle', 'hd6cli.sh')
SHARK = os.path.join(os.path.dirname(__file__), '..', '..',
    'champions-campaign-manager/resources/bestiary/HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/CHAPTER_6/SHARKS/MAKO_SHARK_HSB.hdc')
EAGLE = os.path.join(os.path.dirname(__file__), '..', '..',
    'champions-campaign-manager/resources/bestiary/HERO_System_Bestiary_6th_Edition_Character_Pack/HSB HD Files/CHAPTER_6/BIRDS_OF_PREY/EAGLE_HAWK_HSB.hdc')

def debug_java(hdc_path, name):
    r = subprocess.run([HD6CLI, '--debug', hdc_path, name],
                       capture_output=True, text=True, timeout=30)
    print(f"=== Java debug for {name} in {os.path.basename(hdc_path)} ===")
    print(r.stdout)
    if r.returncode != 0:
        print("STDERR:", r.stderr[:500])

def dump_java(hdc_path, xmlid):
    r = subprocess.run([HD6CLI, hdc_path], capture_output=True, text=True, timeout=30)
    out = r.stdout
    data = json.loads(out[out.find('{'):])
    for p in data['powers']:
        if p.get('xmlid') == xmlid:
            print(json.dumps(p, indent=2))

print("--- DETECT debug (Mako Shark - Electrosense) ---")
debug_java(SHARK, 'Electrosense')

print("\n--- TELESCOPIC debug (Eagle/Hawk - Eagle Eyes) ---")
debug_java(EAGLE, 'Eagle')
