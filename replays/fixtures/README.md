<!--
title: '🧪 REPLAY FIXTURES'
description: 'The facts of four won games, one of each, as the profile''s engine writes them: what the tests draw a replay from.'
tags: [replays, tests, fixtures, json]
category: docs
-->

<div align="center">

# 🧪 REPLAY FIXTURES

<a name="top"></a>

**Four won games, one of each, as the profile writes them down.**

_Real facts. Never edited by hand._

</div>

---

## 💡 What This Folder Is For

Each file is one game's `game-<N>.replay.json`, exactly as the profile's engine
writes it beside the game's record: every turn's side, notation, words, player
and day, and what it did on the board in its game's own terms. Each is valid by
the kit's own check, and the end-to-end test in
[`test_build.py`](../test_build.py) has the real kit draw all four, then draw
them again once two of their accounts are gone. Between them both sides win:
GitHub in Chess and Pentago, and the house in Checkers and Tic-Tac.

Change one only for a new version of the facts, by taking a game the engine
wrote: a turn edited by hand can draw a board no game could reach.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                          | Purpose                                                                                      |
| :--------------------------------------------- | :------------------------------------------------------------------------------------------- |
| [`checkers.replay.json`](checkers.replay.json) | Checkers game 1, won by @tannergolden with 18... 22x13 in 36 turns, no move left for Black.  |
| [`chess.replay.json`](chess.replay.json)       | Chess game 1, won by @hubot for GitHub with 8... Nf3# in 16 turns.                           |
| [`pentago.replay.json`](pentago.replay.json)   | Pentago game 1, won by @octocat for GitHub with 7. f6-ur-acw# in 15 turns, the ghosts first. |
| [`README.md`](README.md)                       | This file.                                                                                   |
| [`tictac.replay.json`](tictac.replay.json)     | Tic-Tac game 1, won by @tannergolden with 21... Xc3# in 44 turns, the ghosts first.          |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push, and keeps each
description here, since JSON facts carry none of their own.

---

<div align="center">

**Each game, as it was won.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](../../LICENSE).

</div>
