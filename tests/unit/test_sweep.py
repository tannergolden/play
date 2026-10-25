#!/usr/bin/env python3
"""Tests for the sweep.

WHY THIS EXISTS. `sweep.py` acts on its own, once an hour, on issues that
players opened: it marks them, comments on them, locks them, opens the
outage notice and sends moves again. Every one of those has to happen to the
right issue, once, and never to the owner's own, an app's, or one already
answered, so each is pinned here against a stand-in for GitHub that records
every call.

Nothing here reaches GitHub. Run it from the root of the repository:

    PYTHONPATH=src/intake:src/replays python3 -m unittest discover -s tests/unit -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import unittest
from unittest import mock

import route
import sweep

REPO = 'tannergolden/play'
OWNER = 'tannergolden'
RUN = 'https://github.com/tannergolden/play/actions/runs/1'
NOW = dt.datetime(2026, 10, 17, 12, 0, tzinfo=dt.timezone.utc)


def stamp(minutes_ago: float) -> str:
    return (NOW - dt.timedelta(minutes=minutes_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')


def issue(number: int, *, title: str = 'chess: e2e4 · game 1 · move 1', login: str = 'octocat',
          kind: str = 'User', labels: tuple[str, ...] = ('move', 'game: chess'), opened: float = 30,
          touched: float | None = None, locked: bool = False, **extra: object) -> dict:
    return {
        'number': number, 'title': title, 'user': {'login': login, 'id': 583231, 'type': kind},
        'labels': [{'name': name} for name in labels], 'created_at': stamp(opened),
        'updated_at': stamp(opened if touched is None else touched), 'locked': locked, 'state': 'open', **extra,
    }


class GitHub:
    """A stand-in for `gh`: the open issues, the 🚀 and label events on each, and every call made, in order."""

    def __init__(self, issues: list[dict], *, rockets: tuple[int, ...] = (), overdue_before: tuple[int, ...] = (),
                 labels: tuple[str, ...] = (), fail: tuple[str, ...] = ()) -> None:
        self.issues, self.rockets, self.overdue_before = issues, set(rockets), set(overdue_before)
        self.labels, self.fail, self.calls, self.next = set(labels), fail, [], 100

    def __call__(self, *args: str) -> str:
        self.calls.append(args)
        said = ' '.join(args)
        if any(part in said for part in self.fail):
            raise sweep.Failed('HTTP 502: Bad Gateway')
        if args[0] == 'workflow':
            return ''
        path = args[1]
        method = args[args.index('--method') + 1] if '--method' in args else 'GET'
        fields = dict(args[at + 1].split('=', 1) for at, arg in enumerate(args) if arg == '-f')
        if method == 'GET' and path.startswith(f'repos/{REPO}/issues?'):
            return json.dumps([self.issues])
        if method == 'GET' and '/reactions' in path:
            number = int(path.split('/')[4])
            found = [{'content': 'rocket', 'user': {'login': sweep.SENDER}}] if number in self.rockets else []
            return json.dumps([[{'content': 'rocket', 'user': {'login': 'octocat'}}, *found]])
        if method == 'GET' and '/events' in path:
            number = int(path.split('/')[4])
            found = [{'event': 'labeled', 'label': {'name': 'overdue'}}] if number in self.overdue_before else []
            return json.dumps([[{'event': 'locked'}, *found]])
        if method == 'POST' and path == f'repos/{REPO}/labels':
            if fields['name'] in self.labels:
                raise sweep.Failed('HTTP 422: Validation Failed')
            self.labels.add(fields['name'])
            return '{}'
        if method == 'POST' and path == f'repos/{REPO}/issues':
            self.next += 1
            return json.dumps({'number': self.next})
        if method == 'PUT' and path.endswith('/lock'):
            return ''
        if method == 'POST':
            return '{}'
        raise AssertionError(f'an unexpected call: {args}')

    def made(self, what: str) -> list[tuple[str, ...]]:
        """The calls of one kind: `comment`, `label`, `lock`, `notice` or `again`."""
        def kind(args: tuple[str, ...]) -> str:
            if args[0] == 'workflow':
                return 'again'
            path = args[1]
            if path.endswith('/comments'):
                return 'comment'
            if path.endswith('/lock'):
                return 'lock'
            if path == f'repos/{REPO}/issues' and '--method' in args:
                return 'notice'
            if path.endswith('/labels') and path != f'repos/{REPO}/labels':
                return 'label'
            return 'other'
        return [args for args in self.calls if kind(args) == what]

    def sent_again(self) -> list[int]:
        return [int(args[-1].split('=')[1]) for args in self.made('again')]

    def numbers(self, what: str) -> list[int]:
        return [int(args[1].split('/')[4]) for args in self.made(what)]

    def field(self, args: tuple[str, ...], name: str) -> str:
        return dict(args[at + 1].split('=', 1) for at, arg in enumerate(args) if arg == '-f')[name]


class SweepTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.routes = route.load()

    def run_sweep(self, github: GitHub) -> sweep.Sweep:
        with mock.patch.object(sweep, 'gh', github):
            return sweep.sweep(REPO, OWNER, RUN, NOW, self.routes)


class OverdueTests(SweepTestCase):
    """A move sent on that has waited 15 minutes for its ruling."""

    def test_it_is_marked_its_player_told_and_the_owner_told_once(self) -> None:
        github = GitHub([issue(7)], rockets=(7,))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.told, done.opened, done.sent), ([7], [7], 101, []))
        notice, = github.made('notice')
        self.assertEqual(github.field(notice, 'title'), '🧯 The Arbiter is down')
        self.assertEqual(github.field(notice, 'labels[]'), 'arbiter-outage')
        self.assertIn(f'@{OWNER}, [this sweep]({RUN}) found #7 sent on', github.field(notice, 'body'))
        label, = github.made('label')
        self.assertEqual(github.field(label, 'labels[]'), 'overdue')
        comment, = github.made('comment')
        self.assertTrue(github.field(comment, 'body').startswith(
            "⏳ **Your move was sent on, but the Arbiter hasn't ruled on it yet.**\nIt's being looked into in"
            f' [#101](https://github.com/{REPO}/issues/101)'))
        self.assertEqual(github.numbers('lock'), [101, 7])
        self.assertIn('overdue', github.labels)

    def test_an_open_notice_is_linked_and_no_one_is_pinged_again(self) -> None:
        notice = issue(3, title=sweep.NOTICE, login='official-arbiter[bot]', kind='Bot', labels=('arbiter-outage',))
        github = GitHub([notice, issue(7)], rockets=(7,))
        done = self.run_sweep(github)
        self.assertEqual((done.outage, done.opened, done.flagged), (3, None, [7]))
        self.assertEqual(github.made('notice'), [])
        comment, = github.made('comment')
        self.assertIn(f'[#3](https://github.com/{REPO}/issues/3)', github.field(comment, 'body'))

    def test_a_move_already_answered_on_is_not_told_again(self) -> None:
        # Locked: the Arbiter's failure reply, or the intake's, already told its player.
        github = GitHub([issue(7, locked=True)], rockets=(7,))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.told), ([7], []))
        self.assertEqual(github.made('comment'), [])
        self.assertEqual(github.numbers('label'), [7])

    def test_a_move_overdue_before_is_told_once(self) -> None:
        github = GitHub([issue(7)], rockets=(7,), overdue_before=(7,))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.told), ([7], []))
        self.assertEqual(github.made('comment'), [])

    def test_a_move_still_in_flight_is_left_alone(self) -> None:
        github = GitHub([issue(7, opened=5), issue(8, opened=30, touched=5)], rockets=(7, 8))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.sent), ([], []))
        self.assertEqual([args for args in github.calls if args[1] != f'repos/{REPO}/issues?state=open&per_page=100'],
                         [])

    def test_a_rocket_from_anyone_else_is_not_the_intake_s(self) -> None:
        github = GitHub([issue(7)])  # only the player's own 🚀
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.sent), ([], [7]))


class SentAgainTests(SweepTestCase):
    """What goes through the intake again, and when."""

    def test_stranded_and_overdue_moves_go_again_once_the_outage_is_over(self) -> None:
        github = GitHub([issue(5, labels=('move', 'stranded'), locked=True, opened=300, touched=1),
                         issue(6, labels=('move', 'overdue'), locked=True, opened=200)])
        done = self.run_sweep(github)
        self.assertEqual(done.sent, [5, 6])
        self.assertEqual(github.sent_again(), [5, 6])
        self.assertEqual(github.made('again')[0], ('workflow', 'run', 'intake.yml', '--repo', REPO, '-f', 'issue=5'))
        self.assertEqual((github.made('comment'), github.made('label'), github.made('notice')), ([], [], []))

    def test_while_the_outage_lasts_only_the_oldest_stranded_move_goes(self) -> None:
        notice = issue(3, title=sweep.NOTICE, login='official-arbiter[bot]', kind='Bot', labels=('arbiter-outage',))
        github = GitHub([notice, issue(9, labels=('move', 'stranded'), opened=100),
                         issue(5, labels=('move', 'stranded'), opened=300),
                         issue(6, labels=('move', 'overdue'), opened=400)])
        done = self.run_sweep(github)
        self.assertEqual(done.sent, [5])

    def test_an_issue_never_answered_goes_again_whatever_the_outage(self) -> None:
        notice = issue(3, title=sweep.NOTICE, login='official-arbiter[bot]', kind='Bot', labels=('arbiter-outage',))
        github = GitHub([notice, issue(8, labels=('move',)), issue(9, title='hello there', labels=())])
        done = self.run_sweep(github)
        self.assertEqual(done.sent, [8, 9])
        self.assertEqual(done.flagged, [])

    def test_at_most_ten_go_in_one_sweep_oldest_first(self) -> None:
        github = GitHub([issue(number, labels=('move', 'stranded'), opened=1000 - number) for number in range(1, 15)])
        done = self.run_sweep(github)
        self.assertEqual(done.sent, list(range(1, 11)))

    def test_a_sweep_that_marks_a_move_holds_the_rest_for_the_notice_it_opened(self) -> None:
        github = GitHub([issue(7), issue(5, labels=('move', 'overdue'), opened=100),
                         issue(4, labels=('move', 'stranded'), opened=200)], rockets=(7,))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.opened, done.sent), ([7], 101, [4]))


class LeftAloneTests(SweepTestCase):
    """What a sweep never touches."""

    def test_nothing_waiting_does_nothing(self) -> None:
        github = GitHub([])
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.sent, done.opened, done.failed), ([], [], None, []))
        self.assertEqual(len(github.calls), 1)

    def test_apps_bots_pull_requests_notices_and_answered_issues(self) -> None:
        github = GitHub([
            issue(1, login='official-arbiter[bot]', kind='Bot', labels=('arbiter-logbook',)),
            issue(2, login='dependabot[bot]', kind='Bot', labels=()),
            issue(3, pull_request={'url': 'x'}),
            issue(4, labels=('move', 'played')),
            issue(5, labels=('move', 'turned away')),
            issue(6, labels=('invalid',)),
            issue(10, labels=('arbiter-outage',)),
        ], rockets=(4, 5))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.sent), ([], []))
        self.assertEqual(github.made('again'), [])

    def test_the_owner_s_own_issues_but_not_their_moves(self) -> None:
        github = GitHub([
            issue(1, login=OWNER, title='A note to myself', labels=()),
            issue(2, login='TannerGolden', title='Another note', labels=('documentation',)),
            issue(3, login=OWNER, labels=()),  # a move by its title alone
            issue(4, login=OWNER, title='odd', labels=('move',)),  # a move by its label
        ])
        done = self.run_sweep(github)
        self.assertEqual(done.sent, [3, 4])

    def test_issues_that_are_not_shaped_as_issues(self) -> None:
        broken = [None, 'x', {'number': 'one'}, issue(7, created_at='now'), {**issue(8), 'user': None}]
        github = GitHub(broken)
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.sent), ([], []))


class FailureTests(SweepTestCase):
    """A call that doesn't go through is said in the log, and the sweep goes on."""

    def test_a_failed_send_is_reported_and_the_rest_still_go(self) -> None:
        github = GitHub([issue(5, labels=('stranded',)), issue(6, labels=('stranded',), opened=20)],
                        fail=('issue=5',))
        done = self.run_sweep(github)
        self.assertEqual(done.sent, [6])
        self.assertEqual(done.failed, ['#5: it could not be sent again: HTTP 502: Bad Gateway'])

    def test_a_move_that_cannot_be_marked_is_reported(self) -> None:
        github = GitHub([issue(7)], rockets=(7,), fail=('/issues/7/labels',))
        done = self.run_sweep(github)
        self.assertEqual(done.flagged, [])
        self.assertEqual(done.failed, ['#7: it could not be marked overdue: HTTP 502: Bad Gateway'])

    def test_a_rocket_that_cannot_be_read_leaves_the_move_for_the_next_sweep(self) -> None:
        github = GitHub([issue(7)], fail=('/reactions',))
        done = self.run_sweep(github)
        self.assertEqual((done.flagged, done.sent), ([], []))
        self.assertEqual(done.failed, ["#7: its 🚀 could not be read: HTTP 502: Bad Gateway"])


