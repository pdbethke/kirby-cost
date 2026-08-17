# Unship `template_6e.json` — read templates from the user's own `.hdt`

**Status:** SHIPPED 2026-08-16 (branch `feat/hdt-templates`)
**Date:** 2026-08-16

## Why

`kirby_cost/data/template_6e.json` is 409K of Hero Games' published catalogue
committed inside the runtime package. It is not hand-authored: it is a dump of a
licensed `Main6E.hdt` produced by `hd6cli --dump-template` (see
`TemplateData.from_dict`) — a build artifact of one developer's licensed HD
install that happens to be checked in.

The library's stated position is that users bring their own HD licence and their
own templates. That is only true once the package stops carrying the data.

**Goal:** kirby-cost ships no Hero Games template data, and a standalone user
supplies their own `.hdt`.

## Prior art — most of this already exists

Do not design this from scratch. Three pieces are already built and were last
touched **2026-08-15**, so they are current, not legacy:

1. **`kirby_cost/io/hdt_parser.py` (`HDTParser`)** — a complete `.hdt` reader and
   writer covering every section, with nested adders, options, types and
   excludes. Nothing inside kirby-cost imports it, which makes it easy to miss —
   but **kirby-api does**, at `kirby/builds/importer.py:118`.
2. **A consumer-side HDT import path** — `kirby-build import-template /path/Main6E.hdt`
   parses the user's own template with `HDTParser` and writes it to kirby-api's
   relational catalog (`Template` / `TemplateObject` / `TemplateObjectType`).
3. **A consumer-side database provider** — serves kirby-cost's
   `TemplateProvider` protocol from those tables. `kirby/engines/cost/hdc.py`
   already costs through it.

So the HDT → `TemplateData` conversion **is already solved**; today it runs
through a database round-trip. What is missing is a *file-backed* path for a
consumer that has no database — which is the standalone library's case.

## Direction of dependency — kirby-cost stands alone

**kirby-cost must work with nothing but a `.hdt` file.** No database, no
consumer, no service. It owns the HDT → `TemplateData` conversion; consumers
load *it*.

That the conversion currently happens to run inside a consumer's database import
is an accident of where the code was written, not the architecture. The
conversion belongs here, in the library that owns the contract; a consumer that
wants templates in its own storage projects them from this library's output.

Practically: the conventions that consumer's import path already encodes are
**knowledge to lift, not a dependency to take**. Nothing in kirby-cost may import
from a consumer, and the provider must be constructible from a path alone.

A consumer that today falls back to the bundled JSON when its own template source
fails will need its own answer once the JSON is gone — but that is the
consumer's change to make, not a blocker on this one.

## Design

1. `kirby_cost/template/hdt_provider.py` — `HDTTemplateProvider(path)`
   implementing the existing `TemplateProvider` protocol: parse once with
   `HDTParser`, index by xmlid, convert to `TemplateData` on demand.
2. **Lift the conversion conventions from the existing consumer-side import
   path rather than re-deriving them** — including its 2026-08-15 fix
   ("two-step top-level-first template lookup, fix `base_value`"). Copy the
   knowledge into this repo; take no dependency. Re-deriving rules elsewhere is
   how the TS SDK got stuck at 91%.
3. Provider resolution for the default: explicit path → `KIRBY_COST_HDT` env var
   → an error naming what to set. No silent fallback, because there is no
   bundled file to fall back to.
4. Remove `template_6e.json` from the repo and from `package_data`.

## Measured HDT-vs-JSON gap (2026-08-16)

Evidence for the conversion, and for what the JSON silently loses.

| | count |
|---|---|
| xmlids in `Main6E.hdt` | 364 |
| xmlids in the JSON | 357 |
| shared | 347 |
| JSON-only | 10 |
| HDT-only | 17 |

