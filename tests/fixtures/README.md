<!--
title: '🧷 TEST FIXTURES'
description: 'Fixed inputs the tests read: real data as another repository writes it, one folder for each script that reads it.'
type: index
-->

<div align="center">

# 🧷 TEST FIXTURES

<a name="top"></a>

**Fixed inputs the tests read, and never write.**

_Real data, kept as it was written._

</div>

---

## 💡 What This Folder Is For

A fixture is data a test reads as it is, in the very form something outside
the test writes it, so the test holds the script to the real format and not to
a copy of it. Each folder here holds the fixtures of one script, and its README
says where they came from and which tests read them.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                           | Purpose                                                                                                           |
| :------------------------------ | :---------------------------------------------------------------------------------------------------------------- |
| [`replays/`](replays/README.md) | The facts of four won games, one of each, as the profile's engine writes them: what the tests draw a replay from. |
| [`README.md`](README.md)        | This file.                                                                                                        |

<!-- AUTO-INDEX:END -->

🗂️ Machined Indexes redraws this log after every push to the default branch.
Each folder logs its own files.

---

<div align="center">

**Read as written. Never written by a test.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the terms in [LICENSE](/LICENSE).

</div>
