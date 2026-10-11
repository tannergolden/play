<!--
title: '🛤️ GOLDEN PATH (PRIVATE)'
description: 'A private scaffold with no imposed structure, inheriting its community health files from the account .github repository.'
tags: [template, scaffold, private, engineering-standards]
category: docs
-->


<div align="center">

# 🛤️ GOLDEN PATH (PRIVATE)

<a name="top"></a>

**The paved road, with the paving stones left for you to place.**

_Standards wired. Structure yours to invent._

</div>

---

## 💡 What This Is

**A standards-wired empty room.** Every guardrail is already connected -
continuous integration, secret scanning, static analysis, workflow linting,
governance, pull request validation - and the structure those guardrails will
eventually protect does not exist yet, because you are going to invent it.

That is the whole difference between this and its public counterpart:

|                    | [`tannergolden/path`](https://github.com/tannergolden/path) (public) | This one (private)                               |
| :----------------- | :------------------------------------------------------------------- | :----------------------------------------------- |
| **Purpose**        | A boilerplate. A working shape, already decided                      | A foundation. Build the shape from scratch       |
| **Standards**      | By link, from the standards repository                               | Identical - by link, same pins                   |
| **Structure**      | Ships `src/`, `tests/`, `packages/`, `benchmarks/`                   | Ships none of it                                 |
| **Assets**         | `branding/`, `screenshots/`, `diagrams/`, `html/` in `assets/`       | Identical - the Markdown Kit draws into it       |
| **Seed documents** | `docs/`, in plain sight                                              | `.github/docs/`, in with the other scaffolding   |
| **Health files**   | Copied in, so any owner gets a complete repository                   | Inherited from the account's `.github`           |
| **Licence**        | MIT                                                                  | Proprietary and confidential                     |
| **Ownership**      | CODEOWNERS rules all commented, owner unknown                        | One live rule: `@tannergolden`                   |
| **For**            | Anyone, including you, starting a conventional project               | You, starting something whose shape is the point |

Reach for the public one when the project fits a normal shape and you would
rather not think about it. Reach for this one when the structure **is** the
design work - a monorepo that is not laid out like anyone else's, a research
tree, a service with an unusual topology - and an imposed `src/` would be the
first thing you delete.

---

## 🔀 Fork, Or "Use This Template"

Both buttons hand you every file in this repository. They differ in exactly one
thing: whether your copy keeps a **link back to this one**.

**Fork it** when you want this repository's history, and to pull later changes
back down through git. A fork remembers where it came from, so `Sync fork` and
`git pull upstream` both work.

**Click "Use this template"** when you want the current version as a starting
point. You get a clean repository with a single `Initial commit` and no parent,
and later fixes to the scaffold can still reach it - whenever you run
**🔄 Template Sync**, as a pull request, one file at a time, merged with your
changes. It is the route this template is built for, and the one
**🚀 The First Five Minutes** assumes further down.

|                              | Fork                                               | "Use this template"                 |
| :--------------------------- | :------------------------------------------------- | :---------------------------------- |
| **Link back to here**        | Kept - `Sync fork` works                           | None                                |
| **Later scaffold fixes**     | `Sync fork`: every change, or none                 | 🔄 Template Sync: per file, as a PR |
| **History**                  | Every commit this repository has                   | One `Initial commit`                |
| **Actions**                  | **Disabled until you enable them**, per GitHub     | On from the start                   |
| **Issues**                   | Off by default                                     | On                                  |
| **A new pull request**       | Defaults to targeting **this** repository          | Targets yours                       |
| **Visibility**               | Private, and a fork's visibility cannot be changed | Yours to choose                     |
| **Your contributions graph** | Commits to a fork do not count                     | They count                          |

### What a fork actually buys you

Less than it looks, and it is worth knowing why before choosing it. **The
standards reach both routes identically** - by link, same pins, as the table
above says. Every `uses:` here points at `tannergolden/standards@v1`, a moving
major tag, so every fix in the v1 line arrives the moment it is published
whether you forked or generated. Forking does not make you more current; that
part is already free.

What a fork does sync is the **scaffold**: the fifteen stub workflows and the
seeded documents in `.github/docs/` - and this template ships no structure to
sync in the first place, which is the whole of difference one. A generated
repository can take those fixes too - every stub but `cut-release.yml` -
whenever you run 🔄 Template Sync, so what a fork adds is the shared history -
and with it, every change at once or none. In a
fork, delete `.github/workflows/template-sync.yml`: `Sync fork` already carries
the same changes, and two routes to them would only collide.

> [!IMPORTANT]
> **Initialisation and `Sync fork` want opposite things.** Once Actions are
> running, the `init` job claims the repository and **force-pushes the default
> branch** - here it is mostly rewriting the bare "Initial commit" into a
> Conventional Commit, but the force-push is the same. That is the moment your
> history stops being a fast-forward of this one's, so `Sync fork` begins
> offering to discard your commits rather than catch you up.
>
> Neither is misbehaving: a fork wants a shared history, and initialisation
> deliberately rewrites one. If you want the fork **and** the shared history,
> delete `.github/TEMPLATE_INIT` before enabling Actions. That skips
> initialisation entirely.

> [!WARNING]
> **What follows your copy down both routes - and what does not.**
>
> The **licence propagates** either way - difference four, covered in full under
> 🔒 Licence below. Anything you fork or generate from here starts proprietary.
>
> The **parity check stays behind, and is yours to delete.** 📐 Template Parity
> carries the inverted guard (`if: is_template`, as **🌿 The Workflows**
> explains), so it runs here and nowhere else: neither route inherits that flag,
> so it will never fire in your copy or measure your tree against
> `tannergolden/path`. Inert rather than dangerous - but still five files
> enforcing a contract that is not yours, so delete
> `.github/template-parity.yml`, its lock `.github/template-parity.lock`, its
> two scripts, and its workflow.
>
> The **community health files do not follow at all.** Difference three inherits
> them from [`tannergolden/.github`](https://github.com/tannergolden/.github),
> and that inheritance is per account. A copy landing outside `tannergolden` has
> no code of conduct, contributing guide, security policy, issue forms or pull
> request template until you provide them - see **⚠️ Three Things About
> Inheritance** below.

> [!TIP]
> **There is a third route.** Generate with "Use this template", then add this
> repository as a second remote:
>
> ```bash
> git remote add template https://github.com/tannergolden/repo
> git fetch template
> ```
>
> Cherry-pick whatever you want from it, whenever you want it, with none of the
> fork's costs - no disabled Actions, no force-push collision, and no pull
> request that opens against the template by mistake. For the template's own
> fixes, prefer 🔄 Template Sync: a cherry-pick arrives in the template author's
> identity, unmerged with your edits.

> [!NOTE]
> **Neither route carries the template flag over.** Ten of the fifteen stubs
> are guarded by `!github.event.repository.is_template`, and 🏷️ Cut Release and
> the parity check by its inverse - which is what keeps those ten silent here
> and the other two silent everywhere else. 🔄 Template Sync reads the same flag
> to decide whether to check its list or to sync. A fork inherits that flag no
> more than a generated repository does, so your copy lands on the right side of
> every guard.

---

## 📐 Exactly Five Differences

This is a **contract, not a description**. These five are the only ways this
repository is permitted to differ from
[`tannergolden/path`](https://github.com/tannergolden/path). Everything else -
all fifteen trigger workflows (the stub ceiling check among them), `.editorconfig`,
`.gitignore`, `.markdownlint.json`, `.env.example`, `.devcontainer`, `.vscode` and
`assets/` - is byte-identical,
and every seeded document is identical but for the licence footer that
difference four requires.

**Any difference outside these five is drift, and drift is a defect.** Fix it,
do not document it.

> [!IMPORTANT]
> **The contract is enforced, not just asserted.** It lives as data in
> [`.github/template-parity.yml`](.github/template-parity.yml), and
> [`📐 Template Parity`](.github/workflows/template-parity.yml) compares the two
> trees against it on every pull request, every push to the default branch, and
> once a day. That file is the contract; this section describes it.
>
> It was prose alone for a long time, and prose does not fail a check. Eight
> seeded documents had quietly diverged by the time anybody diffed the trees -
> each one carrying an absolute cross-link that encoded its own depth.
>
> The same contract also drives the **parity sync**, which brings the public
> template's changes here when you ask - see **And this template, from the
> public one** below. The
> standards are explicit that [a rule and its gate change
> together](https://github.com/tannergolden/standards/blob/Development/README.md);
> this was the rule that had no gate.

### 1. No imposed structure

No `src/`, `tests/`, `packages/`, or `benchmarks/`. The public template ships
those as empty homes so somebody arriving cold has an obvious place for a first
file. You do not need telling; you need the tree left alone so the shape can
follow the project.

**`assets/` is here anyway, and it is not structure.** It ships for one reason:
so the [Markdown Kit](https://github.com/tannergolden/markdown), when a page
uses it, has a place to put each file it generates. The kit makes a folder there
for each part it draws, `banners/`, `badges/`, `trophies/` and `elements/`, the
first time it draws it. And every repository carries an `assets/` folder
whatever its project, because every project has something to show, so it starts
with four folders: `branding/`, `screenshots/`, `diagrams/` and `html/`. So this
one ships the public template's `assets/` byte for byte, and the parity check
holds it to that.

### 2. Seed documents live in `.github/docs/`

Not `docs/` at the root, and not a dot-directory of its own. `.github` is
already where repository scaffolding lives, so putting the seeds inside it keeps
them clear of your structure **and** lets them keep a plain name. One hidden
directory instead of two.

Everything the template seeds therefore sits outside the tree you are building,
and the first visible directory in this repository will be one you created. Copy
what you want out into whatever shape you decide on.

> [!NOTE]
> `.github/docs/` is not a path GitHub treats specially. Only particular
> **filenames** under `.github` carry meaning - the workflows directory,
> CODEOWNERS, the health files - and an arbitrary subdirectory beside them is
> just files. Nothing collides.

### 3. No community health files

Inherited from [`tannergolden/.github`](https://github.com/tannergolden/.github)
instead: code of conduct, contributing guide, governance charter, security
policy, support guide, funding target, issue forms, discussion forms, and pull
request template. One copy, edited in one place, reaching every repository on
the account at once. The conditions this depends on are below.

### 4. A proprietary licence

Not MIT. Details in the licence section further down, including the part that
matters most - it propagates to everything generated from here.

### 5. A named owner in CODEOWNERS

The public template ships every ownership rule commented out, because it cannot
know who will generate from it and a rule naming an owner without write access
is a GitHub error rather than a warning. This one knows: it is private and
single-maintainer, so it names `@tannergolden` in a single live rule and drops
the placeholders entirely.

That does not block your own pull requests. The shipped rulesets require zero
approvals and do not require code-owner review, so a solo maintainer cannot
deadlock on being unable to approve their own work. What it buys is an
automatic review request on anything opened by somebody else - Dependabot, or an
agent acting on your behalf.

### What follows from these, and is not a sixth difference

`.gitattributes` differs only because difference two moved the seeds:
it classifies `.github/docs/**` as well as `docs/**`, which stays for the tree
you instantiate the seeds into. Every seeded document
differs by its licence footer, because difference four requires it. The two
index documents differ further, because they name the seed path **in prose**:
`.github/docs/templates/README.md` where it says where instantiated documents
go, and `.github/docs/README.md` by one paragraph more, since the sentence
explaining that the seeds sit outside the tree you are building is only true on
this side. `README.md` differs because it is this file. `.github/TEMPLATE_INIT` differs
because difference three shaped what initialisation has to say here: the public
copy names a `git grep` recipe over paths this tree does not have, and the
funding target and issue chooser its initialisation rewrites are inherited
rather than local. The parity contract, its sync's lock and
the workflow enforcing it exist only here because this repository is the one
defined as a delta - the baseline cannot check parity against itself. The
READMEs in `.github/workflows/` and `.github/scripts/` differ for the same
reason: each logs every file in its folder, and those folders hold the parity
check's workflow and scripts on this side alone. `.github/template-sync` differs
because each template names the files it ships, and after differences one, two
and three the two ship different files. None of these is an independent
decision, and none needs one.

**Cross-links between seeded documents are relative, and that is load-bearing.**
A relative link resolves the same at either depth, so it is the same string on
both sides; an absolute one encodes the depth and reintroduces a difference in
every file that carries a link. That is exactly how the eight documents above
drifted. Relative is also the convention the [Standards
Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md)
uses throughout, so seeds and standards now link the same way.

---

## ⚠️ Three Things About Inheritance

**1. The `.github` repository must stay public.** GitHub will not serve default
community health files from a private one. It can be public while every
repository inheriting from it stays private - that part is fine.

**2. `ISSUE_TEMPLATE` is all-or-nothing.** The moment this repository contains
_any_ file in its own `.github/ISSUE_TEMPLATE/`, GitHub stops using **every**
inherited issue form, not just the one you added. Adding a single
project-specific template means copying the whole set down first.

**3. Three files are never inherited**, which is why they are still here:

| File             | Why it must be local                 |
| :--------------- | :----------------------------------- |
| `CODEOWNERS`     | Read only from the repository itself |
| `dependabot.yml` | Same                                 |
| `release.yml`    | Same                                 |

`LICENSE`, `.gitignore`, `.gitattributes`, and `.editorconfig` are not GitHub
features at all and are likewise always local.

---

## 🔒 Licence

**Proprietary and confidential. All rights reserved.** Not MIT, not open source,
and not available under any public licence - unlike
[`tannergolden/path`](https://github.com/tannergolden/path), which is MIT and
stays that way.

> [!IMPORTANT]
> **The licence propagates.** Every repository generated from this template
> inherits `LICENSE` verbatim, so anything built here starts proprietary by
> default. That is the intent - but if you ever generate something you mean to
> open source, replace `LICENSE` and the document footers **before** the first
> public push, not after.

The shared workflows and actions this repository calls are published separately
under their own licence and are unaffected by this one.

---

## ⚠️ CI Is Green, And Only Half Configured

The `ci` job in `checks.yml` runs the commands **you** give it, and **fails when every stage resolves
to nothing** rather than reporting a green check that checked nothing. An empty
room has no source code to lint - but that is not the same as nothing to
validate.

So `lint-command` starts out pointing at
[`.github/scripts/validate-repository.py`](.github/scripts/validate-repository.py),
which checks what exists from the first commit: every YAML and JSON file parses,
every workflow `uses:` is pinned to a tag or a commit rather than a branch, no
CRLF or stray whitespace. It lives under `.github/` so the root stays yours.

Nothing is testing or building anything yet, because there is nothing there yet.
Replace the command when that changes:

```yaml
jobs:
  ci:
    uses: tannergolden/standards/.github/workflows/ci.yml@v1
    with:
      lint-command: 'golangci-lint run'
      test-command: 'go test ./...'
      build-command: 'go build ./...'
```

| Stack  | `lint-command`                      | `test-command`  | `build-command`         |
| :----- | :---------------------------------- | :-------------- | :---------------------- |
| Go     | `golangci-lint run`                 | `go test ./...` | `go build ./...`        |
| Rust   | `cargo clippy -- -D warnings`       | `cargo test`    | `cargo build --release` |
| Python | `ruff check .`                      | `pytest`        | `python -m build`       |
| Node   | `npm run lint`                      | `npm test`      | `npm run build`         |
| .NET   | `dotnet format --verify-no-changes` | `dotnet test`   | `dotnet build`          |

One real command is enough. A `Makefile` with `lint`, `test`, `build`, and `docs`
targets works too - delete the `with:` block and the `ci` job falls back to
`make <target>`. That would put a file in the root, which is yours to decide.

---

## 🤖 No AI Infrastructure, On Purpose

This template ships **no agent instruction files and no agent configuration**.
That is a decision, not an omission.

Agent instructions are **always loaded**. Every byte is paid on every session, in
every repository, forever. They also carry conventions that belong to a project
rather than to a scaffold: how you write commits, what must never be touched by
hand, which commands actually build the thing. Shipping a default set makes that
choice on your behalf, invisibly, and the usual result is a file nobody wrote and
nobody trusts.

**Nothing here depends on them.** Initialisation, CI, the rulesets, the release
flow and every workflow behave identically with none of it present. Adding it is
additive, and so is taking it away.

When you do want it, there are two supported routes and no wrong answer:

| Route                                                       | You commit                  | Updates arrive by                            |
| :----------------------------------------------------------- | :-------------------------- | :------------------------------------------- |
| **By hand**                                                 | the instructions themselves | you editing them                             |
| **[`tannergolden/intelligence`](https://github.com/tannergolden/intelligence)** | one workflow stub | a release moving a tag, with no pull request |

Writing them by hand suits conventions that are specific to one project. The
publisher suits several repositories that share one set, for the same reason the
workflows here are called rather than copied: the law lives in one place, and a
fix reaches everything pinned to it. Its README carries the stub to copy and the
version to pin.

> [!IMPORTANT]
> **Whichever route you take, confirm the tools you actually use load what you
> wrote.** They do not agree on which filename to read, and some will not find a
> shared file at all unless a small per-tool file points them at it. Instructions
> nothing loads are worse than none, because they look finished.

> [!TIP]
> **Either route stays reversible.** What you write by hand is yours to delete.
> What the publisher delivers is listed with digests in a lockfile, so the
> inventory of what arrived is also the manifest for removing it.

---

## 🎉 What Happens On Its Own

The `init` job in `lifecycle.yml` runs once and deletes `.github/TEMPLATE_INIT` so it never
runs again. Because you own both this template and whatever it generates, the
identity substitution has almost nothing to do - the real work it does here is
**rewriting GitHub's bare "Initial commit" into a proper Conventional Commit**,
so a new repository's history is compliant from its first entry rather than its
second.

> [!NOTE]
> GitHub does not reliably fire an event when a repository is created from a
> template. If nothing happens within a minute or two, run it from the Actions
> tab. Running it twice is harmless.

---

## 🚀 The First Five Minutes

> [!TIP]
> Every step below, plus signing and the token, is kept as one canonical
> checklist in the standards:
> [🙋 What You Do By Hand](https://github.com/tannergolden/standards/blob/Development/docs/introduction/What-You-Do-By-Hand.md).

1. **Check that init ran** - `.github/TEMPLATE_INIT` should be gone and the
   first commit should read as a Conventional Commit rather than GitHub's bare
   "Initial commit". If not, dispatch **🎯 Standards Lifecycle** from the
   Actions tab; the `init` job is the one that claims the repository.
2. **Sign your commits off.** `git commit -s` adds the `Signed-off-by` trailer
   the DCO check requires. Once branch protection is on, a commit without it
   blocks the merge. `git config alias.ci 'commit -s'` and forget about it.
3. **Configure the `ci` job in `checks.yml`**, as above, once you have
   something to build. Until then it runs the repository validator and passes
   honestly - the job fails only when every stage resolves to nothing, and
   `lint-command` never does.
4. **Apply the settings, then the protection** - run **🎯 Apply Standards**
   from the Actions tab. `apply-settings` writes the repository settings
   (squash-only merges, head branches deleted on merge, auto-merge, the
   security features); `apply-rulesets` writes branch protection. Both preview
   by default and change nothing until you turn `dry-run` off. Do settings
   first: they are checkboxes, while a wrong ruleset blocks every merge.
5. **Confirm `.github/CODEOWNERS` names the right owner.** Unlike the public
   template this ships one live rule rather than commented placeholders, and
   initialisation rewrites it. It never blocks your own work: the shipped
   rulesets require zero approvals and no code-owner review, so a solo
   maintainer cannot deadlock on approving their own pull request.
6. **Enable ecosystems in `.github/dependabot.yml`** as you add manifests. Only
   `github-actions` is on, because it is the only one guaranteed to apply.
7. **Add a `BOT_ACCESS_TOKEN` secret that can read this template**, if you
   mean to run 🔄 Template Sync. It is private, so the sync cannot even fetch
   it without one; with one, the stubs under `.github/workflows/` update too. While you are there, put a `#`
   in front of anything in `.github/template-sync` you want to own outright.
8. **Replace this README.** Everything above describes the template, not your
   project. Nothing rewrites it for you, because only you know what this
   repository is for. The sections worth keeping are the workflow table and
   the licence note; the rest is scaffolding that has done its job.

> [!IMPORTANT]
> **🎯 Apply Standards needs a token for two of its three jobs.** Applying the
> label taxonomy needs nothing. **Writing the settings and the rulesets** each
> need a token with administration write as `ADMIN_TOKEN`. Without it, those
> jobs stop with a sentence naming the missing token instead of a bare `403`.
>
> A fine-grained token scoped to your repositories generated from the
> templates, with **Administration: Read and write** and nothing else, is all
> it needs. Step-by-step:
> [Creating the ADMIN_TOKEN](https://github.com/tannergolden/standards/blob/Development/docs/operations/Branch-Protection.md#-creating-the-admin_token).
> You can skip it entirely by applying the settings and rulesets yourself,
> where your own rights are already enough.

> [!NOTE]
> **CodeQL skipping is expected here, not a failure.** Code scanning cannot
> accept results from a private repository without GitHub Advanced Security,
> so the job checks visibility and skips with a notice rather than erroring.
> A repository with Advanced Security can analyse privately through GitHub's
> built-in default setup instead.

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

Nothing else. The root carries only what a tool discovers there by mechanism.

**Every folder carries a `README.md` that logs each file inside it**, with one
exception. GitHub shows a README in `.github/` in place of this page, so that
folder's own files are logged here instead. 🗂️ Machined Indexes redraws both
tables after every push:

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

## 🌿 The Workflows

| Workflow                   | Gives you                                             |
| :------------------------- | :---------------------------------------------------- |
| `checks.yml`               | Lint/test/build, secret scan, CodeQL, workflow lint   |
| `governance.yml`           | PR title and DCO checks, triage, stale sweep, slash commands |
| `release.yml`              | Draft notes, publish assets, prune superseded releases |
| `maintenance.yml`          | Prunes stale deployments and draft releases           |
| `lifecycle.yml`            | Claims this repository once; flags a new major        |
| `dependabot-automerge.yml` | Approves and queues patch and minor updates           |
| `ci-failure-alert.yml`     | Opens an issue when a watched workflow fails          |
| `apply-standards.yml`      | Dispatch-only. The label taxonomy and branch protection |
| `auto-format.yml`          | Formats what a push touched                           |
| `preview-deploy.yml`       | Deploys pushes to a preview target, once configured   |
| `prune-runs.yml`           | Deletes old workflow runs, with their logs and artifacts |
| `verify-stubs.yml`         | Proves every ceiling matches its called workflow      |
| `auto-index.yml`           | Redraws every folder log and index after a push       |
| `template-sync.yml`        | Proposes this template's later fixes as one pull request, when run |
| `cut-release.yml`          | Template only. Publishes the releases generated repositories follow |
| `template-parity.yml`      | Enforces the five-differences contract. Runs only in this template |

**Do not rename the job ids** `ci` and `secrets` (in `checks.yml`) or `pr`
(in `governance.yml`) - branch protection depends on them; the file a job
lives in does not matter, but its id does. Only `preview-deploy.yml` names a
branch, because `Preview` is a promotion branch rather than your default one;
everywhere else a pull request always runs and a push runs only on the default
branch, whatever it happens to be called.

Every workflow ships installed, and most carry an `is_template` guard, so they
are silent here and come alive in every repository generated from this one.
**Three do not, and run in the template as well:** `prune-runs.yml`, because a
template accumulates run history like any repository and nothing else would
ever clear it, `verify-stubs.yml`, because a stub with a wrong ceiling is
broken wherever it sits, and `auto-index.yml`, because the template's own
folder logs need keeping too. `template-sync.yml` runs on both sides of the
guard, differently: here it checks that `.github/template-sync` names every
file the template ships, and in your copy it syncs when you run it. `cut-release.yml` and
`template-parity.yml` invert the guard instead - they run *only* here. Delete any
file that does not fit; each one is yours, and 🔄 Template Sync switches a
deleted file off rather than bringing it back.

> [!IMPORTANT]
> **🎯 Apply Standards previews by default and changes nothing** until you turn
> `dry-run` off - a wrong ruleset blocks every merge here. Labels need no
> token; writing rulesets needs `ADMIN_TOKEN`.

**Sign your commits off.** `git commit -s` - the DCO check is a required status
check once the rulesets are on, and a commit without the trailer blocks the
merge.

> [!NOTE]
> Nothing here pins a third-party action; every `uses:` points at
> `tannergolden/standards`, so the pins that need maintaining are maintained
> once, there. The one caveat to leaving a repository alone: **GitHub disables
> scheduled workflows in a public repository after 60 days of inactivity** -
> not an issue for this private one, but it applies to anything public you
> generate from it. Dependabot is exempt from that rule and still surfaces a
> new major, so a dormant repository finds out either way.

> [!IMPORTANT]
> **CodeQL needs a public repository or GitHub Advanced Security.** On a private
> repository without it, that job skips rather than failing - so it will not
> redden anything, and it will not analyse anything either.

---

## 🔄 Template Sync: Fixes When You Ask

This template keeps improving after you generate from it - a stub gains a
guard, the repository validator learns a check, a seeded document gets
clearer. **🔄 Template Sync** is how those fixes reach your copy, and it runs
only when you run it.

**Nothing happens on its own.** There is no schedule. When you want the
template's latest release, run **🔄 Template Sync** from the Actions tab: it
compares your repository with that release and proposes whatever changed as
**one pull request** on `chore/template-sync`, which you review and merge like
any other. If you never run it, nothing in your repository ever changes.

| It always...                  | Because                                                                                                        |
| :---------------------------- | :------------------------------------------------------------------------------------------------------------- |
| Merges rather than overwrites | Each file is merged with whatever you changed in it, by the same three-way merge git uses                      |
| Writes in your identity       | The template is rewritten exactly as initialisation rewrote it, so footers and the owner stay yours            |
| Leaves a conflict untouched   | A file you and the template changed in the same place stays as you have it; the pull request shows the change |
| Respects a deletion           | A file you delete is switched off, under its old name or a new one, until you take the `#` off its line again  |
| Leaves your own files alone   | This README, the licence, CODEOWNERS and `assets/` start switched off, and nothing you add is ever touched   |

Three files describe it, and only one of them is yours to edit:

| File                                                   | What it is                                                                                         |
| :----------------------------------------------------- | :------------------------------------------------------------------------------------------------- |
| [`.github/template-sync`](.github/template-sync)       | Every path the template ships, in `.gitignore` syntax. Put a `#` in front of a line to keep that file as yours |
| `.github/template-sync.lock`                           | Where each file was last synced from. Written by the sync alone; never edit it                     |
| [`.github/template-sync.md`](.github/template-sync.md) | The full explanation: every outcome, every option, and what to do when something waits on you      |

> [!IMPORTANT]
> **This template is private, so the sync needs a `BOT_ACCESS_TOKEN` that can
> read it** - without one it cannot even fetch the template. The same secret
> lets workflow files under `.github/workflows/` arrive, which GitHub's default
> token can never write, and lets CI run on the pull request.

**You follow a major, and a new one is your decision.** This template publishes
versions with 🏷️ Cut Release, moving `v1` to each new one, and a sync takes
whatever `v1` points at. A breaking change ships as `v2`, which nothing follows
until you change `ref:` in `.github/workflows/template-sync.yml`. To remove the
option altogether, delete that file.

### And this template, from the public one

The same engine keeps this template close to
[`tannergolden/path`](https://github.com/tannergolden/path), through the
five-differences contract rather than a list. Dispatch **📐 Template Parity**
with `sync` ticked and it proposes everything the public template changed as
one pull request on `chore/template-parity`: the seeds move to `.github/docs/`
and take this repository's footer, nothing absent, inherited or listed under
`sync-never` in [`.github/template-parity.yml`](.github/template-parity.yml)
arrives, and every other file is merged, so the permitted differences survive.
`.github/template-sync` gains or loses a line for every file that comes or goes,
so its own check stays green. Like everything else here, it never runs
unasked; the daily run only checks. It follows the public template's default
branch rather than its releases - the tree the check compares against - holds
workflow files back without a `BOT_ACCESS_TOKEN` that can write them, and keeps
whatever waits on you in one issue, **📐 Template Parity Sync is waiting on
you**.

The engine lives in [`tannergolden/standards`](https://github.com/tannergolden/standards/blob/Development/docs/distribution/automation/Template-Sync.md),
called rather than copied, like every other workflow here.

---

## 📚 The Standards

Everything about how to branch, review, release, and secure a repository lives
in the [Standards Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md).
Follow it **by link**. A standard copied into your repository is a standard that
starts going stale the moment you paste it.

The one exception is [`.github/docs/templates/`](.github/docs/templates/README.md),
which is meant to be copied: those are fill-in documents that become _your_
project's decisions. A fill-in document's destination mirrors its path minus
`templates/`, and where you put it is yours to choose.

---

<div align="center">

**Same road. Your paving stones.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden). Proprietary and confidential; all rights reserved.

</div>
