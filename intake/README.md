<!--
title: '🎲 MOVE INTAKE'
description: 'The router every move passes through: the table of games, the script that reads each title against it, and the tests that hold both to it.'
tags: [intake, routing, issueops, python]
category: docs
-->

<div align="center">

# 🎲 MOVE INTAKE

<a name="top"></a>

**Every move comes in through here, and only a move goes out.**

_One table. One script. Every title read against both._

</div>

---

## 💡 What This Folder Is For

Every move on the profile is a link that opens an issue in this repository with
the move already in its title, such as `chess: e2e4 · game 1 · move 1`. Anyone
on GitHub can open an issue here, with any title at all, so one script reads
the title against one table, and nothing else acts on it.

- **`routes.json` is the table.** Each game's name, the repository and workflow
  its moves go to, the branch that workflow runs on, and the pattern a move for
  that game must match from end to end.
- **`route.py` makes the decision.** It finds the title's game in the table and
  matches the move against that game's pattern. A match becomes the inputs of
  the game's workflow; anything else is turned away. 🎲 Move Intake carries out
  what it decides, and nothing here talks to GitHub.

| The issue                          | Decision   | What 🎲 Move Intake does                                               |
| :--------------------------------- | :--------- | :--------------------------------------------------------------------- |
| A move for a game in the table     | `dispatch` | Starts the game's workflow, reacts 🚀, replies, closes it as completed |
| Anything else, from anyone else    | `reject`   | Replies with how to play, closes it as not planned                     |
| Anything else, from the owner      | `ignore`   | Leaves it open: the owner files their own issues here too              |
| Anything opened by an app or a bot | -          | Never runs: the game's own notices are left alone                      |

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                            | Purpose                                                                              |
| :------------------------------- | :----------------------------------------------------------------------------------- |
| [`README.md`](README.md)         | This file.                                                                           |
| [`route.py`](route.py)           | Route one move issue to the game it names, or turn it away.                          |
| [`routes.json`](routes.json)     | Every game the intake serves: where its moves go, and what a move for it looks like. |
| [`test_route.py`](test_route.py) | Tests for the move router.                                                           |

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

For chess that adds `uci`, `game` and `move_number`. Every value a pattern
captures is one short token of letters, digits and `_.+#=-`, whatever the
pattern itself would allow, so a loose pattern can never pass a sentence along.

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
4. **Add the new game's titles to `test_route.py`**, both the ones that go
   through and the ones that must not.

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
