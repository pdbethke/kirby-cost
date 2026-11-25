"""Edits on a build doc: add, replace or remove a purchase, by HD's ``ID``.

The builder's first layer (two-databases spec §4a). It works on the CURATED
build doc (`kirby_cost.io.build_json`: `to_build_json` writes it,
`build_from_json` costs it), the shape a relational store keeps: one object
per purchase, with HD's own ``id``, its framework named by ``parent``, and
its modifiers and adders nested inside it. So an edit's payload is exactly
what a store keeps as one purchase's rows, and blending a campaign's edits
over a codex base never converts between shapes (Peter, 2026-11-25, option
A). The HDC element tree (`export(format="json")`) stays kirby-cost's
import/export transport; it is not edited here.

Two callers, one function:

* a CAMPAIGN keeps a character's base in the codex and stores only its own
  changes, then blends them over the base (`apply`);
* an AI builds NPCs, bases and equipment by proposing the same edits.

TARGETING. Every purchase carries ``id``; framework slots are siblings in
their section naming the framework in ``parent`` (HD's own layout). An edit
needs only an id to replace or remove, and a `Section` to add into. A
purchase is edited WHOLE: changing a modifier is a `Replace` of the
purchase that carries it.

NOTHING IS PATCHED OVER. An edit that does not fit the doc is refused by
name (`EditConflict`), never skipped: a replace or remove of an id the doc
lacks, a replacement that changes its own id, an add whose id (or any id
inside it) is taken, an add whose ``parent`` names nothing, and a remove
that would leave slots pointing at a framework that is gone. A campaign
that hits one of these resolves it as a new version; an AI that hits one is
told what it got wrong.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Union

from kirby_cost.io.build_json import Section

#: One purchase in the curated build doc.
Obj = dict[str, Any]

#: Where a purchase carries other objects that may have ids of their own.
_NESTED = ("sub_powers", "modifiers", "adders")


class EditConflict(Exception):
    """An edit that does not fit the build it was applied to."""


@dataclass(frozen=True)
class Replace:
    """Put ``obj`` where the purchase with ``hd_id`` is. ``obj`` keeps that
    ``id``: a replacement is the same purchase, changed."""

    hd_id: str
    obj: Obj


@dataclass(frozen=True)
class Add:
    """Append ``obj`` to the build's ``section``. A slot names its framework
    in its own ``parent``."""

    section: Section
    obj: Obj


@dataclass(frozen=True)
class Remove:
    """Take the purchase with ``hd_id`` off the build."""

    hd_id: str


Edit = Union[Replace, Add, Remove]


def _walk(obj: Obj) -> Iterator[Obj]:
    yield obj
    for key in _NESTED:
        for child in obj.get(key) or []:
            yield from _walk(child)
    rec = obj.get("endurance_reserve_rec")
    if rec is not None:
        yield from _walk(rec)


def _ids_in(obj: Obj) -> set[str]:
    return {str(o["id"]) for o in _walk(obj) if o.get("id") is not None}


def purchases(doc: dict) -> Iterator[tuple[Section, Obj]]:
    """Every purchase in ``doc``, with its section, in the doc's order."""
    for section in Section:
        for obj in doc.get(section.key) or []:
            yield section, obj


def ids(doc: dict) -> set[str]:
    """Every id ``doc`` holds, nested ones included."""
    out: set[str] = set()
    for _, obj in purchases(doc):
        out |= _ids_in(obj)
    return out


def _locate(doc: dict, hd_id: str) -> tuple[list, int] | None:
    """(section list, index) of the purchase with ``hd_id``."""
    for section in Section:
        objs = doc.get(section.key) or []
        for i, obj in enumerate(objs):
            if str(obj.get("id")) == hd_id:
                return objs, i
    return None


def _apply_one(doc: dict, edit: Edit) -> None:
    if isinstance(edit, Replace):
        where = _locate(doc, edit.hd_id)
        if where is None:
            raise EditConflict(f"replace {edit.hd_id}: the build has no purchase with that ID")
        if str(edit.obj.get("id")) != edit.hd_id:
            raise EditConflict(
                f"replace {edit.hd_id}: a replacement keeps its ID, and this one "
                f"has {edit.obj.get('id')!r}")
        objs, i = where
        inner = _ids_in(edit.obj) - {edit.hd_id}
        taken = inner & (ids(doc) - _ids_in(objs[i]))
        if taken:
            raise EditConflict(f"replace {edit.hd_id}: IDs already in the build: {sorted(taken)}")
        objs[i] = copy.deepcopy(edit.obj)
        return

    if isinstance(edit, Add):
        if not isinstance(edit.section, Section):
            raise TypeError(f"add: section must be a Section, not {edit.section!r}")
        if edit.obj.get("id") is None:
            raise EditConflict(f"add to {edit.section.key}: the purchase has no ID")
        taken = _ids_in(edit.obj) & ids(doc)
        if taken:
            raise EditConflict(
                f"add to {edit.section.key}: IDs already in the build: {sorted(taken)}")
        parent = edit.obj.get("parent")
        if parent is not None and _locate(doc, str(parent)) is None:
            raise EditConflict(
                f"add {edit.obj['id']}: its parent {parent!r} names no "
                "framework in the build")
        doc.setdefault(edit.section.key, []).append(copy.deepcopy(edit.obj))
        return

    if isinstance(edit, Remove):
        where = _locate(doc, edit.hd_id)
        if where is None:
            raise EditConflict(f"remove {edit.hd_id}: the build has no purchase with that ID")
        slots = sorted(str(o["id"]) for _, o in purchases(doc)
                       if str(o.get("parent")) == edit.hd_id)
        if slots:
            raise EditConflict(
                f"remove {edit.hd_id}: slots still name it as their framework: "
                f"{slots}; remove them first")
        objs, i = where
        del objs[i]
        return

    raise TypeError(f"not a builder edit: {edit!r}")


def apply(doc: dict, edits: Iterable[Edit]) -> dict:
    """A new build doc: ``doc`` with ``edits`` applied in order. ``doc`` is
    not changed. Raises `EditConflict` naming the first edit that does not
    fit."""
    out = copy.deepcopy(doc)
    for edit in edits:
        _apply_one(out, edit)
    return out


__all__ = ["Add", "Edit", "EditConflict", "Obj", "Remove", "Replace", "apply",
           "ids", "purchases"]
