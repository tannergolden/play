#!/usr/bin/env python3
"""Tests for the pre-check of all four games.

WHY THIS EXISTS. `check.py` answers a move here, before its game runs, only
when the game could do nothing but turn it away. If it ever refused a move
the game would have played, a player would lose their move, so the moves it
sends on are pinned as carefully as the ones it refuses: a state that is
behind the game, a state that couldn't be read, a game whose opener it can't
know yet, and the owner, who is never limited. Every refusal is held to the
game's own words, word for word, in every game, and both ways round in the
two games the Arbiter opens for a side drawn at random.

Nothing here reads or writes outside a throwaway folder. Run it from the root
of the repository:

    python3 -m unittest discover -s intake -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

import check
import route

OWNER, OWNER_ID = 'tannergolden', '24684994'
OCTOCAT, HUBOT = '583231', '480938'
BOARD = '[the board](https://github.com/tannergolden)'
TANNER = '[@tannergolden](https://github.com/tannergolden)'
NOW = dt.datetime(2026, 10, 12, 18, 0, tzinfo=dt.timezone.utc)


def by(player: str | None, player_id: str | None, issue: int | None = None) -> dict:
    """Who played a move on record: a player, or the Arbiter when there is none."""
    if player is None:
        return {'player': None, 'player_id': None, 'issue': None, 'arbiter': True}
    return {'player': player, 'player_id': int(player_id), 'issue': issue, 'arbiter': False}


ARBITER = by(None, None)
TANNER_MOVED = by(OWNER, OWNER_ID, 40)
OCTOCAT_MOVED = by('octocat', OCTOCAT, 41)

# Game 3 of chess, two moves in: the owner's 1. e4, then @octocat's 1... e5.
CHESS = {'game': 3, 'started': '2026-10-11T16:00:00Z', 'moves': [
    {'uci': 'e2e4', 'san': 'e4', **TANNER_MOVED},
    {'uci': 'e7e5', 'san': 'e5', **OCTOCAT_MOVED},
]}
# Game 6 of checkers, three moves in. GitHub opens every game as Black, here with @octocat's 1. 11-15; then come the
# owner's 1... 22-18 as White, and @octocat's 2. 15x22.
CHECKERS = {'game': 6, 'started': '2026-10-10T16:00:00Z', 'moves': [
    {'move': '11-15', 'shown': '11-15', **OCTOCAT_MOVED},
    {'move': '22-18', 'shown': '22-18', **TANNER_MOVED},
    {'move': '15x22', 'shown': '15x22', **OCTOCAT_MOVED},
]}
# Game 9 of Tic-Tac-Toe, where the owner always plays X and GitHub O. The Arbiter opened it for the house, so X moved
# first, with the Arbiter's 1. Xb2; then came @octocat's 1... Oa1.
TICTACTOE = {'game': 9, 'started': '2026-10-12T16:00:00Z', 'opens': 'house', 'moves': [
    {'move': 'b2', 'shown': 'Xb2', **ARBITER},
    {'move': 'a1', 'shown': 'Oa1', **OCTOCAT_MOVED},
]}
# The same game the other way round: the Arbiter opened it for GitHub, so O moved first, with the Arbiter's 1. Ob2;
# then came the owner's 1... Xa1.
TICTACTOE_GITHUB = {**TICTACTOE, 'opens': 'github', 'moves': [
    {'move': 'b2', 'shown': 'Ob2', **ARBITER},
    {'move': 'a1', 'shown': 'Xa1', **TANNER_MOVED},
]}
# Game 4 of Connect Four, where the owner always drops the White discs and GitHub the Black. The Arbiter opened it for
# the house, so White moved first, with the Arbiter's 1. ⚪4; then came @octocat's 1... ⚫4, and the owner's 2. ⚪3.
CONNECTFOUR = {'game': 4, 'started': '2026-10-09T16:00:00Z', 'opens': 'house', 'moves': [
    {'move': '4', 'shown': '⚪4', **ARBITER},
    {'move': '4', 'shown': '⚫4', **OCTOCAT_MOVED},
    {'move': '3', 'shown': '⚪3', **TANNER_MOVED},
]}
# The same game the other way round: the Arbiter opened it for GitHub, so Black moved first, with the Arbiter's
# 1. ⚫4; then came the owner's 1... ⚪4, and @octocat's 2. ⚫3.
CONNECTFOUR_GITHUB = {**CONNECTFOUR, 'opens': 'github', 'moves': [
    {'move': '4', 'shown': '⚫4', **ARBITER},
    {'move': '4', 'shown': '⚪4', **TANNER_MOVED},
    {'move': '3', 'shown': '⚫3', **OCTOCAT_MOVED},
]}
STATES = {'tictactoe': TICTACTOE, 'connectfour': CONNECTFOUR, 'checkers': CHECKERS, 'chess': CHESS}
CODES = {'tictactoe': 'c3', 'connectfour': '5', 'checkers': '25x18', 'chess': 'g1f3'}


def move(key: str, code: str, game: int, number: int, player_id: str) -> dict:
    """A move as the router sends it on: its game's own input for the move, then the game, the move and the player."""
    return {check.GAMES[key].code: code, 'game': str(game), 'move_number': str(number), 'issue': '50',
            'player': 'someone', 'player_id': player_id}


