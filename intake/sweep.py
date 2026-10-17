#!/usr/bin/env python3
"""Answer every issue left waiting: mark the moves whose ruling is overdue, and send again the ones that never got there.

WHY THIS EXISTS. A move's issue stays open from the moment 🎲 Move Intake
sends it on until its game rules on it: the Official Arbiter replies there,
labels it `played` or `turned away`, and closes it. Three things can leave an
issue open with nobody to tell. A move that never reached its game is marked
`stranded` by the intake, which tells its player and the owner once, and then
waits on the owner's fix. A move sent on can lose its ruling, when its game's
run fails before it can reply. And an issue can go unanswered altogether, when
its run never starts, or when GitHub drops it while it waits behind the same
player's last. ⏳ Move Sweep runs this twice an hour, and it answers all three.

WHAT IT DOES with each open issue a player opened here, leaving out the
owner's own that aren't moves, anything an app or a bot opened, and anything
already answered (`played`, `turned away` or `invalid`):

    sent on, and no ruling for 15 minutes   marked `overdue`, its player told
                                            once, locked, and the owner told
                                            once, in the outage notice
    stranded or overdue                     sent through the intake again, once
                                            no outage notice is open
    unanswered for 15 minutes               sent through the intake again

While an outage notice is open, only the oldest stranded move is sent again,
once a sweep. If it goes through, its game closes the notice, and the next
sweep sends all the rest. A move sent again goes straight to its game, which
knows a move already played from that issue, so nothing is played twice, and
one gone stale is turned away with the reason. At most 10 issues are sent
again in one sweep, oldest first; the next sweep takes the rest.

The outage notice is the same one the intake and the games open: one open
issue labelled `arbiter-outage`, which @mentions the owner once, however many
moves it holds up, and which the next move to go through closes.

The GitHub calls are behind one small function, `gh`, which the tests
replace. Nothing here prints a title, since a line in a run's log can be read
as a workflow command.

Run its tests from the root of the repository:

    python3 -m unittest discover -s intake -p 'test_*.py'
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

import route

WAIT = dt.timedelta(minutes=15)  # how long a move waits for its ruling, or an issue for its answer, before this acts
MOST = 10  # the most issues one sweep sends again, oldest first
INTAKE = 'intake.yml'  # the workflow a move is sent again through, by its issue's number
SENDER = 'github-actions[bot]'  # whose 🚀 says a move was sent on: 🎲 Move Intake's own token
RULED = ('played', 'turned away', 'invalid')  # an issue answered for good, whether or not it was closed
STRANDED = 'stranded'  # the intake's mark on a move that never reached its game
OVERDUE = {'name': 'overdue', 'color': 'd93f0b', 'description': "⏳ Sent on, but the Arbiter hasn't ruled on it yet."}
OUTAGE = {'name': 'arbiter-outage', 'color': '6e7781', 'description': "The Arbiter's own notices"}
NOTICES = ('arbiter-outage', 'arbiter-logbook')  # the Arbiter's own issues, never a player's
NOTICE = '🧯 The Arbiter is down'
NUMBER = re.compile(r'[1-9][0-9]{0,15}')
REPOSITORY = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}')


class Failed(RuntimeError):
    """A GitHub call that didn't go through."""


def gh(*args: str) -> str:
    """One `gh` call, and what it printed. The tests replace this."""
    try:
        done = subprocess.run(['gh', *args], capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Failed(f'gh could not run: {type(exc).__name__}') from None
    if done.returncode:
        said = [line for line in done.stderr.splitlines() if line.strip()]
        raise Failed(said[-1].strip() if said else f'gh exited {done.returncode}')
    return done.stdout


def api(path: str, *fields: str, method: str = 'GET', paginate: bool = False) -> object:
    """One REST call: its answer as JSON, every page of it when `paginate`, or None when it answered nothing."""
    args = ['api', path]
    if method != 'GET':
        args += ['--method', method]
    if paginate:
        args += ['--paginate', '--slurp']
    for value in fields:
        args += ['-f', value]
    text = gh(*args)
    if not text.strip():
        return None
    found = json.loads(text)
    if paginate:
        return [item for page in found for item in page]
    return found


def when(text: object) -> dt.datetime | None:
    """A moment as GitHub writes it, `2026-10-17T10:31:55Z`, or None when it isn't one."""
    if not isinstance(text, str):
        return None
    try:
        moment = dt.datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=dt.timezone.utc)


def names(issue: dict) -> set[str]:
    """The names of the labels an issue carries."""
    return {label['name'] for label in issue.get('labels') or [] if isinstance(label, dict)
            and isinstance(label.get('name'), str)}


