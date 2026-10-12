#!/usr/bin/env python3
"""Turn a move away here, before it starts its game, when the game could only turn it away.

WHY THIS EXISTS. Every move the router sends on costs a run of its game's
workflow. A move for a game that is over, a move already played, a move on
the other side's turn, a move for the next game while the last one's winning
board is still up, or one more move from a player who has sent many this hour
can never be played, so this answers it here, in the game's own words, and
the game never runs for it. The game still checks every move it gets: this
only spares it the ones it would certainly refuse.

WHAT IT KNOWS. The four games, in tier order (GAMES below): where each keeps
its state, the keys a played move is kept under, who opens it, and the words
for each player's side, which never change: the house, @tannergolden, plays
White in Chess, Checkers and Connect Four and X in Tic-Tac-Toe, and GitHub
plays Black, or O. The house opens Chess, as White. GitHub opens Checkers, as
Black, since Black moves first in American checkers. In Connect Four and
Tic-Tac-Toe the Arbiter opens every game with a random legal move, for a side
drawn at random, which the game's state records as `opens`, so O moves first
in a game of Tic-Tac-Toe it opens for GitHub. Why the Arbiter opens those two
is in docs/adrs/ADR-0001-Four-Games-One-Arbiter.md.

WHAT IT READS. 🎲 Move Intake names the game in $GAME, fetches its state,
`.github/<game>/game.json` from the game's repository, into
$RUNNER_TEMP/game.json (`null` when no game has started, and no file at all
when it couldn't be read), and counts the issues the player opened here in
the last hour, whatever the game, into $RUNNER_TEMP/recent. It reads the move
from $RUNNER_TEMP/dispatch.json, which the router wrote. A state can only ever
be behind the game, never ahead of it, so this refuses on the state only what
a later state would refuse too: a game already over, a move already played, a
game that opens later. A move that looks ahead of the board goes on, for the
game to judge, and so does every move whose side it can't tell: in Connect
Four and Tic-Tac-Toe, a move for a game it has not seen opened.

It writes `verdict=refuse` or `verdict=dispatch` to $GITHUB_OUTPUT, and on a
refusal the reply to $RUNNER_TEMP/reply.md. Nothing here talks to GitHub.

    python3 -m unittest discover -s intake -p 'test_*.py'
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass

# The issues one player may open here in an hour, across all four games together. The owner, who plays the house's
# side in every game, has no limit.
LIMIT = 30

STATE = '.github/{key}/game.json'  # where each game keeps the game on its board, in the game's repository
SIDES = ('house', 'github')
EST = dt.timezone(dt.timedelta(hours=-5), 'EST')  # the page tells time in EST, all year
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
LOGIN = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})')


@dataclass(frozen=True)
class Game:
    """What the check knows of one game."""

    key: str  # the game's name in a move's title, its row in routes.json, and its folder in the game's repository
    code: str  # the input that carries the move, and the key a played move keeps it under in the state
    shown: str  # the key a played move's text notation is kept under in the state
    sides: tuple[str, str]  # the words for the house's side, then for GitHub's: the same in every game, whoever opens
    opens: str | None  # who opens every game, the house or GitHub, or None where the Arbiter opens each for a side

    @property
    def state(self) -> str:
        return STATE.format(key=self.key)


GAMES = {game.key: game for game in (
    Game('tictactoe', 'move', 'shown', ('X', 'O'), None),
    Game('connectfour', 'move', 'shown', ('White', 'Black'), None),
    Game('checkers', 'move', 'shown', ('White', 'Black'), 'github'),
    Game('chess', 'uci', 'san', ('White', 'Black'), 'house'),
)}


@dataclass(frozen=True)
class Board:
    """The game on the board, as its state says."""

    number: int
    moves: list
    started: dt.datetime | None  # when it opens, or opened
    opens: str | None  # the side the Arbiter opened it for, in the games it opens


def profile(owner: str) -> str:
    return f'https://github.com/{owner}'


def handle(login: str) -> str:
    """A player named without a ping: the @handle as a link to their profile, as the game names them."""
    return f'[@{login}]({profile(login)})'


def numbered(ply: int, shown: str) -> str:
    """A move as the score sheet writes it, by its number from 1 for the opener's first: `12. Nf3`, `12... Nf6`."""
    return f'{(ply + 1) // 2}. {shown}' if ply % 2 else f'{(ply + 1) // 2}... {shown}'


def day(moment: dt.datetime) -> str:
    """A day as the page writes it, in the page's time: `14 Oct`."""
    local = moment.astimezone(EST)
    return f'{local.day} {MONTHS[local.month - 1]}'


def when(text: object) -> dt.datetime | None:
    """A moment from a game's state, `2026-10-14T16:00:00Z`, or None when it isn't one."""
    if not isinstance(text, str):
        return None
    try:
        moment = dt.datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=dt.timezone.utc)


