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
its state, the keys a played turn is kept under, who opens it, and the words
for each player's side, which never change: the house, @tannergolden, plays
X in Tic-Tac and White in Pentago, Checkers and Chess, and GitHub plays O, or
Black. The house opens Chess, as White. GitHub opens Checkers, as Black,
since Black moves first in American checkers. Tic-Tac and Pentago open under
the Ghost Rule, which takes the first move's edge from both sides: once a
fresh board's start has come, the Arbiter draws the side that places the
first ghost, which the game's state records as `places`; that side places a
ghost, or in Pentago sets one, and then the other side does; and as the
second goes down, the Arbiter draws the side that makes the first move, which
the state records as `opens`. A move's number counts every turn, the ghosts
included, so move 3 is the first move, and the score sheet writes the ghosts
on a row of their own, `G. e5` and `G... b8`, and numbers the moves among the
moves alone. Why those two open so is in the amendment to
docs/adrs/ADR-0001-Four-Games-One-Arbiter.md.

WHAT IT READS. 🎲 Move Intake names the game in $GAME, fetches its state,
`.github/<game>/game.json` from the game's repository, into
$RUNNER_TEMP/game.json (`null` when no game has started, and no file at all
when it couldn't be read), and counts the issues the player opened here in
the last hour, whatever the game, into $RUNNER_TEMP/recent. It reads the move
from $RUNNER_TEMP/dispatch.json, which the router wrote. A state can only ever
be behind the game, never ahead of it, so this refuses on the state only what
a later state would refuse too: a game already over, a move already played, a
game that opens later. A move that looks ahead of the board goes on, for the
game to judge, and so does every move whose side it can't tell: in Tic-Tac
and Pentago, a ghost until the state shows the side drawn to place the first,
which a first game not yet started and a fresh board don't, and a move until
it shows the side drawn to open.

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
GHOSTS = 2  # under the Ghost Rule, the turns before the first move: a ghost from each side
EST = dt.timezone(dt.timedelta(hours=-5), 'EST')  # the page tells time in EST, all year
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
LOGIN = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})')


@dataclass(frozen=True)
class Game:
    """What the check knows of one game."""

    key: str  # the game's name in a move's title, its row in routes.json, and its folder in the game's repository
    code: str  # the input that carries the move, and the key a played turn keeps it under in the state
    shown: str  # the key a played turn's text notation is kept under in the state
    sides: tuple[str, str]  # the words for the house's side, then for GitHub's: the same in every game, whoever opens
    opens: str | None  # who opens every game, the house or GitHub, or None where the Ghost Rule has the Arbiter draw it
    ghost: str | None = None  # under the Ghost Rule, what a side does with its ghost: `place` it, or `set` it
    spot: str | None = None  # and what a ghost stands on: a `square`, or a `hole`

    @property
    def state(self) -> str:
        return STATE.format(key=self.key)


GAMES = {game.key: game for game in (
    Game('tictac', 'move', 'shown', ('X', 'O'), None, 'place', 'square'),
    Game('pentago', 'move', 'shown', ('White', 'Black'), None, 'set', 'hole'),
    Game('checkers', 'move', 'shown', ('White', 'Black'), 'github'),
    Game('chess', 'uci', 'san', ('White', 'Black'), 'house'),
)}


@dataclass(frozen=True)
class Board:
    """The game on the board, as its state says."""

    number: int
    turns: list  # every turn played, in order: under the Ghost Rule its ghosts, then its moves
    started: dt.datetime | None  # when it opens, or opened
    places: str | None  # under the Ghost Rule, the side the Arbiter drew to place the first ghost, once it has
    opens: str | None  # under the Ghost Rule, the side it drew to make the first move, once both ghosts are down


def profile(owner: str) -> str:
    return f'https://github.com/{owner}'


def handle(login: str) -> str:
    """A player named without a ping: the @handle as a link to their profile, as the game names them."""
    return f'[@{login}]({profile(login)})'


def other(side: str) -> str:
    """The other side of a game."""
    return 'github' if side == 'house' else 'house'


def numbered(ply: int, shown: str) -> str:
    """A move as the score sheet writes it, by its number from 1 for the opener's first: `12. Nf3`, `12... Nf6`."""
    return f'{(ply + 1) // 2}. {shown}' if ply % 2 else f'{(ply + 1) // 2}... {shown}'


def turn_named(spec: Game, turn: int, shown: str) -> str:
    """A turn as the score sheet writes it, counting every turn from 1: under the Ghost Rule a ghost on the ghosts' own
    row, `G. e5` and `G... b8`, and a move by its number among the moves alone, so turn 3 is `1. Xd4`."""
    if spec.ghost:
        if turn <= GHOSTS:
            return f'G. {shown}' if turn == 1 else f'G... {shown}'
        turn -= GHOSTS
    return numbered(turn, shown)


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


