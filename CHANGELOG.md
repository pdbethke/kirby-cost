# Changelog

## 0.9.0 — 2026-11-24

### Added — `kirby_cost.builder`: make and change builds through the engine
For a campaign blending its changes over a codex base, and for an AI building NPCs, bases, vehicles and equipment (two-databases spec §4a). Every layer works on the **curated build doc** (`to_build_json` / `build_from_json`), the shape a relational store keeps, so an edit's payload is exactly one purchase's stored rows and blending never converts between shapes. The HDC element tree (`export(format="json")`) stays the import/export transport. Four layers, each usable alone:
- **Edits** (`apply(doc, [Replace | Add | Remove])`) on whole purchases, by HD's own `id`; a slot names its framework with `parent`; an add names its `Section` (an enum, now exported by `io.build_json`, which `_SECTION_TAG` derives from). Anything that does not fit is refused by name (`EditConflict`): an unknown id, a replacement that changes its id, a taken id (nested ones included), a purchase with no id, a `parent` naming nothing, a framework removed with slots still in it. The input doc is never changed. `ids(doc)` and `purchases(doc)` walk a doc.
- **Purchases by XMLID** (`buy(doc, Purchase(kind, xmlid, levels, name, option, adders, modifiers), template=...)`): the purchase states only what was chosen, every name checked against the template (`NotInTemplate`); costs come from the template when the build loads. A picked adder states `selected`, as HD saves it.
- **A new build** (`new_build(Template.VEHICLE, ...)`) holding exactly what HD gives a new character on that template, pinned to the headless oracle for seven templates.
- **A verdict** (`judge(doc)`): total and available points, and every problem in HD's words: a modifier `verifyModifiers()` refuses, or points over budget.

### Added — `HDTTemplateProvider.characteristics()`
The characteristics a new character on the template has, in HD's order: the template chain's own, after REMOVEs, by POSITION; never the earlier-edition fallback's (Main.hdt's COM, Vehicle.hdt's DEF).

### Fixed — a template's `<REMOVE>` is honoured
`Template.java` deletes each section's `<REMOVE>` ids from what the template inherited. The parser skipped them (and in CHARACTERISTICS and POWERS read `REMOVE` as an entry), so every specialised template kept all of Main6E: a Vehicle6E character carried CON, INT, EGO, PRE, OMCV, DMCV, REC, END and STUN. The provider now skips, in ancestors and fallbacks, what a descendant removed. A characteristic bought as a power is gated like every power (Hero.java:2856 restores it only for the template's characteristics). **Behaviour change:** a character on Vehicle6E, Base6E, Computer6E or AI6E holding a characteristic its template removes no longer pays for it; the own-character Vehicle6E copy in `tests/own_copy.py` now totals HD's 377.5 (was 429.5). Parity over the 655 oracle fixtures is unchanged.

## 0.8.4 — 2026-11-15

### Fixed — `CompoundPower.affects_characteristics()` no longer raises AttributeError
It called Java-style getters (`get_dex_increase()` and friends) that no Python object has, so asking any Compound Power with a part whether it is summable raised AttributeError (Ravel's "Wrap 'em and Nap 'em", Bokor's "Green Fungus Powder"). It now reads the parts' `*_increase` attributes, checking exactly the fields HD's CompoundPower.java does: STR through Leaping, not OCV/DCV/OMCV/DMCV or the custom slots.

## 0.8.3 — 2026-11-14

### Changed — no licensed character names
Comments, docstring examples and tests no longer name licensed Hero Games characters. Tests that loaded canon `.hdc` files by machine path now use the maintainer's own characters (Ravel, Bokor, PowerLad), or a temporary copy of one with the object under test added (`tests/own_copy.py`). No behaviour change.

## 0.8.2 — 2026-11-14

### Added — `slot_words(power, *, hero) -> str`: what a slot is, to tell it from its neighbours
HD's column-2 words for a framework slot with its Advantages kept, and without its name, its Limitations or the reserve's: `Blast 6d6, Reduced Endurance (0 END; +1/2)`, `Entangle 3d6, 6 PD/6 ED`, `+45 STR`. `step_display` says what a rung buys and leaves the Advantages out on purpose; two slots that are the same power at the same dice differ only in them, so a menu naming an unnamed slot by its alias ("Blast") could not tell them apart. Read off a copy; the slot is untouched. `hero` as for `ladder`.

## 0.8.1 — 2026-11-14

