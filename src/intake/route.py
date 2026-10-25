#!/usr/bin/env python3
"""Route one move issue to the game it names, or turn it away.

WHY THIS EXISTS. Every move on the profile is a link that opens an issue here
with the move in its title, and anyone on GitHub can open an issue here with
any title at all. 🎲 Move Intake hands that title to this script and to
nothing else. It arrives through the environment, is matched whole against
the table in `routes.json`, and only what the table's pattern captured goes
any further, so nothing a stranger types can reach a shell, a token, or a
repository the table does not name.

WHAT IT DECIDES, one of three:

    dispatch  a move for a game in the table: start that game's workflow,
              and leave the issue open for the game to rule on
    reject    anything else: reply, and close the issue as not planned
    ignore    an issue of the owner's that is not a move: leave it open

A MOVE SENT AGAIN. ⏳ Move Sweep, or the owner, starts 🎲 Move Intake again
by an issue's number for a move that never reached its game, or an issue
that was never answered. The workflow then reads the issue as it is now into
$RUNNER_TEMP/issue.json, and this reads the title and who opened it from
there, in place of the event, and decides the same way. An issue that is
closed, a pull request, one an app or a bot opened, or one that isn't the
issue asked for is left alone, as `ignore`.

It writes the decision, the issue and who opened it, and for a move the game
it is for, to $GITHUB_OUTPUT, and for a move sent again whether it was
`stranded` and whether it is locked. It writes the dispatch's request body to
$RUNNER_TEMP/dispatch.json, the reply to anything that is not a move to
$RUNNER_TEMP/reply.md, and the labels the issue should carry to
$RUNNER_TEMP/labels.json: `move` and the move's game, or `invalid` for
anything else. The workflow posts them as they are, making a label the first
time it is needed. A move gets no reply here: its 🚀 says it was sent on, and
its game's ruling is the one reply it gets.
Nothing here talks to GitHub, and nothing here prints the title, since a
line in a run's log can be read as a workflow command.

Run its tests from the root of the repository:

    python3 -m unittest discover -s intake -p 'test_*.py'
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

ROUTES = pathlib.Path(__file__).resolve().with_name('routes.json')

# A move's title: the game's name, a colon and a space, then the move written
# the way that game's pattern reads it - `chess: e2e4 · game 1 · move 1`.
TITLE = re.compile(r'(?P<name>[a-z][a-z0-9-]{0,31}): (?P<move>.+)')

# What a row of the table may hold, checked before any title is read.
NAME = re.compile(r'[a-z][a-z0-9-]{0,31}')
REPOSITORY = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}')
WORKFLOW = re.compile(r'[A-Za-z0-9._-]{1,100}\.ya?ml')
REF = re.compile(r'[A-Za-z0-9._-]{1,100}(?:/[A-Za-z0-9._-]{1,100}){0,4}')
FIELD = re.compile(r'[a-z][a-z0-9_]{0,31}')
ROW = ('repository', 'workflow', 'ref', 'pattern')

# Who opened the issue, as GitHub reports it.
LOGIN = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})')
NUMBER = re.compile(r'[1-9][0-9]{0,15}')

# Every value a pattern captures is one short token, whatever the pattern
# allows: a loose pattern in the table can never pass a sentence along.
VALUE = re.compile(r'[A-Za-z0-9_.+#=-]{0,64}')

# The inputs every game's workflow receives beside its own, filled here from
# the issue itself rather than from its title. No pattern may name one.
RESERVED = ('issue', 'player', 'player_id')

# The labels an issue answered here carries. The move form gives `move` as the
# issue opens; the intake gives it again, for a move opened without the form,
# such as through the API, and adds what no form can know: the move's game. An
# issue that is not a move gets `invalid`, the shared taxonomy's own. Every
# name comes from here or from the table, never from the title.
MOVE = {'name': 'move', 'color': '1d76db', 'description': '🎲 A move for one of the games on the profile.'}
INVALID = {'name': 'invalid', 'color': 'e4e669', 'description': "This doesn't seem right"}
GAMES = {  # each game's sign and name as the profile shows them, and its label's colour
    'chess': ('♟️', 'Chess', '5319e7'),
    'checkers': ('🏁', 'Checkers', 'd93f0b'),
    'pentago': ('🌀', 'Pentago', '0e8a16'),
    'tictac': ('❌', 'Tic-Tac', 'fbca04'),
}


class TableError(ValueError):
    """`routes.json` says something the intake will not act on."""


def load(path: pathlib.Path = ROUTES) -> dict[str, dict]:
    """The table, every row checked, so a mistake in it stops the run before any title is read."""
    try:
        table = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise TableError(f'{path.name} cannot be read: {exc}') from None
    if not isinstance(table, dict):
        raise TableError(f'{path.name} must be one object, keyed by game.')
    routes = {}
    for name, row in table.items():
        if name == '//':
            continue  # the table's own description, which the folder log reads
        where = f'{path.name}, {name!r}'
        if not NAME.fullmatch(name):
            raise TableError(f'{where}: a game is named in lower case letters, digits and hyphens.')
        if not isinstance(row, dict) or sorted(row) != sorted(ROW):
            raise TableError(f'{where}: a game needs exactly {", ".join(ROW)}.')
        if not all(isinstance(row[key], str) for key in ROW):
            raise TableError(f'{where}: every value is a string.')
        if not REPOSITORY.fullmatch(row['repository']) or row['repository'].endswith(('/.', '/..')):
            raise TableError(f'{where}: {row["repository"]!r} is not an owner/repository.')
        if not WORKFLOW.fullmatch(row['workflow']):
            raise TableError(f'{where}: {row["workflow"]!r} is not a workflow file name.')
        if not REF.fullmatch(row['ref']) or '..' in row['ref']:
            raise TableError(f'{where}: {row["ref"]!r} is not a branch or a tag.')
        try:
            pattern = re.compile(row['pattern'])
        except re.error as exc:
            raise TableError(f'{where}: its pattern does not compile: {exc}.') from None
        if not pattern.groupindex:
            raise TableError(f'{where}: its pattern names no group, so a move would carry nothing.')
        for field in pattern.groupindex:
            if not FIELD.fullmatch(field):
                raise TableError(f'{where}: {field!r} cannot be a workflow input.')
            if field in RESERVED:
                raise TableError(f'{where}: its pattern names {field!r}, which the intake fills itself.')
        owner, repo = row['repository'].split('/')
        routes[name] = {'owner': owner, 'repo': repo, 'workflow': row['workflow'],
                        'ref': row['ref'], 'pattern': pattern}
    if not routes:
        raise TableError(f'{path.name} names no game.')
    return routes


def route(title: str, *, player: str, player_id: str, issue: str, owner: str,
          routes: dict[str, dict]) -> dict:
    """What to do with one issue, decided from its title and its author alone."""
    named = TITLE.fullmatch(title.strip())
    game = routes.get(named['name']) if named else None
    played = game['pattern'].fullmatch(named['move']) if game else None
    if played:
        values = {field: value or '' for field, value in played.groupdict().items()}
        if all(VALUE.fullmatch(value) for value in values.values()):
            return {
                'action': 'dispatch',
                'game': named['name'],
                'owner': game['owner'],
                'repo': game['repo'],
                'workflow': game['workflow'],
                'body': {
                    'ref': game['ref'],
                    'inputs': {**values, 'issue': issue, 'player': player, 'player_id': player_id},
                },
            }
    # The owner files their own issues here too: one that is not a move is
    # theirs to keep, not a stranger's to be turned away.
    if player.casefold() == owner.casefold():
        return {'action': 'ignore'}
    return {'action': 'reject'}


def labels(decision: dict) -> list[dict]:
    """The labels the issue should carry, each with the colour and description it is made with when missing."""
    if decision['action'] == 'dispatch':
        game = decision['game']
        sign, title, colour = GAMES.get(game, ('🎲', game, 'ededed'))
        return [MOVE, {'name': f'game: {game}', 'color': colour, 'description': f'{sign} A move for {title}.'}]
    if decision['action'] == 'reject':
        return [INVALID]
    return []


def reply(owner: str) -> str:
    """The comment anything that is not a move is closed with. Fixed text, so a title can never write any of it."""
    profile = f"[@{owner}'s profile](https://github.com/{owner})"
    return (
        "👋 **This isn't a move, so it's closed.**\n"
        f'This repository only takes moves for the games on {profile}. To play, pick a move under'
        ' the board there: its link opens an issue here with the move already in the title. Submit'
        ' it as it opens, without changing the title.\n'
    )


def again(issue: object, asked: str) -> dict | str:
    """A move sent again: its title, who opened it, and the marks it carries, from the issue as GitHub gives it now;
    or, for an issue that is left alone, why."""
    if not isinstance(issue, dict) or str(issue.get('number')) != asked:
        return "isn't the issue asked for"
    if 'pull_request' in issue:
        return 'is a pull request'
    if issue.get('state') != 'open':
        return 'is closed'
    user = issue.get('user')
    if not isinstance(user, dict) or user.get('type') != 'User':
        return 'was opened by an app or a bot'
    login, uid = user.get('login'), user.get('id')
    marks = {label.get('name') for label in issue.get('labels') or [] if isinstance(label, dict)}
    return {
        'title': issue.get('title') if isinstance(issue.get('title'), str) else '',
        'player': login if isinstance(login, str) else '',
        'player_id': str(uid) if type(uid) is int else '',
        'stranded': 'stranded' in marks,
        'locked': issue.get('locked') is True,
    }


def main() -> int:
    env = os.environ
    owner = env.get('GITHUB_REPOSITORY_OWNER', '')
    temp = pathlib.Path(env['RUNNER_TEMP'])
    issue = env.get('ISSUE', '')
    title, player, player_id = env.get('TITLE', ''), env.get('PLAYER', ''), env.get('PLAYER_ID', '')
    sent_again = env.get('SENT_AGAIN') == 'true'
    found: dict | str = {}
    if sent_again and NUMBER.fullmatch(issue):
        try:
            found = again(json.loads((temp / 'issue.json').read_text(encoding='utf-8')), issue)
        except (OSError, ValueError):
            found = "couldn't be read"
        if isinstance(found, str):
            with open(env['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle:
                handle.write('action=ignore\n')
            print(f'Issue #{issue} {found}, so it was left alone.')
            return 0
        title, player, player_id = found['title'], found['player'], found['player_id']
    for name, value, shape in (
        ('GITHUB_REPOSITORY_OWNER', owner, LOGIN),
        ('PLAYER', player, LOGIN),
        ('PLAYER_ID', player_id, NUMBER),
        ('ISSUE', issue, NUMBER),
    ):
        if not shape.fullmatch(value):
            print(f'::error::{name} is missing or malformed, so this issue was not routed.')
            return 1
    try:
        routes = load(ROUTES)
    except TableError as exc:
        print(f'::error file=src/intake/routes.json::{exc}')
        return 1

    decision = route(title, player=player, player_id=player_id, issue=issue, owner=owner, routes=routes)
    outputs = {'action': decision['action'], 'issue': issue, 'player': player, 'player_id': player_id}
    if sent_again:
        outputs.update(again='true', stranded=str(found['stranded']).lower(), locked=str(found['locked']).lower())
    if decision['action'] == 'dispatch':
        outputs.update(game=decision['game'], owner=decision['owner'], repo=decision['repo'],
                       workflow=decision['workflow'])
        (temp / 'dispatch.json').write_text(json.dumps(decision['body']), encoding='utf-8')
    if decision['action'] == 'reject':
        (temp / 'reply.md').write_text(reply(owner), encoding='utf-8')
    if decision['action'] != 'ignore':
        (temp / 'labels.json').write_text(json.dumps(labels(decision), ensure_ascii=False), encoding='utf-8')
    with open(env['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle:
        handle.writelines(f'{key}={value}\n' for key, value in outputs.items())

    target = ''
    if decision['action'] == 'dispatch':
        target = f" to {decision['owner']}/{decision['repo']}, {decision['workflow']}"
    print(f"Issue #{issue} by @{player}{', sent again' if sent_again else ''}: {decision['action']}{target}.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
