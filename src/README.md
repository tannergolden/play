<!--
title: '💻 APPLICATION SOURCE'
description: 'The source of the move intake and the replays: one folder of standard-library scripts for each, run by their own workflows.'
type: index
-->

<div align="center">

# 💻 APPLICATION SOURCE

<a name="top"></a>

**Where play's code lives: two folders of scripts, standard library only.**

_Run from the root. Each folder is one job._

</div>

---

## 💡 What This Folder Is For

This folder holds the two jobs this repository does, each a folder of
standard-library Python run by its own workflows:

- [`intake/`](intake/README.md) reads every issue opened here as a move, and
  sends it to its game or turns it away. 🎲 Move Intake runs `route.py` and
  `check.py`, and ⏳ Move Sweep runs `sweep.py`.
- [`replays/`](replays/README.md) keeps the replays: 🎬 Replays runs
  `build.py`, which writes the [replays folder](../replays/README.md) at the
  root, where the profile links each replay's page.

It keeps the template's place for code, `src/`, but not the template's three
layers. Each script reads a table, a game's state or a folder, and writes what
it decides for its workflow to carry out, so there is no domain to keep apart
from what it talks to, and each job keeps one folder of its own instead.

This directory is **yours from the first commit**. Nothing here syncs, and
nothing upstream will ever write to it or delete from it: 🔄 Template Sync
leaves this whole folder to you, this README included.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                           | Purpose                                                                                                                                                                                        |
| :------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`intake/`](intake/README.md)   | The router every move passes through, the check that reads each move against its board, and the sweep that answers every move left waiting: the table of the four games and the three scripts. |
| [`replays/`](replays/README.md) | The script that keeps the replays: it draws each game a player's own move won, keeps each game's newest 25, and posts each on its winning move's issue.                                        |
| [`README.md`](README.md)        | This file.                                                                                                                                                                                     |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push to the default branch.
Each folder logs its own files, and the tests for both are in
[`tests/unit/`](../tests/unit/README.md).

---

<div align="center">

**Two jobs, and a folder for each.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](/LICENSE).

</div>