**JSON-only (10)** — no HDT element; must be supplied as explicit engine
knowledge: `ARMOR`, `DAMAGERESISTANCE`, `ENDURANCERESERVEREC`, `FTLTRAVEL`,
`GENERIC_OBJECT`, `GENERIC_OBJECT_List`, `SIZE`, `SUCCOR`, `SUPPRESS`,
`TRANSFER`. (The skill's "9 not in Main6E.hdt" note undercounts by one.)

**HDT-only (17)** — in the template, dropped by the dump: `ADJACENT`,
`ADJACENTFIXED`, `ANALYZESENSE`, `CONCEALED`, `DIMENSIONALALL`,
`DIMENSIONALGROUP`, `EXTRADC`, `MAKEASENSE`, `MANEUVER`, `MENTALAWARENESS`,
`RANGE`, `RANGEDDC`, `RAPID`, `SENSE`, `SENSEGROUP`, `TRANSMIT`,
`WEAPON_ELEMENT`. **`MANEUVER` and `EXTRADC` matter**: the loader's template
gate leaves MARTIALARTS ungated *because* those have no JSON entry. A template
that defines them changes that premise, and gating them took the corpus from 8
failures to 47 once before.

On the 347 shared ids, differences are convention, not missing data: `target`
(274) and `duration` (272) are absent on the element and filled by the dump from
class defaults; `level_value` (163) is HDTParser's `1.0` default vs the dump's
`-1.0`-for-unset; `level_cost` (64) reads a different attribute for skills;
`base_cost` (52); `display` (33) — where **the HDT is richer** (`Active Sonar`
vs the JSON's literal `ACTIVESONAR`). Adder sets differ on 12, option sets on 13:
the JSON has extra adders on `AOE`/`CLAIRSENTIENCE`/`DARKNESS` (injected at dump
time), the HDT has `DETECT` options the JSON lacks (`CLASS`, `LARGECLASS`,
`SINGLE`).

**The dump is lossy.** So "diff to zero against the JSON" is the wrong
acceptance test.

## Acceptance

- The oracle suite holds at its current numbers with the HDT provider as source.
  **Parity against the Java oracle is the test**, not agreement with the JSON.
- Every remaining difference from the JSON is explained here or filed as a JSON
  defect.
- No Hero Games data ships; `tests/test_pure_code.py` still passes.
- A fresh clone plus a user-supplied `.hdt` loads and costs a character with no
  database and no consumer present.
- Absent a `.hdt`, the error says exactly what to provide.

## Risks

- The template touches every cost path; one convention fixed wrongly moves many
  numbers at once. Change one at a time, re-run the oracle.
- The oracle fixtures were generated through the JSON path, so a fixture and the
  provider can agree while both diverge from HD. The Java CLI is the tiebreaker.
- Re-checking the template gate against a template that now defines `MANEUVER`
  and `EXTRADC` (see above).


## What shipped

`HDTTemplateProvider` reads the user's own `.hdt`; `template_6e.json`,
`JSONTemplateProvider` and `scripts/extract_defaults_from_oracle.py` are gone.
Resolution is explicit path → `KIRBY_COST_HDT` → an error naming what to set.
Tests take the same route (`tests/conftest.py`), falling back to a developer's
untracked `HERODesignerSource/` copy.

**Oracle: 653/656 characters, the same three residuals `main` carries**
(UNDEAD_LICH, SHADOW_COLOSSUS, THE_STARBIRD — the HD-global-state cases already
documented). Full suite 1223 passed / 3 failed / 24 pre-existing errors, against
`main`'s 1204 passed / 3 oracle failures / 24 errors.

Four things the `.hdt` states indirectly, which the dump had already resolved
and a first pass at the provider dropped:

1. **Nested adder types.** Only the outer layer of an element's adders reached
   `TemplateData`, so Transport Familiarity's CAMELS/DOGS/EQUINES arrived
   untyped and its Riding discount never fired — 13 characters overcharged. The
   type map now walks to any depth and matches the dump's 175 entries exactly.
2. **Sense-group options.** A sense-affecting power names TARGETINGCOST and
   NONTARGETINGCOST once; HD expands them into one option per sense group at
   load time (`SenseAffectingPower.getOptions`, and `Shapeshift.java:196` which
   prices them its own way). Ported; all six powers' option tables now match the
   dump exactly.
3. **Identity.** Senses and sense groups share a tag and name themselves with an
   `XMLID` attribute, so all six groups filed under one key. They are also a
   separate registry in Java and a name can appear in both — Mind Scan is a
   `<SENSE>` in the Mental Group *and* a power at 5/level — so purchasable
   definitions are indexed first and a sense may not shadow one.
4. **No template, no sense groups.** The loader already knew a character with no
   `TEMPLATE` attribute cannot resolve a `*GROUP` option (UNDEAD_GHOUL); sense
   adders now honour it too, via `SenseAdder.sense_groups_defined`.

### Maneuvers, indexed by display (fixed after the fact)

Shipped lossy and then repaired: the 53 `<MANEUVER>` elements are distinguished
by DISPLAY, not by xmlid — the template's element carries no `XMLID` attribute
at all — so keying them like everything else filed all 53 under `MANEUVER` and
the first (Basic Strike) won.

Java matches maneuvers on display, and only maneuvers (`Hero.java:2706-2731`),
scanning `LIST` containers as well as top-level entries and falling through to
`new Maneuver(sk)` — a custom maneuver built from the character's element and
nothing else — when none matches. `EXTRADC`, `RANGEDDC` and `WEAPON_ELEMENT`
sit in the same section but name themselves properly, and Java looks those up
by xmlid in three separate scans just above.

So the provider gained `get_maneuver(display)` / `get_maneuver_map()`, the
loader routes `MANEUVER` through it, and `TemplateData` gained an `attributes`
map — a maneuver is mostly detail (OCV, DCV, PHASE, DC, KILLING, EFFECT) that
no named field carries, and Java hands the whole cloned Maneuver to whoever
asks.

One more thing the clone semantics imply: Java does not build the maneuver from
the character's element and then dress it, it clones the *template's* Maneuver
— base cost already read from `<MANEUVER BASECOST="4">` — and calls
`restoreFromSave` on the clone. The template's cost is therefore the starting
point and an HDC `BASECOST` overrides it, where the loader had treated the HDC
attribute as the only source. `Maneuver._init`'s `base_cost = 3`
(`Maneuver.java:417`) is the *custom* maneuver's default, which is exactly why
a template match has to replace it.

**Why the corpus never caught it.** All 308 maneuver elements across the 794
HDC files carry an explicit `BASECOST`, which wins over any template default —
so every maneuver costed correctly while wearing Basic Strike's other defaults.
43 of the 53 maneuvers state a base cost other than Basic Strike's 3 and 7 are
`TARGET="SELFONLY"` against its `DCV`; the visible symptom was Martial Dodge
loading as `DCV`. The oracle is unmoved by the fix — 3 failures before, the
same 3 after, and the 18 "Custom Maneuver" entries that now take the
no-template path are unchanged too.

### Known limitations, deliberately left

- The gate premise did change as predicted: this template *does* define
  `MANEUVER` and `EXTRADC`. MARTIALARTS remains ungated regardless, and the
  corpus is green, so nothing was adjusted.
- `FTLTRAVEL` and `SIZE` resolve to nothing (no HDT element, in this template or
  the 5E fallback). No corpus character uses either. `GENERIC_OBJECT` is
  deliberately never a template entry — the loader excepts it from the gate.
- The remaining JSON-only ids (`ARMOR`, `DAMAGERESISTANCE`, `SUCCOR`,
  `SUPPRESS`, `TRANSFER`, `ENDURANCERESERVEREC`) all resolve, through the
  earlier-edition template beside the primary — which is how HD finds them too.
