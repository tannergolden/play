<!--
title: '🎲 PLAY'
description: 'Public move intake for the interactive games on the tannergolden profile README: every move arrives as a pre-filled issue, is checked, and is passed to its game through a GitHub App.'
tags: [issueops, github-actions, profile-readme, chess]
category: docs
-->

<div align="center">

# 🎲 PLAY

<a name="top"></a>

**Every move on the profile starts here.**

_Click a move. An issue opens. A bot checks it, passes it on, and closes it._

</div>

---

## 💡 What This Is

The games on [@tannergolden's profile](https://github.com/tannergolden) are
played with links. Every move on the board is a link that opens a ready-made
issue in this repository, with the move already in its title. Submit it, and
**🎲 Move Intake** checks it, passes it to that game's repository, replies, and
closes the issue, all within a minute. The game then decides whether the move
stands, redraws the board, and says so on the same issue.

This repository holds no game. It is the door every move comes through:

- **one issue form**, the only kind of issue it takes;
- **one table**, [`intake/routes.json`](intake/routes.json), naming each game
  and where its moves go;
- **one script**, [`intake/route.py`](intake/route.py), that reads each title
  against that table;
- **one workflow**, [`intake.yml`](.github/workflows/intake.yml), that does
  what the script decides.

---

## 🧭 How A Move Travels

1. **A player clicks a move** on the profile. Its link opens the **🎲 Play a
   move** form here, with the title filled in: `chess: e2e4 · game 1 · move 1`.
2. **They submit it** as it opens.
3. **🎲 Move Intake reads the title** against the table. Only a title that
   matches one game's pattern from end to end is a move.
4. **The move goes to its game.** A short-lived token from the GitHub App
   starts the game's workflow, with the move, the issue's number and the
   player.
5. **The issue is answered:** a 🚀, a reply, and closed as completed. The game
   replies on the same issue once it has played the move, or says why it could
   not.

| The issue                          | What happens                                              |
| :--------------------------------- | :-------------------------------------------------------- |
| A move for a game in the table     | Passed to its game, answered, and closed as completed     |
| Anything else, from anyone else    | A reply saying how to play, and closed as not planned     |
| Anything else, from the owner      | Left open: the owner files their own issues here too      |
| Anything opened by an app or a bot | Never touched, so each game can post its own notices here |
| A move that cannot reach its game  | Left open, with a reply that @mentions the owner          |

A move link is the issue form plus the title, URL-encoded:

```text
https://github.com/tannergolden/play/issues/new?template=move.yml&title=chess%3A%20e2e4%20%C2%B7%20game%201%20%C2%B7%20move%201
```

---

## 🗺️ The Routes

| Game    | Its moves go to             | Workflow                   | A move's title                       |
| :------ | :-------------------------- | :------------------------- | :----------------------------------- |
| `chess` | `tannergolden/tannergolden` | `chess.yml` on Development | `chess: <uci> · game <n> · move <n>` |

`<uci>` is the move in UCI notation: the square the piece leaves, the square
it lands on, and the piece a pawn becomes when it promotes, as in `e2e4` or
`e7e8q`. The board stamps the game and the move number into every link it
writes, so the game can tell a click on the current board from one on a board
that has since moved on.

**Adding a game** is a row in the table, a workflow in the game's repository
that accepts the move, and the GitHub App installed there.
[`intake/README.md`](intake/README.md) has the steps, and what every game's
workflow receives.

---

## 🔑 The GitHub App

Every move crosses into another repository, so the intake needs one GitHub
App, owned by this account, installed here and on every game's repository.
Each run asks it for a token that lives an hour at most, reaches only the one
repository the move's row names, can do nothing there but start a workflow,
and is revoked when the job ends. There is no long-lived token to leak, and
none to expire and quietly stop the game.

| Permission                | Where                  | Used by        | For                                            |
| :------------------------ | :--------------------- | :------------- | :--------------------------------------------- |
| **Actions:** Read & write | Each game's repository | 🎲 Move Intake | Starting the game's workflow                   |
| **Issues:** Read & write  | This repository        | Each game      | Its replies on a move's issue, and its notices |
| **Metadata:** Read-only   | Both                   | -              | Granted to every App                           |

Setting it up, once:

1. **Create the App** under your account's **Settings → Developer settings →
   GitHub Apps**. It needs no webhook, so clear **Active** under Webhook. Give
   it the permissions above, and let it be installed on this account only.
2. **Generate a private key**, and note the App's **Client ID**.
3. **Install it** on `tannergolden/play` and `tannergolden/tannergolden`, as
   selected repositories.
4. **Store both here**, under **Settings → Secrets and variables → Actions**:
   the Client ID as the variable `PLAY_APP_CLIENT_ID`, and the whole private
   key file as the secret `PLAY_APP_PRIVATE_KEY`.

Until both exist, every move fails with a reply that @mentions the owner.
Each game's repository keeps its own copy of the same two, for its replies.

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
  when the job ends. Replies and closing use this repository's own token,
  which reaches nothing else.
- **Nothing here runs a stranger's code.** The workflow checks out only the
  intake folder, from the default branch, without credentials, and runs only
  the router.
- **The game is the judge.** The intake only checks that a title is shaped
  like a move. Whether it is legal, whose turn it is and whether the click is
  current are the game's to decide, and its inputs are untrusted there too.

Every action is pinned to a commit or to the standards' `v1`, every runner is
hardened, and every workflow passes actionlint and zizmor's pedantic audit in
🚦 Checks.

---

## 🔔 Notifications

Every move is an issue here, so a repository watched the usual way sends a
notification for every move anyone plays. Set this one to **Watch →
Participating and @mentions**, and what reaches you is what needs you:

- **a move that could not reach its game**, whose reply @mentions you;
- **anything a game @mentions you in**, such as its notice that it is your
  turn.

🚨 CI Failure Alerts also opens an issue when 🎲 Move Intake fails, but it
mentions no one, so under this setting it shows on the Issues tab rather than
in your notifications.

---

## 🌿 The Workflows

| Workflow                   | Gives you                                                                   |
| :------------------------- | :-------------------------------------------------------------------------- |
| `intake.yml`               | 🎲 Move Intake: every move issue, routed to its game. This repository's own |
| `checks.yml`               | Lint and tests, the intake's included; secret scan, CodeQL, workflow lint   |
| `governance.yml`           | PR title and DCO checks, triage, stale sweep, slash commands                |
| `ci-failure-alert.yml`     | Opens an issue when a watched workflow fails, 🎲 Move Intake included       |
| `release.yml`              | Draft notes, publish assets, prune superseded releases                      |
| `maintenance.yml`          | Prunes stale deployments and draft releases                                 |
| `lifecycle.yml`            | Claimed this repository once; flags a new major of the standards            |
| `dependabot-automerge.yml` | Approves and queues patch and minor updates                                 |
| `apply-standards.yml`      | Dispatch-only. The label taxonomy, the settings and branch protection       |
| `auto-format.yml`          | Formats what a push touched, once a formatter is configured                 |
| `auto-index.yml`           | Redraws every folder log and index after a push                             |
| `preview-deploy.yml`       | Deploys pushes to a preview target, once configured                         |
| `prune-runs.yml`           | Deletes old workflow runs, with their logs and artifacts                    |
| `verify-stubs.yml`         | Proves every stub's permission ceiling matches its called workflow          |
| `template-sync.yml`        | Proposes the template's later fixes as one pull request, when run           |

`cut-release.yml` belongs to the template, and its guard keeps it from ever
running here. Of the rest, all but `intake.yml` and `verify-stubs.yml`, which
run scripts kept here, are stubs that call
[`tannergolden/standards`](https://github.com/tannergolden/standards), so a fix
there reaches this repository without a commit here.

**Do not rename the job ids** `ci` and `secrets` (in `checks.yml`) or `pr` (in
`governance.yml`): branch protection depends on them. **Sign your commits
off** with `git commit -s`; the DCO check is required once the rulesets are on.

> [!NOTE]
> **GitHub pauses scheduled workflows in a public repository after 60 days
> without activity.** 🎲 Move Intake runs on issues, not on a schedule, so the
> game never pauses; the weekly sweeps can be switched back on from the
> Actions tab.

---

## 🔄 Template Sync

This repository was generated from the private `tannergolden/repo` template.
**🔄 Template Sync** brings that template's later fixes here, but only when
you run it from the Actions tab, and only as one pull request you review. It
needs a `BOT_ACCESS_TOKEN` secret that can read the template, since the
template is private; see [`.github/template-sync.md`](.github/template-sync.md).

Every change this repository made to a file the template ships is protected
in [`.github/template-sync`](.github/template-sync), the list the sync reads:

| File                                               | Changed here                   | Kept by                                                           |
| :------------------------------------------------- | :----------------------------- | :---------------------------------------------------------------- |
| `README.md`, `LICENSE`                             | This page, and the MIT licence | Yours from the start: the sync never touches them                 |
| `.github/workflows/governance.yml`                 | No welcome on a new issue      | `# keep mine`: where you both changed a line, yours stands        |
| `.github/workflows/checks.yml`                     | Runs the intake's tests        | `# keep mine`                                                     |
| `.github/workflows/ci-failure-alert.yml`           | Watches 🎲 Move Intake         | `# keep mine`                                                     |
| `.github/ISSUE_TEMPLATE/`, `intake/`, `intake.yml` | This repository's own          | A `!` rule: stopped, should the template ship the same name       |
| The seeded documents in `.github/docs/`            | The MIT footer                 | The per-file merge: the template's other changes arrive around it |

A file you and the template changed in the same place is left exactly as you
have it, so none of this is ever overwritten. Two things still need your eye
in a sync's pull request:

- **A footer the template rewrites waits on you**, as a conflict. Do not make
  it match the template's, as the pull request suggests. Add
  `# keep mine: /path/to/the/document.md` under **Your rules** instead, and
  the MIT footer stands from then on.
- **A seeded document the template adds arrives with the template's footer**,
  "Proprietary and confidential; all rights reserved." Change that line to
  the MIT one in the same pull request.

Where `# keep mine` keeps your lines, the template's change to them is shown
in the pull request rather than applied: a new workflow for 🚨 CI Failure
Alerts to watch, say. Copy across anything worth having.

---

## 📦 What's Inside

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                       | Purpose                                                                                                                                    |
| :------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------- |
| [`.devcontainer/`](.devcontainer/README.md) | The language-neutral development container this repository ships, and how to give it the toolchain your project needs.                     |
| [`.github/`](.github/)                      | CODEOWNERS, Dependabot, release notes config, the issue form, the seeds, scripts and workflows - logged below                              |
| [`.vscode/`](.vscode/README.md)             | The VS Code settings and extension recommendations this repository shares, and why every other file in this folder stays out of git.       |
| [`assets/`](assets/README.md)               | Where this project keeps what presents it: four folders to start, a name ready for every other kind, and the rules every file follows.     |
| [`intake/`](intake/README.md)               | The router every move passes through: the table of games, the script that reads each title against it, and the tests that hold both to it. |
| [`.editorconfig`](.editorconfig)            | Editor defaults every editor honours: UTF-8, LF, a final newline, and indentation per language                                             |
| [`.env.example`](.env.example)              | Environment variable template for this project.                                                                                            |
| [`.gitattributes`](.gitattributes)          | Git attributes - line endings, diffs, and what counts as binary                                                                            |
| [`.gitignore`](.gitignore)                  | &#x1F5C4;&#xFE0F; Universal Ignore Patterns                                                                                                |
| [`.markdownlint.json`](.markdownlint.json)  | Repository-wide markdownlint rules. Discovered by mechanism, which is why this lives at the root.                                          |
| [`LICENSE`](LICENSE)                        | MIT License                                                                                                                                |
| [`README.md`](README.md)                    | This file.                                                                                                                                 |

<!-- AUTO-INDEX:END -->

**Every folder carries a `README.md` that logs each file inside it**, with two
exceptions. GitHub shows a README in `.github/` in place of this page, so that
folder's own files are logged here instead, and `.github/ISSUE_TEMPLATE/`
holds only what GitHub reads there. 🗂️ Machined Indexes redraws both tables
after every push:

<!-- AUTO-INDEX:BEGIN dir=./.github style=log -->

| Entry                                              | Purpose                                                                                                                             |
| :------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| [`docs/`](.github/docs/README.md)                  | Where this project keeps its own documents, and where the engineering standards it follows actually live.                           |
| [`ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/)       | The move form, and a chooser that offers nothing else                                                                               |
| [`scripts/`](.github/scripts/README.md)            | The checks this repository runs on its own configuration, and the tests that guard them.                                            |
| [`workflows/`](.github/workflows/README.md)        | Every workflow in this repository: the name it shows in the Actions tab, what triggers it, and what it does.                        |
| [`CODEOWNERS`](.github/CODEOWNERS)                 | CODEOWNERS - review ownership                                                                                                       |
| [`dependabot.yml`](.github/dependabot.yml)         | Dependabot - automated dependency updates                                                                                           |
| [`release.yml`](.github/release.yml)               | GitHub auto-generated release notes configuration.                                                                                  |
| [`template-sync`](.github/template-sync)           | Every path tannergolden/repo ships, and whether &#x1F504; Template Sync, when you run it, keeps it current in this repository.      |
| [`template-sync.lock`](.github/template-sync.lock) | Where each file here was last synced from.                                                                                          |
| [`template-sync.md`](.github/template-sync.md)     | How this repository takes its template's later fixes when you run &#x1F504; Template Sync, what you control, and what waits on you. |

<!-- AUTO-INDEX:END -->

---

## 📚 The Standards

Everything about how to branch, review, release and secure a repository lives
in the [Standards Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md).
This repository follows it **by link**, like every repository generated from
the same template.

---

## 🔒 Licence

**MIT.** See [`LICENSE`](LICENSE). The template this repository came from is
proprietary; everything here is MIT, the seeded documents' footers included.
The shared workflows and actions it calls are published separately, under
their own licence.

---

<div align="center">

**Click a move. The rest is automatic.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden). Distributed under the MIT License.

</div>
