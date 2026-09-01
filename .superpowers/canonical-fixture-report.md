# Canonical fixture correction — `fix/skill-characteristic-linkage`

*2026-09-01*

## The question

"Does not canonical imply default?" It did not. `HDCLoader` is this project's
canon — 100% Java-oracle parity, and the only path that reads what HERO
Designer actually wrote. But the skill-roll tests on this branch asserted
against `tests/fixtures/authored/Ravel.json`, an **oracle dump**, and the one
test that loaded through the canonical path was gated on `KIRBY_COST_AUTHORED`,
which nothing set. Sixteen dump-based tests ran; the faithful one did not.

The dump is lossy in two ways that matter:

1. It omits `CHARACTERISTIC` on every skill.
2. It does not record which ITEM a multi-ITEM skill (`PROFESSIONAL_SKILL`,
   `SCIENCE_SKILL`) was bought as, so the engine can only take the template's
   first.

That produced two false alarms in one evening — five "proficiency regressions"
and two "multi-ITEM build-doc gaps" — both of which evaporate on a real load.

## What changed

**1. The characters are bundled.** `tests/fixtures/authored/` now holds three
`.hdc` files, verified by `CHARACTER_NAME` before copying:

| file | bytes | `CHARACTER_NAME` |
|---|---|---|
| `Ravel.hdc` | 172,400 | `Ravel, The Unmade Man` |
| `Bokor.hdc` | 140,178 | `Bokor` |
| `PowerLad.hdc` | 85,944 | `Power Lad` |

md5 verified identical to the originals. **Nothing else was copied** from
`~/Documents/Champions` — not `Ravel_background.hdc`, not `Ravel (CSI Kit).hdc`,
not any licensed third-party character. `.gitignore` gained explicit
`!` negations for exactly these three plus a comment saying three files, no
more, so tightening `tests/fixtures/*.hdc` later cannot silently drop them and
a fourth cannot be added by accident.

**2. `authored_hdc()` finds them with no environment variable.**
`tests/corpus.py` gained `BUNDLED_AUTHORED`; `authored_hdc(name)` checks
`KIRBY_COST_AUTHORED` first and falls back to the bundle. The override is
per-name, so a maintainer pointing at his own store still gets his working
copies, and a name that store lacks still resolves.

**3. A missing canonical fixture FAILS.** New `require_authored_hdc(name)`
raises `FileNotFoundError` naming the bundled path. The canonical tests carry
**no skip guard at all** — in `test_skill_characteristic_roll.py`,
`test_campaign_cost_fields.py`, and `test_authored_characters.py`'s `_cases()`.
These files are tracked, so absence is a deletion, not an unconfigured machine.

**4. The skip guard was ARMED, not bypassed.** `conftest.py`'s design is
untouched: it still reads `INPUTS` twice, to report what a run was configured
with and to decide whether a skip is acceptable or a defect.
`KIRBY_COST_AUTHORED` stays in `INPUTS` — it is still honoured as an override.
What changed is `missing_inputs()`: via `_BUNDLE_SATISFIES`, an input the
repository itself carries is no longer "missing". That tightens the guard
rather than loosening it. The run header on this machine now reads:

```
kirby-cost: all 9 inputs present — any skip will fail the run
```

Before, it reported `KIRBY_COST_AUTHORED` missing and the guard excused all 14
skips. Three tests in `test_test_inputs.py` pin the new contract (bundle
satisfies; variable still overrides; missing bundle raises).

**5. The tests moved to the canonical path.** `test_skill_characteristic_roll.py`
is now explicitly two-lane, and says which lane each test is in:

- **Canonical** — the `ravel` fixture is `HDCLoader().load_file(...)`,
  function-scoped and reloaded per test on purpose, because `load_file`
  *installs the active hero* and `roll_value`'s characteristic branch reads it.
  Caching it would be correct only until another test loaded another character.
- **Degraded, deliberately** — the `ravel_dump` fixture builds from the JSON
  dump, and is the only shape in which the template fallback fires at all
  (across the 655-character corpus it fires on zero of 4,434 skill-like
  objects). `test_the_dump_states_no_characteristic_at_all` pins that premise,
  so the fallback tests cannot go on passing while testing nothing. The
  familiarity/Everyman short-circuit tests keep building from a mutated doc,
  labelled as such.

