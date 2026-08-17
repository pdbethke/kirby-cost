# kirby-cost

[![PyPI](https://img.shields.io/pypi/v/kirby-cost)](https://pypi.org/project/kirby-cost/)
[![Python](https://img.shields.io/pypi/pyversions/kirby-cost)](https://pypi.org/project/kirby-cost/)
[![Licence: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/licence-PolyForm%20Noncommercial%201.0.0-blue)](LICENSE)

A Python library for reading HERO Designer's own files — `.hdt` templates and `.hdc`
characters — and reproducing HERO Designer's point-cost arithmetic exactly.

It exists so that **personal Python projects can work with the files HERO Designer
produces**: read a character you built in HD, walk its powers, skills and frameworks as
real objects, and get the same Total / Active / Real costs HD itself would show.

Ported from the **licensed HERO Designer Java source code**, purchased from Hero Games
(see [Provenance](#provenance)).

## What it is for

HERO Designer is where you build a character. This library is for the things you might
want to do afterwards, in Python, for yourself:

- Read an `.hdc` file into typed objects instead of hand-parsing XML.
- Get per-object costs — Total, Active, Real — and character totals, computed the way HD
  computes them rather than re-derived from the rulebook.
- Feed a character you already built into a personal project: a virtual tabletop, a
  campaign tracker, a combat simulator, a spreadsheet, a bit of analysis.
- Verify arithmetic — confirm that what you have matches what HD says it costs.

The point is interoperability with HD's file formats from Python. If you can already do
what you want inside HERO Designer, do it there.

## What it is not

**This is not a replacement for HERO Designer, and not a competitor to it.**

It is a calculator over a build that HERO Designer already authored. It has no character
creation interface — nothing in this library creates or edits a character; it reads one
and does arithmetic on it. And it cannot run without HD: the templates that define what
powers exist and what they cost are HD's, and you supply them from your own licensed
installation.

If you want to create a HERO System character, buy HERO Designer. This library assumes
you already have.

## Requirements — bring your own HERO Designer licence and templates

kirby-cost ships no Hero Games content. To use it you supply, from your own licensed
HERO Designer installation:

- **Your own HERO Designer licence.** This library neither includes nor substitutes for one.
- **Your own template files (`.hdt`)** — `Main6E.hdt` and any others you use. The
  templates encode Hero Games' published catalogue of powers, skills, modifiers and
  their costs. That data is theirs; it is not redistributed here.
- **Your own character files (`.hdc`)**, and any published character packs you cost
  with it.

Point the engine at your template with `KIRBY_COST_HDT`:

```bash
export KIRBY_COST_HDT="$HOME/HERO Designer/template/Main6E.hdt"
```

or pass a path directly:

```python
from kirby_cost.template.hdt_provider import HDTTemplateProvider
loader = HDCLoader(provider=HDTTemplateProvider("/path/to/Main6E.hdt"))
```

There is no bundled fallback — without a template the loader raises and names what to
set. Templates reach the engine through the `TemplateProvider` interface
(`kirby_cost/template/provider.py`), so a consumer that keeps its catalogue elsewhere
implements that protocol against its own storage and passes the provider in.

### How it is verified, and why you cannot reproduce that here

The engine is validated by costing published characters and comparing every number
against HERO Designer's own engine, run headless. As of 2026-08-17 that is 655
characters, 27,019 objects and 82,367 individual cost values, with zero mismatches.

**None of that apparatus is public, and cannot be.** The comparison harness wraps the
licensed HERO Designer source, and the corpus is built from commercial character packs —
names, power names and full costed builds, which together amount to a machine-readable
copy of published stat blocks. Neither is redistributable, so neither is here. The
fixtures directory is gitignored so a locally generated corpus cannot be committed by
accident.

What that means for you: the parity claim above is the maintainer's measurement, not
something this repository lets you re-run. The tests that ship exercise the engine's own
logic and pass without any of it:

```
  375 passed, 159 skipped     # the code alone: no templates, no corpus
  416 passed, 118 skipped     # your templates, no corpus
```

If you own the HERO Designer source package and want to reproduce the full comparison,
contact the maintainer.

## Installation

```bash
pip install kirby-cost
```

or from a clone, for development:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```python
from kirby_cost.io import HDCLoader

# reads the .hdt named by KIRBY_COST_HDT
hero = HDCLoader().load_file("MyCharacter.hdc")

print(hero.name, hero.total_points, hero.available_points)

for power in hero.powers:
    print(f"{power.name or power.alias}: {power.real_cost}")
```

`hero` also exposes `characteristics`, `skills`, `perks`, `talents` and `martial_arts`.

`hero.powers` is flat and holds framework containers alongside their slots, the way HD
writes them. A Multipower or VPP appears as an object in its own right, its slots carry
`slot.parent`, and the container also holds them in `container.objects`. Slot costs
follow the framework's rules — a Multipower slot is a fraction of the reserve, and a
power inside a VPP costs nothing at all, because the pool already paid for it. Grouping
containers HD creates for the character sheet appear too, costed at zero.

## Status

- **100% parity with HERO Designer.** Every one of 655 published characters matches the
  Java application's own output on every object and on character totals — 27,019 objects
  and 82,367 individual cost values, with zero mismatches.
- **1,290 tests.** 375 of them need nothing but the code; the rest need your own
  templates, and the parity suite needs a corpus you generate locally.
- Pure code — no database, no web framework, no network access.

Parity is measured against HERO Designer's own engine, run headless over the same
character files. Both halves of that comparison have been wrong before and been
corrected: the figure means "every value the corpus compares", and the corpus is
described above so you can judge what that covers.

## Provenance

**This is a port of licensed source code, purchased from Hero Games.**

The **HERO Designer Source Code** package is an official product Hero Games sells, offered
precisely so people can build software that works with HD. Its product page says so
directly: *"many potential software projects for the HERO System could make use of
portions of the source code which drives HERO Designer. It is for this reason that we are
pleased to offer access to HD's source code."* The purchase receipt and the product page
are retained by the maintainer; they are deliberately not in this repository, which
carries no Hero Games material of any kind. It provides:

- The HERO Designer Java source, updated as the application updates
- The Eclipse project definitions
- Access to the HD Developer Access forum, to ask the developer questions directly

The licensed source is what this port is built on, cited against, and verified against.
The class- and line-level citations throughout this repository (e.g. `Converted from
com.hero.objects.GenericObject.java`) refer to it.

### Licence terms, and how this project sits inside them

Quoted from the product page:

> - You are welcome to change the code or utilize it however you want for your own personal use.
> - If the product you develop is distributed, you will need to pursue licensing with HERO Games -- the terms are exceedingly easy.
> - If the product you develop is intended for sale, there may be a licensing discussion needed with both HERO Games and the developer/owner of the HERO Designer source code. Generally speaking, use of the HERO Designer source code which does not replace or replicate the character generation process does not fall into this category.

**This project follows those guidelines deliberately.**

- The source licence was **purchased**, at full price, from Hero Games' own store.
- Use here is **personal**, which the first condition permits without conditions.
- kirby-cost **does not replace or replicate the character generation process**. It has
  no creation interface; it costs a build HD already produced, and depends on HD's
  templates and licence to run at all.
- It is **noncommercial** — offered under PolyForm Noncommercial 1.0.0, not for sale —
  so the third condition's "intended for sale" case is not engaged.
- **The second condition is acknowledged, not hidden.** This repository is public, which
  the terms treat as distribution. The project is built to sit inside those terms rather
  than at their edge: the source was bought, nothing of Hero Games' is redistributed —
  not the templates, not the character packs, not the test corpus derived from them —
  and the library cannot create a character. Hero Games describe the licensing terms as
  "exceedingly easy", and if they want that arrangement formalised, see below.

If Hero Games, or the owner of the HERO Designer source, sees any of this differently,
we want to hear it — contact the maintainer and it will be acted on.

### Copyright and trademark

HERO Designer is © 2002, 2003, 2006, 2009 by DOJ, Inc. d/b/a Hero Games. **HERO System™**
is DOJ, Inc.'s trademark for its roleplaying system. Game rules content remains the
property of its copyright holders, and no claim is made to ownership of the HERO Designer
application, the game rules, or the game mechanics. This project is an independent work
and is not affiliated with or endorsed by DOJ, Inc. d/b/a Hero Games.

See [`LICENSE`](LICENSE) for the terms this code is offered under
(PolyForm Noncommercial 1.0.0).