@dataclass
class Waiting:
    """An open issue a player opened here, still waiting on an answer."""

    number: int
    opened: dt.datetime
    marks: set[str]
    locked: bool
    quiet: bool  # nothing has happened on it for WAIT, since it was opened or last touched


@dataclass
class Sweep:
    """What one sweep found, and what it did."""

    outage: int | None = None  # the open outage notice, if there is one
    flagged: list[int] = field(default_factory=list)  # marked overdue this sweep
    told: list[int] = field(default_factory=list)  # of those, the ones whose player was told
    sent: list[int] = field(default_factory=list)  # sent through the intake again
    opened: int | None = None  # the outage notice this sweep opened
    failed: list[str] = field(default_factory=list)  # every call that didn't go through, as the log says it


def waiting(issues: list, owner: str, now: dt.datetime, routes: dict) -> list[Waiting]:
    """Every open issue a player opened here that is still waiting on an answer, oldest first. The owner's own count
    only when they are moves, by their label or their title; an app's or a bot's, a pull request, the Arbiter's own
    notices and anything answered for good never do."""
    found = []
    for issue in issues:
        if not isinstance(issue, dict) or 'pull_request' in issue:
            continue
        user, number, opened = issue.get('user'), issue.get('number'), when(issue.get('created_at'))
        touched = when(issue.get('updated_at')) or opened
        if not isinstance(user, dict) or user.get('type') != 'User' or not isinstance(user.get('login'), str):
            continue
        if type(number) is not int or number < 1 or opened is None:
            continue
        marks = names(issue)
        if marks & {*RULED, *NOTICES}:
            continue
        if user['login'].casefold() == owner.casefold() and 'move' not in marks:
            title = issue.get('title') if isinstance(issue.get('title'), str) else ''
            routed = route.route(title, player=user['login'], player_id='1', issue=str(number), owner=owner,
                                 routes=routes)
            if routed['action'] != 'dispatch':
                continue  # the owner's own issue, which the intake leaves alone
        found.append(Waiting(number, opened, marks, issue.get('locked') is True,
                             opened <= now - WAIT and touched <= now - WAIT))
    return sorted(found, key=lambda one: (one.opened, one.number))


def sent_on(repo: str, number: int) -> bool:
    """Whether the intake sent this move on: its 🚀, from the intake's own token."""
    reactions = api(f'repos/{repo}/issues/{number}/reactions?content=rocket&per_page=100', paginate=True)
    return any(isinstance(one, dict) and isinstance(one.get('user'), dict) and one['user'].get('login') == SENDER
               for one in reactions or [])


def once_overdue(repo: str, number: int) -> bool:
    """Whether this issue was marked overdue before, and its player told then."""
    events = api(f'repos/{repo}/issues/{number}/events?per_page=100', paginate=True)
    return any(isinstance(one, dict) and one.get('event') == 'labeled' and isinstance(one.get('label'), dict)
               and one['label'].get('name') == OVERDUE['name'] for one in events or [])


def overdue_text(repo: str, outage: int) -> str:
    """What a player is told when their move has waited too long for its ruling. Fixed text, with no title in it."""
    return (f"⏳ **Your move was sent on, but the Arbiter hasn't ruled on it yet.**\nIt's being looked into in"
            f" [#{outage}](https://github.com/{repo}/issues/{outage}), and your move is sent again by itself once"
            " that's closed: there's nothing you need to do.\n")


def notice_text(owner: str, run_url: str, first: int) -> str:
    """The outage notice a sweep opens: the owner @mentioned once, for every move it holds up."""
    return (f"🧯 **The Arbiter is down**, so moves aren't being ruled on.\n@{owner}, [this sweep]({run_url}) found"
            f" #{first} sent on to its game more than 15 minutes ago, with no ruling. Every move found waiting links"
            " here, and nobody is pinged again. This closes itself when a move goes through, and once it's closed,"
            " the next sweep sends every waiting move again.\n")


def label(repo: str, number: int, spec: dict) -> None:
    """Give an issue a label, made the first time it is needed with its colour and description."""
    try:
        api(f'repos/{repo}/labels', f"name={spec['name']}", f"color={spec['color']}",
            f"description={spec['description']}", method='POST')
    except Failed:
        pass  # already made, as it is every time after the first
    api(f'repos/{repo}/issues/{number}/labels', f"labels[]={spec['name']}", method='POST')


def lock(repo: str, number: int) -> None:
    api(f'repos/{repo}/issues/{number}/lock', 'lock_reason=resolved', method='PUT')


