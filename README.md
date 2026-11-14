<!--
title: '🎲 PLAY'
description: 'Public move intake for the interactive games on the tannergolden profile README: every move arrives as a pre-filled issue, is checked, and is passed to its game through a GitHub App.'
type: index
-->

<div align="center">

# 🎲 PLAY

<a name="top"></a>

**Every move on the profile starts here.**

_Click a move. An issue opens. A bot checks it, passes it on, and closes it._

</div>

---

## 💡 What It Is

The four games on [@tannergolden's profile](https://github.com/tannergolden),
Chess, Checkers, Pentago and Tic-Tac, are played with links: every move on a
board opens a ready-made issue here, with the move already in its title. This
repository holds no game. It is the door every move comes through: one issue
form, one routing table, one check, and the workflows that pass each move to
its game and answer every move left waiting. It also keeps the
[replays](#-replays).

- **Status**: Active.

---

## 🚀 Quick Start

1. **Pick a move** under a board on [the profile](https://github.com/tannergolden).
   Its link opens the **🎲 Play a move** form here, titled like
   `chess: e2e4 · game 1 · move 1`.
2. **Tick its one box and submit it.** The box agrees to the games' rules and
   to how they show a player's move, username and avatar. A GitHub account is
   all a player needs.
3. **The game rules on it**, usually within a minute: the Official Arbiter
   answers on the same issue and closes it as `played` or `turned away`.

---

## 📖 Using It

### 🧭 How A Move Travels

**🎲 Move Intake** reads each new issue's title against
[`src/intake/routes.json`](src/intake/routes.json). A title that matches one
game's pattern from end to end is a move: it is checked against the board, a
move its game could only refuse is answered and closed here, and the rest goes
to its game through a short-lived GitHub App token. Anything else is answered
with how to play and closed, except the owner's own issues and anything an
app or a bot opened.

**No move is left waiting.** Once an hour, ⏳ Move Sweep marks a move its game
has not ruled on in 15 minutes as `overdue`, tells its player and the owner
once, and sends it through again once the outage is over. A game knows a move
it already played, so nothing is ever played twice.

A move link is the issue form plus the title, URL-encoded:

```text
https://github.com/tannergolden/play/issues/new?template=move.yml&title=chess%3A%20e2e4%20%C2%B7%20game%201%20%C2%B7%20move%201
```

Every step is in [Move Intake & Move Sweep](docs/technical/Move-Intake-&-Move-Sweep.md),
every label and reply in [Labels & Replies](docs/references/Labels-&-Replies.md),
and what to do about a move that went wrong in
[Troubleshooting A Move](docs/operations/Troubleshooting-Moves.md).

### 🗺️ The Routes

| Game       | Its moves go to             | Workflow                      | A move's title                            |
| :--------- | :-------------------------- | :---------------------------- | :---------------------------------------- |
| `chess`    | `tannergolden/tannergolden` | `chess.yml` on Development    | `chess: <uci> · game <n> · move <n>`      |
| `checkers` | `tannergolden/tannergolden` | `checkers.yml` on Development | `checkers: <move> · game <n> · move <n>`  |
| `pentago`  | `tannergolden/tannergolden` | `pentago.yml` on Development  | `pentago: <marble> · game <n> · move <n>` |
| `tictac`   | `tannergolden/tannergolden` | `tictac.yml` on Development   | `tictac: <square> · game <n> · move <n>`  |

Each player's side never changes: @tannergolden plays White, and X in Tic-Tac,
and everyone else on GitHub plays Black, or O. Pentago and Tic-Tac open under
the Ghost Rule
([ADR-0001](docs/adrs/ADR-0001-Four-Games-One-Arbiter.md#-amendment-the-ghost-rule)).
**Adding a game** is a row in the table, the game taught to the check, a
workflow in the game's repository and the GitHub App installed there:
[`src/intake/README.md`](src/intake/README.md) has the steps, and
[Cross-Repository Contracts](docs/references/Cross-Repository-Contracts.md)
what a game and this repository must keep agreeing on.

### 🎬 Replays

**Every game won by a player's own move is played again**, move by move,
drawn by [tannergolden/markdown](https://github.com/tannergolden/markdown).
Each game's newest 25 are kept in [`replays/`](replays/README.md), the newest
twelve of all four are pictures here, and every other replay is a link.

<!-- replays:start -->

_No game has been won by a player's own move yet, so there is no replay to show._

<!-- replays:end -->

### 🔑 The GitHub App

Every move crosses into another repository, so the intake needs one GitHub
App, the **Official Arbiter**, installed here and on every game's repository.
Each run asks it for a token that lives an hour at most, reaches only the one
repository the move's row names, and can do nothing there but start a
workflow. Players need nothing but a GitHub account.

| Permission                | Where                                | Used by                                   | For                                                                |
| :------------------------ | :----------------------------------- | :---------------------------------------- | :----------------------------------------------------------------- |
| **Actions:** Read & write | Each game's repository, and this one | 🎲 Move Intake, each game                 | Starting the game's workflow, and 🎬 Replays after a win           |
| **Issues:** Read & write  | This repository                      | Each game, 🎬 Replays, and 🎲 Move Intake | Its rulings on a move's issue, its notices and replays, and its 👀 |
| **Metadata:** Read-only   | Both                                 | -                                         | Granted to every App                                               |

Store its Client ID as the variable `PLAY_APP_CLIENT_ID` and its private key as
the secret `PLAY_APP_PRIVATE_KEY`; until both exist, every move fails with a
reply. [`docs/operations/GitHub-App.md`](docs/operations/GitHub-App.md) has
the setup, what players see and how to rotate the key.

### 🛡️ Why It Is Safe

- **A title is never code.** It reaches the router through an environment
  variable, and no `run:` step here contains a `${{ }}` expression.
- **The table decides where a move goes**, and only one short token of safe
  characters from each captured field goes on.
- **The token is narrow and brief**, and nothing here runs a stranger's code.
- **The game is the judge**: whether a move is legal is always the game's to
  decide.

Set this repository to **Watch → Participating and @mentions**, so what
reaches you is the outage notice and what a game @mentions you in, not every
move. [`.github/workflows/README.md`](.github/workflows/README.md) logs every
workflow.

---

## 📦 What's Inside

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                              | Purpose                                                                                                                                                                 |
| :------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`.devcontainer/`](.devcontainer/README.md)        | The language-neutral development container this repository ships, and how to give it the toolchain your project needs.                                                  |
| [`.github/`](.github/)                             | CODEOWNERS, Dependabot, release notes config, the issue form, scripts and workflows - logged below                                                                      |
| [`.vscode/`](.vscode/README.md)                    | The VS Code settings and extension recommendations this repository shares, and why every other file in this folder stays out of git.                                    |
| [`assets/`](assets/README.md)                      | Where this project keeps what presents it: four folders to start, a name ready for every other kind, and the rules every file follows.                                  |
| [`benchmarks/`](benchmarks/README.md)              | The benchmark suites and recorded results that defend the performance budgets of this project.                                                                          |
| [`docs/`](docs/README.md)                          | Where this project keeps its own documents, and where the engineering standards it follows actually live.                                                               |
| [`examples/`](examples/README.md)                  | Runnable examples that show how to use this project, one per task, built and checked with the code they show.                                                           |
| [`packages/`](packages/README.md)                  | Workspace packages, one folder each, for when a second consumer needs shared code.                                                                                      |
| [`replays/`](replays/README.md)                    | Every game a player's own move won, played again: each game's newest 25 replays, and the index of every one ever made.                                                  |
| [`src/`](src/README.md)                            | The source of the move intake and the replays: one folder of standard-library scripts for each, run by their own workflows.                                             |
| [`tests/`](tests/README.md)                        | The test suites, from isolated units to whole user journeys, and how CI comes to run them.                                                                              |
| [`.editorconfig`](.editorconfig)                   | Editor defaults every editor honours: UTF-8, LF, a final newline, and indentation per language                                                                          |
| [`.env.example`](.env.example)                     | Environment variable template for this project.                                                                                                                         |
| [`.git-blame-ignore-revs`](.git-blame-ignore-revs) | Commits that changed only formatting, which `git blame` should look through.                                                                                            |
| [`.gitattributes`](.gitattributes)                 | Git attributes - line endings, diffs, and what counts as binary                                                                                                         |
| [`.gitignore`](.gitignore)                         | &#x1F5C4;&#xFE0F; Universal Ignore Patterns                                                                                                                             |
| [`.markdownlint.json`](.markdownlint.json)         | Repository-wide markdownlint rules. Discovered by mechanism, which is why this lives at the root.                                                                       |
| [`AGENTS.md`](AGENTS.md)                           | How AI agents work in tannergolden/play: the universal rules first, then the rules for the moves, the games and this public repository. Read it before any change here. |
| [`LICENSE`](LICENSE)                               | PROPRIETARY LICENCE                                                                                                                                                     |
| [`README.md`](README.md)                           | This file.                                                                                                                                                              |

<!-- AUTO-INDEX:END -->

**Every folder carries a `README.md` that logs each file inside it**, with two
exceptions. GitHub shows a README in `.github/` in place of this page, so that
folder's own files are logged here instead, and `.github/ISSUE_TEMPLATE/`
holds only what GitHub reads there. 🗂️ Machined Indexes redraws both tables
after every push:

<!-- AUTO-INDEX:BEGIN dir=./.github style=log -->

| Entry                                                           | Purpose                                                                                                                                              |
| :-------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`actions/`](.github/actions/README.md)                         | The composite actions this repository keeps for its own workflows, and for any other repository that calls them.                                     |
| [`DISCUSSION_TEMPLATE/`](.github/DISCUSSION_TEMPLATE/README.md) | The discussion category forms, each bound by its file name to the category it shapes.                                                                |
| [`ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/README.md)           | The move form every move link on the profile opens, and the chooser that offers it and nothing else.                                                 |
| [`scripts/`](.github/scripts/README.md)                         | The checks this repository runs on its own configuration, and the tests that guard them.                                                             |
| [`workflows/`](.github/workflows/README.md)                     | Every workflow in this repository: the name it shows in the Actions tab, what triggers it, and what it does.                                         |
| [`ACCESSIBILITY.md`](.github/ACCESSIBILITY.md)                  | The accessibility this project aims for, how to report a barrier, and what happens after you do.                                                     |
| [`CODE_OF_CONDUCT.md`](.github/CODE_OF_CONDUCT.md)              | The code of conduct governing participation in this project, how to report a violation, and how harm is addressed and repaired.                      |
| [`CODEOWNERS`](.github/CODEOWNERS)                              | Folder-based ownership rules                                                                                                                         |
| [`commit-template.txt`](.github/commit-template.txt)            | &lt;type&gt;(&lt;scope&gt;): &lt;emoji&gt; &lt;subject starting lowercase, no em dash&gt;                                                            |
| [`CONTRIBUTING.md`](.github/CONTRIBUTING.md)                    | How to contribute, covering branching, commits, code style, testing, and the pull-request process.                                                   |
| [`dependabot.yml`](.github/dependabot.yml)                      | Dependabot - automated dependency updates                                                                                                            |
| [`FUNDING.yml`](.github/FUNDING.yml)                            | &#x1F496; Funding Options                                                                                                                            |
| [`GOVERNANCE.md`](.github/GOVERNANCE.md)                        | How this project is led, who decides what, how access continues, and the review and security standards every change meets.                           |
| [`pull_request_template.md`](.github/pull_request_template.md)  | This template becomes the body of your pull request.                                                                                                 |
| [`release.yml`](.github/release.yml)                            | GitHub auto-generated release notes configuration.                                                                                                   |
| [`SECURITY.md`](.github/SECURITY.md)                            | How to report a vulnerability privately, what happens after you do, which versions receive security fixes, and the protections this repository runs. |
| [`SUPPORT.md`](.github/SUPPORT.md)                              | Where to get help with this repository - the right channel for every kind of question.                                                               |
| [`template-sync`](.github/template-sync)                        | Every path tannergolden/path ships, and whether &#x1F504; Template Sync, when you run it, keeps it current in this repository.                       |
| [`template-sync.lock`](.github/template-sync.lock)              | Where each file here was last synced from.                                                                                                           |
| [`template-sync.md`](.github/template-sync.md)                  | How this repository takes its template's later fixes when you run &#x1F504; Template Sync, what you control, and what waits on you.                  |
| [`VULNERABILITY_REPORT.yml`](.github/VULNERABILITY_REPORT.yml)  | Report a suspected vulnerability privately, so the maintainers can fix it before it is made public.                                                  |

<!-- AUTO-INDEX:END -->

---

## 🤝 Getting Involved

- **Playing**: the move form is the only issue this repository takes.
- **Questions**: [`SUPPORT.md`](/.github/SUPPORT.md) says where to ask.
- **A change**: [`CONTRIBUTING.md`](/.github/CONTRIBUTING.md) explains how,
  every change follows the
  [standards](https://github.com/tannergolden/standards/blob/Development/docs/README.md)
  by link, and every contribution follows the
  [code of conduct](/.github/CODE_OF_CONDUCT.md).
- **Who decides**: [`GOVERNANCE.md`](/.github/GOVERNANCE.md) names the
  maintainers.

This repository was generated from the public `tannergolden/path` template.
🔄 Template Sync brings its fixes when you run it, and every change this
repository made to a file the template ships is protected in
[`.github/template-sync`](.github/template-sync)
([how](.github/template-sync.md)).

---

## 🛡️ Security

Report a vulnerability privately, never in an issue:
[`SECURITY.md`](/.github/SECURITY.md) says how, and how fast a fix follows.

---

## ⚖️ Licence

**Proprietary. All rights reserved.** Everything here is Tanner Golden's
alone, under [`LICENSE`](LICENSE): nothing in it may be used, copied, adapted,
sold or resold by anyone, no permission will ever be granted, and no AI system
may train on it or reproduce it. Anyone may still play the games from
[the profile](https://github.com/tannergolden), and submitting a move lets the
games record and show it with your username. GitHub's own Terms let any user
view and fork this repository on GitHub, and nothing more. Versions published
under the MIT License before 14 October 2026 stay under it, as to those
versions only. The shared workflows and actions it calls are published
separately, under their own licence
([ADR-0002](docs/adrs/ADR-0002-The-Games-Are-Proprietary.md)).

---

<div align="center">

**Click a move. The rest is automatic.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden). Proprietary; all rights reserved.

</div>
