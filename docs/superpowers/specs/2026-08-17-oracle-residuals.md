# The oracle residuals — all of them, and how each one fell

*2026-08-17. Supersedes the scattered notes in the kirby-cost skill.*

**Outcome: 100% parity. 656/656 oracle fixtures, an empty residual ledger, and
655 characters / 27,019 objects / 82,367 cost values verified independently of
the suite with zero mismatches.**

The day started at 3 per-object failures and a 78-entry character-total ledger,
most of it filed as "HD global-state cases, do not force green". That framing
was wrong about every single one. Nine root causes: seven in the port, and then
**two in the oracle itself**, found only after the port had been made to agree
with the broken version.

> **Read §8 and §9 before trusting anything else here.** Parity was declared
> once today against an oracle that silently costed every character against
> Main6E no matter which template it declared. The number was the same; it
> meant something different. Two fixes in §7 and §8 were fitted to that fault
> and had to be reverted — including one whose corpus evidence looked
> overwhelming.

---

## The method that found them

One rule did most of the work: **measure across the corpus before touching
code.** A rule bug shows up as a whole class failing; an edge case shows up as
one failure in hundreds. Every fix below was predicted by a query, then
confirmed by one.

Five traps, each of which produced a confident wrong answer at least once
today. The fifth is the one that matters most, and it is last because it was
learned last:

1. **Positional alignment lies.** Comparing `zip(engine_list, fixture_list)`
   silently pairs different objects wherever the lists differ in order or
   length. It manufactured 1329 phantom mismatches in one pass and 90 in
   another. Key by xmlid, and treat any large diff as a suspected alignment
   bug until proven otherwise.
2. **A zero result usually means a broken predicate.** Searching
   `XMLID == "VPP"` matches nothing in the 794-file corpus, because a pool is
   `<VPP XMLID="GENERIC_OBJECT">` — the TAG carries the identity. Same for
   `<MULTIPOWER>`, and for `<MANEUVER>`, which is identified by DISPLAY. If a
   search over the whole corpus returns nothing, suspect the query first.
3. **The oracle dump is not the oracle's own arithmetic.** The fixture's
   `real_cost` for a framework slot is its PRE-LIST value; the character total
   excludes the slot entirely. Comparing the wrong attribute makes a correct
   engine look broken.
4. **"I can't find the rule" is not "there is no rule."** Re-run the Java CLI.
   Deterministic output means a rule exists and has not been found yet.
5. **A corpus survey is only as sound as the oracle behind it.** This is the
   trap that outranks the other four, because it defeats them. The survey that
   justified "no template, no sense groups" read

       has TEMPLATE + *GROUP option  ->  group rate   (72 of 72)
       no  TEMPLATE + *GROUP option  ->  single rate  ( 1 of  1)

   which looks like an overwhelming majority confirming a real exception. It
   was 73 readings from an instrument with a systematic fault, and the rule
   built on it shipped and had to be reverted the same day. Determinism does
   not help either: a broken oracle is deterministically broken. Before
   trusting a survey that turns on ONE character, ask what is different about
   that character's FILE, and whether the oracle handles it.

---

## The nine

### 1. Maneuvers are named by DISPLAY, not xmlid

`<MANEUVER>` in the template carries no `XMLID` attribute at all; every HDC
maneuver is written `XMLID="MANEUVER"`. Indexing by xmlid filed all 53 under one
key and Basic Strike won. Java matches maneuvers — and only maneuvers — on
display (`Hero.java:2706-2731`), searching `LIST` containers too, and falls
through to a custom maneuver when none matches.

The clone semantics came with it: Java clones the template's Maneuver, base cost
already read, and restores onto the clone, so the template's cost is the
starting point and an HDC `BASECOST` overrides it. `Maneuver._init`'s
`base_cost = 3` is the *custom* maneuver default.

Invisible to the corpus because all 308 maneuver elements carry an explicit
BASECOST. The leak was elsewhere: Martial Dodge loading as `TARGET="DCV"`
instead of `SELFONLY`.

### 2. Concentration was applying HD's editing intelligence

`Concentration.assigned_modifiers` filtered out a CONTINUOUSCONCENTRATION
sub-modifier. Java does too — but it is an authoring affordance (hiding a
meaningless option while you build an INSTANT power), gated on
`getActiveHero()`/`isLoading()` and the `isModifierIntelligenceOn()`
preference. The port left a `TODO` where the hero-state guard belongs and
assumed the branch that filters.