def board(spec: Game, state: object) -> Board | None:
    """The game a state holds: the first game, still to come, when none has started, and None for a state that isn't
    shaped as a game's, which is judged as one that couldn't be read. Under the Ghost Rule a game holds two ghosts at
    most, and moves only once both are down; and a side the Arbiter drew is taken only once the state shows it, the
    opener only with the second ghost."""
    if state is None:
        return Board(1, [], None, None, None)
    if not isinstance(state, dict):
        return None
    number, moves = state.get('game'), state.get('moves')
    ghosts = state.get('ghosts', []) if spec.ghost else []
    if type(number) is not int or number < 1 or not isinstance(moves, list) or not isinstance(ghosts, list):
        return None
    if not all(isinstance(turn, dict) for turn in (*ghosts, *moves)):
        return None
    if len(ghosts) > GHOSTS or (spec.ghost and moves and len(ghosts) < GHOSTS):
        return None
    places, opens = (state.get('places'), state.get('opens')) if spec.ghost else (None, None)
    return Board(number, [*ghosts, *moves], when(state.get('started')), places if places in SIDES else None,
                 opens if opens in SIDES and len(ghosts) == GHOSTS else None)


def whose(spec: Game, on: Board | None, turn: int) -> str | None:
    """Whose turn a turn is, counting from 1, or None when it can't be told. The opener has the odd moves and the other
    side the even ones: the house opens every game of Chess and GitHub every game of Checkers, whatever the state
    says. Under the Ghost Rule the first ghost is the side's the Arbiter drew to place it and the second the other
    side's, and the moves after them start with the side it drew to open, so each is known only once the state of the
    game on the board, `on`, shows that draw."""
    first = spec.opens
    if spec.ghost:
        if on is None:
            return None
        if turn <= GHOSTS:
            if on.places is None:
                return None
            return on.places if turn == 1 else other(on.places)
        first, turn = on.opens, turn - GHOSTS
    if first is None:
        return None
    return first if turn % 2 else other(first)


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
    on = board(spec, state) if known else None
    if on:
        moment = now or dt.datetime.now(dt.timezone.utc)
        if not on.turns and on.number > 1 and on.started and on.started > moment and game <= on.number:
            # The last game's winning board is on show, and nothing can be played until the next game opens.
            return (f"⏳ **Game {on.number} opens {day(on.started)}**, so `{code}` wasn't played.\nGame"
                    f" {on.number - 1}'s final board stays up until then: pick a move from {link} once game"
                    f' {on.number} is on it.\n')
        if game < on.number:
            return (f"⌛ **Game {game} is over**, so `{code}` wasn't played.\nGame {on.number} is under way on"
                    f' {link}: pick a move there.\n')
        if game == on.number and ply <= len(on.turns):
            earlier = on.turns[ply - 1]
            shown, player = earlier.get(spec.shown), earlier.get('player')
            by = ('the Arbiter' if earlier.get('arbiter') else
                  'you' if str(earlier.get('player_id')) == request['player_id'] else
                  handle(player) if isinstance(player, str) and LOGIN.fullmatch(player) else '')
            if not (isinstance(shown, str) and shown and by):
                return ''  # a turn on record that can't be named: the game says what became of this one
            return (f"⌛ **Too late: move {ply} is already on the board**, so `{code}` wasn't played.\n"
                    f'{turn_named(spec, ply, shown)} got there first, played by {by}. Pick a move from {link} as it'
                    ' stands now.\n')
    # Whose turn it is, where the state can tell (see `whose`): a ghost on the other side's turn is told whose ghost
    # is due, and a move whose move it is. Each side is named in its own words, whoever opened.
    side = whose(spec, on if on and game == on.number else None, ply)
    if side is None:
        return ''
    if spec.ghost and ply <= GHOSTS:
        if side == 'house' and not mine:
            return (f"⏳ **It's {handle(owner)}'s turn to {spec.ghost} a ghost**, so `{code}` wasn't played.\nOnce"
                    f" {handle(owner)}'s ghost is down, pick a {spec.spot} for GitHub's on {link}.\n")
        if side == 'github' and mine:
            return (f"⏳ **It's GitHub's turn to {spec.ghost} a ghost**, so `{code}` wasn't played.\nGitHub's ghost is"
                    ' for everyone but you. Your turn comes next.\n')
        return ''
    house, github = spec.sides
    if side == 'house' and not mine:
        return (f"⏳ **It's {handle(owner)}'s turn as {house}**, so `{code}` wasn't played.\nGitHub plays {github}:"
                f" once {house} moves, pick {github}'s reply on {link}.\n")
    if side == 'github' and mine:
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
