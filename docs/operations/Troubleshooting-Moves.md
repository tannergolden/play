<!--
title: '🩺 TROUBLESHOOTING A MOVE'
description: 'What to do when a move is stranded, overdue or never answered, when a reply looks wrong, and when a replay is missing: how to read the issue and its run, what mends itself, and what the owner does about the rest. Read it when a move or a replay has gone wrong.'
type: guide
-->

<div align="center">

# 🩺 TROUBLESHOOTING A MOVE

<a name="top"></a>

**Where a move stopped, what mends itself, and what the owner does about the rest.**

_Read the issue first, then the run._

</div>

---

## 💡 Before You Start

- **Every action on this page is the owner's.** An AI agent working on this
  repository never opens, comments on, labels, locks or closes an issue
  here, and never starts a workflow: [AGENTS.md](../../AGENTS.md) forbids it.
- **Most faults mend themselves.** ⏳ Move Sweep sends again whatever never got
  through, the next move to go through closes the outage notice, and nobody has
  to play a move twice.
- **The App's own failures**, a missing key or a missing installation, are in
  [GitHub App](GitHub-App.md#-when-a-move-fails) with their fixes. This page
  links there rather than repeating them.

How each step decides is in
[Move Intake & Move Sweep](../technical/Move-Intake-&-Move-Sweep.md), and what
each label and reply means in [Labels & Replies](../references/Labels-&-Replies.md).

---

## 🔎 Read The Issue First

What a move's issue carries says how far it got:

| The issue shows                                                                                | Where it stopped                                                                          | What happens by itself                                                                       | What to do                                                                                        |
| :--------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------ |
| No 👀, no reply, and no label but the form's `move`                                            | Its run never started, or GitHub dropped it while it waited behind the same player's last | ⏳ Move Sweep sends it through 🎲 Move Intake once nothing has happened on it for 15 minutes | Nothing, or send it now, as below                                                                 |
| `move` and its game, but no 👀                                                                 | The Arbiter's token couldn't be minted, or the 👀 couldn't be set                         | Nothing else changes: the move goes on                                                       | Read the run's warning; a missing pair is stored as in [GitHub App](GitHub-App.md#-setting-it-up) |
| 👀 and 🚀, open, and no reply yet                                                              | Sent on: its game is playing it                                                           | Once nothing has happened on it for 15 minutes, the sweep marks it `overdue`                 | Wait: a game usually rules within a few minutes                                                   |
| `stranded`, locked, and "⚠️ **Your move didn't reach the board yet**"                          | 🎲 Move Intake couldn't start its game                                                    | Sent again once the outage notice is closed; until then the oldest is tried each sweep       | Find the step that failed, below, and fix its cause; then close the notice, unless a move has     |
| `overdue`, locked, and "⏳ **Your move was sent on, but the Arbiter hasn't ruled on it yet.**" | Its game was started, but its run failed before it could reply, or hasn't run yet         | Sent again once the notice is closed; a ruling that was only late arrives by itself          | Fix the game's failed run, in the Actions tab of tannergolden/tannergolden; then close the notice |
| `invalid`, closed, and "👋 **This isn't a move, so it's closed.**"                             | The title doesn't match its game's pattern from end to end                                | -                                                                                            | Nothing: the player picks a move on the board again. Judge the title, below                       |
| `turned away`, closed, with a reply from `github-actions[bot]`                                 | The intake's check turned it away at the door, in the game's own words                    | -                                                                                            | Nothing: the reply says why. Judge it, below, if it looks wrong                                   |
| `played` or `turned away`, closed, with a reply from `official-arbiter[bot]`                   | Its game ruled on it                                                                      | -                                                                                            | Nothing                                                                                           |
| The owner's own issue, left open with nothing on it                                            | Nowhere: the intake leaves the owner's own issues alone                                   | -                                                                                            | Nothing                                                                                           |

Four searches on the Issues tab find what is waiting:

```text
is:issue is:open label:stranded
is:issue is:open label:overdue
is:issue is:open label:arbiter-outage
is:issue is:open label:move
```

The first two are the moves waiting to go again, the third is the open outage
notice, and the last is every move still waiting for its game's ruling.

---

## 🧭 Then Read The Run

🎲 Move Intake's run for the issue names it on 🧭 Read The Title, as
`Issue #<n> by @<player>: dispatch to ...`, and the step that failed says why:

| The step that failed                                     | What became of the issue                                                     | Fix                                                                                        |
| :------------------------------------------------------- | :--------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------- |
| 🔑 Mint The Game Token, or 🎯 Start The Game             | `stranded`                                                                   | Each message and its fix is in [GitHub App](GitHub-App.md#-when-a-move-fails)              |
| 🧭 Read The Title, with an error on `intake/routes.json` | `stranded`, a move or not, as is every issue opened until the table is fixed | Fix what the error names, a row or the file: the table is checked before any title is read |
| ⚖️ Check The Move                                        | `stranded`                                                                   | Judge the move on your machine against the game's state, below, to see what stopped it     |
| ⛔ Turn The Move Away, or 👋 Turn It Away                | Answered as far as the step got: replied, perhaps not closed or locked       | Close it as not planned and lock it, as the step would have; its log shows how far it got  |
| 📥 Read The Issue, for an issue sent again               | Nothing is said on it                                                        | Check the number, and send it again                                                        |

🚨 CI Failure Alerts doesn't watch 🎲 Move Intake, so a run that failed is seen
in the Actions tab, or through the outage notice when it stranded a move.

An issue that wasn't a move, stranded while the table was broken, is sent
through the router again with the rest, which then decides it as what it is.
The owner's own issue is the exception: the sweep leaves it alone from then on,
its `stranded` label and its lock with it, so take those off by hand.

---

## 🧯 The Outage Notice

- **What it is.** One open issue, `🧯 The Arbiter is down`, labelled
  `arbiter-outage` and locked, which @mentions the owner once, however many
  moves it holds up. Every stranded and overdue move links to it.
- **Who opens it.** 🎲 Move Intake, when a move can't reach its game;
  ⏳ Move Sweep, when a move sent on goes unruled; or a game. A run that finds
  one open links to it rather than opening another.
- **Who closes it.** The game, when the next move goes through, or the owner,
  by hand, once the fault is fixed. Either way the next sweep sends every
  `stranded` and `overdue` move through 🎲 Move Intake again.
- **While it is open**, each sweep tries the oldest stranded move alone, so a
  fix nobody announces is found by itself. An overdue move is never the one
  tried, so an outage that left only overdue moves ends when a new move goes
  through, or when the owner closes the notice.
- **Close it only once the fault is fixed.** With the fault still there, the
  moves sent again fail again, and the first of them opens a fresh notice that
  @mentions the owner again.

---

## 🔁 Sending An Issue Again

| To                                     | From the Actions tab                                     | From a terminal                                                         |
| :------------------------------------- | :------------------------------------------------------- | :---------------------------------------------------------------------- |
| Send one issue through the intake      | 🎲 Move Intake, <kbd>Run workflow</kbd>, with its number | `gh workflow run intake.yml --repo tannergolden/play -f issue=<number>` |
| Sweep every issue left waiting at once | ⏳ Move Sweep, <kbd>Run workflow</kbd>                   | `gh workflow run sweep.yml --repo tannergolden/play`                    |

- **It is safe.** An issue sent again is read as it is now and goes straight to
  its game, which knows a move already played from that issue: nothing is
  played twice, and a move gone stale is turned away with the reason.
- **Only an open issue goes.** A closed one, a pull request, or one an app or a
  bot opened is left alone, and the run's log says why.
- **Leave the branch as the default.** The sweep runs on no other, and the
  intake run on another branch would use that branch's router.
- **A sweep sends ten at most**, oldest first; the next one takes the rest.
- **A schedule can be late or paused.** GitHub starts a scheduled run late when
  it is busy, sometimes by hours, and pauses the schedules of a public
  repository after 60 days without activity. Switch ⏳ Move Sweep and
  🎬 Replays back on from the Actions tab, and their first runs catch up.

---

## 🧪 Judging A Title On Your Machine

The router and the check read nothing but their environment and a folder of
files, so a title can be judged exactly as a run judges it, with no token and
nothing posted. From the root of the repository:

```bash
export RUNNER_TEMP="$(mktemp -d)" GITHUB_OUTPUT="$(mktemp)"
export GITHUB_REPOSITORY_OWNER=tannergolden ISSUE=1 PLAYER=octocat PLAYER_ID=583231
env -u GH_TOKEN -u GITHUB_TOKEN TITLE='chess: e2e4 · game 1 · move 1' python3 intake/route.py
cat "$GITHUB_OUTPUT"
```

`action=dispatch` means the title is a move, with its inputs in
`$RUNNER_TEMP/dispatch.json`, and `reject` writes its reply to
`$RUNNER_TEMP/reply.md`. Set `PLAYER=tannergolden` and `PLAYER_ID=24684994`
to judge it as the owner's.

For a move, run the check next, against the board as a run reads it and the
player's count for the hour:

```bash
gh api 'repos/tannergolden/tannergolden/contents/.github/chess/game.json?ref=Development' \
  -H 'Accept: application/vnd.github.raw+json' > "$RUNNER_TEMP/game.json"
echo 1 > "$RUNNER_TEMP/recent"
env -u GH_TOKEN -u GITHUB_TOKEN GAME=chess OWNER_ID=24684994 python3 intake/check.py
cat "$GITHUB_OUTPUT"
```

`verdict=refuse` puts the reply, word for word, in `$RUNNER_TEMP/reply.md`.
The `gh api` line only reads the game's public state: write a state by hand in
its place to try a board that isn't up, or leave `game.json` out to judge as a
run that couldn't read one. Start each title with a fresh `RUNNER_TEMP`, as a
run does.

---

## 🎬 When A Replay Is Missing

| What you see                                                                 | Why                                                                                                                                                                                 | What to do                                                                                         |
| :--------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------- |
| A won game with no replay, and nothing about it in 🎬 Replays' log           | None is made for a draw, a win the Arbiter's move made, a Pentago turn that made five for the other side, a game older than its game's newest 25, or a winner whose account is gone | Nothing                                                                                            |
| A replay in the folder, but no comment                                       | A win the owner's move ran by hand has no issue to post on                                                                                                                          | Nothing                                                                                            |
| 🧭 Plan The Run warns `<Game> game <n>: <why>, so no replay was made of it.` | The game's facts fail a check in `problem()` in `replays/build.py`                                                                                                                  | Mend the facts at the profile's engine, or the check if it is wrong; the next run draws it         |
| The run fails at 🧯 Fail On A Replay Not Drawn                               | The kit couldn't draw it; its last lines are in 🎬 Draw And Save's log                                                                                                              | Nothing, for a passing fault: every run tries again, and one runs hourly                           |
| The run fails at 🔑 Mint The Arbiter Token                                   | The Arbiter's pair is missing here, or can't be used                                                                                                                                | Store it, as in [GitHub App](GitHub-App.md#-setting-it-up); the comment waits, the replay is saved |
| A warning that comments `did not go through, and wait for the next run`      | GitHub refused the comment                                                                                                                                                          | Nothing: the next run finds any comment already posted rather than posting a second                |
| `could not save the replays to <branch> after five attempts`                 | The push lost its race five times                                                                                                                                                   | Nothing: the next run starts from the branch as it is then                                         |
| A player drawn by their initials                                             | Their avatar couldn't be had, or ImageMagick couldn't be installed                                                                                                                  | Nothing: the run goes on                                                                           |
| No run for a long while                                                      | GitHub paused the schedule after 60 days without a commit here                                                                                                                      | Switch 🎬 Replays back on: its first run draws every replay it missed                              |

🎬 Replays can be run by hand from the Actions tab at any time; tick `accounts`
to look up every account behind a replay here, as the daily run does.

---

## 🚨 When An Alert Opens

🚨 CI Failure Alerts watches ⏳ Move Sweep and 🎬 Replays here, but not
🎲 Move Intake, whose outage notice is its alarm. It opens an issue when either
fails on the default branch and closes it when that workflow next succeeds. It
mentions nobody, so with this repository watched for participating and
@mentions it shows on the Issues tab rather than in your notifications.

A sweep's warnings name each issue and the call that failed, such as
`#5: it could not be sent again: HTTP 502: Bad Gateway`, and the next sweep
tries again by itself. A sweep that couldn't read the open issues, or the
table, says so as an error and does nothing else.

---

## 🔗 See also

- [GitHub App](GitHub-App.md) - the Official Arbiter, its keys, and the messages of a move that failed to reach its game
- [Move Intake & Move Sweep](../technical/Move-Intake-&-Move-Sweep.md) - every step of both workflows, and what strands a move
- [Labels & Replies](../references/Labels-&-Replies.md) - what each label and reply means, and who posts it
- [Replays](../../replays/README.md) - what is drawn, what is kept, and what an account that is gone takes down
- [Troubleshooting](https://github.com/tannergolden/standards/blob/Development/docs/operations/Troubleshooting.md) - common repository and pipeline faults, in the standards

---

<div align="center">

**Find where it stopped. The sweep does the rest.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Proprietary; all rights reserved under [LICENSE](../../LICENSE).

</div>
