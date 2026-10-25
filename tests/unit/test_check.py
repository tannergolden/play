#!/usr/bin/env python3
"""Tests for the pre-check of all four games.

WHY THIS EXISTS. `check.py` answers a move here, before its game runs, only
when the game could do nothing but turn it away. If it ever refused a move
the game would have played, a player would lose their move, so the moves it
sends on are pinned as carefully as the ones it refuses: a state that is
behind the game, a state that couldn't be read, a game whose sides it can't
know yet, and the owner, who is never limited. Every refusal is held to the
game's own words, word for word, in every game, and in the two games that
open under the Ghost Rule every way round the Arbiter can draw: either side
to place the first ghost, and either side to make the first move.

Nothing here reads or writes outside a throwaway folder. Run it from the root
of the repository:

    PYTHONPATH=src/intake:src/replays python3 -m unittest discover -s tests/unit -p 'test_*.py'
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
    """Who played a turn on record: a player, or the Arbiter when there is none."""
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
# Game 9 of Tic-Tac, where the owner always plays X and GitHub O, four turns in under the Ghost Rule. The Arbiter drew
# the house to place the first ghost: the owner's G. e5, then @octocat's G... b8. It drew the house to open, so X made
# the first mark, the owner's 1. Xd4, which sent O to the lower left board, and @octocat's 1... Oa1 there sent X to it.
TICTAC = {'game': 9, 'started': '2026-10-12T16:00:00Z', 'places': 'house', 'ghosts': [
    {'move': 'e5', 'shown': 'e5', **TANNER_MOVED},
    {'move': 'b8', 'shown': 'b8', **OCTOCAT_MOVED},
], 'opens': 'house', 'moves': [
    {'move': 'd4', 'shown': 'Xd4', **TANNER_MOVED},
    {'move': 'a1', 'shown': 'Oa1', **OCTOCAT_MOVED},
]}
# The same game the other way round: the Arbiter drew GitHub to place the first ghost, @octocat's G. e5, then came the
# owner's G... b8; and it drew GitHub to open, so O made the first mark, @octocat's 1. Od4, and the owner replied
# 1... Xa1.
TICTAC_GITHUB = {**TICTAC, 'places': 'github', 'ghosts': [
    {'move': 'e5', 'shown': 'e5', **OCTOCAT_MOVED},
    {'move': 'b8', 'shown': 'b8', **TANNER_MOVED},
], 'opens': 'github', 'moves': [
    {'move': 'd4', 'shown': 'Od4', **OCTOCAT_MOVED},
    {'move': 'a1', 'shown': 'Xa1', **TANNER_MOVED},
]}
# Game 4 of Pentago, where the owner always plays White and GitHub Black, five turns in under the Ghost Rule. The
# Arbiter drew GitHub to set the first ghost, @octocat's G. b5, then came the owner's G... e2; and it drew the house to
# open, so White set the first marble, the owner's 1. c4-ul-cw, then came @octocat's 1... d3-lr-acw and the owner's
# 2. a1-ll-cw.
PENTAGO = {'game': 4, 'started': '2026-10-09T16:00:00Z', 'places': 'github', 'ghosts': [
    {'move': 'b5', 'shown': 'b5', **OCTOCAT_MOVED},
    {'move': 'e2', 'shown': 'e2', **TANNER_MOVED},
], 'opens': 'house', 'moves': [
    {'move': 'c4-ul-cw', 'shown': 'c4-ul-cw', **TANNER_MOVED},
    {'move': 'd3-lr-acw', 'shown': 'd3-lr-acw', **OCTOCAT_MOVED},
    {'move': 'a1-ll-cw', 'shown': 'a1-ll-cw', **TANNER_MOVED},
]}
# The same game the other way round: the Arbiter drew the house to set the first ghost, the owner's G. b5, and set
# GitHub's itself, G... e2, after a week without one; and it drew GitHub to open, so Black set the first marble,
# @octocat's 1. c4-ul-cw, then came the owner's 1... d3-lr-acw and @octocat's 2. a1-ll-cw.
PENTAGO_GITHUB = {**PENTAGO, 'places': 'house', 'ghosts': [
    {'move': 'b5', 'shown': 'b5', **TANNER_MOVED},
    {'move': 'e2', 'shown': 'e2', **ARBITER},
], 'opens': 'github', 'moves': [
    {'move': 'c4-ul-cw', 'shown': 'c4-ul-cw', **OCTOCAT_MOVED},
    {'move': 'd3-lr-acw', 'shown': 'd3-lr-acw', **TANNER_MOVED},
    {'move': 'a1-ll-cw', 'shown': 'a1-ll-cw', **OCTOCAT_MOVED},
]}
STATES = {'tictac': TICTAC, 'pentago': PENTAGO, 'checkers': CHECKERS, 'chess': CHESS}
CODES = {'tictac': 'c3', 'pentago': 'f6-ur-cw', 'checkers': '25x18', 'chess': 'g1f3'}
GHOST_CODES = {'tictac': 'e5', 'pentago': 'b5'}  # a ghost's square, or its hole
GHOSTLY = ('tictac', 'pentago')  # the two games that open under the Ghost Rule


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


def ghosting(places: str, ghosts: int, opens: str | None = None, moves: int = 0) -> dict:
    """Game 2 under the Ghost Rule, from its start: the side drawn to place the first ghost, the ghosts down, each by
    its own side, and once both are, the side drawn to open and the moves made."""
    sides = [places, 'github' if places == 'house' else 'house']
    if opens:
        sides += [opens if ply % 2 else 'github' if opens == 'house' else 'house' for ply in range(1, moves + 1)]
    turns = [{'move': 'a1', 'shown': 'a1', **(TANNER_MOVED if side == 'house' else OCTOCAT_MOVED)}
             for side in sides]
    state = {'game': 2, 'started': '2026-10-12T16:00:00Z', 'places': places, 'ghosts': turns[:ghosts],
             'moves': turns[2:2 + moves]}
    return {**state, 'opens': opens} if opens else state


def house_turn(house: str, github: str, code: str) -> str:
    return (f"⏳ **It's {TANNER}'s turn as {house}**, so `{code}` wasn't played.\nGitHub plays {github}: once {house}"
            f" moves, pick {github}'s reply on {BOARD}.\n")


def github_turn(github: str, code: str) -> str:
    return (f"⏳ **It's GitHub's turn as {github}**, so `{code}` wasn't played.\n{github}'s moves are for everyone but"
            ' you. Your turn comes next.\n')


def house_ghost(verb: str, code: str, spot: str = 'square') -> str:
    return (f"⏳ **It's {TANNER}'s turn to {verb} a ghost**, so `{code}` wasn't played.\nOnce {TANNER}'s ghost is"
            f" down, pick a {spot} for GitHub's on {BOARD}.\n")


def github_ghost(verb: str, code: str) -> str:
    return (f"⏳ **It's GitHub's turn to {verb} a ghost**, so `{code}` wasn't played.\nGitHub's ghost is for everyone"
            ' but you. Your turn comes next.\n')


class SentOn(unittest.TestCase):
    def test_the_side_to_move_on_the_board_goes_on(self) -> None:
        self.assertEqual(verdict('chess', move('chess', 'g1f3', 3, 3, OWNER_ID)), '')
        self.assertEqual(verdict('checkers', move('checkers', '25x18', 6, 4, OWNER_ID)), '')
        self.assertEqual(verdict('tictac', move('tictac', 'c3', 9, 5, OWNER_ID)), '')
        self.assertEqual(verdict('tictac', move('tictac', 'c3', 9, 5, HUBOT), TICTAC_GITHUB), '')
        self.assertEqual(verdict('pentago', move('pentago', 'f6-ur-cw', 4, 6, HUBOT)), '')
        self.assertEqual(verdict('pentago', move('pentago', 'f6-ur-cw', 4, 6, OWNER_ID), PENTAGO_GITHUB), '')

    def test_the_side_to_place_a_ghost_goes_on(self) -> None:
        # The Arbiter drew the house to place Tic-Tac's first ghost and GitHub to set Pentago's.
        self.assertEqual(verdict('tictac', move('tictac', 'e5', 2, 1, OWNER_ID), ghosting('house', 0)), '')
        self.assertEqual(verdict('tictac', move('tictac', 'b8', 2, 2, HUBOT), ghosting('house', 1)), '')
        self.assertEqual(verdict('pentago', move('pentago', 'b5', 2, 1, HUBOT), ghosting('github', 0)), '')
        self.assertEqual(verdict('pentago', move('pentago', 'e2', 2, 2, OWNER_ID), ghosting('github', 1)), '')

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
        self.assertEqual(verdict('tictac', move('tictac', 'c3', 9, 7, OWNER_ID)), '')
        self.assertEqual(verdict('pentago', move('pentago', 'f6-ur-cw', 4, 8, HUBOT)), '')
        # GitHub's ghost, before the house's is down.
        self.assertEqual(verdict('tictac', move('tictac', 'b8', 2, 2, HUBOT), ghosting('house', 0)), '')

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

    def test_under_the_ghost_rule_a_side_it_can_t_know_is_left_to_the_game(self) -> None:
        # Whose ghost is due depends on the side the Arbiter drew to place the first, and whose move it is on the side
        # it drew to open, and only the state shows either, once the Arbiter has drawn it.
        for key in GHOSTLY:
            state, number = STATES[key], STATES[key]['game']
            undrawn = {'game': number, 'started': state['started'], 'moves': []}  # its start has come, its draw not
            one = {**undrawn, 'places': state['places'], 'ghosts': state['ghosts'][:1]}  # one ghost down
            for player_id in (OWNER_ID, HUBOT):
                for turn in (1, 2, 3, 4):
                    code = GHOST_CODES[key] if turn <= 2 else CODES[key]
                    request = move(key, code, number, turn, player_id)
                    with self.subTest(key=key, player_id=player_id, turn=turn):
                        self.assertEqual(verdict(key, request, state=None, known=False), '', 'an unread state')
                        self.assertEqual(verdict(key, request, undrawn), '', 'no side drawn to place the first ghost')
                        for places in (None, 'nobody', 'House', 1):
                            self.assertEqual(verdict(key, request, {**undrawn, 'places': places, 'ghosts': []}), '',
                                             places)
                        later = move(key, code, number + 1, turn, player_id)
                        self.assertEqual(verdict(key, later), '', 'a game after the one on the board')
                        first = move(key, code, 1, turn, player_id)
                        self.assertEqual(verdict(key, first, state=None), '', 'no game yet')
                for turn in (3, 4):
                    request = move(key, CODES[key], number, turn, player_id)
                    with self.subTest(key=key, player_id=player_id, turn=turn):
                        self.assertEqual(verdict(key, request, one), '', 'no side drawn to open')
                        self.assertEqual(verdict(key, request, {**one, 'opens': 'house'}), '',
                                         'a side to open, but only one ghost down')
                for turn in (len(state['ghosts'] + state['moves']) + 1, len(state['ghosts'] + state['moves']) + 2):
                    request = move(key, CODES[key], number, turn, player_id)
                    with self.subTest(key=key, player_id=player_id, turn=turn):
                        unsaid = {name: value for name, value in state.items() if name != 'opens'}
                        self.assertEqual(verdict(key, request, unsaid), '', 'no side drawn to open')
                        for opens in (None, 'nobody', 'House', 1):
                            self.assertEqual(verdict(key, request, {**state, 'opens': opens}), '', opens)

    def test_the_owner_is_never_limited(self) -> None:
        self.assertEqual(verdict('chess', move('chess', 'g1f3', 3, 3, OWNER_ID), recent=500), '')
        self.assertEqual(verdict('checkers', move('checkers', '25x18', 6, 4, OWNER_ID), recent=500), '')
        self.assertEqual(verdict('tictac', move('tictac', 'c3', 9, 5, OWNER_ID), recent=500), '')
        self.assertEqual(verdict('pentago', move('pentago', 'f6-ur-cw', 4, 6, OWNER_ID), PENTAGO_GITHUB,
                                 recent=500), '')
        self.assertEqual(verdict('pentago', move('pentago', 'b5', 2, 1, OWNER_ID), ghosting('house', 0),
                                 recent=500), '')

    def test_a_move_on_record_that_can_t_be_named_is_left_to_the_game(self) -> None:
        nameless = {**CHECKERS, 'moves': [{**CHECKERS['moves'][0], 'shown': None}, CHECKERS['moves'][1]]}
        self.assertEqual(verdict('checkers', move('checkers', '9-14', 6, 1, HUBOT), nameless), '')
        unsigned = {**CHECKERS, 'moves': [{**CHECKERS['moves'][0], 'player': 'a b'}, CHECKERS['moves'][1]]}
        self.assertEqual(verdict('checkers', move('checkers', '9-14', 6, 1, HUBOT), unsigned), '')
        nameless = {**TICTAC, 'ghosts': [{**TICTAC['ghosts'][0], 'shown': ''}, TICTAC['ghosts'][1]]}
        self.assertEqual(verdict('tictac', move('tictac', 'a3', 9, 1, HUBOT), nameless), '')


class TurnedAway(unittest.TestCase):
    def test_more_than_an_hour_s_share_across_all_four_games(self) -> None:
        self.assertEqual(check.LIMIT, 30)
        # GitHub's next turn in each game here: move 4 in Chess, move 5 in Checkers, which GitHub opens, and move 6 in
        # Tic-Tac and Pentago, whose ghosts are moves 1 and 2.
        for key, number in (('tictac', 6), ('pentago', 6), ('checkers', 5), ('chess', 4)):
            request = move(key, CODES[key], STATES[key]['game'], number, HUBOT)
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
            # Under the Ghost Rule a move's number counts the ghosts, which the score sheet writes on a row of their
            # own, and numbers each move among the moves alone.
            ('tictac', move('tictac', 'a3', 9, 1, HUBOT), TICTAC, late(1, 'a3', 'G. e5', TANNER)),
            ('tictac', move('tictac', 'a3', 9, 2, HUBOT), TICTAC, late(2, 'a3', 'G... b8', octocat)),
            ('tictac', move('tictac', 'a3', 9, 2, OCTOCAT), TICTAC, late(2, 'a3', 'G... b8', 'you')),
            ('tictac', move('tictac', 'a3', 9, 3, HUBOT), TICTAC, late(3, 'a3', '1. Xd4', TANNER)),
            ('tictac', move('tictac', 'c1', 9, 4, OCTOCAT), TICTAC, late(4, 'c1', '1... Oa1', 'you')),
            ('tictac', move('tictac', 'a3', 9, 1, OWNER_ID), TICTAC_GITHUB, late(1, 'a3', 'G. e5', octocat)),
            ('tictac', move('tictac', 'a3', 9, 3, HUBOT), TICTAC_GITHUB, late(3, 'a3', '1. Od4', octocat)),
            ('tictac', move('tictac', 'c1', 9, 4, OWNER_ID), TICTAC_GITHUB, late(4, 'c1', '1... Xa1', 'you')),
            ('pentago', move('pentago', 'a6', 4, 1, OWNER_ID), PENTAGO, late(1, 'a6', 'G. b5', octocat)),
            ('pentago', move('pentago', 'a6', 4, 2, OWNER_ID), PENTAGO, late(2, 'a6', 'G... e2', 'you')),
            ('pentago', move('pentago', 'f1-lr-cw', 4, 4, HUBOT), PENTAGO, late(4, 'f1-lr-cw', '1... d3-lr-acw',
                                                                                   octocat)),
            ('pentago', move('pentago', 'f1-lr-cw', 4, 5, HUBOT), PENTAGO, late(5, 'f1-lr-cw', '2. a1-ll-cw', TANNER)),
            ('pentago', move('pentago', 'a6', 4, 2, HUBOT), PENTAGO_GITHUB, late(2, 'a6', 'G... e2', 'the Arbiter')),
            ('pentago', move('pentago', 'f1-lr-cw', 4, 3, OWNER_ID), PENTAGO_GITHUB, late(3, 'f1-lr-cw',
                                                                                          '1. c4-ul-cw', octocat)),
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

    def test_the_wrong_side_of_a_ghost_in_tic_tac(self) -> None:
        # The Arbiter drew the house to place the first ghost, so move 1 is the owner's ghost and move 2 GitHub's.
        self.assertEqual(verdict('tictac', move('tictac', 'e5', 2, 1, HUBOT), ghosting('house', 0)),
                         f"⏳ **It's {TANNER}'s turn to place a ghost**, so `e5` wasn't played.\nOnce {TANNER}'s"
                         f" ghost is down, pick a square for GitHub's on {BOARD}.\n")
        self.assertEqual(verdict('tictac', move('tictac', 'b8', 2, 2, OWNER_ID), ghosting('house', 1)),
                         "⏳ **It's GitHub's turn to place a ghost**, so `b8` wasn't played.\nGitHub's ghost is for"
                         ' everyone but you. Your turn comes next.\n')
        # Drawn the other way, move 1 is GitHub's ghost and move 2 the owner's.
        self.assertEqual(verdict('tictac', move('tictac', 'e5', 2, 1, OWNER_ID), ghosting('github', 0)),
                         "⏳ **It's GitHub's turn to place a ghost**, so `e5` wasn't played.\nGitHub's ghost is for"
                         ' everyone but you. Your turn comes next.\n')
        self.assertEqual(verdict('tictac', move('tictac', 'b8', 2, 2, HUBOT), ghosting('github', 1)),
                         f"⏳ **It's {TANNER}'s turn to place a ghost**, so `b8` wasn't played.\nOnce {TANNER}'s"
                         f" ghost is down, pick a square for GitHub's on {BOARD}.\n")

    def test_the_wrong_side_of_a_ghost_in_pentago(self) -> None:
        # In Pentago a side sets its ghost. The Arbiter drew GitHub to set the first, so move 2 is the owner's.
        self.assertEqual(verdict('pentago', move('pentago', 'b5', 2, 1, OWNER_ID), ghosting('github', 0)),
                         "⏳ **It's GitHub's turn to set a ghost**, so `b5` wasn't played.\nGitHub's ghost is for"
                         ' everyone but you. Your turn comes next.\n')
        self.assertEqual(verdict('pentago', move('pentago', 'e2', 2, 2, HUBOT), ghosting('github', 1)),
                         f"⏳ **It's {TANNER}'s turn to set a ghost**, so `e2` wasn't played.\nOnce {TANNER}'s"
                         f" ghost is down, pick a hole for GitHub's on {BOARD}.\n")
        self.assertEqual(verdict('pentago', move('pentago', 'b5', 2, 1, HUBOT), ghosting('house', 0)),
                         f"⏳ **It's {TANNER}'s turn to set a ghost**, so `b5` wasn't played.\nOnce {TANNER}'s"
                         f" ghost is down, pick a hole for GitHub's on {BOARD}.\n")
        self.assertEqual(verdict('pentago', move('pentago', 'e2', 2, 2, OWNER_ID), ghosting('house', 1)),
                         "⏳ **It's GitHub's turn to set a ghost**, so `e2` wasn't played.\nGitHub's ghost is for"
                         ' everyone but you. Your turn comes next.\n')

    def test_the_wrong_side_in_tic_tac_both_ways_round(self) -> None:
        # The owner always plays X and GitHub O. Drawn to open, the house makes the first mark, so after the two
        # ghosts the owner has the odd moves among the moves: move 5, the third, is X's, and move 6 O's.
        self.assertEqual(verdict('tictac', move('tictac', 'c3', 9, 5, HUBOT)),
                         f"⏳ **It's {TANNER}'s turn as X**, so `c3` wasn't played.\nGitHub plays O: once X moves,"
                         f" pick O's reply on {BOARD}.\n")
        self.assertEqual(verdict('tictac', move('tictac', 'c1', 9, 6, OWNER_ID)),
                         "⏳ **It's GitHub's turn as O**, so `c1` wasn't played.\nO's moves are for everyone but you."
                         ' Your turn comes next.\n')
        # Drawn the other way, GitHub makes the first mark, as O, so the owner, still X, has the even ones.
        self.assertEqual(verdict('tictac', move('tictac', 'c3', 9, 5, OWNER_ID), TICTAC_GITHUB),
                         "⏳ **It's GitHub's turn as O**, so `c3` wasn't played.\nO's moves are for everyone but you."
                         ' Your turn comes next.\n')
        self.assertEqual(verdict('tictac', move('tictac', 'c1', 9, 6, HUBOT), TICTAC_GITHUB),
                         f"⏳ **It's {TANNER}'s turn as X**, so `c1` wasn't played.\nGitHub plays O: once X moves,"
                         f" pick O's reply on {BOARD}.\n")

    def test_the_wrong_side_in_pentago_both_ways_round(self) -> None:
        # The owner always plays White and GitHub Black. Drawn to open, the house sets the first marble, so move 6,
        # the fourth after the ghosts, is Black's, and move 7 White's.
        self.assertEqual(verdict('pentago', move('pentago', 'f6-ur-cw', 4, 6, OWNER_ID)),
                         "⏳ **It's GitHub's turn as Black**, so `f6-ur-cw` wasn't played.\nBlack's moves are for"
                         ' everyone but you. Your turn comes next.\n')
        self.assertEqual(verdict('pentago', move('pentago', 'f5-lr-acw', 4, 7, HUBOT)),
                         f"⏳ **It's {TANNER}'s turn as White**, so `f5-lr-acw` wasn't played.\nGitHub plays Black:"
                         f" once White moves, pick Black's reply on {BOARD}.\n")
        # Drawn the other way, GitHub sets the first marble, as Black, so the owner, still White, has the even moves.
        self.assertEqual(verdict('pentago', move('pentago', 'f6-ur-cw', 4, 6, HUBOT), PENTAGO_GITHUB),
                         f"⏳ **It's {TANNER}'s turn as White**, so `f6-ur-cw` wasn't played.\nGitHub plays Black:"
                         f" once White moves, pick Black's reply on {BOARD}.\n")
        self.assertEqual(verdict('pentago', move('pentago', 'f5-lr-acw', 4, 7, OWNER_ID), PENTAGO_GITHUB),
                         "⏳ **It's GitHub's turn as Black**, so `f5-lr-acw` wasn't played.\nBlack's moves are for"
                         ' everyone but you. Your turn comes next.\n')

    def test_each_turn_is_the_side_the_arbiter_drew_for_it(self) -> None:
        # Under the Ghost Rule move 1 is the ghost of the side drawn to place the first, move 2 the other side's
        # ghost, and from move 3 the side drawn to open has the odd moves among the moves; the two draws are apart.
        for key, verb, spot, (house, github) in (('tictac', 'place', 'square', ('X', 'O')),
                                                  ('pentago', 'set', 'hole', ('White', 'Black'))):
            for places in check.SIDES:
                for opens in check.SIDES:
                    states = (ghosting(places, 0), ghosting(places, 1), ghosting(places, 2, opens),
                              ghosting(places, 2, opens, 1), ghosting(places, 2, opens, 2))
                    other = {'house': 'github', 'github': 'house'}
                    for turn, (state, side) in enumerate(zip(states, (places, other[places], opens, other[opens],
                                                                      opens)), 1):
                        code = GHOST_CODES[key] if turn <= 2 else CODES[key]
                        right, wrong = (OWNER_ID, HUBOT) if side == 'house' else (HUBOT, OWNER_ID)
                        if turn <= 2:
                            said = house_ghost(verb, code, spot) if side == 'house' else github_ghost(verb, code)
                        else:
                            said = house_turn(house, github, code) if side == 'house' else github_turn(github, code)
                        with self.subTest(key=key, places=places, opens=opens, turn=turn):
                            self.assertEqual(verdict(key, move(key, code, 2, turn, right), state), '')
                            self.assertEqual(verdict(key, move(key, code, 2, turn, wrong), state), said)
                            if turn > 1:  # read from a state a turn behind, it is told the same
                                self.assertEqual(verdict(key, move(key, code, 2, turn, wrong), states[turn - 2]),
                                                 said if turn != 3 else '', 'no side drawn to open yet')

    def test_a_move_while_the_winning_board_is_up(self) -> None:
        # Game 6 ended at 16:00 UTC on 12 Oct, so game 7 opens two days later: 11:00 EST on 14 Oct. The fresh board
        # keeps the game that ended until then, and under the Ghost Rule its draws are still to come.
        for key in check.GAMES:
            state = waiting(7, '2026-10-14T16:00:00Z', ended={**STATES[key], 'game': 6})
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
        # In Tic-Tac and Pentago the first ghost is the side's the Arbiter draws once the start has passed, which this
        # state doesn't show yet: either side's goes on, for the game to judge.
        for key in GHOSTLY:
            for player_id in (OWNER_ID, HUBOT):
                with self.subTest(key=key, player_id=player_id):
                    self.assertEqual(verdict(key, move(key, GHOST_CODES[key], 7, 1, player_id), state, now=started),
                                     '')

    def test_a_start_still_to_come_holds_back_only_a_game_with_nothing_on_its_board(self) -> None:
        # A game already under way, or the very first game, is never held back by its start.
        early = {**CHESS, 'started': '2026-10-20T16:00:00Z'}
        self.assertEqual(verdict('chess', move('chess', 'g1f3', 3, 3, OWNER_ID), early), '')
        first = waiting(1, '2026-10-20T16:00:00Z')
        self.assertEqual(verdict('chess', move('chess', 'e2e4', 1, 1, OWNER_ID), first), '')
        # A ghost is a turn on the board like any move.
        ghosted = {**ghosting('house', 1), 'game': 7, 'started': '2026-10-20T16:00:00Z'}
        self.assertEqual(verdict('tictac', move('tictac', 'b8', 7, 2, HUBOT), ghosted), '')
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
                said = verdict('tictac', move('tictac', 'e5', 10, 1, HUBOT), waiting(10, started), now=NOW)
                self.assertTrue(said.startswith(f'⏳ **Game 10 opens {day}**, so `e5` wasn\'t played.\n'), said)


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
            ('tictac', move('tictac', 'c3', 9, 5, OWNER_ID)),
            ('pentago', move('pentago', 'f6-ur-cw', 4, 6, HUBOT)),
        ):
            with self.subTest(key=key):
                output, reply, printed = self.run_check(key, request)
                self.assertEqual((output, reply), ('verdict=dispatch\n', None))
                self.assertIn(f"{key} {request[check.GAMES[key].code]} for game {request['game']}", printed)

    def test_a_refusal_writes_its_reply(self) -> None:
        output, reply, _ = self.run_check('chess', move('chess', 'd7d5', 3, 2, HUBOT))
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith('⌛ **Too late: move 2 is already on the board**'))
        output, reply, _ = self.run_check('pentago', move('pentago', 'f6-ur-cw', 4, 6, OWNER_ID))
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith("⏳ **It's GitHub's turn as Black**"))
        output, reply, _ = self.run_check('tictac', move('tictac', 'b8', 2, 2, OWNER_ID), ghosting('house', 1))
        self.assertEqual(output, 'verdict=refuse\n')
        self.assertTrue(reply.startswith("⏳ **It's GitHub's turn to place a ghost**"))

    def test_the_next_game_is_judged_by_the_time_now(self) -> None:
        later = waiting(7, '2999-01-01T16:00:00Z')
        output, reply, _ = self.run_check('tictac', move('tictac', 'e5', 7, 2, HUBOT), later)
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
        # Under the Ghost Rule a game holds two ghosts at most, each a turn, and moves only once both are down.
        for state in ({**TICTAC, 'ghosts': None}, {**TICTAC, 'ghosts': 'e5'}, {**TICTAC, 'ghosts': ['e5', 'b8']},
                      {**TICTAC, 'ghosts': [*TICTAC['ghosts'], TICTAC['ghosts'][0]]},
                      {**TICTAC, 'ghosts': TICTAC['ghosts'][:1]}):
            with self.subTest(state=state):
                output, reply, _ = self.run_check('tictac', move('tictac', 'c3', 8, 5, OWNER_ID), state=state)
                self.assertEqual((output, reply), ('verdict=dispatch\n', None))

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
        self.assertEqual(list(check.GAMES), ['tictac', 'pentago', 'checkers', 'chess'])
        self.assertEqual(list(route.load()), list(check.GAMES))

    def test_each_route_passes_the_move_under_the_input_the_check_reads(self) -> None:
        routes = route.load()
        for key, game in check.GAMES.items():
            with self.subTest(key=key):
                self.assertEqual(sorted(routes[key]['pattern'].groupindex), sorted([game.code, 'game', 'move_number']))
        self.assertEqual(check.GAMES['chess'].code, 'uci')
        self.assertEqual(check.GAMES['chess'].shown, 'san')

    def test_each_player_keeps_one_side_and_each_game_its_opening(self) -> None:
        # The house plays X, or White, and GitHub O, or Black, in every game. The house opens Chess and GitHub opens
        # Checkers; Tic-Tac and Pentago open under the Ghost Rule, where a side places its ghost, or in Pentago sets
        # it, and the Arbiter draws who places first and who opens.
        self.assertEqual({key: (game.opens, game.ghost, game.sides) for key, game in check.GAMES.items()}, {
            'tictac': (None, 'place', ('X', 'O')),
            'pentago': (None, 'set', ('White', 'Black')),
            'checkers': ('github', None, ('White', 'Black')),
            'chess': ('house', None, ('White', 'Black')),
        })

    def test_the_workflow_reads_each_game_s_state_where_the_check_expects_it(self) -> None:
        workflow = pathlib.Path(__file__).resolve().parents[2] / '.github' / 'workflows' / 'intake.yml'
        text = workflow.read_text(encoding='utf-8')
        self.assertIn(f"contents/{check.STATE.format(key='$GAME')}?ref=", text)
        for key, game in check.GAMES.items():
            with self.subTest(key=key):
                self.assertEqual(game.state, f'.github/{key}/game.json')


if __name__ == '__main__':
    unittest.main()