def verdict(key: str, request: dict, state: object = 'theirs', recent: int | None = 1, known: bool = True,
            now: dt.datetime = NOW) -> str:
    state = STATES[key] if state == 'theirs' else state
    return check.verdict(key, request, state, recent, OWNER, OWNER_ID, known, now)


def waiting(number: int, started: str, **extra: object) -> dict:
    """The next game while the last one's winning board is on show: no moves, and a start still to come."""
    return {'game': number, 'started': started, 'moves': [], **extra}


class SentOn(unittest.TestCase):
    def test_the_side_to_move_on_the_board_goes_on(self) -> None:
        self.assertEqual(verdict('chess', move('chess', 'g1f3', 3, 3, OWNER_ID)), '')
        self.assertEqual(verdict('checkers', move('checkers', '25x18', 6, 4, OWNER_ID)), '')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 9, 3, OWNER_ID)), '')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 9, 3, HUBOT), TICTACTOE_GITHUB), '')
        self.assertEqual(verdict('connectfour', move('connectfour', '5', 4, 4, HUBOT)), '')
        self.assertEqual(verdict('connectfour', move('connectfour', '5', 4, 4, OWNER_ID), CONNECTFOUR_GITHUB), '')

    def test_the_first_move_of_the_first_game(self) -> None:
        # The house opens Chess, as White, and GitHub opens Checkers, as Black.
        self.assertEqual(verdict('chess', move('chess', 'e2e4', 1, 1, OWNER_ID), state=None), '')
        self.assertEqual(verdict('checkers', move('checkers', '11-15', 1, 1, HUBOT), state=None), '')

    def test_a_move_that_looks_ahead_of_the_board_is_the_game_s_to_judge(self) -> None:
        # The state read here can be behind the game, never ahead: a move past it may be the one on the board now.
        self.assertEqual(verdict('chess', move('chess', 'g8f6', 3, 4, HUBOT)), '')
        self.assertEqual(verdict('chess', move('chess', 'e2e4', 4, 1, OWNER_ID)), '')
        self.assertEqual(verdict('checkers', move('checkers', '24-19', 6, 6, OWNER_ID)), '')
        self.assertEqual(verdict('checkers', move('checkers', '11-15', 7, 1, HUBOT)), '')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 9, 5, OWNER_ID)), '')

    def test_a_state_that_couldn_t_be_read_refuses_only_the_wrong_side_where_the_opener_never_changes(self) -> None:
        # The house opens every game of Chess and GitHub every game of Checkers, so move 2 is GitHub's in Chess and
        # the owner's in Checkers, whatever the state would have said.
        for key, code, right, wrong, said in (
            ('chess', 'd7d5', HUBOT, OWNER_ID, "It's GitHub's turn as Black"),
            ('checkers', '22-18', OWNER_ID, HUBOT, f"It's {TANNER}'s turn as White"),
        ):
            with self.subTest(key=key):
                self.assertEqual(verdict(key, move(key, code, 3, 2, right), state=None, known=False), '')
                self.assertIn(said, verdict(key, move(key, code, 3, 2, wrong), state=None, known=False))

    def test_in_the_arbiter_s_games_a_side_it_can_t_know_is_left_to_the_game(self) -> None:
        # Whose turn it is there depends on the side the Arbiter opened the game for, which only the state shows.
        unopened = waiting(9, '2026-10-12T16:00:00Z', opens='house')
        for key in ('tictactoe', 'connectfour'):
            state = STATES[key]
            for player_id in (OWNER_ID, HUBOT):
                for number in (len(state['moves']) + 1, len(state['moves']) + 2):
                    request = move(key, CODES[key], state['game'], number, player_id)
                    with self.subTest(key=key, player_id=player_id, number=number):
                        self.assertEqual(verdict(key, request, state=None, known=False), '', 'an unread state')
                        unsaid = {name: value for name, value in state.items() if name != 'opens'}
                        self.assertEqual(verdict(key, request, state=unsaid), '', 'no opener')
                        for opens in (None, 'nobody', 'House', 1):
                            self.assertEqual(verdict(key, request, state={**state, 'opens': opens}), '', opens)
                        self.assertEqual(verdict(key, move(key, CODES[key], 9, number, player_id), unopened), '',
                                         'a game not yet opened')
                        later = move(key, CODES[key], state['game'] + 1, number, player_id)
                        self.assertEqual(verdict(key, later), '', 'a game after the one on the board')
            self.assertEqual(verdict(key, move(key, CODES[key], 1, 1, HUBOT), state=None), '', 'no game yet')

    def test_the_owner_is_never_limited(self) -> None:
        self.assertEqual(verdict('chess', move('chess', 'g1f3', 3, 3, OWNER_ID), recent=500), '')
        self.assertEqual(verdict('checkers', move('checkers', '25x18', 6, 4, OWNER_ID), recent=500), '')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 9, 3, OWNER_ID), recent=500), '')
        self.assertEqual(verdict('connectfour', move('connectfour', '5', 4, 4, OWNER_ID), CONNECTFOUR_GITHUB,
                                 recent=500), '')

    def test_a_move_on_record_that_can_t_be_named_is_left_to_the_game(self) -> None:
        nameless = {**CHECKERS, 'moves': [{**CHECKERS['moves'][0], 'shown': None}, CHECKERS['moves'][1]]}
        self.assertEqual(verdict('checkers', move('checkers', '9-14', 6, 1, HUBOT), nameless), '')
        unsigned = {**CHECKERS, 'moves': [{**CHECKERS['moves'][0], 'player': 'a b'}, CHECKERS['moves'][1]]}
        self.assertEqual(verdict('checkers', move('checkers', '9-14', 6, 1, HUBOT), unsigned), '')


