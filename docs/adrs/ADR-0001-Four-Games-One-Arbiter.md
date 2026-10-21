<!--
title: '📄 ADR-0001: FOUR GAMES, ONE ARBITER'
description: 'Chess, Checkers, Connect Four and Tic-Tac-Toe, and no other game, share one intake, one Arbiter, one Hall of Fame and one leaderboard, and each keeps its own voice, board and rules.'
type: record
status: 'Accepted'
date: '2026-10-12'
evidence: 'N/A'
-->

<div align="center">

# 📄 ADR-0001: FOUR GAMES, ONE ARBITER

<a name="top"></a>

**Chess, Checkers, Connect Four and Tic-Tac-Toe, and no other game, share one intake, one Arbiter, one Hall of Fame and one leaderboard, and each keeps its own voice, board and rules.**

_Formalized rationale. Transparent intent. Auditable evolution._

</div>

---

> [!NOTE]
> **Amended on 2026-10-13.** Tic-Tac and Pentago have taken the places of Tic-Tac-Toe and Connect Four, and both open under the Ghost Rule in place of the Arbiter's random first move. The record below stands as it was decided, and [its amendment](#-amendment-the-ghost-rule) says what changed.

---

## 📋 Meta Information

| Attribute     | Specification                              |
| :------------ | :----------------------------------------- |
| **Deciders**  | Tanner Golden                              |
| **Consulted** | Claude Code                                |
| **Informed**  | Everyone who plays on @tannergolden's page |

---

## 🎯 Context & Problem Statement

The profile plays one game today: chess, @tannergolden as White against GitHub, anyone else, as Black. A player picks a move under the board on the profile; its link opens an issue here; the [intake](../../intake/README.md) routes it to the game's workflow; the game rules on it; the Official Arbiter replies on the issue; and [tannergolden/markdown](https://github.com/tannergolden/markdown) draws the board, its Hall of Fame and its leaderboard on the page.

Three more games are coming, chosen as tiers of complexity for GitHub to choose between:

| Tier | Game         | Positions                                                  | Solved                                                             |
| :--- | :----------- | :--------------------------------------------------------- | :----------------------------------------------------------------- |
| 4    | Chess        | about 10⁴³ to 10⁵⁰                                         | Not at all: more paths through a game than atoms in the universe   |
| 3    | Checkers     | about 5 × 10²⁰                                             | Weakly, in 2007: perfect play draws                                |
| 2    | Connect Four | about 4.5 × 10¹² (4,531,985,219,092 by John Tromp's count) | Weakly in 1988, strongly in 1995: the first player can force a win |
| 1    | Tic-Tac-Toe  | about 765                                                  | Long ago: perfect play always draws                                |

No game follows these: four is the whole set. The question is what the four share, and what each keeps for itself, so that a player has one place to play and one standing, while each game still feels like its own.

---

## 🚦 Decision Drivers

- **One front door**: every game is played the same way, from a link on the profile to an issue here, answered by the same Arbiter.
- **One standing**: a player's record across all four games sits in one Hall of Fame and one leaderboard.
- **Four worlds**: each game must feel unique, in its voice, its board and its rules, not four skins of one game.
- **Fair limits**: the hourly cap must never stop a player who plays every game, and must still stop a flood.
- **A closed set**: with exactly four games, the shared parts are built for four from the start, not for any number.

---

## 🏗️ Considered Options

1. **A system per game**: its own intake, Arbiter, Hall of Fame and leaderboard.
2. **One system, the same for every game**: every game through identical machinery and words.
3. **One frame, each game its own**: the machinery shared, and in every shared part a place for each game to be itself.

---

## ✅ Decision Outcome

**Chosen Option**: One frame, each game its own

### Rationale for Selection

What the four share:

- **The intake.** One router and one table, `intake/routes.json`, with a row per game. One pre-check, `intake/check.py`, that knows each game's state, its turns and its words. One queue per player, one locking of answered issues, and one notice when the Arbiter is down.
- **The hourly cap.** One overall budget per player, 30 issues an hour, counted across all four games together and balanced so that a player active in every game never meets it while a flood does.
- **The Arbiter.** One App, one way of laying out a reply, and one logbook for the moves it plays when a side lets a week pass.
- **The clock.** One clock for all four games, twice an hour and off the hour, ticking every game in one run. A week to move, then the Arbiter plays a random legal move, in every game; and a fresh board comes once a winning board's two days are up.
- **The winning board.** Every finished game, chess included, shows its winning board for two days, and then a fresh board comes by itself. A move for the next game before then is turned away with the day it opens.
- **One Hall of Fame.** A shared podium across all four games, with each game's results under it.
- **One leaderboard.** One table: the owner's row on top, then GitHub's players. Each game has its own column of wins, then come the moves and the wins across all four. A win counts only for the player who makes the winning move, and nothing the Arbiter plays counts for anyone.
- **The page.** The kit's frame for drawing a board, its panel and its motion, and the README block round it: the folded list of legal moves, the Hall of Fame and the leaderboard.

What each game keeps for itself:

- **Its door**: its row in the table, its titles in the one issue form, and its own words in the one pre-check, which turns away at the door what the game could only refuse.
- **Its rules**: its own engine, and its own words for how a game ends.
- **Its voice**: chess names every move as an army's order; every other game gets a voice of its own, with its own move names and emoji.
- **Its board**: its own pieces, notation and motion, drawn in the same frame and hand as chess, so the four read as one family.
- **Its sides**: each player's side never changes, and who moves first changes only in the two games the Arbiter opens. The house, @tannergolden, always plays White in Chess, Checkers and Connect Four, and X in Tic-Tac-Toe; GitHub always plays Black, or O. The house opens every game of Chess, as White, the side that moves first in chess. GitHub opens every game of Checkers, as Black, since Checkers follows American checkers, where Black moves first. The Arbiter opens every game of Connect Four and Tic-Tac-Toe, for a side drawn at random, with a random legal move, because in both the first player has a far higher chance of winning: Connect Four is solved, and its first player can force a win by opening in the centre column, as James D. Allen and Victor Allis showed independently in 1988; and of the 255,168 possible games of Tic-Tac-Toe, counted with X moving first, X wins 131,184, O wins 77,904 and 46,080 are drawn, so any slip favours whoever moves first. The side the Arbiter opens for moves first, so O moves first in a game of Tic-Tac-Toe it opens for GitHub.
- **Its column**: its own wins on the leaderboard.

---

## 📈 Consequence Matrix

| Category         | Impact / Consequence |
| :--------------- | :------------------- |
| **Positive (+)** | One place to play and one standing for every player. A fix to the shared machinery reaches all four games at once. A new game's work is only what makes it itself: its rules, voice, board and door. |
| **Negative (-)** | The shared parts must be built for four games from the start, the leaderboard's columns among them. A change to the shared frame touches all four games, so it is tested against all four. |
| **Neutral (~)**  | Chess goes on as it is while the others are built; it is the first of the four, not a special case. |

---

## ⚖️ Trade-off Comparative

### Option A: A system per game

- ✅ Each game is free in everything.
- ❌ Four doors, four standings, and every fix made four times; a player's record splits in four.

### Option B: One system, the same for every game

- ✅ The least to build.
- ❌ Four games that feel like one: the same words, the same board, the same voice.

### Option C: One frame, each game its own

- ✅ One door and one standing, with four games that each feel like their own.
- ❌ Every shared part needs a place for each game's own words and look, designed in from the start.

---

## 👻 Amendment: The Ghost Rule

_Amended on 2026-10-13. The decision above stands, but for what follows._

**Two of the four games changed.** Tic-Tac took Tic-Tac-Toe's place as tier 1: Tic-Tac-Toe on nine boards at once, also known as Ultimate Tic-Tac-Toe, where the square a mark takes sends the other side to the board in that place, and three boards in a row wins. Pentago took Connect Four's place as tier 2: six holes by six in four quarters that turn, where a move sets a marble and then turns any quarter a quarter turn, and five in a row wins.

**The Ghost Rule replaced the Arbiter's random first move** in both, to take the first move's edge from both sides:

1. **Once a fresh board's start has come, the Arbiter draws the side that places the first ghost**, which the game's state records as `places`.
2. **That side places its ghost, and then the other side places the second.** In Tic-Tac a ghost locks a square that nobody can take and no line runs through; in Pentago it is a marble that is nobody's, which turns with its quarter.
3. **As the second ghost goes down, the Arbiter draws the side that makes the first move**, anywhere, which the state records as `opens`. From there the two sides take turns.

- **The draws count for nobody**, as nothing the Arbiter plays does. A ghost is a turn like any move: a side that lets a week pass without placing its ghost has one placed for it, at random.
- **Each player's side still never changes.** The house, @tannergolden, plays X in Tic-Tac and White in Pentago, Checkers and Chess, and GitHub plays O, or Black. The draws decide only the order of play, and Chess and Checkers open as before.
- **A move's number counts the ghosts.** Moves 1 and 2 are the ghosts and move 3 is the first move. The score sheet writes the ghosts on a row of their own, `G. e5` and `G... b8`, and numbers each move among the moves alone, so move 3 is `1. Xd4`.
- **The door knows the rule.** The pre-check reads `places`, `ghosts` and `opens` from the game's state and turns away, in the game's own words, a ghost or a move from the side whose turn it isn't. Until the state shows a draw, it leaves the side to the game.

---

## 🔗 Traceability & Links

- [The intake](../../intake/README.md): the router, its table and the pre-check of all four games.
- [The GitHub App](../operations/GitHub-App.md): the Official Arbiter, and splitting its App in two.
- [tannergolden/markdown](https://github.com/tannergolden/markdown): the kit that draws every board, the Hall of Fame and the leaderboard.

### 🔗 See also

> [!TIP]
> Every canonical guide is indexed in the [&#x1F4DA; Standards Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md). If you rename or move a file, update every reference to it across the repository to prevent link drift.

---

<div align="center">

**One decision. One record. Zero ambiguity.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Proprietary; all rights reserved under [LICENSE](../../LICENSE).

</div>