`Modifier.getTotalValue()` applies advantage math to a modifier from its own
sub-modifiers exactly as a power does: −0.25 × (1 + 1.0) = −0.5. All 8 corpus
sites record the unfiltered value; only two reach the filter, and both agree.
**A cost engine never applies modifier intelligence.**

### 3. A framework's `<ADDER>` children were never read

The loader's framework branch read `<MODIFIER>` children only. A VPP carries its
control cost in a CONTROLCOST adder whose LEVELS the file supplies, and
`VariablePowerPool.__init__` synthesises that adder (as Java's `init()` does)
with the rate but no levels — so the stub survived at 0 and **all 93 pools in
the corpus costed their control at 0**.

`_build_adder` was correct all along; it was simply never called for a
framework. GREATER_DEMON: pool 40 + control 20 = 60, ×(1 + 2.0) advantages on
the non-pool part + pool = 100, against the engine's 40.

### 4. Powers inside a pool cost the character nothing

`VariablePowerPool.getRealCostForChild()` is literally `return 0;` — the pool
buys the capacity. The totals loop was summing the slots, overcharging every
pool-bearing character by the whole contents of its pool (MENTON: 1313 points).

Applied in the totals loop, **not** in `real_cost_for_child`: a slot's own
reported cost is non-zero in the oracle dump, and `real_cost` on a child
delegates to the parent, so zeroing the method would collapse 13 per-object
values to fix one total.

### 5. CHARACTERISTICS is driven by the template, not the file

Java walks the hero's characteristic set — built from the template — and pulls
each one OUT of the section by name (`Hero.java:2472`). It never iterates the
file's children, so an element the template does not define is never read.

Four vehicles carry `<SIZE LEVELS="4">`; the engine charged 15/level for it.

This **reversed** a standing note that characteristics "must stay ungated —
gating them takes the corpus from 8 failures to 47". That was measured against
the JSON template dump; against a real `.hdt` all 20 standard characteristics
resolve. A test pins that premise, because gating a section on the template is
only safe while the template genuinely defines everything it should.

**The example has since changed sides, and the rule survived it.** SIZE was read
as "undefined, therefore dropped" — but SIZE *is* defined, by the `Vehicle6E.hdt`
those characters declare, and neither engine was resolving it (§9). A vehicle now
loads SIZE and pays Vehicle6E's 5/level. What the gate actually says is that a
characteristic the RESOLVED template does not define is never loaded, which is
still true and still tested — with a synthetic template-less character, since
the corpus no longer contains an example.

### 6. A framework did not hold its own slots

`List.objects` is Java's `getObjects()` and rules read it, but the loader linked
children upward only and never populated the container's list — so every
framework reported an empty pool. `Charges.parentUsesEND()` asks a reserve's
SLOTS whether they use END, because a reserve never does itself
(`Charges.java:450`); with nothing to iterate it answered "no", set `max = 0`,
and clamped the modifier away.

Both halves were needed. An earlier probe of the List branch alone appeared to
do nothing, because the container held nothing to iterate — and that null result
was briefly written up as evidence the branch was a red herring.

### 7. No template, no sense groups — WRONG, reverted the same day

Kept because it is the most instructive failure of the day.

6E deducts a capability's `sense_cost` from a Sense whose GROUP already provides
it. Java gates that on the group having adders to provide, and the group
registry is built by `SenseGroup.clear()`, which "should only be called during a
template load". UNDEAD_LICH's file declares no `TEMPLATE`, so — the reasoning
went — no groups are registered and the deduction never fires.

The corpus appeared to confirm it decisively. Of the 12 Detects with a NOGROUP
group and a prior `OPTION=ALL` EnhancedPerception, the LICH is the only file
without a template, and the only one the oracle did not deduct for. The sibling
rule `SenseAdder.sense_groups_defined` (UNDEAD_GHOUL's `*GROUP` option rate) had
the same 72-of-72 vs 1-of-1 backing. Two competing hypotheses had already been
tested and disproved. The Java CLI reproduced the number on every run, which
was taken as proof of determinism and therefore of a rule.

**All of that was true and the conclusion was still wrong.** The oracle could
not resolve `builtIn.` template names (§9), so the Main6E bootstrap loaded
*without the parent chain that registers the sense groups*. The oracle's "no
template" reading was really "template loaded incompletely". With the oracle
fixed, UNDEAD_LICH deducts and costs 31 — the engine's original answer, before
any of the four hypotheses — and UNDEAD_GHOUL takes the group rate, 6 not 3.

Both gates are gone: the one added here, and the older
`SenseAdder.sense_groups_defined`. `tests/test_nogroup_sense_deduction.py` lists
all four hypotheses for that single number, including this one, which passed
the corpus test and shipped anyway.

### 8. The Vehicle6E emulation — half right, deleted for the wrong reason

THE_STARBIRD's FLIGHT came out 105 against the oracle's 131. The loader was
emulating Vehicle6E for characters that name it: `_V6E_NO_END` forced
`uses_end = False` on movement powers, because Vehicle6E writes `USESEND="No"`
where Main6E writes `"Yes"`.

The conclusion drawn was that HD costs against the template it has LOADED and
the CLI loads Main6E throughout, so the emulation was modelling a template
nobody loaded. Deleting it made STARBIRD match at 131 and moved no other
character.

**The premise was an artifact.** The CLI loaded Main6E throughout only because
it could not resolve `builtIn.Vehicle6E.hdt` (§9). With that fixed the oracle
says 105 — what the emulation produced. It had the rule right: a vehicle's
movement powers genuinely do not use END.

It was still the wrong code. Hand-rolling a template's contents inside the
loader is the bug, and the emulation's own docstring had already recorded half
of it being retracted for diverging from the oracle. The fix is for the engine
to RESOLVE the declared template, which it now does — see §9.

### 9. The oracle could not load templates at all

Not a port bug. The bug in the instrument that produced §7 and §8.

Since the headless fork was created on 2026-04-08 it could not resolve a single
`builtIn.` template name. HD names built-in templates that way in a character's
`TEMPLATE` attribute and in the parent chain every `.hdt` declares, and resolves
them by stripping the prefix and calling
`ClassLoader.getSystemResourceAsStream(name)` (`Template.java:790`) — the
original shipped `template/` as a **classpath entry**, and the fork's own
`.classpath` still declares it. `hd6cli.sh` never reproduced that, so:

- **Characters silently kept the Main6E bootstrap.** `setTemplate` found
  nothing and left the active template alone, with no diagnostic.
- **Main6E itself loaded without its parents**, because the same lookup fails
  for those, and a null InputStream reaching SAXBuilder is exactly the
  `MalformedURLException: "spec" is null` the fork had documented — as a
  malformed-`.hdc` symptom, which it was not.

It was visible in the output the whole time: the oracle recorded PD at
`(LVLCOST 1, LVLVAL 1)` for every character on every template, including the
four Vehicle6E ones, though `Vehicle6E.hdt` states `(3, 2)`.

Fixed in `kirby-hd-oracle@fcf62bf`, outside the 341 byte-identical
engine files. Measured across all 655 characters: **647 unchanged, 8 changed,
0 errors** — exactly those naming a non-Main6E template (4 Vehicle6E,
2 Computer6E) plus the 2 naming none.

The engine then had to learn what it had been shielded from:

- `HDTTemplateProvider` follows `extends="builtIn.Main6E.hdt"`. Every
  specialised template is a thin override layer, so a Vehicle6E provider that
  does not walk the chain resolves only the ~47 objects its own file lists.
- `HDCLoader` costs each character against its declared template.
- `apply_template` lets a template's `LVLVAL` win. It had applied only when the
  object's value was still `0.0`, letting a class default beat the template: PD
  initialises to 1.0, so Vehicle6E's `LVLVAL="2"` never took and 13 PD cost
  `13 x 3 = 39` instead of `13/2 x 3 = 19.5`. Invisible while everything
  resolved to Main6E, whose PD `LVLVAL` is 1. XML provenance and option
  overrides still outrank the template — each was found by breaking it.

**Generalise this one:** hand-rolling a template's contents inside the loader is
the bug, in either engine. Per-character templates belong in a
`TemplateProvider` that resolves the named `.hdt`, never a patch over Main6E.

---

## Standing ledger

`tests/fixtures/oracle_known_residuals.json` is **empty**, and
`test_totals_residual_ledger_is_not_stale` ratchets: it fails the moment a
listed character starts passing. With nothing listed, the ledger's only job now
is to stay empty. Any new entry is a regression, not a discovery.