### Fixed — Skill Levels or a Talent bought in a Multipower slot no longer crash its ladder or its words
`ladder`, `levels_within` and `step_display` read `damage_display`, which only powers and characteristics have, so a slot holding Combat Skill Levels or a Talent (Lightning Reflexes) raised `AttributeError` and a fight with such a character failed at its opening split. Such a slot is now:
- **not laddered**: `ladder`/`levels_within` raise `NotLadderable`, so it is off or as bought, never a part-share;
- **worded in HD's column-2 words** by `step_display`, without its name or Limitations and without the reserve's own Limitations (`+1 with Block`, `Lightning Reflexes (+2 DEX to act first with All Actions)`), read off a copy so the slot itself is untouched.

## 0.8.0 — 2026-11-13

### Fixed — Killing damage is counted in Damage Classes, not half-die steps (6E2 p.99)
`augment_with_str` added STR to a Killing attack one half die per DC. A Killing DC is 5 Active Points: +1 pip, and 3 of them to the die. So STR 5 on a 1d6 HKA came out 1 1/2d6 where the book gives 1d6+1, STR 10 came out 2d6 where it gives 1 1/2d6, and the Doubling Rule capped a 1d6 HKA at 2 DC of STR instead of 3. A +1 pip (a 1d6+1 knife) was dropped entirely, because the function had no way to hear about it. Every HKA wielder whose STR isn't a multiple of 15 above the attack's own dice hit too hard.

### Changed (breaking) — `augment_with_str(dice, damage_type, strength) -> Dice`
It takes and returns a `Dice` rather than `(full, half)`, so the pips travel with the dice. A damage type other than `normal` or `killing` raises `ValueError` rather than being returned unchanged.