class MainTests(unittest.TestCase):
    """The script as the workflow runs it."""

    def run_main(self, github: GitHub, **env: str) -> tuple[int, str]:
        environment = {'GITHUB_REPOSITORY': REPO, 'GITHUB_REPOSITORY_OWNER': OWNER,
                       'GITHUB_SERVER_URL': 'https://github.com', 'GITHUB_RUN_ID': '1', **env}
        printed = io.StringIO()
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(sweep, 'gh', github), \
                mock.patch.object(sweep, 'clock', return_value=NOW), contextlib.redirect_stdout(printed):
            code = sweep.main()
        return code, printed.getvalue()

    def test_a_sweep_says_what_it_did_and_never_a_title(self) -> None:
        github = GitHub([issue(7, title='::error::chess: e2e4 · game 1 · move 1'),
                         issue(5, labels=('stranded',), title='::set-output name=x::y')], rockets=(7,))
        code, printed = self.run_main(github)
        self.assertEqual(code, 0)
        self.assertNotIn('::error::', printed)
        self.assertNotIn('set-output', printed)
        self.assertIn('#7: overdue, its player told, and locked.', printed)
        self.assertIn('Opened the outage notice, #101.', printed)

    def test_nothing_to_do_is_said(self) -> None:
        code, printed = self.run_main(GitHub([]))
        self.assertEqual((code, printed), (0, 'Nothing is waiting.\n'))

    def test_a_failed_call_fails_the_run(self) -> None:
        code, printed = self.run_main(GitHub([issue(5, labels=('stranded',))], fail=('issue=5',)))
        self.assertEqual(code, 1)
        self.assertIn('::warning::#5: it could not be sent again: HTTP 502: Bad Gateway', printed)

    def test_open_issues_that_cannot_be_read_stop_the_sweep(self) -> None:
        code, printed = self.run_main(GitHub([], fail=('state=open',)))
        self.assertEqual(code, 1)
        self.assertIn('::error::The open issues could not be read, so nothing was swept: HTTP 502', printed)

    def test_a_malformed_repository_stops_the_sweep(self) -> None:
        for env in ({'GITHUB_REPOSITORY': ''}, {'GITHUB_REPOSITORY_OWNER': 'a b'}):
            with self.subTest(env=env):
                github = GitHub([])
                code, printed = self.run_main(github, **env)
                self.assertEqual(code, 1)
                self.assertIn('::error::', printed)
                self.assertEqual(github.calls, [])


class GhTests(unittest.TestCase):
    """The one function that runs `gh`."""

    def test_its_last_line_of_complaint_is_what_is_said(self) -> None:
        import subprocess
        with mock.patch.object(sweep.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 1, '', 'gh: Not Found\ngh: Not Found (HTTP 404)\n')
            with self.assertRaisesRegex(sweep.Failed, r'^gh: Not Found \(HTTP 404\)$'):
                sweep.gh('api', 'x')
            run.side_effect = subprocess.TimeoutExpired('gh', 60)
            with self.assertRaisesRegex(sweep.Failed, 'TimeoutExpired'):
                sweep.gh('api', 'x')

    def test_every_page_is_read(self) -> None:
        with mock.patch.object(sweep, 'gh', return_value='[[{"a": 1}], [{"a": 2}]]') as gh:
            self.assertEqual(sweep.api('repos/x/issues', paginate=True), [{'a': 1}, {'a': 2}])
        self.assertEqual(gh.call_args.args, ('api', 'repos/x/issues', '--paginate', '--slurp'))


if __name__ == '__main__':
    unittest.main()
