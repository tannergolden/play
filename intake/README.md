<!--
title: '🎲 MOVE INTAKE'
description: 'The router every move passes through, the check that reads each move against its board, and the sweep that answers every move left waiting: the table of the four games, the three scripts and their tests.'
type: index
keywords: [routing, issueops, python]
-->

<div align="center">

# 🎲 MOVE INTAKE

<a name="top"></a>

**Every move comes in through here, and only a move goes out.**

_One table. One router. One check. One sweep. No move left waiting._

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
- **`sweep.py` answers every move left waiting.** ⏳ Move Sweep runs it twice
  an hour: it marks a move whose ruling is overdue, and sends a move that
  never reached its game through 🎲 Move Intake again, as
  [below](#-no-move-left-waiting).

| The issue                            | Decision   | What 🎲 Move Intake does                                                                 |
| :----------------------------------- | :--------- | :--------------------------------------------------------------------------------------- |
| A move for a game in the table       | `dispatch` | Starts the game's workflow, reacts 🚀, and leaves it open for the game's ruling          |
| A move its game could only turn away | `refuse`   | Replies in the game's words, labels it `turned away`, closes it as not planned, locks it |
| Anything else, from anyone else      | `reject`   | Replies with how to play, closes it as not planned, locks it                             |
| Anything else, from the owner        | `ignore`   | Leaves it open: the owner files their own issues here too                                |
| Anything opened by an app or a bot   | -          | Never runs: the game's own notices, its logbook and outages are left alone               |
| A move that can't reach its game     | -          | Labels it `stranded`, tells its player once, locks it, and opens the outage notice       |

Every issue 🎲 Move Intake answers gets the Official Arbiter's 👀 as soon as
its title is read, before anything else is done with it, so whoever opened it
sees at once that it was picked up. The 👀 comes from a token of the
Arbiter's own, with Issues write here alone, and without it the 👀 is left
out and nothing else is. The owner's own issues, which the intake leaves
alone, get none.

**A move gets one reply: its game's ruling.** The intake says nothing on a
move it sends on but its 🚀, and leaves the issue open. The game's Arbiter
replies there once it has played the move or turned it away, labels it
`played` or `turned away`, files it in its game's milestone, such as
`Chess · game 1`, and closes it: as completed if it was played, as not
planned if not. It locks the issue as it replies, so nobody but the owner and
the Arbiter writes on an answered issue again.

### 🏷️ Labels

Every issue answered here is labelled, so moves can be filtered by game and
told apart from everything else:

| The issue                                      | Labels                                                                                   |
| :--------------------------------------------- | :--------------------------------------------------------------------------------------- |
| A move, sent on or turned away                 | `move`, and its game: `game: chess`, `game: checkers`, `game: pentago` or `game: tictac` |
| A move its game played                         | `played`, from the game                                                                  |
| A move turned away, here or by its game        | `turned away`                                                                            |
| A move that couldn't reach its game            | `stranded`, until it is sent again                                                       |
| A move sent on with no ruling after 15 minutes | `overdue`, from ⏳ Move Sweep, until it is sent again                                    |
| Anything else, from anyone else                | `invalid`                                                                                |
| Anything else, from the owner                  | None: it's left as it is                                                                 |

The move form gives `move` as the issue opens. `route.py` names the rest, in
`$RUNNER_TEMP/labels.json`, and 🎲 Move Intake applies them: `move` again, for
a move opened without the form, such as through the API, and the game, which
no form can know. Every name comes from `route.py` (`MOVE`, `INVALID` and
`GAMES`) and the table, never from the title. A label missing from the
repository is made the first time it is needed, with the colour and
description `route.py` gives it, and a label that can't be set is a warning,
never a stop. A new game's label is `game: <name>`; add its sign, name and
colour to `GAMES` in `route.py`, or it is made plain.

The marks a move's issue gets after it is sent on are made the same way, the
first time each is needed, and each is made with the same colour and
description wherever it is made: `turned away` here and by the game, `played`
by the game alone, `stranded` by 🎲 Move Intake, and `overdue` by ⏳ Move
Sweep (`OVERDUE` in `sweep.py`).

---

## ⏳ No Move Left Waiting

A move's issue stays open from its 🚀 until its game rules on it, so an issue
left open too long is one something went wrong with. Twice an hour, at 11 and
41 minutes past, ⏳ Move Sweep runs `sweep.py` over every open issue a player
opened here, and answers each one left waiting:

| What it finds                                                              | What it does                                                                                 |
| :------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| A move sent on, with no ruling for 15 minutes                              | Labels it `overdue`, tells its player once, locks it, and opens the outage notice if none is |
| A move labelled `stranded` or `overdue`                                    | Sends it through 🎲 Move Intake again, once no outage notice is open                         |
| An issue never answered, for 15 minutes                                    | Sends it through 🎲 Move Intake again, whatever the notice                                   |
| The owner's own issues, an app's or a bot's, and anything already answered | Leaves them alone                                                                            |

- **The owner is told once.** The outage notice is the one open issue labelled
  `arbiter-outage`, which 🎲 Move Intake and each game open too, and which
  @mentions the owner once, however many moves it holds up. The next move to
  go through closes it, and the next sweep then sends every waiting move
  again. Closing it by hand, once the fault is fixed, does the same.
- **An outage is probed, not hammered.** While the notice is open, a sweep
  sends only the oldest stranded move again: if it goes through, its game
  closes the notice.
- **A player is told once.** `overdue` comes with a comment only on an issue
  nothing has been said on since its 🚀, and never twice; a move stranded
  again isn't told again.
- **Nothing is played twice.** 🎲 Move Intake reads a move sent again from its
  issue as it is now, through `$RUNNER_TEMP/issue.json` in place of the event,
  and sends it straight to its game, without `check.py`: only the game can
  tell a move already played from that very issue, which it answers as
  played. A move gone stale since is turned away with the reason. The intake
  unlocks the issue for the game's reply, and takes `stranded` and `overdue`
  off as it sends the move.
- **At most 10 issues go again in a sweep**, oldest first; the next sweep
  takes the rest.
- **A schedule can run late.** GitHub starts a scheduled run late when it is
  busy, sometimes by hours, so a move can wait longer than 15 minutes before
  a sweep finds it. The owner can run ⏳ Move Sweep from the Actions tab at any
  time.

The owner can send any issue through the intake again by hand, from the
Actions tab: run 🎲 Move Intake with the issue's number.

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

| Entry                            | Purpose                                                                                                                |
| :------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| [`check.py`](check.py)           | Turn a move away here, before it starts its game, when the game could only turn it away.                               |
| [`README.md`](README.md)         | This file.                                                                                                             |
| [`route.py`](route.py)           | Route one move issue to the game it names, or turn it away.                                                            |
| [`routes.json`](routes.json)     | Every game the intake serves: where its moves go, and what a move for it looks like.                                   |
| [`sweep.py`](sweep.py)           | Answer every issue left waiting: mark the moves whose ruling is overdue, and send again the ones that never got there. |
| [`test_check.py`](test_check.py) | Tests for the pre-check of all four games.                                                                             |
| [`test_route.py`](test_route.py) | Tests for the move router.                                                                                             |
| [`test_sweep.py`](test_sweep.py) | Tests for the sweep.                                                                                                   |

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
> the dispatch, and the move is `stranded`, with a reply on its issue. It also
> treats each one as untrusted: they are checked here, and checked again there.

---

## ➕ Adding A Game

1. **Give the game's workflow a `workflow_dispatch` trigger** with an input for
   every group in its pattern, plus `issue`, `player` and `player_id`.
2. **Add its row to `routes.json`**, keyed by the game's name in lower case,
   with `repository`, `workflow`, `ref` and `pattern`. Name every part of the
   move worth passing on as a group, such as `(?P<uci>...)`.
3. **Install the GitHub App on the game's repository**, with Actions write, so
   the intake can start its workflow there.
4. **Give it a label**: its sign, name and colour in `GAMES` in `route.py`.
5. **Teach `check.py` the game**, in `GAMES`: the input its move comes in, the
   key its state keeps a move's notation under, who opens it, or its ghost's
   verb where the Ghost Rule opens it, and the words for the house's side and
   for GitHub's.
6. **Add the new game's titles to `test_route.py`**, both the ones that go
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

## 🔗 See also

- [Move Intake & Move Sweep](../docs/technical/Move-Intake-&-Move-Sweep.md) - every step of both workflows, what they hand each other, and what strands a move
- [Labels & Replies](../docs/references/Labels-&-Replies.md) - each label's colour and maker, and each reply with the code that writes it
- [Cross-Repository Contracts](../docs/references/Cross-Repository-Contracts.md) - the dispatch, the game state the check reads, and what a game does here
- [Troubleshooting A Move](../docs/operations/Troubleshooting-Moves.md) - a move stranded, overdue or never answered, from what its issue shows

---

<div align="center">

**Anyone can knock. Only a move gets through.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](../LICENSE).

</div>
