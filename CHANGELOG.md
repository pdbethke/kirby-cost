# Changelog

## 0.6.1 — 2026-09-02

### Fixed
- **The build doc carries `AFFECTS_PRIMARY` / `AFFECTS_TOTAL`.** 0.6.0 made
  those flags decide whether a purchase contributes to a temporal
  characteristic, but the (legacy, curated) build doc did not emit them — so a
  consumer that stores the doc relationally and rebuilds from it took the class
  default of True and counted purchases HD keeps out of the character's totals.
  Measured downstream: `Cobra.hdc` carries a +2 DCV power marked
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
  sheet as a situational ability, and it was not being read. Gorgon's "Tail"
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
