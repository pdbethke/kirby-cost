# Skill ↔ characteristic linkage — fix report

Branch: `fix/skill-characteristic-linkage` (off `main`)

## STATUS: FIXED. No cost moved.

## The defect

A skill names the characteristic its roll is taken against only inside its
`<CHARACTERISTIC_CHOICE>` block — never as an attribute of the skill element:

```xml
<SKILL XMLID="DEDUCTION" ...>
  <CHARACTERISTIC_CHOICE>
    <ITEM CHARACTERISTIC="INT" BASECOST="3" LVLCOST="2" LVLVAL="1" />
  </CHARACTERISTIC_CHOICE>
```

`HDTParser` has always parsed that block, and `hdt_provider._template_data`
already read its **costs** (BASECOST / LVLCOST / LVLVAL fall back to the first
ITEM). It dropped the one thing that identified the skill: the characteristic's
name. `TemplateData` had no field to carry it, so nothing downstream could set
`Skill.characteristic`, which stayed at its constructor default of 0 (GENERAL).

`Skill.roll_value` then took its `self.characteristic == 0` branch, which uses
`Rules.general_level` (10), giving `9 + 10/5 = 11` for every characteristic-based
skill on every character. The two halves agreed by accident — the general level
and a defaulted characteristic are both 10 — which is why nothing red ever
appeared.

Confirmed against the shipped oracle dump `tests/fixtures/authored/Ravel.json`,
whose `column2_output` is HERO Designer's own printed line:

| skill | oracle | engine before | engine after |
|---|---|---|---|
| Deduction | `Deduction 14-` | 11 | **14** |
| Criminology | `Criminology 14-` | 11 | 14 |
| Forensic Medicine | `Forensic Medicine 14-` | 11 | 14 |
| Paramedics | `Paramedics 14-` | 11 | 14 |
| Computer Programming | `Computer Programming 14-` | 11 | 14 |
| Navigation | `Navigation (Space) 14-` | 11 | 14 |
| Acting | `Acting 13-` | 11 | 13 |
| Charm | `Charm 13-` | 11 | 13 |
| KS: String Body Tricks | `KS: String Body Tricks 13-` | 13 | 13 (unchanged) |