class TurnedAway(unittest.TestCase):
    def test_more_than_an_hour_s_share_across_all_four_games(self) -> None:
        self.assertEqual(check.LIMIT, 30)
        for key, state in STATES.items():
            # GitHub's turn in each game here: move 4, or move 5 in Checkers, which GitHub opens.
            request = move(key, CODES[key], state['game'], 5 if key == 'checkers' else 4, HUBOT)
            with self.subTest(key=key):
                self.assertEqual(verdict(key, request, recent=30), '', 'the thirtieth issue of the hour')
                said = verdict(key, request, recent=31)
                self.assertEqual(said, "🐢 **Slow down**: you've opened 31 issues here in the last hour, more than the"
                                       f" 30 the games take from one player, so `{CODES[key]}` wasn't played.\n"
                                       f'Pick your next move from {BOARD} in a little while.\n')
                self.assertNotIn(f'@{OWNER}', said, 'a refusal pings nobody')

    def test_a_game_that_is_over(self) -> None:
        for key, state in STATES.items():
            with self.subTest(key=key):
                number = state['game']
                self.assertEqual(verdict(key, move(key, CODES[key], number - 1, 9, OWNER_ID)),
                                 f"⌛ **Game {number - 1} is over**, so `{CODES[key]}` wasn't played.\nGame {number}"
                                 f' is under way on {BOARD}: pick a move there.\n')

    def test_a_move_already_played_names_who_got_there_first(self) -> None:
        def late(number: int, code: str, sheet: str, who: str) -> str:
            return (f"⌛ **Too late: move {number} is already on the board**, so `{code}` wasn't played.\n{sheet} got"
                    f' there first, played by {who}. Pick a move from {BOARD} as it stands now.\n')

        octocat = '[@octocat](https://github.com/octocat)'
        for key, request, state, said in (
            ('chess', move('chess', 'd7d5', 3, 2, HUBOT), CHESS, late(2, 'd7d5', '1... e5', octocat)),
            ('chess', move('chess', 'd7d6', 3, 2, OCTOCAT), CHESS, late(2, 'd7d6', '1... e5', 'you')),
            ('checkers', move('checkers', '15x22', 6, 3, HUBOT), CHECKERS, late(3, '15x22', '2. 15x22', octocat)),
            ('checkers', move('checkers', '24-20', 6, 2, OWNER_ID), CHECKERS, late(2, '24-20', '1... 22-18', 'you')),
            ('tictactoe', move('tictactoe', 'a3', 9, 1, HUBOT), TICTACTOE, late(1, 'a3', '1. Xb2', 'the Arbiter')),
            ('tictactoe', move('tictactoe', 'c1', 9, 2, HUBOT), TICTACTOE, late(2, 'c1', '1... Oa1', octocat)),
            ('tictactoe', move('tictactoe', 'a3', 9, 1, HUBOT), TICTACTOE_GITHUB, late(1, 'a3', '1. Ob2',
                                                                                       'the Arbiter')),
            ('tictactoe', move('tictactoe', 'c1', 9, 2, OWNER_ID), TICTACTOE_GITHUB, late(2, 'c1', '1... Xa1', 'you')),
            ('connectfour', move('connectfour', '1', 4, 1, OWNER_ID), CONNECTFOUR, late(1, '1', '1. ⚪4',
                                                                                        'the Arbiter')),
            ('connectfour', move('connectfour', '7', 4, 2, HUBOT), CONNECTFOUR, late(2, '7', '1... ⚫4', octocat)),
            ('connectfour', move('connectfour', '1', 4, 1, HUBOT), CONNECTFOUR_GITHUB, late(1, '1', '1. ⚫4',
                                                                                            'the Arbiter')),
            ('connectfour', move('connectfour', '2', 4, 3, HUBOT), CONNECTFOUR_GITHUB, late(3, '2', '2. ⚫3',
                                                                                            octocat)),
        ):
            with self.subTest(key=key, request=request):
                self.assertEqual(verdict(key, request, state), said)
        arbiter = {**CHESS, 'moves': [CHESS['moves'][0], {**CHESS['moves'][1], **ARBITER}]}
        self.assertIn('played by the Arbiter.', verdict('chess', move('chess', 'd7d6', 3, 2, OCTOCAT), arbiter))

    def test_the_wrong_side_in_chess(self) -> None:
        self.assertEqual(verdict('chess', move('chess', 'd2d4', 3, 3, HUBOT)),
                         f"⏳ **It's {TANNER}'s turn as White**, so `d2d4` wasn't played.\nGitHub plays Black: once"
                         f" White moves, pick Black's reply on {BOARD}.\n")
        self.assertEqual(verdict('chess', move('chess', 'g8f6', 3, 4, OWNER_ID)),
                         "⏳ **It's GitHub's turn as Black**, so `g8f6` wasn't played.\nBlack's moves are for everyone"
                         ' but you. Your turn comes next.\n')

    def test_the_wrong_side_in_checkers(self) -> None:
        # GitHub opens as Black, so Black has the odd moves and the owner, as White, the even ones.
        self.assertEqual(verdict('checkers', move('checkers', '25x18', 6, 4, HUBOT)),
                         f"⏳ **It's {TANNER}'s turn as White**, so `25x18` wasn't played.\nGitHub plays Black: once"
                         f" White moves, pick Black's reply on {BOARD}.\n")
        self.assertEqual(verdict('checkers', move('checkers', '9-13', 6, 5, OWNER_ID)),
                         "⏳ **It's GitHub's turn as Black**, so `9-13` wasn't played.\nBlack's moves are for"
                         ' everyone but you. Your turn comes next.\n')

    def test_checkers_opens_with_github_as_black(self) -> None:
        # Black moves first in American checkers, and GitHub plays Black, so every fresh board is GitHub's to open:
        # game 1's, before its state is first written and once it is, and a later game's once its start has passed.
        said = ("⏳ **It's GitHub's turn as Black**, so `11-15` wasn't played.\nBlack's moves are for everyone but"
                ' you. Your turn comes next.\n')
        fresh = {'game': 1, 'started': '2026-10-12T16:00:00Z', 'moves': []}
        for state, known in ((None, True), (None, False), (fresh, True), ({**fresh, 'game': 7}, True)):
            number = state['game'] if state else 1
            with self.subTest(state=state, known=known):
                self.assertEqual(verdict('checkers', move('checkers', '11-15', number, 1, OWNER_ID), state,
                                         known=known), said)
                self.assertEqual(verdict('checkers', move('checkers', '11-15', number, 1, HUBOT), state,
                                         known=known), '')
        # Once GitHub has opened, the owner replies as White.
        opened = {**fresh, 'moves': CHECKERS['moves'][:1]}
        self.assertEqual(verdict('checkers', move('checkers', '22-18', 1, 2, OWNER_ID), opened), '')
        self.assertEqual(verdict('checkers', move('checkers', '22-18', 1, 2, HUBOT), opened),
                         f"⏳ **It's {TANNER}'s turn as White**, so `22-18` wasn't played.\nGitHub plays Black: once"
                         f" White moves, pick Black's reply on {BOARD}.\n")

    def test_the_wrong_side_in_tic_tac_toe_both_ways_round(self) -> None:
        # The owner always plays X and GitHub O. Opened for the house, X moves first, so the owner has the odd moves.
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 9, 3, HUBOT)),
                         f"⏳ **It's {TANNER}'s turn as X**, so `c3` wasn't played.\nGitHub plays O: once X moves,"
                         f" pick O's reply on {BOARD}.\n")
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c1', 9, 4, OWNER_ID)),
                         "⏳ **It's GitHub's turn as O**, so `c1` wasn't played.\nO's moves are for everyone but you."
                         ' Your turn comes next.\n')
        # Opened for GitHub, O moves first, so GitHub has the odd moves and the owner, still X, the even ones.
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 9, 3, OWNER_ID), TICTACTOE_GITHUB),
                         "⏳ **It's GitHub's turn as O**, so `c3` wasn't played.\nO's moves are for everyone but you."
                         ' Your turn comes next.\n')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c1', 9, 4, HUBOT), TICTACTOE_GITHUB),
                         f"⏳ **It's {TANNER}'s turn as X**, so `c1` wasn't played.\nGitHub plays O: once X moves,"
                         f" pick O's reply on {BOARD}.\n")

    def test_tic_tac_toe_opened_for_github_moves_o_first(self) -> None:
        # Game 1 as the profile has it: the Arbiter opened it for GitHub with O's 1. Oa1, so the owner replies as X.
        opened = {'game': 1, 'started': '2026-10-12T06:15:46Z', 'opens': 'github', 'moves': [
            {'move': 'a1', 'shown': 'Oa1', **ARBITER},
        ]}
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'b2', 1, 2, OWNER_ID), opened), '')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'b2', 1, 2, HUBOT), opened),
                         f"⏳ **It's {TANNER}'s turn as X**, so `b2` wasn't played.\nGitHub plays O: once X moves,"
                         f" pick O's reply on {BOARD}.\n")
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 1, 3, HUBOT), opened), '')
        self.assertEqual(verdict('tictactoe', move('tictactoe', 'c3', 1, 3, OWNER_ID), opened),
                         "⏳ **It's GitHub's turn as O**, so `c3` wasn't played.\nO's moves are for everyone but you."
                         ' Your turn comes next.\n')
        self.assertIn('1. Oa1 got there first, played by the Arbiter.',
                      verdict('tictactoe', move('tictactoe', 'b2', 1, 1, OWNER_ID), opened))

    def test_the_wrong_side_in_connect_four_both_ways_round(self) -> None:
        # The owner always drops the White discs and GitHub the Black. Opened for the house, White moves first, so
        # GitHub has the even moves.
        self.assertEqual(verdict('connectfour', move('connectfour', '5', 4, 4, OWNER_ID)),
                         "⏳ **It's GitHub's turn as Black**, so `5` wasn't played.\nBlack's moves are for everyone"
                         ' but you. Your turn comes next.\n')
        self.assertEqual(verdict('connectfour', move('connectfour', '6', 4, 5, HUBOT)),
                         f"⏳ **It's {TANNER}'s turn as White**, so `6` wasn't played.\nGitHub plays Black: once White"
                         f" moves, pick Black's reply on {BOARD}.\n")
        # Opened for GitHub, Black moves first, so the owner, still White, has the even moves.
        self.assertEqual(verdict('connectfour', move('connectfour', '5', 4, 4, HUBOT), CONNECTFOUR_GITHUB),
                         f"⏳ **It's {TANNER}'s turn as White**, so `5` wasn't played.\nGitHub plays Black: once White"
                         f" moves, pick Black's reply on {BOARD}.\n")
        self.assertEqual(verdict('connectfour', move('connectfour', '6', 4, 5, OWNER_ID), CONNECTFOUR_GITHUB),
                         "⏳ **It's GitHub's turn as Black**, so `6` wasn't played.\nBlack's moves are for everyone but"
                         ' you. Your turn comes next.\n')

    def test_connect_four_opened_for_the_house_moves_white_first(self) -> None:
        # Game 1 as the profile has it: the Arbiter opened it for the house with White's 1. ⚪6, so GitHub replies as
        # Black.
        opened = {'game': 1, 'started': '2026-10-12T06:15:46Z', 'opens': 'house', 'moves': [
            {'move': '6', 'shown': '⚪6', **ARBITER},
        ]}
        self.assertEqual(verdict('connectfour', move('connectfour', '4', 1, 2, HUBOT), opened), '')
        self.assertEqual(verdict('connectfour', move('connectfour', '4', 1, 2, OWNER_ID), opened),
                         "⏳ **It's GitHub's turn as Black**, so `4` wasn't played.\nBlack's moves are for everyone"
                         ' but you. Your turn comes next.\n')
        self.assertEqual(verdict('connectfour', move('connectfour', '3', 1, 3, OWNER_ID), opened), '')
        self.assertEqual(verdict('connectfour', move('connectfour', '3', 1, 3, HUBOT), opened),
                         f"⏳ **It's {TANNER}'s turn as White**, so `3` wasn't played.\nGitHub plays Black: once White"
                         f" moves, pick Black's reply on {BOARD}.\n")
        self.assertIn('1. ⚪6 got there first, played by the Arbiter.',
                      verdict('connectfour', move('connectfour', '4', 1, 1, HUBOT), opened))

    def test_a_move_while_the_winning_board_is_up(self) -> None:
        # Game 6 ended at 16:00 UTC on 12 Oct, so game 7 opens two days later: 11:00 EST on 14 Oct.
        for key in check.GAMES:
            state = waiting(7, '2026-10-14T16:00:00Z', **({} if check.GAMES[key].opens else {'opens': 'house'}))
            for number, player_id in ((7, HUBOT), (7, OWNER_ID), (6, HUBOT), (2, OWNER_ID)):
                with self.subTest(key=key, number=number, player_id=player_id):
                    self.assertEqual(verdict(key, move(key, CODES[key], number, 1, player_id), state),
                                     f"⏳ **Game 7 opens 14 Oct**, so `{CODES[key]}` wasn't played.\nGame 6's final"
                                     f' board stays up until then: pick a move from {BOARD} once game 7 is on it.\n')

    def test_the_next_game_opens_the_moment_its_start_passes(self) -> None:
        state = waiting(7, '2026-10-14T16:00:00Z')
        started = dt.datetime(2026, 10, 14, 16, 0, tzinfo=dt.timezone.utc)
        before = started - dt.timedelta(seconds=1)
        for key in check.GAMES:
            with self.subTest(key=key):
                # The game's first move, sent from the side that may open it: GitHub opens Checkers.
                request = move(key, CODES[key], 7, 1, HUBOT if key == 'checkers' else OWNER_ID)
                self.assertTrue(verdict(key, request, state, now=before).startswith('⏳ **Game 7 opens 14 Oct**'))
                self.assertEqual(verdict(key, request, state, now=started), '')
                self.assertEqual(verdict(key, request, state, now=started + dt.timedelta(hours=1)), '')
        # Once it has opened, Chess is the house's to open and Checkers GitHub's, and a move for the old game is over.
        self.assertIn("It's [@tannergolden](https://github.com/tannergolden)'s turn as White",
                      verdict('chess', move('chess', 'e2e4', 7, 1, HUBOT), state, now=started))
        self.assertIn("It's GitHub's turn as Black",
                      verdict('checkers', move('checkers', '11-15', 7, 1, OWNER_ID), state, now=started))
        self.assertTrue(verdict('checkers', move('checkers', '11-15', 6, 9, HUBOT), state, now=started).startswith(
            '⌛ **Game 6 is over**'))

    def test_a_start_still_to_come_holds_back_only_a_game_with_nothing_on_its_board(self) -> None:
        # A game already under way, or the very first game, is never held back by its start.
        early = {**CHESS, 'started': '2026-10-20T16:00:00Z'}
        self.assertEqual(verdict('chess', move('chess', 'g1f3', 3, 3, OWNER_ID), early), '')
        first = waiting(1, '2026-10-20T16:00:00Z')
        self.assertEqual(verdict('chess', move('chess', 'e2e4', 1, 1, OWNER_ID), first), '')
        for started in (None, 'soon', 20261014, ''):
            with self.subTest(started=started):
                self.assertEqual(verdict('chess', move('chess', 'e2e4', 7, 1, OWNER_ID), waiting(7, started)), '',
                                 'a start that is not a moment holds nothing back')
        for started in ('2026-10-14T16:00:00Z', '2026-10-14T16:00:00+00:00', '2026-10-14T11:00:00-05:00',
                        '2026-10-14T16:00:00'):
            with self.subTest(started=started):
                said = verdict('chess', move('chess', 'e2e4', 7, 1, OWNER_ID), waiting(7, started))
                self.assertTrue(said.startswith('⏳ **Game 7 opens 14 Oct**'), 'a stamp without a zone is in UTC')

    def test_the_day_a_game_opens_is_written_as_the_page_writes_days(self) -> None:
        # The page tells time in EST, five hours behind UTC all year, and writes a day without a leading zero.
        for started, day in (
            ('2026-10-14T16:00:00Z', '14 Oct'),
            ('2026-10-15T03:00:00Z', '14 Oct'),
            ('2026-11-02T05:00:00Z', '2 Nov'),
            ('2027-07-04T04:30:00Z', '3 Jul'),
            ('2027-01-01T04:59:59Z', '31 Dec'),
        ):
            with self.subTest(started=started):
                said = verdict('tictactoe', move('tictactoe', 'b2', 10, 1, HUBOT), waiting(10, started), now=NOW)
                self.assertTrue(said.startswith(f'⏳ **Game 10 opens {day}**, so `b2` wasn\'t played.\n'), said)