**6. The test that would have caught tonight.**
`test_ravel_reproduces_every_roll_hero_designer_printed` loads Ravel
canonically and asserts sixteen skill rolls against HD's own rendered output.
`test_the_transcribed_rolls_are_still_the_ones_hero_designer_printed`
re-derives that table from the dump's `column2_output` so the transcription
cannot rot into a test of a typo. Seven of the sixteen — the five Proficiencies
and both multi-ITEM skills — are precisely the cases a dump-based test cannot
state.

## Ravel against HD's printed rolls, via the canonical loader

Every skill for which HD renders a roll. **16 of 16 agree, 0 mismatched.**

| skill | characteristic | engine | HD printed |
|---|---|---|---|
| PROFESSIONAL_SKILL | INT | 14 | 14 |
| SCIENCE_SKILL | INT | 14 | 14 |
| DEDUCTION | INT | 14 | 14 |
| CRIMINOLOGY | INT | 14 | 14 |
| FORENSIC_MEDICINE | INT | 14 | 14 |
| PARAMEDICS | INT | 14 | 14 |
| COMPUTER_PROGRAMMING | INT | 14 | 14 |
| NAVIGATION | INT | 14 | 14 |
| ACTING | PRE | 13 | 13 |
| CHARM | PRE | 13 | 13 |
| KNOWLEDGE_SKILL | GENERAL | 13 | 13 |
| HIGH_SOCIETY | PRE | 10 | 10 |
| BUREAUCRATICS | PRE | 10 | 10 |
| SECURITY_SYSTEMS | INT | 10 | 10 |
| STREETWISE | PRE | 10 | 10 |
| INTERROGATION | PRE | 10 | 10 |

`LANGUAGES` and `SKILL_LEVELS` are excluded because HD renders no roll for
either, and the provenance test asserts that exclusion set exactly.

The five Proficiencies sit at 10 despite PRE/INT linkage: `roll_value`
short-circuits on the proficiency flag before it consults the characteristic
(6E1 p57 sets the linked base; a Proficiency is bought as a flat roll).

## Gates

**Oracle (release gate):** `656 passed`, exit 0.
`tests/fixtures/oracle_known_residuals.json` untouched — `git status` reports
no modification to it.

**Full suite**, `KIRBY_COST_HDT` pointed at the complete 17-template directory:

| | passed | skipped |
|---|---|---|
| before (stashed working tree) | 1732 | **14** |
| after | **1753** | **0** |

The 14 skips were all `KIRBY_COST_AUTHORED unset`: 12 in
`test_authored_characters.py` (4 parametrized tests x 3 characters), 1 in
`test_campaign_cost_fields.py`, 1 in `test_skill_characteristic_roll.py`.
All 14 now run. **Zero skips remain.**

+21 net passing: 12 previously-skipped authored tests + 2 previously-skipped
canonical tests, plus the new canonical and provenance tests in
`test_skill_characteristic_roll.py` and three new guard tests in
`test_test_inputs.py`, less the dump-based tests that were folded into the
canonical ones.

## The caution that did not fire

`test_authored_characters.py` compares each `.hdc` against its JSON fixture on
every cost and every display string, for all three characters. Those twelve
tests had never run in this environment. **They pass on first run** — no
disagreement between the real files and the dumps on anything those tests
compare. That is a genuinely useful negative result: the dumps are faithful on
*costs and strings*, and lossy specifically on the **skill characteristic
linkage and multi-ITEM selection**, which is the narrow seam this branch is
about. Nothing was adjusted to make anything pass.

## Not touched

`Hero.characteristic_value()` — unchanged.
`tests/fixtures/oracle_known_residuals.json` — unchanged.
`conftest.py` — unchanged; the guard mechanism it implements is now armed by
default rather than modified.

---

# Fix round — the licensing rail was inert

*2026-09-01, after review*

## What was wrong

The three `!tests/fixtures/authored/*.hdc` negations I added were **inert**,
and worse than inert: they were a claim of protection where none existed.

