<!--
title: '🎲 MOVE INTAKE'
description: 'The router every move passes through, and the check that reads each move against its board: the table of the four games, both scripts and their tests.'
tags: [intake, routing, issueops, python]
category: docs
-->

<div align="center">

# 🎲 MOVE INTAKE

<a name="top"></a>

**Every move comes in through here, and only a move goes out.**

_One table. One router. One check. Every title read against all three._

</div>

---

## 💡 What This Folder Is For

Every move on the profile is a link that opens an issue in this repository with
the move already in its title, such as `chess: e2e4 · game 1 · move 1`, for one
of the four games there: Chess, Checkers, Pentago and Tic-Tac. Anyone
on GitHub can open an issue here, with any title at all, so one script reads
the title against one table, and nothing else acts on it.

- **`routes.json` is the table.** Each game's name, the repository and workflow
  its moves go to, the branch that workflow runs on, and the pattern a move for
  that game must match from end to end.
- **`route.py` makes the decision.** It finds the title's game in the table and
  matches the move against that game's pattern. A match becomes the inputs of
  the game's workflow; anything else is turned away. 🎲 Move Intake carries out
  what it decides, and nothing here talks to GitHub.
- **`check.py` spares each game what it could only refuse.** 🎲 Move Intake
  hands it the game's state, `.github/<game>/game.json` in the game's
  repository, and how many issues the player opened here this past hour,
  whatever the game. It answers in the game's own words a move for a game that
  is over, a move already played, a move on the other side's turn, a move for
  the next game while the last one's winning board is still up, or one from a
  player past the hour's share. A state read here can only be behind the game,
  so a move that looks ahead of the board always goes on to the game.

| The issue                            | Decision   | What 🎲 Move Intake does                                                   |
| :----------------------------------- | :--------- | :------------------------------------------------------------------------- |
| A move for a game in the table       | `dispatch` | Starts the game's workflow, reacts 🚀, replies, closes it as completed     |
| A move its game could only turn away | `refuse`   | Replies in the game's words, closes it as not planned, locks it            |
| Anything else, from anyone else      | `reject`   | Replies with how to play, closes it as not planned, locks it               |
| Anything else, from the owner        | `ignore`   | Leaves it open: the owner files their own issues here too                  |
| Anything opened by an app or a bot   | -          | Never runs: the game's own notices, its logbook and outages are left alone |

A move's own issue is locked by its game once it has replied, so nobody but the
owner and the Arbiter writes on an answered issue again.

---

## 🗺️ The Four Games

| Game     | A move's title                        | Workflow       | The move                                                   | The house | GitHub | Who opens                                    |
| :------- | :------------------------------------ | :------------- | :--------------------------------------------------------- | :-------- | :----- | :------------------------------------------- |
| Chess    | `chess: e2e4 · game 1 · move 12`      | `chess.yml`    | `uci`: `e2e4`, or `e7e8q` for promotion                    | White     | Black  | The house, as White                          |
| Checkers | `checkers: 11-15 · game 6 · move 10`  | `checkers.yml` | `move`: `11-15`, `22x15` or `22x15x8`                      | White     | Black  | GitHub, as Black                             |
| Pentago  | `pentago: e4-ur-cw · game 1 · move 9` | `pentago.yml`  | `move`: hole, quarter and way, `e4-ur-cw`; a ghost's, `b5` | White     | Black  | The side the Arbiter draws, after the ghosts |
| Tic-Tac  | `tictac: e5 · game 1 · move 3`        | `tictac.yml`   | `move`: the square, `a1` to `i9`, a ghost's or a mark's    | X         | O      | The side the Arbiter draws, after the ghosts |