class MainTests(unittest.TestCase):
    def run_check(self, key: str, request: dict, state: object = 'theirs',
                  recent: str | None = '1') -> tuple[str, str | None, str]:
        with tempfile.TemporaryDirectory() as temp:
            folder = pathlib.Path(temp)
            (folder / 'dispatch.json').write_text(json.dumps({'ref': 'Development', 'inputs': request}),
                                                  encoding='utf-8')
            state = STATES.get(key) if state == 'theirs' else state
            if isinstance(state, str) and state.startswith('raw:'):
                (folder / 'game.json').write_text(state[4:], encoding='utf-8')
            elif state != 'unread':
                (folder / 'game.json').write_text(json.dumps(state), encoding='utf-8')
            if recent is not None:
                (folder / 'recent').write_text(recent, encoding='utf-8')
            env = {'RUNNER_TEMP': temp, 'GITHUB_OUTPUT': str(folder / 'output'),
                   'GITHUB_REPOSITORY_OWNER': OWNER, 'OWNER_ID': OWNER_ID, 'GAME': key}
            printed = io.StringIO()
            with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(printed):
                self.assertEqual(check.main(), 0)
            reply = folder / 'reply.md'
            return ((folder / 'output').read_text(encoding='utf-8'),
                    reply.read_text(encoding='utf-8') if reply.exists() else None, printed.getvalue())

    def test_a_move_for_the_game_is_sent_on_and_nothing_written(self) -> None:
        for key, request in (
            ('chess', move('chess', 'g1f3', 3, 3, OWNER_ID)),
            ('checkers', move('checkers', '25x18', 6, 4, OWNER_ID)),
            ('tictactoe', move('tictactoe', 'c3', 9, 3, OWNER_ID)),
            ('connectfour', move('connectfour', '5', 4, 4, HUBOT)),
        ):
            with self.subTest(key=key):
                output, reply, printed = self.run_check(key, request)
                self.assertEqual((output, reply), ('verdict=dispatch\n', None))
                self.assertIn(f"{key} {request[check.GAMES[key].code]} for game {request['game']}", printed)

    def test_a_refusal_writes_its_reply(self) -> None:
        output, reply, _ = self.run_check('chess', move('chess', 'd7d5', 3, 2, HUBOT))
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith('⌛ **Too late: move 2 is already on the board**'))
        output, reply, _ = self.run_check('connectfour', move('connectfour', '5', 4, 4, OWNER_ID))
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith("⏳ **It's GitHub's turn as Black**"))

    def test_the_next_game_is_judged_by_the_time_now(self) -> None:
        later = waiting(7, '2999-01-01T16:00:00Z', opens='github')
        output, reply, _ = self.run_check('tictactoe', move('tictactoe', 'b2', 7, 2, HUBOT), later)
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith('⏳ **Game 7 opens 1 Jan**'))
        opened = waiting(7, '2026-01-01T16:00:00Z')
        self.assertEqual(self.run_check('chess', move('chess', 'e2e4', 7, 1, OWNER_ID), opened)[:2],
                         ('verdict=dispatch\n', None))

    def test_no_game_yet_and_an_unread_state_are_told_apart(self) -> None:
        self.assertEqual(self.run_check('chess', move('chess', 'e2e4', 1, 1, OWNER_ID), state=None)[0],
                         'verdict=dispatch\n')
        self.assertEqual(self.run_check('chess', move('chess', 'e2e4', 2, 1, OWNER_ID), state='unread')[0],
                         'verdict=dispatch\n')
        self.assertEqual(self.run_check('chess', move('chess', 'e2e4', 2, 1, OWNER_ID), state=None)[0],
                         'verdict=dispatch\n', 'a game after the first, with none started, is the game to judge')

    def test_a_state_that_isn_t_a_game_s_is_judged_as_unread(self) -> None:
        # Game 2 is over on the real board, which the check can only know from a state it can read.
        for state in ('raw:not json', 'raw:', [], 'a string', {'game': '3', 'moves': []}, {'game': True, 'moves': []},
                      {'game': 0, 'moves': []}, {'game': 3}, {'game': 3, 'moves': ['e4']}):
            with self.subTest(state=state):
                output, reply, _ = self.run_check('chess', move('chess', 'e2e4', 2, 1, OWNER_ID), state=state)
                self.assertEqual((output, reply), ('verdict=dispatch\n', None))
        output, reply, _ = self.run_check('chess', move('chess', 'e7e5', 2, 2, OWNER_ID), state='raw:{')
        self.assertEqual(output, 'verdict=refuse\n', 'an unread state still turns away the wrong side')
        self.assertTrue(reply.startswith("⏳ **It's GitHub's turn as Black**"))
        for number in (True, 1.0):  # neither is game 1, whose first move would otherwise be already on the board
            with self.subTest(number=number):
                state = {**CHESS, 'game': number}
                self.assertEqual(self.run_check('chess', move('chess', 'e2e4', 1, 1, OWNER_ID), state=state)[:2],
                                 ('verdict=dispatch\n', None))

    def test_a_count_that_isn_t_a_number_limits_nobody(self) -> None:
        for recent in ('', 'lots', '٣٣', None):
            with self.subTest(recent=recent):
                self.assertEqual(self.run_check('chess', move('chess', 'g8f6', 3, 4, HUBOT), recent=recent)[0],
                                 'verdict=dispatch\n')
        self.assertEqual(self.run_check('chess', move('chess', 'g8f6', 3, 4, HUBOT), recent='31\n')[0],
                         'verdict=refuse\n')

    def test_a_game_the_check_doesn_t_know_is_sent_on(self) -> None:
        output, reply, printed = self.run_check('go', {'point': 'd4', 'issue': '50'}, state=None)
        self.assertEqual((output, reply), ('verdict=dispatch\n', None))
        self.assertEqual(printed, 'No check for go: sent on.\n')


