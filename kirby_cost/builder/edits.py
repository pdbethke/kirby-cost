"""Edits on a build doc: add, replace or remove an element, by HD's ``ID``.

The builder's first layer (two-databases spec §4a). It works on the JSON
build doc `LoadedHero.export(format="json")` writes: a transport encoding of
the HDC element tree (``{tag, attrs, children}``) in which HD's element IDs
survive. Editing that tree, rather than a second model of a character, means
there is no field list here to drift from the loader: `load_build(doc,
format="json")` costs the result exactly as it costs any other build.

Two callers, one function:

* a CAMPAIGN keeps a character's base in the codex and stores only its own
  changes, then blends them over the base (`apply`);
* an AI builds NPCs, bases and equipment by proposing the same edits.

TARGETING. Every element that can be bought carries ``ID``; framework slots
are siblings in their section pointing at the framework with ``PARENTID``
(HD's own layout). So an edit needs only an ``ID`` to replace or remove, and
a section tag (``"POWERS"``, ``"SKILLS"`` ...) to add into.

NOTHING IS PATCHED OVER. An edit that does not fit the doc is refused by
name (`EditConflict`), never skipped: a replace or remove of an ID the doc
lacks, a replacement that changes its own ID, an add whose ID (or any ID
inside it) is taken, an add whose ``PARENTID`` names nothing, an add into a
section the build lacks, and a remove that would leave slots pointing at a
framework that is gone. A campaign that hits one of these resolves it as a
new version; an AI that hits one is told what it got wrong.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Iterable, Union

Node = dict[str, Any]


class EditConflict(Exception):
    """An edit that does not fit the build it was applied to."""


@dataclass(frozen=True)
class Replace:
    """Put ``node`` where the element with ``hd_id`` is. ``node`` keeps that
    ``ID``: a replacement is the same purchase, changed."""

    hd_id: str
    node: Node


@dataclass(frozen=True)
class Add:
    """Append ``node`` to the build's ``section`` (``"POWERS"``, ...). A slot
    states its framework in its own ``PARENTID``."""

    section: str
    node: Node


@dataclass(frozen=True)
class Remove:
    """Take the element with ``hd_id`` off the build."""

    hd_id: str


Edit = Union[Replace, Add, Remove]


def _id(node: Node) -> str | None:
    return node.get("attrs", {}).get("ID")


def _walk(node: Node):
    yield node
    for child in node.get("children", []) or []:
        yield from _walk(child)


def _ids(root: Node) -> set[str]:
    return {i for n in _walk(root) if (i := _id(n)) is not None}


def _locate(root: Node, hd_id: str) -> tuple[Node, int] | None:
    """(parent, index) of the element with ``hd_id``."""
    for parent in _walk(root):
        for i, child in enumerate(parent.get("children", []) or []):
            if _id(child) == hd_id:
                return parent, i
    return None


def _apply_one(root: Node, edit: Edit) -> None:
    if isinstance(edit, Replace):
        where = _locate(root, edit.hd_id)
        if where is None:
            raise EditConflict(f"replace {edit.hd_id}: the build has no element with that ID")
        if _id(edit.node) != edit.hd_id:
            raise EditConflict(
                f"replace {edit.hd_id}: a replacement keeps its ID, and this one "
                f"has {_id(edit.node)!r}")
        inner = _ids(edit.node) - {edit.hd_id}
        taken = inner & (_ids(root) - _ids(where[0]["children"][where[1]]))
        if taken:
            raise EditConflict(f"replace {edit.hd_id}: IDs already in the build: {sorted(taken)}")
        parent, i = where
        parent["children"][i] = copy.deepcopy(edit.node)
        return

    if isinstance(edit, Add):
        section = next((c for c in root.get("children", []) or []
                        if c.get("tag") == edit.section), None)
        if section is None:
            raise EditConflict(f"add to {edit.section}: the build has no such section")
        new = _ids(edit.node)
        if _id(edit.node) is None:
            raise EditConflict(f"add to {edit.section}: the element has no ID")
        taken = new & _ids(root)
        if taken:
            raise EditConflict(f"add to {edit.section}: IDs already in the build: {sorted(taken)}")
        parent_id = edit.node.get("attrs", {}).get("PARENTID")
        if parent_id and parent_id not in _ids(root):
            raise EditConflict(
                f"add {_id(edit.node)}: its PARENTID {parent_id!r} names no "
                "framework in the build")
        section.setdefault("children", []).append(copy.deepcopy(edit.node))
        return

    if isinstance(edit, Remove):
        where = _locate(root, edit.hd_id)
        if where is None:
            raise EditConflict(f"remove {edit.hd_id}: the build has no element with that ID")
        slots = sorted(_id(n) for n in _walk(root)
                       if n.get("attrs", {}).get("PARENTID") == edit.hd_id)
        if slots:
            raise EditConflict(
                f"remove {edit.hd_id}: slots still name it as their framework: "
                f"{slots}; remove them first")
        parent, i = where
        del parent["children"][i]
        return

    raise TypeError(f"not a builder edit: {edit!r}")


def apply(doc: dict, edits: Iterable[Edit]) -> dict:
    """A new build doc: ``doc`` with ``edits`` applied in order. ``doc`` is
    not changed. Raises `EditConflict` naming the first edit that does not
    fit."""
    out = copy.deepcopy(doc)
    root = out["document"]
    for edit in edits:
        _apply_one(root, edit)
    return out


__all__ = ["Add", "Edit", "EditConflict", "Remove", "Replace", "apply"]