Ravel's INT is 23. 6E1 p57: nine plus a fifth of the linked characteristic,
standard rounding. `round_half_up(23/5)` = `round_half_up(4.6)` = 5, so 9 + 5 = 14.
(6E1 p15's worked example — DEX 20 → 13- — is the same arithmetic.)

## The change

Three files, plus one test-side and one doc-side follow-on.

1. **`kirby_cost/template/dataclasses.py`** — `TemplateData` gains
   `characteristic: str = ""`: the characteristic named by the template's
   default (first) `CHARACTERISTIC_CHOICE` ITEM, or `""` where the template
   names none.

2. **`kirby_cost/template/hdt_provider.py`** — `_template_data` populates it
   from the same `choice` dict it already used for the costs.

3. **`kirby_cost/objects/skills/skill.py`** — `Skill` gains an `apply_template`
   override that sets `self.characteristic` from the template. It:
   - sets the **identity only**. It deliberately does NOT call
     `set_characteristic()` — see the CORRECTION below for the real reason;
     the reason first given here was wrong.
   - respects the document. A new `_characteristic_from_xml` flag (set in
     `Skill._init` when the element states `CHARACTERISTIC`) makes the
     document outrank the template, exactly as `_base_cost_from_xml` does —
     a character who chose to run a Knowledge Skill off INT keeps INT.
   - respects a campaign. `campaign_forced` still wins over the document,
     matching `GenericObject.apply_template`'s own precedence.

4. **`tests/test_campaign_cost_fields.py`** — the new `TemplateData` field
   automatically joins `OVERRIDABLE_FIELDS`, and that suite's guard test
   demanded it be classified. It is EFFECTIVE (measured: forcing
   `characteristic="STR"` on DEDUCTION moves Ravel's Deduction to STR and its
   roll to 17), so it got a plausible value in `_EFFECTIVE_FIELD_VALUES`
   rather than a place in `_UNSUPPORTED_FIELDS`.

5. **`kirby_cost/campaign/rules.py`** — the field-by-field record extended
   with that measurement.

### New tests — `tests/test_skill_characteristic_roll.py` (11 cases)

- the provider reports INT for DEDUCTION, DEX for ACROBATICS, GENERAL for
  KNOWLEDGE_SKILL;
- the linkage survives the load;
- Deduction rolls 14, spelled out as INT 23 → `round_half_up(4.6)` = 5 → 9 + 5,
  so a failure says which half broke;
- each of Ravel's six unambiguously INT-linked skills rolls 14;
- **over-application guard**: KNOWLEDGE_SKILL's template offers GENERAL *or*
  INT, Ravel bought the GENERAL one (it cost him 2, not 3), and it must stay on
  the general base — 13 (= 11 + his two levels), which is what the oracle
  prints, not the 16 his INT would give. LANGUAGES, GENERAL with no levels,
  pins the flat 11.
- the document outranks the template.

The tests are built on `tests/fixtures/authored/Ravel.json`, which ships with
the repo, so they run publicly. No rulebook prose is reproduced; 6E1 p57 and
p15 are cited and paraphrased.

**Deliberately not asserted.** Ravel's DEX comes from a power carrying OIHID,
which this engine does not model, so no DEX-based skill is used here. His
PROFESSIONAL_SKILL and SCIENCE_SKILL have multi-ITEM `CHARACTERISTIC_CHOICE`
blocks and the oracle's build dump does not record which ITEM he picked, so
the engine falls back to the template's first and disagrees with the oracle
(PS → STR 17 vs 14; SS → GENERAL 11 vs 14). That is a gap in the build doc,
not in this rule, and is out of scope. ~~Likewise his five PROFICIENCY skills…~~ **Wrong — see the CORRECTION
below. Those five were a test-harness artifact, and they are now fixed.**

## Oracle numbers

| | before | after |
|---|---|---|
| `tests/test_oracle_fixtures.py` | **656 passed** in 83.35s | **656 passed** in 82.92s |
| `tests/` full (incl. `test_hdc_roundtrip.py`) | 1717 collected: 1716 passed, 13 skipped, 1 failed¹ | **1728 passed, 13 skipped** |

¹ The single "before" failure is the `test_campaign_cost_fields` classification
guard described above — it fired because the new `TemplateData` field appeared,
not because anything repriced. It was measured and classified, not silenced.
(The genuine pre-change baseline, `tests/ --ignore=tests/test_hdc_roundtrip.py`,
was **1711 passed, 13 skipped**.)

`tests/fixtures/oracle_known_residuals.json` was NOT touched and no fixture was
adjusted. The residual ledger is unchanged and its staleness ratchet is intact.

## Cost movement: NONE

**No cost moved.** All 656 oracle fixtures pass unchanged, and
`test_authored_characters.py` (which compares total_cost / active_cost /
real_cost_pre_list on every object of Ravel, Bokor, Power Lad and the Kitchen
Sink) is green.

~~That is not luck; the change was shaped for it:~~ **See the CORRECTION
below — it largely IS inertness, not shaping.**

- `apply_template` sets the characteristic's *identity* and nothing about
  price. The cost half of `CHARACTERISTIC_CHOICE` was already being read by the
  provider before this change and is untouched by it.
- The one live coupling from roll to cost is `AccumulatorSkill.total_cost`
  (`accumulator_skill.py:57-72`), which reads `roll_value` against
  `rules.skill_maxima_limit`. It is gated on `active_hero.rules.use_skill_maxima`,
  which defaults False (`kirby_cost/model/rules.py:77`) and is enabled by no
  character in the fixture set. **Residual risk, stated plainly:** a character
  who DOES enable skill maxima would now see levels above the maxima limit
  charged double where before every roll sat at 11 and nothing ever exceeded the
  limit of 20. That is the correct behaviour under the rule, but it is
  unexercised by the oracle corpus, so it is unproven against HD.

---

# CORRECTION round (post-review)

Review returned **MERGE** with one condition and three follow-ons. All are done.
It also independently reproduced 656/656 with the ledger untouched, and found a
**second parity gate I had not named**: `tests/test_display_fidelity.py`, which
compares `column2_output` strings that *embed* `roll_value` — **91,221 compared,
91,221 exact**, before and after.

## C1 — MERGE CONDITION: the docstring's causal claim was false. Fixed.

I wrote that `set_characteristic()` would re-apply the ITEM's costs and that
avoiding it is why parity held. Untrue. `Skill.characteristic_choices` is
**never populated** — the parse is still a commented-out stub in `Skill._init`,
and all 18 of Ravel's skills carry an empty list — so `set_characteristic()`
iterates nothing and cannot move any cost today.

The override is still right, for a better reason, and the docstring now says
that one: `hdt_provider._template_data` already folds the chosen ITEM's
`BASECOST`/`LVLCOST`/`LVLVAL` into the **same** `TemplateData`, and
`super().apply_template()` has just applied them under the existing precedence
gates. Identity and costs agree **by construction** — same ITEM. Calling
`set_characteristic()` would be a *second* application of those same costs,
outside those gates.

This is worth the words because whoever implements the `CHARACTERISTIC_CHOICE`
parse makes my old comment true and my override wrong **in the same commit**,
and would have read that comment and believed it. The docstring now warns them
explicitly.

## C2 — The parity gates do not exercise this change. Said plainly now.

Measured across the corpus: 655 characters, 4,434 skill-like objects, and the
number where the template fallback actually fires is **zero**. Every `.hdc` HERO
Designer saves writes `CHARACTERISTIC="INT"` on the skill element, so the
document branch always wins and the fallback never runs.

**656 passed is evidence of no harm, not evidence of the fix working.** The
gates are green because the change is *inert* on them.

Where it does fire: documents that omit the attribute — oracle dumps like the
Ravel fixture, and build docs authored outside this repo (kirby-api's relational
re-emission, the in-app editor). That is the path combat consumes, so the fix is
worth having, but it is a **robustness fix for silent documents**, not the
platform-wide roll fix my original report described.
`tests/test_skill_characteristic_roll.py` is the only thing that exercises it,
which is now stated in that file's own docstring.

## C3 — The five "proficiency mismatches" were a harness artifact. Fixed.

Not a defect in the proficiency flag. `tests/fixtures/authored/Ravel.json` is an
oracle dump and writes `is_proficiency` / `is_familiarity` / `is_everyman`, but
`build_json._SKILL_FLAG` reads `proficiency` / `familiarity` / `everyman` — so
every mode flag arrived False and skills HD priced as Proficiencies were rebuilt
as full skills. Real `.hdc` files state `PROFICIENCY="Yes"` and load correctly.

Fixed by accepting the `is_`-prefixed spellings as **input-only** aliases
(`_SKILL_FLAG_ALIASES`); the emitter still writes the canonical name, so a round
trip does not acquire a second spelling. Cost-free, as measured: High Society
stays at `total_cost` 2.0 and its roll moves 13 → **10**, matching HD.

## C4 — The short-circuit branches are now pinned.

Nothing exercised the familiarity / everyman / proficiency short-circuit, because
every Ravel flag read False. Now pinned, and 6E1 p62 puts Deduction on the
Everyman list — so the very skill that proves the linkage also proves it is not
consulted:

| case | characteristic still linked | roll | cost |
|---|---|---|---|
| Deduction as Familiarity | INT | **8** (not 14) | 1.0 |
| Deduction as Everyman | INT | **8** | 0.0 |
| Deduction as Proficiency | INT | **10** | 2.0 |
| Ravel's five real Proficiencies | PRE / INT | **10** each | unchanged |

Plus a test pinning the alias seam itself, so re-introducing the key-name
mismatch fails loudly.

## C5 — A real `.hdc` load is now asserted.

`test_the_characteristic_survives_a_real_hdc_load` loads Ravel's actual `.hdc`
and asserts `_characteristic_from_xml` is True and the roll is 14 — proving the
suite is not exercising only the lossy `build_from_json` path. It skips where
`KIRBY_COST_AUTHORED` is unset (as in this run and in CI), like every other
machine-bound test.

## Ravel against HD's own printed rolls

16 of his 18 skills print a roll (Skill Levels and Language do not).

| | before this branch | after the fix | after the alias fix |
|---|---|---|---|
| exact vs HD | 9 / 16 | 9 / 16 | **14 / 16** |

The two that remain are **not** this rule. `PROFESSIONAL_SKILL` and
`SCIENCE_SKILL` have multi-ITEM `CHARACTERISTIC_CHOICE` blocks, HD asks the
character which ITEM, and the oracle's build dump does not record the answer —
so the engine can only take the template's first (PS → STR 17 vs 14; SS →
GENERAL 11 vs 14). Excluding those two documented build-doc gaps it is
**14 / 14**.

**Follow-up I deliberately did not build:** where a silent document states costs,
the ITEM could be inferred by matching `base_cost`/`level_cost` (Ravel's Science
Skill cost 3, which is the INT ITEM, not the GENERAL one at 2). That would take
it to 16/16. It is cost-adjacent inference nobody asked for, so it is recorded
here rather than written.

## Numbers after the alias change

| gate | result |
|---|---|
| `tests/test_oracle_fixtures.py` | **656 passed** (91.92s) |
| `tests/test_display_fidelity.py` | 91,221 compared, 91,221 exact |
| `tests/` full | **1732 passed, 14 skipped** (was 1728 / 13; +4 tests, +1 skip for the .hdc test) |

`tests/fixtures/oracle_known_residuals.json` still untouched. **No cost moved.**

## Recorded, not mine to fix here

- `test_display_fidelity` passes vacuously when `hdc_path` is missing — it
  `continue`s with no floor on how many characters were compared.
- The roll→cost coupling has four sites, not the single `AccumulatorSkill` one
  my first report named.
- `Skill.characteristic_choices` is still an unimplemented stub (see C1).