The pre-existing pattern is `tests/fixtures/*.hdc`. A single `*` does not
cross a directory separator, so that line never reached
`tests/fixtures/authored/` at all. Nothing there was ever ignored, so
negating it re-admitted nothing. The three bundled files stayed tracked for
the same reason they would have without any of my lines: they were never
matched.

The consequence is the part that mattered. A licensed third-party `.hdc`
dropped into `tests/fixtures/authored/` would have been picked up by
`git add -A` with no warning — the exact failure the comment above it claimed
to prevent. My report said a fourth file "cannot be added by accident" and the
SKILL.md said the three were "explicitly un-ignored". Both described a
mechanism that was not running. A false assurance on the rail that keeps
licensed content out of a public repo is worse than no claim at all, because
it stops anyone from checking.

## The fix

One line, above the negations, which is what makes them load-bearing:

```
tests/fixtures/oracle/
tests/fixtures/*.hdc
tests/fixtures/**/*.hdc      <-- added
tests/fixtures/roundtrip_hd6_costs.json
...
!tests/fixtures/authored/Ravel.hdc
!tests/fixtures/authored/Bokor.hdc
!tests/fixtures/authored/PowerLad.hdc
```

Deny every `.hdc` anywhere under `tests/fixtures/`, then re-admit exactly
three by name. The surrounding comment now says *why* the `**` line exists and
tells the next reader to verify with `git check-ignore -v` rather than trust
the prose — since trusting the prose is what went wrong here.

## Proof, run after the change

```
$ git check-ignore -v "tests/fixtures/authored/Ravel_background.hdc"
.gitignore:75:tests/fixtures/**/*.hdc	tests/fixtures/authored/Ravel_background.hdc
exit=0

$ git check-ignore -v "tests/fixtures/authored/Ravel (CSI Kit).hdc"
.gitignore:75:tests/fixtures/**/*.hdc	tests/fixtures/authored/Ravel (CSI Kit).hdc
exit=0

$ git ls-files tests/fixtures/ | grep hdc
tests/fixtures/authored/Bokor.hdc
tests/fixtures/authored/PowerLad.hdc
tests/fixtures/authored/Ravel.hdc

$ git status --porcelain
 M .gitignore
 M .superpowers/canonical-fixture-report.md
 M tests/test_skill_characteristic_roll.py
```

Both licensed names are now ignored, and `.gitignore:75` names the line doing
it. Exactly the three bundled files remain tracked. The porcelain output shows
only this fix round's own edits and no stray `.hdc`.

**Live drill, not just a dry check.** I copied the real
`Ravel_background.hdc` into `tests/fixtures/authored/`, ran `git add -A .`,
and confirmed the staged set:

```
$ git diff --cached --name-only | grep hdc
NONE STAGED
```

The file was physically present in the directory and `git add -A` did not
stage it. Removed afterwards; the directory holds the three bundled `.hdc`
and their four `.json` fixtures again.

## Minors

- "fifteen skill rolls" corrected to **sixteen** in both places in this
  report. `HD_PRINTED_ROLLS` has sixteen entries and the table above lists
  sixteen rows; the prose was simply wrong.
- `test_the_transcribed_rolls_are_still_the_ones_hero_designer_printed` no
  longer takes the `ravel` fixture. It reads HD's rendered output and the
  transcription and never loads a character, so the parameter was buying an
  `HDCLoader` run per invocation for nothing. Its docstring now says it takes
  no hero, so the parameter does not come back.
- SKILL.md's "explicitly un-ignored" wording replaced. It now states what is
  actually true — everything under `tests/fixtures/` is denied, exactly three
  are negated back in — names the `**` line as the one that reaches
  subdirectories, and records that negations against `*.hdc` alone were inert,
  so the next person does not repeat this.

## Gates re-run after the fix

| | result |
|---|---|
| Oracle | **656 passed**, exit 0; `oracle_known_residuals.json` unmodified |
| Full suite | **1753 passed, 0 skipped**, exit 0 |

Unchanged from before the fix round, as expected: nothing here touches engine
behaviour, and dropping an unused fixture parameter removes a redundant load
rather than a test.
