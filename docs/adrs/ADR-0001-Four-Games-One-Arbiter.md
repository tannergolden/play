<!--
title: '📄 ADR-0001: FOUR GAMES, ONE ARBITER'
description: 'Chess, Checkers, Connect Four and Tic-Tac-Toe, and no other game, share one intake, one Arbiter, one Hall of Fame and one leaderboard, and each keeps its own voice, board and rules.'
tags: [adr, architecture, decisions, games, intake, hall-of-fame, leaderboard]
category: docs
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

| Tier | Game         | Positions          | Solved                                                           |
| :--- | :----------- | :----------------- | :--------------------------------------------------------------- |
| 1    | Tic-Tac-Toe  | about 765          | Long ago: perfect play always draws                              |
| 2    | Connect Four | about 4.5 × 10¹³   | Strongly, in 1988: the first player can force a win              |
| 3    | Checkers     | about 5 × 10²⁰     | Weakly, in 2007: perfect play draws                              |
| 4    | Chess        | about 10⁴³ to 10⁵⁰ | Not at all: more paths through a game than atoms in the universe |

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

- **The intake.** One router and one table, `intake/routes.json`, with a row per game. One pre-check step, run for each game's own check. One queue per player, one locking of answered issues, and one notice when the Arbiter is down.
- **The hourly cap.** One overall budget per player, counted across all four games together and balanced so that a player active in every game never meets it while a flood does.
- **The Arbiter.** One App, one way of laying out a reply, and one logbook for the moves it plays when a side lets a week pass.
- **The clock.** A week to move, then the Arbiter plays a random legal move, in every game.
- **One Hall of Fame.** A shared podium across all four games, with each game's results under it.
- **One leaderboard.** One table: the owner's row on top, then GitHub's players. Each game has its own column of wins, and moves and games count across all four.
- **The page.** The kit's frame for drawing a board, its panel and its motion, and the README block round it: the banner, the folded list of legal moves, the Hall of Fame and the leaderboard.

What each game keeps for itself:

- **Its door**: its row in the table, its issue form, and its own pre-check, which turns away at the door, in the game's own words, what the game could only refuse.
- **Its rules**: its own engine, and its own words for how a game ends.
- **Its voice**: chess names every move as an army's order; every other game gets a voice of its own, with its own move names and emoji.
- **Its board**: its own pieces, notation and motion, drawn in the same frame and hand as chess, so the four read as one family.
- **Its sides**: chess's owner always plays White. Who opens each other game is decided when it is built, since Connect Four's first player can force a win.
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

## 🔗 Traceability & Links

- [The intake](../../intake/README.md): the router, its table and the chess pre-check.
- [The GitHub App](../GitHub-App.md): the Official Arbiter, and splitting its App in two.
- [tannergolden/markdown](https://github.com/tannergolden/markdown): the kit that draws every board, the Hall of Fame and the leaderboard.

### 🔗 See also

> [!TIP]
> Every canonical guide is indexed in the [&#x1F4DA; Standards Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md). If you rename or move a file, update every reference to it across the repository to prevent link drift.

---

<div align="center">

**One decision. One record. Zero ambiguity.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
