#!/usr/bin/env python3
"""Turn a chess move away here, before it starts its game, when the game could only turn it away.

WHY THIS EXISTS. Every move the router sends on costs a run of the game's
workflow. A move for a game that is over, a move already played, a move on
the other side's turn, or one more move from a player who has sent many this
hour can never be played, so this answers it here, in the game's own words,
and the game never runs for it. The game still checks every move it gets: this
only spares it the ones it would certainly refuse.

WHAT IT READS. 🎲 Move Intake fetches the game's state, `.github/chess/game.json`
from the game's repository, into $RUNNER_TEMP/game.json (`null` when no game
has started, and no file at all when it couldn't be read), and counts the
issues the player opened here in the last hour into $RUNNER_TEMP/recent. It
reads the move from $RUNNER_TEMP/dispatch.json, which the router wrote. A
state can only ever be behind the game, never ahead of it, so this refuses on
the state only what a later state would refuse too: a game already over, a
move already played. A move that looks ahead of the board goes on, for the
game to judge.

It writes `verdict=refuse` or `verdict=dispatch` to $GITHUB_OUTPUT, and on a
refusal the reply to $RUNNER_TEMP/reply.md. Nothing here talks to GitHub.

    python3 -m unittest discover -s intake -p 'test_*.py'
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

LIMIT = 20  # the issues one player may open in an hour; the owner, who plays every move as White, has no limit


def profile(owner: str) -> str:
    return f'https://github.com/{owner}'


def handle(login: str) -> str:
    """A player named without a ping: the @handle as a link to their profile, as the game names them."""
    return f'[@{login}]({profile(login)})'


def numbered(move: int, san: str) -> str:
    """A move as the score sheet writes it, by its number from 1 for White's first: `12. Nf3`, `12... Nf6`."""
    return f'{(move + 1) // 2}. {san}' if move % 2 else f'{(move + 1) // 2}... {san}'


def verdict(request: dict, state: dict | None, recent: int | None, owner: str, owner_id: str,
            known: bool = True) -> str:
    """The refusal for a move the game could only turn away, or "" to send it on. `known` is False when the game's
    state couldn't be read, and `state` None when no game has started."""
    uci, game, move = request['uci'], int(request['game']), int(request['move_number'])
    mine = request['player_id'] == owner_id
    board = f'[the board]({profile(owner)})'
    if not mine and recent is not None and recent > LIMIT:
        return (f"🐢 **Slow down**: you've opened {recent} issues here in the last hour, more than the {LIMIT} the"
                f" board takes from one player, so `{uci}` wasn't played.\nPick your next move from {board} in a"
                ' little while.\n')
    if known:
        number, moves = (state['game'], state['moves']) if state else (1, [])
        if game < number:
            return (f"⌛ **Game {game} is over**, so `{uci}` wasn't played.\nGame {number} is under way on {board}:"
                    ' pick a move there.\n')
        if game == number and move <= len(moves):
            earlier = moves[move - 1]
            by = ('the Arbiter' if earlier.get('arbiter') else
                  'you' if str(earlier.get('player_id')) == request['player_id'] else handle(earlier['player']))
            return (f"⌛ **Too late: move {move} is already on the board**, so `{uci}` wasn't played.\n"
                    f'{numbered(move, earlier["san"])} got there first, played by {by}. Pick a move from {board} as'
                    ' it stands now.\n')
    if move % 2 and not mine:
        return (f"⏳ **It's {handle(owner)}'s turn as White**, so `{uci}` wasn't played.\nGitHub plays Black: once"
                f" White moves, pick Black's reply on {board}.\n")
    if not move % 2 and mine:
        return (f"⏳ **It's GitHub's turn as Black**, so `{uci}` wasn't played.\nBlack's moves are for everyone but"
                ' you. Your turn comes next.\n')
    return ''


def main() -> int:
    env = os.environ
    temp = pathlib.Path(env['RUNNER_TEMP'])
    request = json.loads((temp / 'dispatch.json').read_text(encoding='utf-8'))['inputs']
    found = temp / 'game.json'
    known = found.exists()
    state = json.loads(found.read_text(encoding='utf-8')) if known else None
    counted = temp / 'recent'
    text = counted.read_text(encoding='utf-8').strip() if counted.exists() else ''
    recent = int(text) if text.isdecimal() and text.isascii() else None  # uncounted: no limit is applied
    said = verdict(request, state, recent, env['GITHUB_REPOSITORY_OWNER'], env['OWNER_ID'], known)
    if said:
        (temp / 'reply.md').write_text(said, encoding='utf-8')
    with open(env['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle_:
        handle_.write(f"verdict={'refuse' if said else 'dispatch'}\n")
    print(f"Move {request['uci']} for game {request['game']}, move {request['move_number']}: "
          f"{'turned away here' if said else 'sent on'}.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