### Added — `kirby_cost.engine.damage`: one home for Damage Class arithmetic
- **`Dice(full, half, plus_one, minus_one)`**: every field required. `minus_one` is HD's MINUSONEPIP ("+1d6 -1"), whose die is already in `full`.
- **`damage_classes(dice, damage_type) -> int`**: Normal, one per whole die (a half die is not a DC, 6E2 p.101); Killing, 3 a die, 2 a half die, 1 a pip, -1 for the "+1d6 -1" rung (the Peacemaker's 2d6-1 is 5 DC).
- **`dice_for(dcs, damage_type) -> Dice`**: 6E2 p.99's table.
- **`add_damage_classes(dice, damage_type, added) -> Dice`**: 6E2 p.101, whole DCs "regardless of the type of damage": a Martial Strike takes a 3d6 club to 5d6 and a 1d6 HKA sword to 1 1/2d6.

## 0.7.0 — 2026-11-12

### Added — `kirby_cost.engine.allocation`: what a share of a slot buys
A Multipower's variable slot holds the points its owner gave it and has as many levels as fit them (6E1 p.404-406). The pricing belongs here, with the rest of the cost engine, and not in the combat engine that asks.

- **`levels_within(power, active_points, *, hero) -> LevelFit`**: the largest step of the power costing no more than the points, as a re-levelled, re-costed COPY (the original is never touched). Its own Advantages count: 30 points into a Flight bought at 50m with +1/4 Reduced Endurance buy 24m, not 30. Raises `ValueError` when no step fits.
- **`ladder(power, *, hero) -> list[LevelFit]`**: every breakpoint from nothing to the power as bought, ascending by Active Points, one step per distinct cost. At equal cost the step with the most levels wins (a power whose `level_value` is above 1 rounds its units up); at equal levels the whole-die step beats the half-die one. The top step is the power as bought. Resistant Protection and characteristics bought as powers ladder too.
- **`LevelFit`** (`power`, `levels`, `half_die`, `active_points`, `display`).
- **`NotLadderable`** (a `ValueError`): the power's cost is not driven by `levels` (Damage Reduction, Damage Negation), so it has no steps. A caller may still take it whole or not at all.
- **`step_display(power, *, hero)`**: what a power or a rung's copy reads as, in HD's own words: `Blast 6d6`, `Flight 30m`, `Power Defense 5 points`, `Resistant Protection 3 PD/3 ED`, `+5 PD`.
- **`hero` is required on all three** (keyword-only; `None` for a power on no hero). It is bound as `EngineContext`'s active hero while the steps are priced and worded, and whoever was active before is restored. An HKA's display carries HD's "w/STR" bracket, read off the active hero, so without it a process holding many heroes (a fight) worded Power Lad's claws "3d6 (3 1/2d6 w/STR)" or "3d6 (5 1/2d6 / 6 1/2d6 w/STR)" depending on which hero it had loaded last.
- **`Power.defence_levels_display()`** (`""` for every power but one bought as a defence split; `ForceField` overrides it) and **`Characteristic.levels_display()`**, both lifted out of `column2_output`, whose output is unchanged.

### Changed — `characteristic_states` reads a split reserve (6E1 p.404-406)
- **`LoadedHero.characteristic_states(xmlids, *, slots)`**: `slots` is now required. It maps a framework slot purchase's `id` to the purchase as the slot holds it (itself at full, or the copy `levels_within` priced for a share) or `None` for a slot holding nothing. A slot named there counts for what it holds, whatever HD's `AFFECTS_TOTAL` says (HD writes "No" on a slot because it is not always in play; the split says when, and how much); a slot not named is read as written; `{}` is the build as written. A key naming no purchase raises `KeyError`. Before this, a characteristic bought in a slot counted only as HD's flag said: Ravel's +30 STR "Reinforced String" and Power Lad's +45 STR "Just Like the Old Days..." are both `AFFECTS_TOTAL="No"` and never counted at any split.
- **`contribution_from_held_slot(obj)`** (`kirby_cost.model.activation`): `contribution_from_purchase` without the `AFFECTS_TOTAL` check; the Hero-identity condition a slot inherits from its framework still applies.
- `characteristic_state(xmlid)` and `temporal_characteristic` are unchanged: the build as written (`slots={}`). Their "a pooled slot OVERSTATES the character" caveat is replaced by the pointer to `slots`.

### Changed — `build_power_from_spec` reads a FORCEFIELD's split
A FORCEFIELD spec may give `pd_levels` / `ed_levels` / `md_levels` / `powd_levels`; HD writes `LEVELS` as their sum, so a spec giving only the split means that sum. A field left out is not bought, and an explicit `levels` wins. A FORCEFIELD spec with neither `levels` nor any split field raises `ValueError` rather than building a zero-level field.

## 0.6.5 — 2026-11-09

### Fixed — a Compound Power's parts keep their ids through the build doc
HD writes an `ID` on every part of a Compound Power. `to_build_json` emitted
the parts without one, so a rebuild gave each part a load-order counter: a
different id on every load, and a different `ID` in every `.hdc` written from
the doc. A consumer that names a power by its id (kirby-combat's attacks)
could not find a Compound part again in a build rebuilt from its doc. Each
part now carries its own id, as top-level objects always have. Cost parity is
unmoved (1817 passed).

## 0.6.4 — 2026-11-02

### Fixed — the build doc keeps a modifier's name
XMLID="MODIFIER" is HD's custom advantage or limitation, and its ALIAS is the
whole of its meaning. `Modifier.to_build_dict` emitted only the costs, so a
custom limitation reached a consumer as an anonymous value: the Destroid's
Self Destruct System kept its -2 and lost "Self Only", and a combat engine
offered it as an attack on someone else. Every modifier now carries `alias`
when it has one. Cost parity is unmoved: the name costs nothing.

## 0.6.3 — 2026-10-30

### Fixed — the build doc keeps which powers run off an Endurance Reserve
6E1 p.207: the character decides which powers draw on the Reserve. The loader
read HD's `USE_END_RESERVE` and the .hdc writer wrote it back, but
`to_build_json` / `build_from_json` dropped it, so every power rebuilt from a
build doc drew on personal END. The doc now writes `use_end_reserve: true` on
such a power (absent means personal END, as HD writes it). Cost parity is
unmoved: the flag costs nothing.

## 0.6.2 — 2026-10-05

### Fixed — the build doc stops forgetting three things
None of the three moved cost parity, which is why none was caught by it. All
merged on 2026-09-08 and unreleased until now.

- **`native_tongue` on a Language.** A native tongue is free, and the flag is
  the only thing that says so: the element still carries the option's base
  cost. The doc never wrote it, so Bokor rebuilt at 279 against his file's
  276. Written on every Language, true or false.
- **The `equipment` section.** Carried gear is loaded like powers but was not
  a doc section, so a character whose weapon is carried round-tripped
  unarmed.
- **Resistant Protection's `pd_levels` / `ed_levels` / `md_levels` /
  `powd_levels`.** Cost is by LEVELS, so the split moves no points, but it is
  which half is physical: Power Lad's 45 points rebuilt as 0/0. Written when
  non-zero.

Consumers that store the doc relationally need somewhere to keep all three,
or their rebuild differs from the engine's load.

## 0.6.1 — 2026-09-02

### Fixed
- **The build doc carries `AFFECTS_PRIMARY` / `AFFECTS_TOTAL`.** 0.6.0 made
  those flags decide whether a purchase contributes to a temporal
  characteristic, but the (legacy, curated) build doc did not emit them — so a
  consumer that stores the doc relationally and rebuilds from it took the class
  default of True and counted purchases HD keeps out of the character's totals.
  Measured downstream: a corpus villain's file carries a +2 DCV power marked
  `AFFECTS_TOTAL="No"`, and the database rebuilt him at DCV 12 where the
  canonical load says 10. Emitted only when False, since True is the default on
  both, so a character with nothing situational produces the same doc as
  before. Read from the raw attributes rather than the `affect_*` properties —
  `affect_total`'s getter writes to `affects_total`, and serialising a
  character is not allowed to change it.

  This is the flag-carrying half of 0.6.0's behaviour change. Consumers
  persisting the doc need columns for both, or they inherit the old answer.

## 0.6.0 — 2026-09-02

The theme is **one source of truth for what a build says**. Three places had
copies of a rule the engine already owned, and each copy was quietly wrong.

### Added
- **A front door and a back door.** `load_build(source, format=…)` and
  `hero.export(format=…)`, with formats registered (`@import_format` /
  `@export_format`) so adding one is additive rather than an edit to a
  dispatcher. Formats: `hdc` (bytes) and `json` (dict).
- **`kirby_cost.model.modifiers`** — `has_modifier` / `modifier_levels` /
  `find_modifier`, the one walk answering "does this modifier bind this
  purchase", with recursion through containers and inheritance from an
  enclosing purchase (minus PRIVATE modifiers).
- **`LoadedHero.characteristic_states(xmlids)`** — the whole stat block from
  one walk of the purchases. `characteristic_state(xmlid)` is that call with a
  single xmlid.
- **`tests/test_build_doc_fidelity.py`** — the JSON chain held to the same
  attribute-level property as the `.hdc` chain, sharing one survey
  (`tests/export_survey.py`) and carrying its own shrink-only ledger.

### Changed — this moves numbers
- **A purchase HD keeps out of the character's totals no longer contributes to
  a temporal characteristic.** `AFFECTS_PRIMARY` / `AFFECTS_TOTAL` is HD's own
  record of whether a purchase raises the characteristic or merely sits on the
  sheet as a situational ability, and it was not being read. A corpus villain's "Tail"
  +20 STR is `AFFECTS_TOTAL="No"` with its limitation aliased *"Only With
  Tail"* — a restrainable limb — and it was making him STR 80 instead of 60 in
  every calculation, thrown-object damage included. Ravel's pooled "Reinforced
  String" +30 STR is the same shape.
- **JSON is now a transport encoding of the HDC element tree, not a curated
  subset.** The build doc was hand-written in both directions while the XML
  side wrote from declared descriptors, so five fields had been lost one at a
  time (TEXT, NOTES, a power's NAME, a modifier's ALIAS, AFFECTS_PRIMARY /
  AFFECTS_TOTAL) — all cost-neutral, and the doc's only gate compared summed
  cost. Measured over 794 corpus characters, `.hdc → hero → json → hero →
  .hdc` went from **0/794 clean to 791/794**, the same score the `.hdc` chain
  gets, with the same two `matches_hd` entries.
- **HD's element IDs survive the JSON trip.** They were replaced by synthetic
  `O<n>`, so a character came back as a document HD would not recognise, every
  `PARENTID` target renamed. `extract_costs` keys `per_object` by the same rule,
  or those keys join to nothing.

### Fixed
- `BuildNode` had no `.attrib`, so a campaign's whole `RULES` block took the
  character down on the JSON path while the `.hdc` path loaded it fine.
- `hero_to_element` re-appends preserved elements with `deepcopy` and lxml
  rejects a `BuildNode`: 15 corpus characters carrying an embedded template
  failed to write at all.
- Statedness (which attributes the source stated, in its order) is carried
  through the JSON encoding. Without it every explicitly-stated empty value
  (`NAME=""`) was dropped and a dozen defaults per element invented.
- `source_encoding` rides in the JSON envelope; two characters came back
  XML-identical and byte-different without it.
- `ChangeEnvironment.can_add` removed. It called a `super().can_add` that
  exists nowhere, so any call raised `AttributeError`, while its docstring
  advertised logic its body (`return True`) did not contain. Nothing called it.

### Unchanged
- **Oracle parity: 656/656, residual ledger empty.** None of this touches the
  cost path — `characteristic_value` is untouched and remains what costs derive
  from. Suite 1798 passing.
