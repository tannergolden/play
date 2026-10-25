<!--
title: '🏷️ LABELS & REPLIES'
description: 'Every label the issues here carry, with its colour, its description and who makes it, and every reaction, reply and notice the automation posts, with when, from whom and the code that writes it. Consult it when filtering the issues, and before changing a label or a reply.'
type: reference
-->

<div align="center">

# 🏷️ LABELS & REPLIES

<a name="top"></a>

**Every mark a move's issue can get, and every word posted on it, with its source.**

_One name, one colour, wherever it is made._

</div>

---

## 💡 What This Lists

The labels here come from four places: the move form, 🎲 Move Intake and
⏳ Move Sweep in this repository, and each game from its own. A label missing
from the repository is made the first time it is needed, with the same colour
and description wherever it is made, so a change to one is a change to every
place below that makes it. Each reply is fixed text with no title in it; this
page gives its opening line and the code that writes the rest.

How each decision is reached is in [Move Intake](../../src/intake/README.md), and
which identity posts what in
[GitHub App](../operations/GitHub-App.md#-what-players-see).

---

## 🏷️ Labels

| Label             | Colour     | Description                                                                    | Made by                                                                                                | Means                                           |
| :---------------- | :--------- | :----------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------- | :---------------------------------------------- |
| `move`            | `1d76db`   | 🎲 A move for one of the games on the profile.                                 | 🎲 Move Intake, from `MOVE` in `route.py`; the move form gives it as the issue opens, once it exists   | A move, sent on or turned away                  |
| `game: chess`     | `5319e7`   | ♟️ A move for Chess.                                                           | 🎲 Move Intake, from `GAMES` in `route.py`                                                             | The move's game, which no form can know         |
| `game: checkers`  | `d93f0b`   | 🏁 A move for Checkers.                                                        | The same                                                                                               | The same                                        |
| `game: pentago`   | `0e8a16`   | 🌀 A move for Pentago.                                                         | The same                                                                                               | The same                                        |
| `game: tictac`    | `fbca04`   | ❌ A move for Tic-Tac.                                                         | The same                                                                                               | The same                                        |
| `played`          | The game's | The game's                                                                     | The game alone                                                                                         | Played on the board: answered for good          |
| `turned away`     | `b60205`   | ⛔ The Arbiter turned this move away: it wasn't played.                        | 🎲 Move Intake, in ⛔ Turn The Move Away of `intake.yml`, and the game                                 | Not played: answered for good                   |
| `invalid`         | `e4e669`   | This doesn't seem right                                                        | 🎲 Move Intake, from `INVALID` in `route.py`: the shared taxonomy's own label                          | Not a move: answered for good                   |
| `stranded`        | `fbca04`   | 🧯 This move didn't reach its game; it's tried again once the Arbiter is back. | 🎲 Move Intake, in 🧯 Say It Did Not Go Through of `intake.yml`                                        | Waiting to go again; taken off as it is sent on |
| `overdue`         | `d93f0b`   | ⏳ Sent on, but the Arbiter hasn't ruled on it yet.                            | ⏳ Move Sweep, from `OVERDUE` in `sweep.py`                                                            | Waiting to go again; taken off as it is sent on |
| `arbiter-outage`  | `6e7781`   | The Arbiter's own notices                                                      | 🎲 Move Intake, in 🧯 Say It Did Not Go Through; ⏳ Move Sweep, from `OUTAGE` in `sweep.py`; each game | The outage notice                               |
| `arbiter-logbook` | The game's | The game's                                                                     | Each game                                                                                              | The Arbiter's logbook                           |

- **A game the table names but `GAMES` doesn't** is labelled `game: <name>` in
  `ededed`, described as "🎲 A move for <name>.". A new game's sign, name and
  colour go into `GAMES` in `route.py`.
- **⏳ Move Sweep reads the labels.** It never touches an issue answered for
  good, or one labelled `arbiter-outage` or `arbiter-logbook`, and it sends
  `stranded` and `overdue` moves through 🎲 Move Intake again. The owner's own
  issue counts as a move when it carries `move`, or a title the router would
  send on.
- **A label that can't be set is a warning**, never in the way of a move.
- **The shared label taxonomy is here too**, written by ⚖️ Governance's label
  sync from the standards'
  [Repository Labels](https://github.com/tannergolden/standards/blob/Development/docs/references/Repository-Labels.md).
  `invalid` is the one of them the intake gives.

---

## 🗂️ Milestones

The game files each move it rules on in its game's milestone, such as
`Chess · game 1`, as it labels it `played` or `turned away`. Nothing in this
repository makes or names a milestone.

---

## 👀 Reactions

| Reaction | From                                                      | On                                                                                                                               |
| :------- | :-------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------- |
| 👀       | `official-arbiter[bot]`, with a token minted for it alone | Every issue 🎲 Move Intake answers, a move or not, as soon as its title is read; never an issue of the owner's that isn't a move |
| 🚀       | `github-actions[bot]`, 🎲 Move Intake's own token         | A move sent on to its game. ⏳ Move Sweep reads it to tell a move sent on from one never answered, and counts no other 🚀        |

---

## 💬 Replies

| Opening line                                                                                                | Posted by               | On                                                                                       | Then                                                                                 | Written by                                   |
| :---------------------------------------------------------------------------------------------------------- | :---------------------- | :--------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------- | :------------------------------------------- |
| 👋 **This isn't a move, so it's closed.**                                                                   | `github-actions[bot]`   | Anything but a move, from anyone but the owner                                           | `invalid`, closed as not planned, locked                                             | `reply()` in `route.py`                      |
| One of eight, such as ⏳ **It's GitHub's turn as O**, so `e5` wasn't played.                                | `github-actions[bot]`   | A move its game could only turn away                                                     | `turned away`, closed as not planned, locked                                         | `verdict()` in `check.py`                    |
| ⚠️ **Your move didn't reach the board yet**, so nothing's been played.                                      | `github-actions[bot]`   | A move 🎲 Move Intake couldn't send on, unless it was sent again already `stranded`      | `stranded`, locked, left open                                                        | 🧯 Say It Did Not Go Through in `intake.yml` |
| ⏳ **Your move was sent on, but the Arbiter hasn't ruled on it yet.**                                       | `github-actions[bot]`   | A move sent on with no ruling for 15 minutes, once, and only while its issue is unlocked | `overdue`, locked, left open                                                         | `overdue_text()` in `sweep.py`               |
| The game's ruling, in its own words                                                                         | `official-arbiter[bot]` | A move its game played, or turned away                                                   | `played` or `turned away`, its milestone, closed as completed or not planned, locked | The game                                     |
| 🎬 **The replay of game 3 of Pentago**: every move of @octocat's win for GitHub, played again on the board. | `official-arbiter[bot]` | The winning move of a game a player's own move won, once its replay is saved             | The issue left locked, unlocked only to speak                                        | `comment()` in `src/replays/build.py`        |
| 🎬 **The replay of game 3 of Pentago was taken down**, because the account that won it was deleted.         | `official-arbiter[bot]` | The same comment, rewritten once the winner's account is gone                            | -                                                                                    | `taken_down()` in `src/replays/build.py`     |

- **The eight refusals** are listed by their opening lines in
  [the intake's README](../../src/intake/README.md), under The Four Games, each in
  the game's own words, as the game itself would say it.
- **The stranded and overdue replies link the outage notice**, and end the same
  way: the move is sent again by itself once the notice is closed, and there's
  nothing the player needs to do.
- **A replay's comment opens with a line GitHub doesn't show**, such as
  `<!-- replay: pentago game 3 -->`, by which a later run finds the comment
  rather than posting a second. It names the winner, plays the replay pinned to
  the commit that saved it, and links its page.

---

## 📣 The Issues The Automation Opens

| Issue                    | Opened by                                                                                                        | Label                         | Closed by                                                     |
| :----------------------- | :--------------------------------------------------------------------------------------------------------------- | :---------------------------- | :------------------------------------------------------------ |
| `🧯 The Arbiter is down` | 🎲 Move Intake, "so moves aren't reaching the board"; ⏳ Move Sweep, "so moves aren't being ruled on"; or a game | `arbiter-outage`              | The game, as the next move goes through; or the owner         |
| The Arbiter's logbook    | Each game, for the moves the Arbiter plays when a side lets a week pass                                          | `arbiter-logbook`             | -                                                             |
| A failure alert          | 🚨 CI Failure Alerts, when 🎬 Replays or ⏳ Move Sweep fails on the default branch                               | `ci: failure`, the standards' | 🚨 CI Failure Alerts itself, when that workflow next succeeds |

- **The outage notice is opened locked**, and @mentions the owner once, however
  many moves link to it. A run that finds one open links to it rather than
  opening another.
- **None of them is ever a move.** Each is opened by an app or a bot, so
  🎲 Move Intake skips it, and ⏳ Move Sweep leaves it alone.

---

## 🔗 See also

- [Move Intake](../../src/intake/README.md) - each decision, which labels it gives, and the opening line of each refusal
- [Move Intake & Move Sweep](../technical/Move-Intake-&-Move-Sweep.md) - the step that posts each of these, and when it runs
- [Troubleshooting A Move](../operations/Troubleshooting-Moves.md) - what an issue's labels and replies say about where it stopped
- [Replays](../../replays/README.md) - the comment on a winning move, and what becomes of it

---

<div align="center">

**Every mark means one thing, wherever it is made.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Proprietary; all rights reserved under [LICENSE](../../LICENSE).

</div>
