<!--
title: '🎲 PLAY'
description: 'Public move intake for the interactive games on the tannergolden profile README: every move arrives as a pre-filled issue, is checked, and is passed to its game through a GitHub App.'
type: index
keywords: [issueops, github-actions, profile-readme, chess, checkers, pentago, tic-tac]
-->

<div align="center">

# 🎲 PLAY

<a name="top"></a>

**Every move on the profile starts here.**

_Click a move. An issue opens. A bot checks it, passes it on, and closes it._

</div>

---

## 💡 What This Is

The four games on [@tannergolden's profile](https://github.com/tannergolden),
Chess, Checkers, Pentago and Tic-Tac, are played with links. Every
move on a board is a link that opens a ready-made issue in this repository,
with the move already in its title. Submit it, and
**🎲 Move Intake** checks it and passes it to that game's repository within a
minute. The game then decides whether the move stands, redraws the board, says
so on the same issue, and closes it, labelled `played` or `turned away`.

This repository holds no game. It is the door every move comes through:

- **one issue form**, the only kind of issue it takes;
- **one table**, [`intake/routes.json`](intake/routes.json), naming each game
  and where its moves go;
- **one script**, [`intake/route.py`](intake/route.py), that reads each title
  against that table;
- **one check**, [`intake/check.py`](intake/check.py), that turns away, in the
  game's own words, a move its game could only refuse;
- **one workflow**, [`intake.yml`](.github/workflows/intake.yml), that does
  what the two scripts decide;
- **one sweep**, [`intake/sweep.py`](intake/sweep.py), run twice an hour by
  [`sweep.yml`](.github/workflows/sweep.yml), that answers every move left
  waiting.

It also keeps the replays: every game a player's own move won, played again
move by move, in [`replays/`](replays/README.md) and the
[gallery below](#-replays).

---

## 🧭 How A Move Travels

1. **A player clicks a move** on the profile. Its link opens the **🎲 Play a
   move** form here, with the title filled in: `chess: e2e4 · game 1 · move 1`.
2. **They submit it** as it opens. A GitHub account is all a player needs.
3. **🎲 Move Intake reads the title** against the table, and the Official
   Arbiter reacts with 👀 so the player sees it was picked up. Only a title that
   matches one game's pattern from end to end is a move, labelled `move` and its
   game, such as `game: chess`; anything else is labelled `invalid`.
4. **It checks the move against the board**, and answers here a move the game
   could only refuse: one for a game that is over, one already played, one on
   the other side's turn, one for the next game while the last one's winning
   board is still up, or one from a player past the hourly limit. That move is
   labelled `turned away` and closed.
5. **The move goes to its game.** A short-lived token from the GitHub App
   starts the game's workflow, with the move, the issue's number and the
   player, and the issue gets a 🚀. It stays open for the game's ruling.
6. **The game rules on it.** The Arbiter replies on the same issue once it has
   played the move, or says why it could not, labels it `played` or
   `turned away`, files it in its game's milestone, such as `Chess · game 1`,
   and closes it: as completed if it was played, as not planned if not. That
   reply is the one a move gets.

| The issue                          | What happens                                                          |
| :--------------------------------- | :-------------------------------------------------------------------- |
| A move for a game in the table     | A 🚀, passed to its game, and left open for the game's ruling         |
| A move its game could only refuse  | A reply in the game's words, `turned away`, closed as not planned     |
| Anything else, from anyone else    | A reply saying how to play, and closed as not planned                 |
| Anything else, from the owner      | Left open: the owner files their own issues here too                  |
| Anything opened by an app or a bot | Never touched, so each game can post its own notices here             |
| A move that cannot reach its game  | `stranded`, with a reply, the owner told once, and sent again later   |
| A move sent on but never ruled on  | `overdue` after 15 minutes, the owner told once, and sent again later |

**No move is left waiting.** Twice an hour, ⏳ Move Sweep reads every open
issue here. A move sent on that its game hasn't ruled on in 15 minutes is
marked `overdue`, its player is told once, and the owner is told once, in the
same outage notice a move that can't reach its game opens. Once that notice
is closed, which the next move to go through does by itself, the sweep sends
every `stranded` and `overdue` move through 🎲 Move Intake again; while it is
open, it tries the oldest stranded move alone, once a sweep, to find out
whether the outage is over. An issue the intake never answered, such as one
whose run never started, is sent again after 15 minutes either way. A move
sent again goes straight to its game, which knows a move already played from
that issue, so nothing is ever played twice, and one gone stale is turned away
with the reason.

A move link is the issue form plus the title, URL-encoded:

```text
https://github.com/tannergolden/play/issues/new?template=move.yml&title=chess%3A%20e2e4%20%C2%B7%20game%201%20%C2%B7%20move%201
```

Every step of 🎲 Move Intake and ⏳ Move Sweep is in
[Move Intake & Move Sweep](docs/technical/Move-Intake-&-Move-Sweep.md), every
label and reply in [Labels & Replies](docs/references/Labels-&-Replies.md),
and what to do about a move that went wrong in
[Troubleshooting A Move](docs/operations/Troubleshooting-Moves.md).

---

## 🗺️ The Routes

| Game       | Its moves go to             | Workflow                      | A move's title                            |
| :--------- | :-------------------------- | :---------------------------- | :---------------------------------------- |
| `chess`    | `tannergolden/tannergolden` | `chess.yml` on Development    | `chess: <uci> · game <n> · move <n>`      |
| `checkers` | `tannergolden/tannergolden` | `checkers.yml` on Development | `checkers: <move> · game <n> · move <n>`  |
| `pentago`  | `tannergolden/tannergolden` | `pentago.yml` on Development  | `pentago: <marble> · game <n> · move <n>` |
| `tictac`   | `tannergolden/tannergolden` | `tictac.yml` on Development   | `tictac: <square> · game <n> · move <n>`  |

- **`<uci>`** is a chess move in UCI notation: the square the piece leaves, the
  square it lands on, and the piece a pawn becomes when it promotes, as in
  `e2e4` or `e7e8q`.
- **`<move>`** is a checkers move in standard notation, its squares numbered 1
  to 32: `11-15` for a move, `22x15` for a jump, `22x15x8` for a jump that
  goes on.
- **`<marble>`** is a Pentago move: the hole a marble goes in, then the
  quarter that turns, `ul`, `ur`, `ll` or `lr`, and which way, `cw` or `acw`,
  as in `e4-ur-cw`; or a ghost's hole alone, as in `b5`.
- **`<square>`** is a Tic-Tac square, a ghost's or a mark's, named as a chess
  square is: files `a` to `i` from the left and ranks `1` to `9` from the
  bottom, across all nine boards, so `e5` is the centre of the centre board.

The board stamps the game and the move number into every link it writes, so
the game can tell a click on the current board from one on a board that has
since moved on.

**Who plays which side, and who opens.** Each player's side never changes:
@tannergolden always plays White in Chess, Checkers and Pentago, and X in
Tic-Tac, and GitHub, which is everyone else, always plays Black, or O. In
Chess, @tannergolden opens, as White. In Checkers, GitHub opens, as Black,
since Black moves first in American checkers. Pentago and Tic-Tac open under
the Ghost Rule: each side first places a ghost, the Arbiter drawing the side
that places first, and then the Arbiter draws the side that moves first. Their
move numbers count the ghosts, so move 3 is the first move.
[ADR-0001](docs/adrs/ADR-0001-Four-Games-One-Arbiter.md) and
[its amendment](docs/adrs/ADR-0001-Four-Games-One-Arbiter.md#-amendment-the-ghost-rule)
record why. A finished game's winning board stays up for two days before a
fresh board comes, and one hourly limit, 30 issues from each player, covers
all four games.

**Adding a game** is a row in the table, the game taught to the check, a
workflow in the game's repository that accepts the move, and the GitHub App
installed there.
[`intake/README.md`](intake/README.md) has the steps, and what every game's
workflow receives.
[Cross-Repository Contracts](docs/references/Cross-Repository-Contracts.md)
lists everything else a game and this repository must keep agreeing on.

---

## 🎬 Replays

**Every game won by a player's own move is played again**, move by move, on
its own board. The game writes down what each turn did, and
**🎬 Replays** has [tannergolden/markdown](https://github.com/tannergolden/markdown)
draw it, by day and by dark, each player a halftone of their avatar. It keeps
each game's newest 25 in [`replays/`](replays/README.md), and the Official
Arbiter posts each on its winning move's issue. A draw gets none, and neither
does a win the Arbiter's move made, or a Pentago turn that made five for the
other side.

Each picture plays its whole game as the page opens, so only the newest
twelve of all four games are pictures here, and every other replay is a link.

<!-- replays:start -->

_No game has been won by a player's own move yet, so there is no replay to show._

<!-- replays:end -->

---

## 🔑 The GitHub App

Every move crosses into another repository, so the intake needs one GitHub
App, the **Official Arbiter**, owned by this account and installed here and on
every game's repository. Each run asks it for a token that lives an hour at
most, reaches only the one repository the move's row names, can do nothing
there but start a workflow, and is revoked when the job ends. Its 👀 on every
issue the intake answers comes from a second token of the same kind, with
Issues write here and nothing more. There is no long-lived token to leak, and
none to expire and quietly stop the game.

> [!NOTE]
> **Only the owner sets this up, and only once.** Players need nothing but a
> GitHub account: there is nothing for them to install, nothing to authorize,
> and no token of their own. They submit the issue, and the workflow here does
> the rest with this account's App. One App serves every game, so a new game
> is only its repository added to the same installation.

| Permission                | Where                                | Used by                                   | For                                                                |
| :------------------------ | :----------------------------------- | :---------------------------------------- | :----------------------------------------------------------------- |
| **Actions:** Read & write | Each game's repository, and this one | 🎲 Move Intake, each game                 | Starting the game's workflow, and 🎬 Replays after a win           |
| **Issues:** Read & write  | This repository                      | Each game, 🎬 Replays, and 🎲 Move Intake | Its rulings on a move's issue, its notices and replays, and its 👀 |
| **Metadata:** Read-only   | Both                                 | -                                         | Granted to every App                                               |

Setting it up, once:

1. **Create the App** under your account's **Settings → Developer settings →
   GitHub Apps**. It needs no webhook, so clear **Active** under Webhook. Give
   it the permissions above, and let it be installed on this account only.
   Name it **Official Arbiter**: players see it as `official-arbiter[bot]` on
   every 👀 and on every reply a game posts. The intake's own 🚀 and replies,
   and the sweep's, come from `github-actions[bot]`.
2. **Generate a private key**, and note the App's **Client ID**.
3. **Install it** on `tannergolden/play` and `tannergolden/tannergolden`, as
   selected repositories.
4. **Store both here**, under **Settings → Secrets and variables → Actions**:
   the Client ID as the variable `PLAY_APP_CLIENT_ID`, and the whole private
   key file as the secret `PLAY_APP_PRIVATE_KEY`.

Until both exist, every move fails with a reply, the owner is @mentioned
once in the outage notice, no issue gets its 👀, and every replay waits to be
posted. Each game's repository keeps its own copy of the same two, for its
rulings.

The full guide, with what players see, how to rotate the key and what to do
when a move fails, is [`docs/operations/GitHub-App.md`](docs/operations/GitHub-App.md).

---

## 🛡️ Why It Is Safe

Anyone on GitHub can open an issue here, with any title they like, and the
workflow that reads it can start a workflow in another repository. So:

- **A title is never code.** It reaches the router through an environment
  variable, and no `run:` step here contains a `${{ }}` expression. The
  router never prints it, since a line it printed could be read as a workflow
  command.
- **The table decides where a move goes.** A title can only name a game in
  the table; the table names the repository, the workflow and the branch.
- **Only what a pattern captures goes on**, and every captured value is one
  short token of letters, digits and `_.+#=-`, however loose the pattern.
- **The token is narrow and brief:** one repository, Actions write, revoked
  when the job ends. The Arbiter's 👀 is minted the same way, with Issues write
  here alone, and held by that one step. Replies, labels, closing and locking
  use this repository's own token, which reaches nothing else.
- **Nothing here runs a stranger's code.** The workflow checks out only the
  intake folder, from the default branch, without credentials, and runs only
  the router and the check. A move sent again is read from its issue by the
  router, the same way, and only the owner or ⏳ Move Sweep can send one.
- **The game is the judge.** The intake checks that a title is shaped like a
  move, and turns away at the door only what the game could only refuse, from
  the game's state as it last read it. Whether a move is legal is always the
  game's to decide, and its inputs are untrusted there too.
- **A replay is drawn only from what the game wrote.** 🎬 Replays reads each
  won game's facts from the game's repository, checks every field it writes
  into a page before writing it, and has the kit, at its `v1`, draw them. The
  Arbiter's token it posts with is minted after the push, with Issues write
  here alone, and no step that draws ever holds it.

Every action is pinned to a commit or to the standards' `v1`, every runner is
hardened, and every workflow passes actionlint and zizmor's pedantic audit in
🚦 Checks.

---

## 🔔 Notifications

Every move is an issue here, so a repository watched the usual way sends a
notification for every move anyone plays. Set this one to **Watch →
Participating and @mentions**, and what reaches you is what needs you:

- **a move that could not reach its game, or one its game never ruled on**,
  in the outage notice, which @mentions you once however many moves it holds
  up;
- **anything a game @mentions you in**, such as its notice that it is your
  turn.

🚨 CI Failure Alerts also opens an issue when 🎬 Replays or ⏳ Move Sweep
fails, but it mentions no one, so under this setting it shows on the Issues
tab rather than in your notifications. It doesn't watch 🎲 Move Intake: a move
that can't reach its game already opens the outage notice, and one alarm is
enough for one fault.

---

## 🌿 The Workflows

| Workflow                   | Gives you                                                                                  |
| :------------------------- | :----------------------------------------------------------------------------------------- |
| `intake.yml`               | 🎲 Move Intake: every move issue, routed to its game. This repository's own                |
| `sweep.yml`                | ⏳ Move Sweep: every move left waiting, marked or sent again. This repository's own        |
| `replay.yml`               | 🎬 Replays: every won game drawn again, kept and posted. This repository's own             |
| `checks.yml`               | Lint and tests, the intake's and the replays' included; secret scan, CodeQL, workflow lint |
| `governance.yml`           | PR title and DCO checks, triage, stale sweep, slash commands                               |
| `ci-failure-alert.yml`     | Opens an issue when a watched workflow fails, 🎬 Replays and ⏳ Move Sweep included        |
| `release.yml`              | Draft notes, publish assets, prune superseded releases                                     |
| `maintenance.yml`          | Prunes stale deployments and draft releases                                                |
| `lifecycle.yml`            | Claimed this repository once; flags a new major of the standards                           |
| `dependabot-automerge.yml` | Approves and queues patch and minor updates                                                |
| `apply-standards.yml`      | Dispatch-only. The label taxonomy, the settings and branch protection                      |
| `auto-format.yml`          | Formats what a push touched, once a formatter is configured                                |
| `auto-index.yml`           | Redraws every folder log and index after a push                                            |
| `preview-deploy.yml`       | Deploys pushes to a preview target, once configured                                        |
| `prune-runs.yml`           | Deletes old workflow runs, with their logs and artifacts                                   |
| `verify-stubs.yml`         | Proves every stub's permission ceiling matches its called workflow                         |
| `template-sync.yml`        | Proposes the template's later fixes as one pull request, when run                          |

`cut-release.yml` belongs to the template, and its guard keeps it from ever
running here. Of the rest, all but `intake.yml`, `sweep.yml`, `replay.yml`
and `verify-stubs.yml`, which run scripts kept here, are stubs that call
[`tannergolden/standards`](https://github.com/tannergolden/standards), so a fix
there reaches this repository without a commit here.

**Do not rename the job ids** `ci` and `secrets` (in `checks.yml`) or `pr` (in
`governance.yml`): branch protection depends on them. **Sign your commits
off** with `git commit -s`; the DCO check is required once the rulesets are on.

> [!NOTE]
> **GitHub pauses scheduled workflows in a public repository after 60 days
> without activity.** 🎲 Move Intake runs on issues, not on a schedule, so the
> game never pauses; the weekly sweeps can be switched back on from the
> Actions tab. So can 🎬 Replays, should it pause after 60 days without a
> commit here: its first run once it is back on draws every replay it missed.
> And so can ⏳ Move Sweep, whose first sweep answers every move left waiting.

---

## 🔄 Template Sync

This repository was generated from the private `tannergolden/repo` template.
**🔄 Template Sync** brings that template's later fixes here, but only when
you run it from the Actions tab, and only as one pull request you review. It
needs a `BOT_ACCESS_TOKEN` secret that can read the template, since the
template is private; see [`.github/template-sync.md`](.github/template-sync.md).

Every change this repository made to a file the template ships is protected
in [`.github/template-sync`](.github/template-sync), the list the sync reads:

| File                                                                                                   | Changed here                             | Kept by                                                           |
| :----------------------------------------------------------------------------------------------------- | :--------------------------------------- | :---------------------------------------------------------------- |
| `README.md`, `LICENSE`                                                                                 | This page, and the proprietary licence   | Yours from the start: the sync never touches them                 |
| `.github/workflows/governance.yml`                                                                     | No welcome on a new issue                | `# keep mine`: where you both changed a line, yours stands        |
| `.github/workflows/checks.yml`                                                                         | Runs the intake's and the replays' tests | `# keep mine`                                                     |
| `.github/workflows/ci-failure-alert.yml`                                                               | Watches 🎬 Replays and ⏳ Move Sweep     | `# keep mine`                                                     |
| `.github/ISSUE_TEMPLATE/`, `intake/`, `intake.yml`, `sweep.yml`, `replays/`, `replay.yml`, `CLAUDE.md` | This repository's own                    | A `!` rule: stopped, should the template ship the same name       |
| The seeded documents in `docs/`                                                                        | The licence footer                       | The per-file merge: the template's other changes arrive around it |

A file you and the template changed in the same place is left exactly as you
have it, so none of this is ever overwritten. Two things still need your eye
in a sync's pull request:

- **A footer the template rewrites waits on you**, as a conflict. Do not make
  it match the template's, as the pull request suggests. Add
  `# keep mine: /path/to/the/document.md` under **Your rules** instead, and
  this repository's footer stands from then on.
- **A seeded document the template adds arrives with the template's footer**,
  "Proprietary and confidential; all rights reserved." This repository is
  public, so change that line to "Proprietary; all rights reserved." in the
  same pull request.

Where `# keep mine` keeps your lines, the template's change to them is shown
in the pull request rather than applied: a new workflow for 🚨 CI Failure
Alerts to watch, say. Copy across anything worth having.

---

## 📦 What's Inside

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                       | Purpose                                                                                                                                                                                                     |
| :------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`.devcontainer/`](.devcontainer/README.md) | The language-neutral development container this repository ships, and how to give it the toolchain your project needs.                                                                                      |
| [`.github/`](.github/)                      | CODEOWNERS, Dependabot, release notes config, the issue form, scripts and workflows - logged below                                                                                                          |
| [`.vscode/`](.vscode/README.md)             | The VS Code settings and extension recommendations this repository shares, and why every other file in this folder stays out of git.                                                                        |
| [`assets/`](assets/README.md)               | Where this project keeps what presents it: four folders to start, a name ready for every other kind, and the rules every file follows.                                                                      |
| [`docs/`](docs/README.md)                   | Where this project keeps its own documents, and where the engineering standards it follows actually live.                                                                                                   |
| [`intake/`](intake/README.md)               | The router every move passes through, the check that reads each move against its board, and the sweep that answers every move left waiting: the table of the four games, the three scripts and their tests. |
| [`replays/`](replays/README.md)             | Every game a player's own move won, played again: each game's newest 25 replays, the index of every one ever made, and the script that keeps them.                                                          |
| [`.editorconfig`](.editorconfig)            | Editor defaults every editor honours: UTF-8, LF, a final newline, and indentation per language                                                                                                              |
| [`.env.example`](.env.example)              | Environment variable template for this project.                                                                                                                                                             |
| [`.gitattributes`](.gitattributes)          | Git attributes - line endings, diffs, and what counts as binary                                                                                                                                             |
| [`.gitignore`](.gitignore)                  | &#x1F5C4;&#xFE0F; Universal Ignore Patterns                                                                                                                                                                 |
| [`.markdownlint.json`](.markdownlint.json)  | Repository-wide markdownlint rules. Discovered by mechanism, which is why this lives at the root.                                                                                                           |
| [`CLAUDE.md`](CLAUDE.md)                    | The owner's standing rules for every Claude session that works on this repository.                                                                                                                          |
| [`LICENSE`](LICENSE)                        | PROPRIETARY LICENCE                                                                                                                                                                                         |
| [`README.md`](README.md)                    | This file.                                                                                                                                                                                                  |

<!-- AUTO-INDEX:END -->

**Every folder carries a `README.md` that logs each file inside it**, with two
exceptions. GitHub shows a README in `.github/` in place of this page, so that
folder's own files are logged here instead, and `.github/ISSUE_TEMPLATE/`
holds only what GitHub reads there. 🗂️ Machined Indexes redraws both tables
after every push:

<!-- AUTO-INDEX:BEGIN dir=./.github style=log -->

| Entry                                                 | Purpose                                                                                                                             |
| :---------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| [`actions/`](.github/actions/README.md)               | The composite actions this repository keeps for its own workflows, and for any other repository that calls them.                    |
| [`ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/README.md) | The move form every move link on the profile opens, and the chooser that offers it and nothing else.                                |
| [`scripts/`](.github/scripts/README.md)               | The checks this repository runs on its own configuration, and the tests that guard them.                                            |
| [`workflows/`](.github/workflows/README.md)           | Every workflow in this repository: the name it shows in the Actions tab, what triggers it, and what it does.                        |
| [`CODEOWNERS`](.github/CODEOWNERS)                    | Review ownership                                                                                                                    |
| [`dependabot.yml`](.github/dependabot.yml)            | Dependabot - automated dependency updates                                                                                           |
| [`release.yml`](.github/release.yml)                  | GitHub auto-generated release notes configuration.                                                                                  |
| [`template-sync`](.github/template-sync)              | Every path tannergolden/repo ships, and whether &#x1F504; Template Sync, when you run it, keeps it current in this repository.      |
| [`template-sync.lock`](.github/template-sync.lock)    | Where each file here was last synced from.                                                                                          |
| [`template-sync.md`](.github/template-sync.md)        | How this repository takes its template's later fixes when you run &#x1F504; Template Sync, what you control, and what waits on you. |

<!-- AUTO-INDEX:END -->

---

## 📚 The Standards

Everything about how to branch, review, release and secure a repository lives
in the [Standards Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md).
This repository follows it **by link**, like every repository generated from
the same template.

---

## 🔒 Licence

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