class AgreementTests(unittest.TestCase):
    """The check, the router's table and the workflow name the same four games, the same inputs and the same state."""

    def test_the_check_knows_the_games_the_router_routes_in_tier_order(self) -> None:
        self.assertEqual(list(check.GAMES), ['tictactoe', 'connectfour', 'checkers', 'chess'])
        self.assertEqual(list(route.load()), list(check.GAMES))

    def test_each_route_passes_the_move_under_the_input_the_check_reads(self) -> None:
        routes = route.load()
        for key, game in check.GAMES.items():
            with self.subTest(key=key):
                self.assertEqual(sorted(routes[key]['pattern'].groupindex), sorted([game.code, 'game', 'move_number']))
        self.assertEqual(check.GAMES['chess'].code, 'uci')
        self.assertEqual(check.GAMES['chess'].shown, 'san')

    def test_each_player_keeps_one_side_and_the_house_github_or_the_arbiter_opens(self) -> None:
        # The house plays White, or X, and GitHub Black, or O, in every game. The house opens Chess, GitHub opens
        # Checkers, and the Arbiter opens Connect Four and Tic-Tac-Toe for a side it draws.
        self.assertEqual({key: (game.opens, game.sides) for key, game in check.GAMES.items()}, {
            'tictactoe': (None, ('X', 'O')),
            'connectfour': (None, ('White', 'Black')),
            'checkers': ('github', ('White', 'Black')),
            'chess': ('house', ('White', 'Black')),
        })

    def test_the_workflow_reads_each_game_s_state_where_the_check_expects_it(self) -> None:
        workflow = pathlib.Path(__file__).resolve().parents[1] / '.github' / 'workflows' / 'intake.yml'
        text = workflow.read_text(encoding='utf-8')
        self.assertIn(f"contents/{check.STATE.format(key='$GAME')}?ref=", text)
        for key, game in check.GAMES.items():
            with self.subTest(key=key):
                self.assertEqual(game.state, f'.github/{key}/game.json')


if __name__ == '__main__':
    unittest.main()
