<!--
title: '🎬 REPLAYS SCRIPT'
description: 'The script that keeps the replays: it draws each game a player''s own move won, keeps each game''s newest 25, and posts each on its winning move''s issue.'
type: index
-->

<div align="center">

# 🎬 REPLAYS SCRIPT

<a name="top"></a>

**The one script behind every replay.**

_It decides and writes. The workflow pushes. The kit draws._

</div>

---

## 💡 What This Folder Is For

[`build.py`](build.py) is the script 🎬 Replays runs, from
[`replay.yml`](../../.github/workflows/replay.yml). It decides which won games
are new, what leaves the folder, what is said in each comment, and every page,
the index and the gallery in the root README, and writes all of them to the
[replays folder](../../replays/README.md) at the root. The workflow commits and
pushes what it writes, and nothing it writes ever comes from an issue.

What a replay is, what the index keeps, the twenty-five a game, the comment and
what becomes of a replay when an account is gone are all in the
[replays folder's README](../../replays/README.md), beside the replays
themselves.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                    | Purpose                                                                                                           |
| :----------------------- | :---------------------------------------------------------------------------------------------------------------- |
| [`build.py`](build.py)   | Keep the replays: draw each game a player's own move won, keep each game's newest 25, and post each on its issue. |
| [`README.md`](README.md) | This file.                                                                                                        |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push, from each file's own
description.

---

## 🚀 Running The Tests

The tests are [`test_build.py`](../../tests/unit/test_build.py), drawing from
the four won games in
[`tests/fixtures/replays/`](../../tests/fixtures/replays/README.md). From the
root of the repository, with the intake's:

```bash
PYTHONPATH=src/intake:src/replays python3 -m unittest discover -s tests/unit -p 'test_*.py'
```

`checks.yml` runs the same command as part of the `ci` job's `test-command`,
after the template's own script tests. The last test has the real kit draw
every game in the fixtures, when the kit is checked out at
`/home/user/markdown`, or at the `markdown-kit.py` that `MARKDOWN_KIT` names,
and is skipped when it isn't.

---

## 🔗 See also

- [Replays](../../replays/README.md) - every replay, the index, and how each is kept
- [Cross-Repository Contracts](../../docs/references/Cross-Repository-Contracts.md#-the-replay-facts-and-the-theme) - the facts and the theme a replay is drawn from, and how the kit is run

---

<div align="center">

**Won once. Drawn once. Kept where the profile links it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](/LICENSE).

</div>