Every game's workflow is in `tannergolden/tannergolden`, on `Development`, and
keeps the game on its board in `.github/<game>/game.json` there. Each player's
side never changes: the house, @tannergolden, always plays White, or X, and
GitHub, which is everyone else, always plays Black, or O. Whoever opens a
game moves on the odd moves, and the other side on the even ones. The house
opens Chess, as White. GitHub opens Checkers, as Black, since Black moves first
in American checkers. Pentago and Tic-Tac open under the Ghost Rule instead.
Once a fresh board's start has come, the Arbiter draws the side that places the
first ghost, which the state records as `places`: `house` or `github`. The
other side places the second, and the state keeps both in `ghosts`. As the
second goes down, the Arbiter draws the side that makes the first move,
recorded as `opens`. A move's number counts every turn, the ghosts included,
so moves 1 and 2 are the ghosts and move 3 is the opener's first move.
[ADR-0001](../docs/adrs/ADR-0001-Four-Games-One-Arbiter.md) and
[its amendment](../docs/adrs/ADR-0001-Four-Games-One-Arbiter.md#-amendment-the-ghost-rule)
record why.

**What `check.py` says**, word for word as the game would, and only ever one of
these:

| The move                                                            | The reply's first line                                                                |
| :------------------------------------------------------------------ | :------------------------------------------------------------------------------------ |
| One from a player past 30 issues here this hour, all games together | 🐢 **Slow down**: you've opened 31 issues here in the last hour, more than the 30 ... |
| For a game that is over                                             | ⌛ **Game 8 is over**, so `e5` wasn't played.                                         |
| For a move already on the board                                     | ⌛ **Too late: move 3 is already on the board**, so `e5` wasn't played.               |
| On @tannergolden's turn, from anyone else                           | ⏳ **It's @tannergolden's turn as X**, so `e5` wasn't played.                         |
| On GitHub's turn, from @tannergolden                                | ⏳ **It's GitHub's turn as O**, so `e5` wasn't played.                                |
| On @tannergolden's ghost, from anyone else                          | ⏳ **It's @tannergolden's turn to place a ghost**, so `e5` wasn't played.             |
| On GitHub's ghost, from @tannergolden                               | ⏳ **It's GitHub's turn to place a ghost**, so `e5` wasn't played.                    |
| For the next game, while the last one's winning board is still up   | ⏳ **Game 10 opens 14 Oct**, so `e5` wasn't played.                                   |

- **The limit is one hourly budget for all four games**: `LIMIT = 30` issues
  opened here in the last hour, whatever the game. The owner is never limited,
  and a count that could not be made limits nobody.
- **A finished game's winning board stays up for two days.** Meanwhile the
  state already holds the next game, with no moves and a `started` still to
  come, and a move for it, or for an earlier game, is told the day it opens, as
  the page writes days, in EST.
- **A side is only ever named when it is certain.** The house opens every game
  of Chess and GitHub every game of Checkers, so a state that could not be read
  still turns away a move from the wrong side there. In Pentago and Tic-Tac a
  ghost's side depends on `places` and a move's on `opens`, so a state that
  could not be read, a draw the Arbiter has not made yet, or a game after the
  one on the board leaves the side to the game. A ghost's reply says `place`
  in Tic-Tac and `set` in Pentago, as each game does.
- **A turn already on the board is named as the score sheet writes it.** In
  Pentago and Tic-Tac the ghosts have a row of their own, `G. e5` and
  `G... b8`, and each move is numbered among the moves alone, so move 3 is
  `1. Xd4`.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                            | Purpose                                                                                  |
| :------------------------------- | :--------------------------------------------------------------------------------------- |
| [`check.py`](check.py)           | Turn a move away here, before it starts its game, when the game could only turn it away. |
| [`README.md`](README.md)         | This file.                                                                               |
| [`route.py`](route.py)           | Route one move issue to the game it names, or turn it away.                              |
| [`routes.json`](routes.json)     | Every game the intake serves: where its moves go, and what a move for it looks like.     |
| [`test_check.py`](test_check.py) | Tests for the pre-check of all four games.                                               |
| [`test_route.py`](test_route.py) | Tests for the move router.                                                               |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push, from each file's own
description.

---

## 📨 What A Game Receives

The game's workflow starts through `workflow_dispatch`, on the branch its row
names, with one input for every group its pattern names, plus three more that
come from the issue rather than from its title:

| Input       | Holds                                                           |
| :---------- | :-------------------------------------------------------------- |
| `issue`     | The issue's number here, for the game's reply                   |
| `player`    | The login of whoever opened it                                  |
| `player_id` | Their numeric ID, which stays the same when their login changes |

For Chess that adds `uci`, `game` and `move_number`, and for Checkers, Pentago
and Tic-Tac `move`, `game` and `move_number`. Every value a pattern
captures is one short token of letters, digits and `_.+#=-`, whatever the
pattern itself would allow, so a loose pattern can never pass a sentence
along.

> [!IMPORTANT]
> **The game's workflow declares every input it is sent**, or GitHub refuses
> the dispatch, and the move fails with a reply on its issue. It also treats
> each one as untrusted: they are checked here, and checked again there.

---

## ➕ Adding A Game

1. **Give the game's workflow a `workflow_dispatch` trigger** with an input for
   every group in its pattern, plus `issue`, `player` and `player_id`.
2. **Add its row to `routes.json`**, keyed by the game's name in lower case,
   with `repository`, `workflow`, `ref` and `pattern`. Name every part of the
   move worth passing on as a group, such as `(?P<uci>...)`.
3. **Install the GitHub App on the game's repository**, with Actions write, so
   the intake can start its workflow there.
4. **Teach `check.py` the game**, in `GAMES`: the input its move comes in, the
   key its state keeps a move's notation under, who opens it, or its ghost's
   verb where the Ghost Rule opens it, and the words for the house's side and
   for GitHub's.
5. **Add the new game's titles to `test_route.py`**, both the ones that go
   through and the ones that must not, and its refusals to `test_check.py`,
   word for word.

The table is checked before any title is read. A row that names a reserved
input, a pattern that does not compile, or a repository that is not
`owner/name` stops the run with an error naming the row.

---

## 🚀 Running The Tests

From the root of the repository:

```bash
python3 -m unittest discover -s intake -p 'test_*.py'
```

`checks.yml` runs the same command as part of the `ci` job's `test-command`,
after the template's own script tests.

---

<div align="center">

**Anyone can knock. Only a move gets through.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](../LICENSE).

</div>