def board(state: object) -> Board | None:
    """The game a state holds: the first game, still to come, when none has started, and None for a state that isn't
    shaped as a game's, which is judged as one that couldn't be read."""
    if state is None:
        return Board(1, [], None, None)
    if not isinstance(state, dict):
        return None
    number, moves, opens = state.get('game'), state.get('moves'), state.get('opens')
    if type(number) is not int or number < 1 or not isinstance(moves, list):
        return None
    if not all(isinstance(move, dict) for move in moves):
        return None
    return Board(number, moves, when(state.get('started')), opens if opens in SIDES else None)


def verdict(key: str, request: dict, state: object, recent: int | None, owner: str, owner_id: str,
            known: bool = True, now: dt.datetime | None = None) -> str:
    """The refusal for a move the game could only turn away, or "" to send it on. `known` is False when the game's
    state couldn't be read, and `state` None when no game has started; `now` is the time to judge by, in UTC."""
    spec = GAMES[key]
    code, game, ply = request[spec.code], int(request['game']), int(request['move_number'])
    mine = request['player_id'] == owner_id
    link = f'[the board]({profile(owner)})'
    if not mine and recent is not None and recent > LIMIT:
        return (f"🐢 **Slow down**: you've opened {recent} issues here in the last hour, more than the {LIMIT} the"
                f" games take from one player, so `{code}` wasn't played.\nPick your next move from {link} in a"
                ' little while.\n')
    on = board(state) if known else None
    if on:
        moment = now or dt.datetime.now(dt.timezone.utc)
        if not on.moves and on.number > 1 and on.started and on.started > moment and game <= on.number:
            # The last game's winning board is on show, and nothing can be played until the next game opens.
            return (f"⏳ **Game {on.number} opens {day(on.started)}**, so `{code}` wasn't played.\nGame"
                    f" {on.number - 1}'s final board stays up until then: pick a move from {link} once game"
                    f' {on.number} is on it.\n')
        if game < on.number:
            return (f"⌛ **Game {game} is over**, so `{code}` wasn't played.\nGame {on.number} is under way on"
                    f' {link}: pick a move there.\n')
        if game == on.number and ply <= len(on.moves):
            earlier = on.moves[ply - 1]
            shown, player = earlier.get(spec.shown), earlier.get('player')
            by = ('the Arbiter' if earlier.get('arbiter') else
                  'you' if str(earlier.get('player_id')) == request['player_id'] else
                  handle(player) if isinstance(player, str) and LOGIN.fullmatch(player) else '')
            if not (isinstance(shown, str) and shown and by):
                return ''  # a move on record that can't be named: the game says what became of this one
            return (f"⌛ **Too late: move {ply} is already on the board**, so `{code}` wasn't played.\n"
                    f'{numbered(ply, shown)} got there first, played by {by}. Pick a move from {link} as it stands'
                    ' now.\n')
    # Whose turn it is: the opener's on odd plies, the other side's on even ones. The house opens every game of Chess
    # and GitHub every game of Checkers; the side the Arbiter opened a game of Connect Four or Tic-Tac-Toe for is
    # known only once the state shows that game opened. Each side is named in its own words, whoever opened.
    first = spec.opens or (on.opens if on and on.moves and game == on.number else None)
    if not first:
        return ''
    house, github = spec.sides
    turn = first if ply % 2 else 'github' if first == 'house' else 'house'
    if turn == 'house' and not mine:
        return (f"⏳ **It's {handle(owner)}'s turn as {house}**, so `{code}` wasn't played.\nGitHub plays {github}:"
                f" once {house} moves, pick {github}'s reply on {link}.\n")
    if turn == 'github' and mine:
        return (f"⏳ **It's GitHub's turn as {github}**, so `{code}` wasn't played.\n{github}'s moves are for"
                ' everyone but you. Your turn comes next.\n')
    return ''


def main() -> int:
    env = os.environ
    temp = pathlib.Path(env['RUNNER_TEMP'])
    request = json.loads((temp / 'dispatch.json').read_text(encoding='utf-8'))['inputs']
    key = env.get('GAME', '')
    if key not in GAMES:
        # A game this check doesn't know: its own workflow judges every move for it.
        with open(env['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle_:
            handle_.write('verdict=dispatch\n')
        print(f'No check for {key or "an unnamed game"}: sent on.')
        return 0
    found = temp / 'game.json'
    known, state = found.exists(), None
    if known:
        try:
            state = json.loads(found.read_text(encoding='utf-8'))
        except ValueError:
            known = False  # not a state at all: judged as one that couldn't be read
    counted = temp / 'recent'
    text = counted.read_text(encoding='utf-8').strip() if counted.exists() else ''
    recent = int(text) if text.isdecimal() and text.isascii() else None  # uncounted: no limit is applied
    said = verdict(key, request, state, recent, env['GITHUB_REPOSITORY_OWNER'], env['OWNER_ID'], known)
    if said:
        (temp / 'reply.md').write_text(said, encoding='utf-8')
    with open(env['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle_:
        handle_.write(f"verdict={'refuse' if said else 'dispatch'}\n")
    print(f"{key} {request[GAMES[key].code]} for game {request['game']}, move {request['move_number']}: "
          f"{'turned away here' if said else 'sent on'}.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
