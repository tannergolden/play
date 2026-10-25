<!--
title: '🧩 UNIT TESTS'
description: 'Unit tests: fast, isolated checks of one piece of logic each, run on every push.'
type: index
-->

<div align="center">

# 🧩 UNIT TESTS

<a name="top"></a>

**Fast, isolated tests of one piece of logic each, run on every push.**

_In-process, and no I/O._

</div>

---

## 💡 What This Folder Is For

One test file per script: [`test_route.py`](test_route.py),
[`test_check.py`](test_check.py) and [`test_sweep.py`](test_sweep.py) for the
[move intake](../../src/intake/README.md), and [`test_build.py`](test_build.py)
for the [replays](../../src/replays/README.md), which draws from the four won
games in [`fixtures/replays/`](../fixtures/replays/README.md). GitHub, the kit
and ImageMagick are each replaced by a stand-in, so nothing here reads or
writes outside a throwaway folder, but for the last test in `test_build.py`,
which has the real kit draw every fixture when the kit is checked out beside
this repository, and is skipped when it isn't.

Run them from the root of the repository, with both of `src/`'s folders on the
path:

```bash
PYTHONPATH=src/intake:src/replays python3 -m unittest discover -s tests/unit -p 'test_*.py'
```

`checks.yml` runs the same command as part of the `ci` job's `test-command`,
after the template's own script tests.

The runner, coverage targets, naming, test layout, and mocking rules belong in
the fill-in [Unit Test Standards](../../docs/templates/technical/testing/Unit-Test-Standards.md).

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                            | Purpose                                                                                                        |
| :------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| [`README.md`](README.md)         | This file.                                                                                                     |
| [`test_build.py`](test_build.py) | Tests for the replays: what is drawn, what is kept, what is said, and what an account that is gone takes down. |
| [`test_check.py`](test_check.py) | Tests for the pre-check of all four games.                                                                     |
| [`test_route.py`](test_route.py) | Tests for the move router.                                                                                     |
| [`test_sweep.py`](test_sweep.py) | Tests for the sweep.                                                                                           |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push to the default branch,
from what each file says about itself. A subfolder appears as one row, so give
it a README of its own and its row links to that.

---

<div align="center">

**One behaviour per test, proven in milliseconds.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](/LICENSE).

</div>
