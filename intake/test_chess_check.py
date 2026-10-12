#!/usr/bin/env python3
"""Tests for the chess pre-check.

WHY THIS EXISTS. `chess_check.py` answers a move here, before its game runs,
only when the game could do nothing but turn it away. If it ever refused a
move the game would have played, a player would lose their move, so the
moves it sends on are pinned as carefully as the ones it refuses: a state
that is behind the game, a state that couldn't be read, and the owner, who
is never limited.

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
import tempfile
import unittest
from unittest import mock

import chess_check

OWNER, OWNER_ID = 'tannergolden', '24684994'
OCTOCAT, HUBOT = '583231', '480938'
BOARD = '[the board](https://github.com/tannergolden)'
# Game 3, two moves in: the owner's 1. e4, then @octocat's 1... e5.
STATE = {'game': 3, 'started': '2026-10-11T16:00:00Z', 'moves': [
    {'uci': 'e2e4', 'san': 'e4', 'player': OWNER, 'player_id': int(OWNER_ID), 'issue': 40, 'arbiter': False},
    {'uci': 'e7e5', 'san': 'e5', 'player': 'octocat', 'player_id': int(OCTOCAT), 'issue': 41, 'arbiter': False},
]}


def move(uci: str, game: int, number: int, player_id: str) -> dict:
    return {'uci': uci, 'game': str(game), 'move_number': str(number), 'issue': '50', 'player': 'someone',
            'player_id': player_id}


def verdict(request: dict, state: dict | None = STATE, recent: int | None = 1, known: bool = True) -> str:
    return chess_check.verdict(request, state, recent, OWNER, OWNER_ID, known)


class SentOn(unittest.TestCase):
    def test_the_move_on_the_board_from_the_side_to_move_goes_on(self) -> None:
        self.assertEqual(verdict(move('g1f3', 3, 3, OWNER_ID)), '')
        self.assertEqual(verdict(move('e2e4', 1, 1, OWNER_ID), state=None), '', 'the first move of the first game')

    def test_a_move_that_looks_ahead_of_the_board_is_the_game_s_to_judge(self) -> None:
        # The state read here can be behind the game, never ahead: a move past it may be the one on the board now.
        self.assertEqual(verdict(move('g8f6', 3, 4, HUBOT)), '')
        self.assertEqual(verdict(move('e2e4', 4, 1, OWNER_ID)), '')

    def test_a_state_that_couldn_t_be_read_refuses_only_the_wrong_side(self) -> None:
        self.assertEqual(verdict(move('d7d5', 3, 2, HUBOT), state=None, known=False), '')
        self.assertIn("It's GitHub's turn as Black", verdict(move('d7d5', 3, 2, OWNER_ID), state=None, known=False))

    def test_the_owner_is_never_limited(self) -> None:
        self.assertEqual(verdict(move('g1f3', 3, 3, OWNER_ID), recent=500), '')


class TurnedAway(unittest.TestCase):
    def test_a_game_that_is_over(self) -> None:
        self.assertEqual(verdict(move('e2e4', 2, 9, OWNER_ID)),
                         f"⌛ **Game 2 is over**, so `e2e4` wasn't played.\nGame 3 is under way on {BOARD}: pick a move"
                         ' there.\n')

    def test_a_move_already_played_names_who_got_there_first(self) -> None:
        self.assertEqual(verdict(move('d7d5', 3, 2, HUBOT)),
                         "⌛ **Too late: move 2 is already on the board**, so `d7d5` wasn't played.\n1... e5 got there"
                         ' first, played by [@octocat](https://github.com/octocat). Pick a move from'
                         f' {BOARD} as it stands now.\n')
        self.assertIn('played by you.', verdict(move('d7d6', 3, 2, OCTOCAT)))
        arbiter = {**STATE, 'moves': [STATE['moves'][0], {**STATE['moves'][1], 'arbiter': True, 'player': None,
                                                          'player_id': None, 'issue': None}]}
        self.assertIn('played by the Arbiter.', verdict(move('d7d6', 3, 2, OCTOCAT), state=arbiter))

    def test_the_wrong_side(self) -> None:
        self.assertEqual(verdict(move('d2d4', 3, 3, HUBOT)),
                         "⏳ **It's [@tannergolden](https://github.com/tannergolden)'s turn as White**, so `d2d4`"
                         f" wasn't played.\nGitHub plays Black: once White moves, pick Black's reply on {BOARD}.\n")
        self.assertEqual(verdict(move('g8f6', 3, 4, OWNER_ID)),
                         "⏳ **It's GitHub's turn as Black**, so `g8f6` wasn't played.\nBlack's moves are for everyone"
                         ' but you. Your turn comes next.\n')

    def test_more_than_an_hour_s_share(self) -> None:
        self.assertEqual(verdict(move('g8f6', 3, 4, HUBOT), recent=chess_check.LIMIT), '')
        said = verdict(move('g8f6', 3, 4, HUBOT), recent=chess_check.LIMIT + 1)
        self.assertTrue(said.startswith(f"🐢 **Slow down**: you've opened {chess_check.LIMIT + 1} issues here"), said)
        self.assertNotIn(f'@{OWNER}', said.replace(f'[@{OWNER}]', ''), 'a refusal pings nobody')


class MainTests(unittest.TestCase):
    def run_check(self, request: dict, state=STATE, recent: str | None = '1') -> tuple[str, str | None]:
        with tempfile.TemporaryDirectory() as temp:
            folder = pathlib.Path(temp)
            (folder / 'dispatch.json').write_text(json.dumps({'ref': 'Development', 'inputs': request}),
                                                  encoding='utf-8')
            if state != 'unread':
                (folder / 'game.json').write_text(json.dumps(state), encoding='utf-8')
            if recent is not None:
                (folder / 'recent').write_text(recent, encoding='utf-8')
            env = {'RUNNER_TEMP': temp, 'GITHUB_OUTPUT': str(folder / 'output'),
                   'GITHUB_REPOSITORY_OWNER': OWNER, 'OWNER_ID': OWNER_ID}
            with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(chess_check.main(), 0)
            reply = folder / 'reply.md'
            return ((folder / 'output').read_text(encoding='utf-8'),
                    reply.read_text(encoding='utf-8') if reply.exists() else None)

    def test_a_move_for_the_game_is_sent_on_and_nothing_written(self) -> None:
        self.assertEqual(self.run_check(move('g1f3', 3, 3, OWNER_ID)), ('verdict=dispatch\n', None))

    def test_a_refusal_writes_its_reply(self) -> None:
        output, reply = self.run_check(move('d7d5', 3, 2, HUBOT))
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith('⌛ **Too late: move 2 is already on the board**'))

    def test_no_game_yet_and_an_unread_state_are_told_apart(self) -> None:
        self.assertEqual(self.run_check(move('e2e4', 1, 1, OWNER_ID), state=None)[0], 'verdict=dispatch\n')
        self.assertEqual(self.run_check(move('e2e4', 2, 1, OWNER_ID), state='unread')[0], 'verdict=dispatch\n')

    def test_a_count_that_isn_t_a_number_limits_nobody(self) -> None:
        for recent in ('', 'lots', '٣٣', None):
            with self.subTest(recent=recent):
                self.assertEqual(self.run_check(move('g8f6', 3, 4, HUBOT), recent=recent)[0], 'verdict=dispatch\n')


if __name__ == '__main__':
    unittest.main()