def open_notice(repo: str, owner: str, run_url: str, first: int) -> int:
    """Open the outage notice, locked, and give its number."""
    try:
        api(f'repos/{repo}/labels', f"name={OUTAGE['name']}", f"color={OUTAGE['color']}",
            f"description={OUTAGE['description']}", method='POST')
    except Failed:
        pass
    made = api(f'repos/{repo}/issues', f'title={NOTICE}', f'body={notice_text(owner, run_url, first)}',
               f"labels[]={OUTAGE['name']}", method='POST')
    number = made.get('number') if isinstance(made, dict) else None
    if type(number) is not int:
        raise Failed('the outage notice was opened, but GitHub gave no number for it')
    lock(repo, number)
    return number


def sweep(repo: str, owner: str, run_url: str, now: dt.datetime, routes: dict) -> Sweep:
    """One sweep of every open issue here."""
    done = Sweep()
    issues = api(f'repos/{repo}/issues?state=open&per_page=100', paginate=True) or []
    notices = [issue['number'] for issue in issues if isinstance(issue, dict) and 'pull_request' not in issue
               and type(issue.get('number')) is int and OUTAGE['name'] in names(issue)]
    done.outage = min(notices, default=None)
    stranded, overdue, unanswered, late = [], [], [], []
    for one in waiting(issues, owner, now, routes):
        if STRANDED in one.marks:
            stranded.append(one)
        elif OVERDUE['name'] in one.marks:
            overdue.append(one)
        elif one.quiet:
            try:
                (late if sent_on(repo, one.number) else unanswered).append(one)
            except Failed as exc:
                done.failed.append(f'#{one.number}: its 🚀 could not be read: {exc}')

    # A move sent on and still unruled: marked, its player told once, and the owner told once, in the notice.
    for one in late:
        try:
            if done.outage is None:
                done.outage = done.opened = open_notice(repo, owner, run_url, one.number)
            told = not one.locked and not once_overdue(repo, one.number)
            label(repo, one.number, OVERDUE)
            if told:
                api(f'repos/{repo}/issues/{one.number}/comments', f'body={overdue_text(repo, done.outage)}',
                    method='POST')
                done.told.append(one.number)
            lock(repo, one.number)
            done.flagged.append(one.number)
        except Failed as exc:
            done.failed.append(f'#{one.number}: it could not be marked overdue: {exc}')

    # Sent again: everything waiting, once the outage is over; while it lasts, the oldest stranded move alone, to
    # find out whether it is. An issue never answered is answered either way.
    again = [*stranded, *overdue] if done.outage is None else stranded[:1]
    for one in sorted([*again, *unanswered], key=lambda one: (one.opened, one.number))[:MOST]:
        try:
            gh('workflow', 'run', INTAKE, '--repo', repo, '-f', f'issue={one.number}')
            done.sent.append(one.number)
        except Failed as exc:
            done.failed.append(f'#{one.number}: it could not be sent again: {exc}')
    return done


def clock() -> dt.datetime:
    """Now, in UTC. The tests replace this."""
    return dt.datetime.now(dt.timezone.utc)


def main() -> int:
    env = os.environ
    repo, owner = env.get('GITHUB_REPOSITORY', ''), env.get('GITHUB_REPOSITORY_OWNER', '')
    if not REPOSITORY.fullmatch(repo) or not route.LOGIN.fullmatch(owner):
        print('::error::GITHUB_REPOSITORY or GITHUB_REPOSITORY_OWNER is missing or malformed, so nothing was swept.')
        return 1
    run_url = f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{env.get('GITHUB_RUN_ID', '')}"
    try:
        routes = route.load()
        done = sweep(repo, owner, run_url, clock(), routes)
    except route.TableError as exc:
        print(f'::error file=intake/routes.json::{exc}')
        return 1
    except Failed as exc:
        print(f'::error::The open issues could not be read, so nothing was swept: {exc}')
        return 1
    if done.opened:
        print(f'Opened the outage notice, #{done.opened}.')
    for number in done.flagged:
        print(f"#{number}: overdue{', its player told' if number in done.told else ''}, and locked.")
    for number in done.sent:
        print(f'#{number}: sent through the intake again.')
    for said in done.failed:
        print(f'::warning::{said}')
    if not (done.opened or done.flagged or done.sent or done.failed):
        print('Nothing is waiting.' if done.outage is None else f'Nothing more to do while #{done.outage} is open.')
    return 1 if done.failed else 0


if __name__ == '__main__':
    sys.exit(main())
