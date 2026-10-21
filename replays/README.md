<!--
title: '🎬 REPLAYS'
description: 'Every game a player''s own move won, played again: each game''s newest 25 replays, the index of every one ever made, and the script that keeps them.'
type: index
-->

<div align="center">

# 🎬 REPLAYS

<a name="top"></a>

**Every game a player's own move won, played again.**

_Drawn once. Kept twenty-five to a game. Posted where it was won._

</div>

---

## 💡 What This Folder Is For

When a person's own move wins a game on the profile, the game's engine in
tannergolden/tannergolden writes down what every turn did, beside the game's
record: `.github/<game>/games/game-<N>.replay.json`. A draw gets none, and
neither does a win the Arbiter's move made, or a Pentago turn that made five
for the other side. **🎬 Replays** reads those facts, has the kit,
[tannergolden/markdown](https://github.com/tannergolden/markdown), play the
game again from them, and keeps the replay here, four files to a replay:

| File                       | Holds                                                                                     |
| :------------------------- | :---------------------------------------------------------------------------------------- |
| `<game>/game-<N>-day.svg`  | The replay by day: every move again on the game's own board, then the finale, on a loop   |
| `<game>/game-<N>-dark.svg` | The same, by dark                                                                         |
| `<game>/game-<N>.json`     | The facts it was drawn from, copied from the profile, so a redraw never needs the profile |
| `<game>/game-<N>.md`       | Its page, which the profile's final board links: who won which game, when, and how        |

- **`build.py` decides, and writes what it decides.** Which won games are new,
  what leaves the folder, what is said in each comment, and every page, the
  index and the gallery in the root README. The workflow,
  [`replay.yml`](../.github/workflows/replay.yml), commits and pushes what it
  writes, and nothing here is ever written from an issue.
- **The kit draws, and only the kit.** It plays every move with the board's
  own motion, rings the winner and fades the losing side, and draws each
  player as a halftone of their GitHub avatar: a 48 by 48 grey PGM made from
  `https://avatars.githubusercontent.com/u/<id>?s=96` with ImageMagick. A
  player whose avatar can't be had is drawn by their initials, and the run
  goes on.
- **A replay is drawn in the theme the page was won in**, the `theme:` the
  profile's Markdown workflow hands the kit: a print as it is, and any other
  theme in blackprint. The index keeps it, so a redraw keeps the same look.

---

## 🗂️ The Index

[`index.json`](index.json) lists every replay ever made, in the order they
were made, whether it is still in the folder or not. A won game it lists is
never drawn again, so no winning move's issue ever carries two replays.

| Field     | Holds                                                                                                 |
| :-------- | :---------------------------------------------------------------------------------------------------- |
| `key`     | The game: `chess`, `checkers`, `pentago` or `tictac`                                                  |
| `game`    | The game's number                                                                                     |
| `winner`  | The side that won: `house` or `github`                                                                |
| `by`      | The winner's login when they won                                                                      |
| `by_id`   | The winner's account ID, which stays the same when their login changes                                |
| `players` | Every account that played a turn of the game, the owner's included                                    |
| `issue`   | The winning move's issue here, or `null` for a move the owner ran by hand                             |
| `ended`   | When the game ended, in UTC                                                                           |
| `theme`   | The page's theme it was won in, which every drawing of it is drawn in                                 |
| `commit`  | The commit it was first saved in, filled in after the push                                            |
| `drawn`   | The commit that holds its drawing now: the same, until it is drawn again                              |
| `comment` | The ID of the Official Arbiter's comment on the winning move's issue                                  |
| `shows`   | The commit whose pictures that comment plays, or `null` once it says the replay was taken down        |
| `gone`    | The accounts found deleted: drawn as empty dials, or, when the winner's is one, the replay taken down |
| `kept`    | Whether its four files are still in the folder                                                        |

---

## ✂️ Twenty-Five A Game

Each game keeps its newest 25 replays, by game number. The 26th takes its
game's oldest out of the folder in the same commit: its four files go, and its
row in the index stays, with `kept` false. A replay taken down doesn't count
toward the 25, and a won game older than its game's newest 25 is never drawn,
since it would only leave in the same commit.

**The files that leave stay in git's history on purpose.** The comment on the
winning move pins both pictures, and the link to its page, to the commit that
saved them, as
`https://raw.githubusercontent.com/tannergolden/play/<sha>/replays/<game>/game-<N>-day.svg`,
so a replay keeps playing there long after it has left the folder.

The gallery in the [root README](../README.md#-replays) shows the newest 12
of all four games as pictures, two to a row, each a link to its page. Each
picture plays its whole game as the page opens, so every other replay still
here is a link, by game.

---

## 💬 The Comment

Once a replay is pushed, the Official Arbiter posts it on its winning move's
issue: who won, the replay, as a `<picture>` that plays the dark file for a
reader whose setting is dark, and a link to its page. Its first line, which
GitHub doesn't show, names the replay, such as `<!-- replay: pentago game 3 -->`,
so a run that finds the comment already there points it rather than posting a
second. A second, small commit records each comment's ID and the commit its
pictures play from.

A move's issue is locked once it is answered, so, as the games do, the Arbiter
unlocks it to speak if it must, and locks it again. A comment that doesn't go
through, or a run whose Arbiter's token wasn't minted, leaves the replay saved
and its comment for the next run, which tries again.

---

## 🪦 When An Account Is Gone

Once a day, at 09:11 UTC, and whenever 🎬 Replays is run by hand with
`accounts` ticked, every account behind a replay still here is looked up,
each once, with `gh api /user/<id>`. The owner's is never looked up.

| GitHub answers                         | What becomes of the replay                                                                |
| :------------------------------------- | :---------------------------------------------------------------------------------------- |
| A 404 for the winner's account         | Taken down: its four files and its picture go, and its comment says why, in one line      |
| A 404 for another player's account     | Drawn again, that player an empty dashed dial with no name, and its comment pointed at it |
| The account, for everyone              | Nothing                                                                                   |
| Anything else: refused, limited, fails | Nothing: only a 404 says an account is gone, as on the profile's Hall of Fame             |

An account found gone stays gone: it is never looked up again, a replay drawn
after it is drawn with its empty dial from the start, and a won game whose
winner's account is gone is never drawn. Nothing is ever rewritten in git's
history, so a replay taken down leaves the folder and its comment, and only
those.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                             | Purpose                                                                                                            |
| :-------------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| [`fixtures/`](fixtures/README.md) | The facts of four won games, one of each, as the profile's engine writes them: what the tests draw a replay from.  |
| [`build.py`](build.py)            | Keep the replays: draw each game a player's own move won, keep each game's newest 25, and post each on its issue.  |
| [`index.json`](index.json)        | Every replay &#x1F3AC; Replays has made, in the order it made them, kept here or not, so none is ever drawn twice. |
| [`README.md`](README.md)          | This file.                                                                                                         |
| [`test_build.py`](test_build.py)  | Tests for the replays: what is drawn, what is kept, what is said, and what an account that is gone takes down.     |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push, from each file's own
description. Each game's folder comes with its first replay, and holds nothing
but its replays' files.

---

## 🚀 Running The Tests

From the root of the repository:

```bash
python3 -m unittest discover -s replays -p 'test_*.py'
```

`checks.yml` runs the same command as part of the `ci` job's `test-command`,
after the intake's. The last test has the real kit draw every game in
[`fixtures/`](fixtures/README.md), when the kit is checked out at
`/home/user/markdown`, or at the `markdown-kit.py` that `MARKDOWN_KIT` names,
and is skipped when it isn't.

---

## 🔗 See also

- [Cross-Repository Contracts](../docs/references/Cross-Repository-Contracts.md#-the-replay-facts-and-the-theme) - the facts and the theme a replay is drawn from, and how the kit is run
- [Troubleshooting A Move](../docs/operations/Troubleshooting-Moves.md#-when-a-replay-is-missing) - a replay missing, waiting on its comment, or drawn by initials

---

<div align="center">

**Won once. Played again, every time the page opens.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](../LICENSE).

</div>
