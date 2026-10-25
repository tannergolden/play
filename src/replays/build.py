#!/usr/bin/env python3
"""Keep the replays: draw each game a player's own move won, keep each game's newest 25, and post each on its issue.

WHY THIS EXISTS. When a person's own move wins a game on the profile, the
game's engine writes down what every turn did, as
`.github/<game>/games/game-<N>.replay.json` in tannergolden/tannergolden.
🎬 Replays hands those facts to the kit, tannergolden/markdown, whose
`replay` command plays the game again on its own board, by day and by dark.
This script decides what to draw, keeps what was drawn, and words what is
said of it. Nothing it writes comes from an issue, and every field of the
facts it writes into a page or the index is checked here first; the kit
checks every field it draws.

WHAT IT KEEPS, in this folder:

    <game>/game-<N>-day.svg   the replay, by day
    <game>/game-<N>-dark.svg  the replay, by dark
    <game>/game-<N>.json      the facts it was drawn from, so a redraw never needs the profile
    <game>/game-<N>.md        its page: the replay, who won and when, the winning move's issue and the game's record
    index.json                every replay ever made, in the folder or not, so none is ever drawn twice

Each game keeps its newest 25. The 26th takes its game's oldest out of the
folder in the same commit, and the oldest stays in the index and in git's
history, where its comment on the winning move still plays it. The newest 12
of all four games are pictures in the README's gallery, and the rest links.

HOW A RUN GOES, in three steps of 🎬 Replays (.github/workflows/replay.yml):

    plan  finds the won games the index doesn't list; and, on the daily run,
          looks up every account behind a replay still here, each once: a
          winner whose account is gone takes the replay down, and another
          player's has it drawn again, with an empty dial for them
    save  fetches each player's avatar as a grey PGM, has the kit draw what
          the plan names, and writes the folder, the index, the gallery and
          the commit's message; the workflow commits and pushes
    post  fills in the commit that saved each drawing, then, as the Official
          Arbiter, posts each new replay on its winning move's issue, points a
          redrawn one's comment at its new commit, and says on a taken-down
          one's why; the workflow commits the index again

Only GitHub's 404 says an account is gone, as on the profile's Hall of Fame:
any other answer leaves it as it was. Nothing here ever rewrites history. The
GitHub calls, the kit, ImageMagick and git are each behind one small function
(`account`, `draw`, `face`, `commits` and `Arbiter`), which the tests replace.

Run its tests from the root of the repository:

    python3 -m unittest discover -s replays -p 'test_*.py'
"""

from __future__ import annotations

import argparse
import datetime as dt
import functools
import http.client
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[2]
OWNER = 'tannergolden'
PLAY = f'{OWNER}/play'
PROFILE = f'{OWNER}/{OWNER}'
KEEP = 25  # the replays each game keeps in its folder
SHOWN = 12  # the newest replays the gallery shows as pictures: each plays its whole game as the page opens
FALLBACK = 'blackprint'  # the page's theme when it can't be read, which is the print the kit falls back on
EST = dt.timezone(dt.timedelta(hours=-5), 'EST')  # the page tells time in EST, all year
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
START, END = '<!-- replays:start -->', '<!-- replays:end -->'  # the gallery's place in the README
AVATAR = 'https://avatars.githubusercontent.com/u/{uid}?s=96'
FACE = 48  # a face's side in pixels, as the grey PGM the kit draws a player's halftone from
HEAVIEST = 1 << 20  # the most an avatar may weigh, in bytes
NOTE = 'Every replay 🎬 Replays has made, in the order it made them, kept here or not, so none is ever drawn twice.'
FIELDS = ('key', 'game', 'winner', 'by', 'by_id', 'players', 'issue', 'ended', 'theme', 'commit', 'drawn', 'comment',
          'shows', 'gone', 'kept')
SECRETS = ('GH_TOKEN', 'GITHUB_TOKEN', 'MARKDOWN_TOKEN')  # never handed to the kit or to ImageMagick

LOGIN = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})')
MOMENT = re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ')
NOTATION = re.compile(r'[A-Za-z0-9 .+#=-]{1,40}')  # a turn as the score sheet writes it: `8... Nf3#`, `G. e5`
FACTS = re.compile(r'game-([1-9][0-9]{0,8})\.replay\.json')
SHA = re.compile(r'[0-9a-f]{40}')
# The page's theme, as the profile's Markdown workflow hands it to the kit: `theme: blackprint # the page's one theme`.
THEME = re.compile(r'''^[ \t]+theme:[ \t]*(['"]?)([a-z][a-z0-9-]{0,39})\1[ \t]*(?:#.*)?$''', re.M)
MOST = 10 ** 16


@dataclass(frozen=True)
class Game:
    """What the replays know of one game."""

    key: str  # its name in a move's title, and its folder here and in the profile
    name: str  # as the page names it
    sides: tuple[str, str]  # the words for the house's side, then for GitHub's
    reason: str  # how a game of it is won, word for word as its facts say


GAMES = {game.key: game for game in (
    Game('chess', 'Chess', ('White', 'Black'), 'checkmate'),
    Game('checkers', 'Checkers', ('White', 'Black'), 'no move left'),
    Game('pentago', 'Pentago', ('White', 'Black'), 'five in a row'),
    Game('tictac', 'Tic-Tac', ('X', 'O'), 'three boards in a row'),
)}


class GitHubError(RuntimeError):
    """A call to GitHub that did not go through."""


# --- the facts ------------------------------------------------------------------------------------------------------
def count(value: object, low: int = 1, high: int = MOST) -> bool:
    return type(value) is int and low <= value <= high


def problem(facts: object, key: str, number: int) -> str:
    """Why a won game's facts can't be kept here, or "" when they can. The kit checks every field it draws; this
    checks the ones the folder, the index and the page are written from."""
    spec = GAMES[key]
    if not isinstance(facts, dict) or facts.get('replay') != 1:
        return "they are not the facts of a replay, as the profile's engine writes them"
    if facts.get('kind') != key or not count(facts.get('game')) or facts['game'] != number:
        return f'they are not the facts of {spec.name} game {number}'
    if facts.get('winner') not in ('house', 'github'):
        return 'they name no side as the winner'
    if not (isinstance(facts.get('by'), str) and LOGIN.fullmatch(facts['by']) and count(facts.get('by_id'))):
        return 'they name nobody as the winner'
    if facts.get('issue') is not None and not count(facts.get('issue')):
        return "the winning move's issue is not a number"
    if facts.get('reason') != spec.reason:
        return f'a game of {spec.name} is won by {spec.reason}'
    if not (isinstance(facts.get('ended'), str) and MOMENT.fullmatch(facts['ended'])):
        return 'they say no moment the game ended'
    players = facts.get('players')
    if not (isinstance(players, list) and all(isinstance(p, dict) and isinstance(p.get('player'), str)
                                              and LOGIN.fullmatch(p['player']) and count(p.get('player_id'))
                                              for p in players)):
        return "GitHub's players are not each a login and an account"
    plies = facts.get('plies')
    if not (isinstance(plies, list) and plies and all(isinstance(p, dict) for p in plies)):
        return 'they hold no turns'
    if not all(p.get('by_id') is None or count(p.get('by_id')) for p in plies):
        return 'a turn names no account'
    last = plies[-1]
    if not (isinstance(last.get('notation'), str) and NOTATION.fullmatch(last['notation'])):
        return 'the winning move is not written as the score sheet writes it'
    if last.get('side') != facts['winner'] or last.get('by_id') != facts['by_id']:
        return "the last turn is not the winner's own"
    return ''


def players_of(facts: dict) -> list[int]:
    """Every account that played a turn of the game: the winner's, each turn's and each of GitHub's players'."""
    ids = {facts['by_id'], *(p['by_id'] for p in facts['plies'] if p.get('by_id') is not None),
           *(p['player_id'] for p in facts['players'])}
    return sorted(ids)


def won(profile: pathlib.Path) -> tuple[dict[tuple[str, int], dict], list[str]]:
    """Every won game's facts the profile holds, by game and number, and why each file that can't be kept is not."""
    found, passed = {}, []
    for key, spec in GAMES.items():
        folder = profile / '.github' / key / 'games'
        for path in sorted(folder.glob('game-*.replay.json')) if folder.is_dir() else ():
            named = FACTS.fullmatch(path.name)
            if not named:
                continue
            number = int(named[1])
            try:
                facts = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                passed.append(f'{spec.name} game {number}: its facts are not JSON')
                continue
            said = problem(facts, key, number)
            if said:
                passed.append(f'{spec.name} game {number}: {said}')
                continue
            found[key, number] = facts
    return found, passed


def theme_of(profile: pathlib.Path) -> str:
    """The page's theme, as the profile's Markdown workflow hands it to the kit, or blackprint when it can't be read.
    The kit draws a replay in the page's print, and in blackprint when its theme is not a print."""
    try:
        text = (profile / '.github' / 'workflows' / 'markdown.yml').read_text(encoding='utf-8')
    except OSError:
        return FALLBACK
    found = THEME.search(text)
    return found[2] if found else FALLBACK


# --- the index ------------------------------------------------------------------------------------------------------
def dump(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def load(root: pathlib.Path) -> list[dict]:
    """Every replay the index lists, in the order they were made: none before the first."""
    path = root / 'replays' / 'index.json'
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding='utf-8'))['replays']
    for entry in entries:
        if not (isinstance(entry, dict) and set(entry) == set(FIELDS) and entry['key'] in GAMES
                and count(entry['game'])):
            raise ValueError(f'replays/index.json lists a replay it does not hold whole: {entry!r}')
    return entries


def write_index(root: pathlib.Path, entries: list[dict]) -> None:
    folder = root / 'replays'
    folder.mkdir(parents=True, exist_ok=True)
    rows = [{name: entry[name] for name in FIELDS} for entry in entries]
    (folder / 'index.json').write_text(dump({'//': NOTE, 'replays': rows}), encoding='utf-8')


def entry_of(facts: dict, theme: str, gone: list[int]) -> dict:
    """A new replay's row in the index, before its commit and its comment are known."""
    return {'key': facts['kind'], 'game': facts['game'], 'winner': facts['winner'], 'by': facts['by'],
            'by_id': facts['by_id'], 'players': players_of(facts), 'issue': facts.get('issue'),
            'ended': facts['ended'], 'theme': theme, 'commit': None, 'drawn': None, 'comment': None, 'shows': None,
            'gone': gone, 'kept': True}


def name(entry: dict) -> str:
    return f"{GAMES[entry['key']].name} game {entry['game']}"


def newest(entry: dict) -> tuple:
    """How recent a replay is: by the moment its game ended, then by game and number."""
    return entry['ended'], -list(GAMES).index(entry['key']), entry['game']


# --- what a run does ------------------------------------------------------------------------------------------------
def plan(entries: list[dict], found: dict[tuple[str, int], dict], theme: str, lookup=None,
         owner_id: int | None = None) -> dict:
    """What a run does. `fresh` are the won games the index doesn't list, oldest first, but for any older than its
    game's newest 25 and any whose winner's account is known to be gone, which are never drawn. With `lookup`, the
    daily run, every account behind a replay still here is looked up once, the owner's never, as the Hall of Fame
    reads them: `lookup` answers True, False on GitHub's 404, or None for anything else, which leaves the account as
    it was. A replay whose winner's account is gone goes in `down`, and one where only another player's is in
    `redraw`, each with every account of its players found gone. `faces` are the accounts to fetch an avatar for."""
    listed = {(entry['key'], entry['game']) for entry in entries}
    known = {uid for entry in entries for uid in entry['gone']}  # an account found gone once stays gone
    down, redraw = [], []
    if lookup is not None:
        kept = [entry for entry in entries if entry['kept']]
        asked: dict[int, bool | None] = {}
        for entry in kept:
            for uid in entry['players']:
                if uid not in asked and uid not in known and uid != owner_id:
                    asked[uid] = lookup(uid)
        known |= {uid for uid, here in asked.items() if here is False}
        for entry in kept:
            newly = [uid for uid in entry['players'] if uid in known and uid not in entry['gone']]
            if newly:
                gone = sorted({*entry['gone'], *newly})
                (down if entry['by_id'] in newly else redraw).append([entry['key'], entry['game'], gone])
    leaving = {(key, number) for key, number, _ in down}
    fresh = []
    for key in GAMES:
        kept = [entry['game'] for entry in entries
                if entry['key'] == key and entry['kept'] and (key, entry['game']) not in leaving]
        new = [number for (game, number), facts in found.items()
               if game == key and (game, number) not in listed and facts['by_id'] not in known]
        room = sorted(kept + new, reverse=True)[:KEEP]
        fresh += [(found[key, number]['ended'], -list(GAMES).index(key), number, key) for number in new
                  if number in room]
    fresh = [[key, number] for *_, number, key in sorted(fresh)]
    faces = {uid for key, number in fresh for uid in players_of(found[key, number]) if uid not in known}
    for key, number, gone in redraw:
        faces |= {uid for uid in next(e for e in entries if (e['key'], e['game']) == (key, number))['players']
                  if uid not in gone}
    return {'theme': theme, 'fresh': fresh, 'redraw': redraw, 'down': down, 'gone': sorted(known),
            'faces': sorted(faces)}


@dataclass
class Saved:
    """What a save did, for its commit's message."""

    added: list[dict] = field(default_factory=list)
    redrawn: list[dict] = field(default_factory=list)
    down: list[dict] = field(default_factory=list)
    left: list[dict] = field(default_factory=list)  # the oldest, out of the folder to keep each game's newest 25
    failed: list[str] = field(default_factory=list)  # the replays the kit could not draw: tried again next run


def files(folder: pathlib.Path, number: int) -> list[pathlib.Path]:
    """A replay's four files in its game's folder."""
    return [folder / f'game-{number}-day.svg', folder / f'game-{number}-dark.svg', folder / f'game-{number}.json',
            folder / f'game-{number}.md']


def remove(root: pathlib.Path, entry: dict) -> None:
    """Takes a replay's four files out of the folder. Git's history keeps them, and the comment that plays them."""
    folder = root / 'replays' / entry['key']
    for path in files(folder, entry['game']):
        path.unlink(missing_ok=True)
    try:
        folder.rmdir()  # only once its game's last replay has gone
    except OSError:
        pass


def drawn(drawer, facts: pathlib.Path, folder: pathlib.Path, number: int, theme: str, faces: pathlib.Path,
          gone: list[int], scratch: pathlib.Path) -> bool:
    """Has the kit draw a replay into a scratch folder, and moves both files into the game's folder only once both
    are drawn, so a drawing that fails leaves the one before it whole."""
    out = scratch / f'{folder.name}-{number}'
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    if not drawer(facts, out, f'game-{number}', theme, faces, gone):
        return False
    made = [out / f'game-{number}-day.svg', out / f'game-{number}-dark.svg']
    if not all(path.is_file() and path.stat().st_size for path in made):
        return False
    for path in made:
        shutil.move(str(path), str(folder / path.name))
    return True


def save(chosen: dict, root: pathlib.Path, profile: pathlib.Path, drawer, fetch, work: pathlib.Path) -> Saved:
    """Does what the plan says: draws each fresh replay and copies its facts and page beside it, takes down each whose
    winner's account is gone, takes each game's oldest out past its newest 25, draws again each whose other players'
    accounts are gone, and writes every kept replay's page, the index and the gallery. `drawer` is the kit (`draw`),
    `fetch` makes a player's face (`face`), and `work` is the run's own folder, outside the repository."""
    entries = load(root)
    listed = {(entry['key'], entry['game']): entry for entry in entries}
    faces, scratch = work / 'faces', work / 'drawn'
    faces.mkdir(parents=True, exist_ok=True)
    for uid in chosen['faces']:
        fetch(uid, faces)  # a face that can't be had is only initials on the replay
    known, theme, saved = set(chosen['gone']), chosen['theme'], Saved()
    found = won(profile)[0] if chosen['fresh'] else {}
    for key, number in chosen['fresh']:
        facts = found.get((key, number))
        if (key, number) in listed or facts is None:
            continue  # never drawn twice
        folder = root / 'replays' / key
        folder.mkdir(parents=True, exist_ok=True)
        gone = sorted(known & set(players_of(facts)))
        copy = folder / f'game-{number}.json'
        copy.write_text(dump(facts), encoding='utf-8')
        if not drawn(drawer, copy, folder, number, theme, faces, gone, scratch):
            remove(root, {'key': key, 'game': number})
            saved.failed.append(f'{GAMES[key].name} game {number}')
            continue
        entry = entry_of(facts, theme, gone)
        entries.append(entry)
        listed[key, number] = entry
        saved.added.append(entry)
    for key, number, gone in chosen['down']:
        entry = listed.get((key, number))
        if entry and entry['kept']:
            remove(root, entry)
            entry.update(kept=False, gone=gone)
            saved.down.append(entry)
    for key in GAMES:
        kept = sorted((entry for entry in entries if entry['key'] == key and entry['kept']),
                      key=lambda entry: entry['game'], reverse=True)
        for entry in kept[KEEP:]:
            remove(root, entry)
            entry['kept'] = False
            saved.left.append(entry)
    for key, number, gone in chosen['redraw']:
        entry = listed.get((key, number))
        if not (entry and entry['kept']):
            continue
        folder = root / 'replays' / key
        if drawn(drawer, folder / f'game-{number}.json', folder, number, entry['theme'], faces, gone, scratch):
            entry.update(gone=gone, drawn=None)
            saved.redrawn.append(entry)
        else:
            saved.failed.append(f'{GAMES[key].name} game {number}')
    for entry in entries:
        if entry['kept']:
            write_page(root, entry)
    write_index(root, entries)
    write_gallery(root / 'README.md', entries)
    return saved


def due(entry: dict) -> str | None:
    """What a replay's comment still needs, once its drawing's commit is known: `post` it, `point` it at a new
    drawing, or say it is taken `down`; None when nothing, or when there is no issue to say it on."""
    if entry['issue'] is None:
        return None
    if entry['by_id'] in entry['gone']:
        return 'down' if entry['comment'] is not None and entry['shows'] is not None else None
    if entry['drawn'] is None:
        return ('point' if entry['comment'] is not None else 'post') if entry['kept'] else None
    if entry['comment'] is None:
        return 'post'
    return 'point' if entry['shows'] != entry['drawn'] else None


@dataclass
class Posted:
    """What a post did, for the second commit's message."""

    saved: list[dict] = field(default_factory=list)  # the replays whose drawing's commit was filled in
    posted: list[dict] = field(default_factory=list)
    pointed: list[dict] = field(default_factory=list)
    down: list[dict] = field(default_factory=list)
    waiting: list[dict] = field(default_factory=list)  # comments that didn't go through: tried again next run


def post(root: pathlib.Path, history, arbiter, token: bool) -> Posted:
    """Fills in the commit each kept drawing was saved in, from `history` (`commits`), then does what each comment
    still needs through `arbiter` (`Arbiter`), when the Arbiter's `token` was minted. A comment that doesn't go
    through waits for the next run, and one already posted is found by its marker rather than posted twice."""
    entries, done = load(root), Posted()
    for entry in entries:
        if entry['kept'] and entry['drawn'] is None:
            found = history(root, f"replays/{entry['key']}/game-{entry['game']}-day.svg")
            if found:
                entry['drawn'] = found[0]
                entry['commit'] = entry['commit'] or found[-1]
                done.saved.append(entry)
    for entry in entries:
        need = due(entry)
        if need is None or (need != 'down' and entry['drawn'] is None):
            continue
        if not token:
            done.waiting.append(entry)
            continue
        try:
            if need == 'down':
                arbiter.edit(entry['issue'], entry['comment'], taken_down(entry))
                entry['shows'] = None
                done.down.append(entry)
                continue
            said = comment(entry, entry['drawn'])
            if need == 'post':
                found = arbiter.find(entry['issue'], marker(entry))
                if found is None:
                    entry['comment'] = arbiter.say(entry['issue'], said)
                else:
                    arbiter.edit(entry['issue'], found, said)
                    entry['comment'] = found
            else:
                arbiter.edit(entry['issue'], entry['comment'], said)
            entry['shows'] = entry['drawn']
            (done.posted if need == 'post' else done.pointed).append(entry)
        except GitHubError as exc:
            print(f'{name(entry)}: its comment did not go through ({exc}); the next run tries again.')
            done.waiting.append(entry)
    write_index(root, entries)
    return done


# --- what is written ------------------------------------------------------------------------------------------------
def handle(login: str) -> str:
    """A player named without a ping, as the intake names them: the @handle as a link to their profile."""
    return f'[@{login}](https://github.com/{login})'


def date(stamp: str) -> str:
    """A moment from the facts as the page writes a day with its year, in the page's time: `21 Oct 2026`."""
    local = dt.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).astimezone(EST)
    return f'{local.day} {MONTHS[local.month - 1]} {local.year}'


def won_as(key: str, winner: str) -> str:
    """The side a replay's winner played: `as White` for the house, `for GitHub, as Black` for anyone else."""
    house, github = GAMES[key].sides
    return f'as {house}' if winner == 'house' else f'for GitHub, as {github}'


def page(facts: dict) -> str:
    """A replay's page: the replay, by day or by dark as the reader's own setting is, who won which game and when,
    the winning move with its issue, and the game's record in the profile."""
    spec, number, key = GAMES[facts['kind']], facts['game'], facts['kind']
    record = f'https://github.com/{PROFILE}/tree/HEAD/.github/{key}/games'
    issue = f", from [its issue](https://github.com/{PLAY}/issues/{facts['issue']})" if facts.get('issue') else ''
    return (f"<!--\ntitle: '🎬 {spec.name.upper()}, GAME {number}'\n"
            f"description: 'The replay of game {number} of {spec.name}, won by @{facts['by']} on"
            f" {date(facts['ended'])}.'\n-->\n\n"
            '<div align="center">\n\n'
            f'# 🎬 {spec.name.upper()}, GAME {number}\n\n'
            f"**{handle(facts['by'])} won game {number} of {spec.name} {won_as(key, facts['winner'])}, on"
            f" {date(facts['ended'])}.**\n\n"
            '_Every move played again on the board, then the win, on a loop._\n\n'
            '<picture>\n'
            f'  <source media="(prefers-color-scheme: dark)" srcset="game-{number}-dark.svg">\n'
            f'  <img alt="The replay of game {number} of {spec.name}, won by @{facts["by"]}"'
            f' src="game-{number}-day.svg">\n'
            '</picture>\n\n'
            '</div>\n\n'
            '---\n\n'
            f"- **The winning move**: `{facts['plies'][-1]['notation']}`, {spec.reason}{issue}.\n"
            f"- **The game's record**: [every finished game of {spec.name}]({record}), on the profile.\n"
            f"- **The other replays**: [the gallery](../../README.md#-replays), with each game's newest {KEEP}.\n"
            f'- **The board**: [the profile](https://github.com/{OWNER}), where the next game is played.\n')


def write_page(root: pathlib.Path, entry: dict) -> None:
    """A kept replay's page, written again from the facts beside it, so a change to the page reaches every one."""
    folder = root / 'replays' / entry['key']
    try:
        facts = json.loads((folder / f"game-{entry['game']}.json").read_text(encoding='utf-8'))
    except (OSError, ValueError):
        print(f"::warning::{name(entry)}'s facts are missing here, so its page was left as it was.")
        return
    if problem(facts, entry['key'], entry['game']):
        print(f"::warning::{name(entry)}'s facts here can't be read, so its page was left as it was.")
        return
    (folder / f"game-{entry['game']}.md").write_text(page(facts), encoding='utf-8')


def picture(source: str, alt: str, width: str = '') -> str:
    """A replay as a picture: the dark file for a reader whose setting is dark, the day file for everyone else."""
    size = f' width="{width}"' if width else ''
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{source}-dark.svg">'
            f'<img alt="{alt}" src="{source}-day.svg"{size}></picture>')


def gallery(entries: list[dict]) -> str:
    """The README's gallery: the newest replays of all four games as pictures, two to a row, each a link to its page,
    then every other replay still here as a link, by game, newest first."""
    kept = sorted((entry for entry in entries if entry['kept']), key=newest, reverse=True)
    if not kept:
        return "_No game has been won by a player's own move yet, so there is no replay to show._"
    lines = ['<table>']
    for row in range(0, min(len(kept), SHOWN), 2):
        lines.append('<tr>')
        for entry in kept[row:min(row + 2, SHOWN)]:
            source = f"replays/{entry['key']}/game-{entry['game']}"
            alt = f"The replay of game {entry['game']} of {GAMES[entry['key']].name}, won by @{entry['by']}"
            lines += ['<td align="center" width="50%">',
                      f'<a href="{source}.md">{picture(source, alt, "404")}</a><br>',
                      f"<sub><b>{GAMES[entry['key']].name}, game {entry['game']}</b>: @{entry['by']}"
                      f"{'' if entry['winner'] == 'house' else ' for GitHub'}, {date(entry['ended'])}</sub>",
                      '</td>']
        lines.append('</tr>')
    lines.append('</table>')
    rest = kept[SHOWN:]
    if rest:
        lines += ['', '**Every other replay here**, newest first:', '']
        for key, spec in GAMES.items():
            mine = sorted((entry for entry in rest if entry['key'] == key), key=lambda entry: entry['game'],
                          reverse=True)
            if mine:
                links = ', '.join(f"[game {entry['game']}](replays/{key}/game-{entry['game']}.md)" for entry in mine)
                lines.append(f'- **{spec.name}**: {links}')
    return '\n'.join(lines)


def write_gallery(readme: pathlib.Path, entries: list[dict]) -> None:
    """The gallery, written between its markers in the README, and nothing else of the README touched."""
    text = readme.read_text(encoding='utf-8')
    start, end = text.find(START), text.find(END)
    if start < 0 or end < start:
        raise ValueError(f'{readme.name} has no {START} and {END} for the gallery to go between.')
    readme.write_text(f'{text[:start + len(START)]}\n\n{gallery(entries)}\n\n{text[end:]}', encoding='utf-8')


def marker(entry: dict) -> str:
    """The line, unseen on GitHub, that a replay's comment is found by: one per replay."""
    return f"<!-- replay: {entry['key']} game {entry['game']} -->"


def comment(entry: dict, sha: str) -> str:
    """The Arbiter's comment on the winning move: the replay, its pictures pinned to the commit that holds them, so
    it plays there after the replay has left the folder, and a link to its page at the same commit."""
    spec, number = GAMES[entry['key']], entry['game']
    source = f"https://raw.githubusercontent.com/{PLAY}/{sha}/replays/{entry['key']}/game-{number}"
    link = f"https://github.com/{PLAY}/blob/{sha}/replays/{entry['key']}/game-{number}.md"
    whose = f"{handle(entry['by'])}'s win{'' if entry['winner'] == 'house' else ' for GitHub'}"
    return (f'{marker(entry)}\n'
            f'🎬 **The replay of game {number} of {spec.name}**: every move of {whose}, played again on the'
            ' board.\n\n'
            f'<a href="{link}">{picture(source, f"The replay of game {number} of {spec.name}")}</a>\n\n'
            f"[Its page]({link}) names the winning move, and links the game's record.\n")


def taken_down(entry: dict) -> str:
    """What the comment says once the account that won the game is gone: one line, and the replay gone from it."""
    return (f'{marker(entry)}\n🎬 **The replay of game {entry["game"]} of {GAMES[entry["key"]].name} was taken'
            " down**, because the account that won it was deleted.\n")


def joined(parts: list[str]) -> str:
    return parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"


def saved_message(saved: Saved, run_url: str = '') -> str:
    """The save's commit message: a Conventional Commit, as the profile's bot writes them, and never naming an issue
    or pinging a player."""
    kinds = [(saved.added, 'add'), (saved.redrawn, 'redraw'), (saved.down, 'take down')]
    kinds = [(entries, verb) for entries, verb in kinds if entries]
    if sum(len(entries) for entries, _ in kinds) == 1:
        entries, verb = kinds[0]
        subject = f'{verb} the replay of {name(entries[0])}'
    elif kinds:
        parts = [f'{verb} {len(entries)}' for entries, verb in kinds]
        parts[0] += ' replay' if len(kinds[0][0]) == 1 else ' replays'
        subject = joined(parts)
    else:
        subject = 'bring the replays and the gallery up to date'
    lines = [f"{name(entry)}: won by {entry['by']} {won_as(entry['key'], entry['winner'])}." for entry in saved.added]
    lines += [f'{name(entry)}: drawn again, with every account deleted since as an empty dial.'
              for entry in saved.redrawn]
    lines += [f'{name(entry)}: taken down, since the account that won it was deleted.' for entry in saved.down]
    lines += [f'{name(entry)}: out of the folder, as each game keeps its newest {KEEP}.' for entry in saved.left]
    body = '\n'.join(lines)
    run = f'Run: {run_url}' if run_url else ''
    return '\n\n'.join(part for part in (f'chore(replays): 🎬 {subject}', body, run) if part) + '\n'


def recorded_message(done: Posted, run_url: str = '') -> str:
    """The second commit's message: where each replay was saved, and what became of its comment, a line each."""
    touched = list({id(entry): entry for entry in (*done.saved, *done.posted, *done.pointed, *done.down,
                                                   *done.waiting)}.values())
    subject = (f'record the replay of {name(touched[0])}' if len(touched) == 1 else
               f'record {len(touched)} replays' if touched else 'record the replays')
    lines = []
    for entry in touched:
        said = [f"saved in {entry['drawn'][:12]}"] if any(entry is e for e in done.saved) else []
        said += [f"posted as comment {entry['comment']}"] if any(entry is e for e in done.posted) else []
        said += ([f"comment {entry['comment']} now plays {entry['shows'][:12]}"]
                 if any(entry is e for e in done.pointed) else [])
        said += ([f"comment {entry['comment']} now says it was taken down"]
                 if any(entry is e for e in done.down) else [])
        said += ['its comment waits for the next run'] if any(entry is e for e in done.waiting) else []
        lines.append(f'{name(entry)}: {joined(said)}.')
    run = f'Run: {run_url}' if run_url else ''
    return '\n\n'.join(part for part in (f'chore(replays): 🔖 {subject}', '\n'.join(lines), run) if part) + '\n'


# --- the outside world, each behind one small function ---------------------------------------------------------------
def account(uid: int) -> bool | None:
    """Whether GitHub still has the account with this ID: True, False only on its 404, and None on any other answer,
    refused, limited or failing, which leaves the account as it was."""
    try:
        done = subprocess.run(['gh', 'api', f'/user/{uid}', '--silent'], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode == 0:
        return True
    return False if 'HTTP 404' in done.stderr else None


def image(data: bytes) -> str | None:
    """The coder ImageMagick reads an avatar with, named rather than guessed from what the file says it is."""
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    return None


def face(uid: int, faces: pathlib.Path) -> bool:
    """One player's avatar as the kit draws their portrait from it: a 48 by 48 grey PGM, `<uid>.pgm` in `faces`.
    False when it can't be had, and the player is drawn by their initials: never a failed run."""
    target = faces / f'{uid}.pgm'
    if target.is_file():
        return True
    try:
        with urllib.request.urlopen(AVATAR.format(uid=uid), timeout=20) as answer:
            data = answer.read(HEAVIEST + 1)
    except (OSError, ValueError, http.client.HTTPException):
        return False
    coder, tool = image(data), shutil.which('magick') or shutil.which('convert')
    if len(data) > HEAVIEST or coder is None or tool is None:
        return False
    source = faces / f'{uid}.avatar'
    source.write_bytes(data)
    size = f'{FACE}x{FACE}'
    try:
        done = subprocess.run([tool, f'{coder}:{source}[0]', '-background', 'white', '-alpha', 'remove', '-alpha',
                               'off', '-resize', f'{size}^', '-gravity', 'center', '-extent', size, '-colorspace',
                               'Gray', '-depth', '8', f'pgm:{target}'], capture_output=True, timeout=60, env=quiet())
        made = done.returncode == 0 and target.read_bytes().startswith(b'P5')
    except (OSError, subprocess.SubprocessError):
        made = False
    finally:
        source.unlink(missing_ok=True)
    if not made:
        target.unlink(missing_ok=True)
    return made


def quiet() -> dict:
    """The environment a program gets from here: this run's, without a token in it."""
    return {key: value for key, value in os.environ.items() if key not in SECRETS}


def draw(kit: pathlib.Path, facts: pathlib.Path, out: pathlib.Path, name_: str, theme: str, faces: pathlib.Path,
         gone: list[int]) -> bool:
    """One replay drawn by the kit, `<name>-day.svg` and `<name>-dark.svg` in `out`: True once both are."""
    command = [sys.executable, str(kit), 'replay', str(facts), '--out', str(out), '--name', name_, '--tone', theme]
    if faces.is_dir():
        command += ['--faces', str(faces)]
    if gone:
        command += ['--gone', ','.join(str(uid) for uid in gone)]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=600, env=quiet())
    except (OSError, subprocess.SubprocessError) as exc:
        print(f'::error::The kit could not be run for {name_}: {type(exc).__name__}.')
        return False
    if done.returncode != 0:
        print(f'::error::The kit could not draw {facts.parent.name} {name_}: it stopped with {done.returncode}.')
        for line in (done.stderr or done.stdout).strip().splitlines()[-5:]:
            print(f'  kit: {line}')
        return False
    return True


def commits(root: pathlib.Path, path: str) -> list[str]:
    """Every commit that touched a file, newest first, as far back as the checkout's history goes: in a shallow one,
    a file not touched since ends at the commit checked out, which holds it all the same."""
    try:
        done = subprocess.run(['git', 'log', '--format=%H', '--', path], cwd=root, capture_output=True, text=True,
                              timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    return [line for line in done.stdout.split() if SHA.fullmatch(line)] if done.returncode == 0 else []


def api(*args: str, body: dict | None = None) -> str:
    """`gh api` with the token in GH_TOKEN: what it printed, or GitHubError when GitHub said no."""
    command = ['gh', 'api', *args, *(['--input', '-'] if body is not None else [])]
    try:
        done = subprocess.run(command, input=None if body is None else json.dumps(body), capture_output=True,
                              text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitHubError(type(exc).__name__) from None
    if done.returncode != 0:
        said = done.stderr.strip().splitlines()
        raise GitHubError(said[-1] if said else f'gh stopped with {done.returncode}')
    return done.stdout


class Arbiter:
    """The Official Arbiter on play's issues, through `gh api` and the App's token. As the games' Arbiter does, it
    unlocks a locked issue to speak when it must, locks it again, and locks the issue it posts on."""

    def find(self, issue: int, mark: str) -> int | None:
        """The Arbiter's comment on an issue that carries `mark`, or None when there is none."""
        out = api(f'repos/{PLAY}/issues/{issue}/comments', '--paginate', '--jq',
                  f'.[] | select(.user.type == "Bot" and ((.body // "") | contains({json.dumps(mark)}))) | .id')
        ids = [int(line) for line in out.split() if line.isdecimal()]
        return ids[0] if ids else None

    def say(self, issue: int, text: str) -> int:
        """Posts a comment on an issue, and gives its ID back."""
        def once() -> int:
            said = api('--method', 'POST', f'repos/{PLAY}/issues/{issue}/comments', '--jq', '.id',
                       body={'body': text}).strip()
            if not said.isdecimal():
                raise GitHubError('no comment ID came back')
            return int(said)

        posted = self.unlocked(issue, once)
        try:
            locked = api(f'repos/{PLAY}/issues/{issue}', '--jq', '.locked').strip() == 'true'
        except GitHubError:
            locked = False
        if not locked:
            self.lock(issue)
        return posted

    def edit(self, issue: int, comment_id: int, text: str) -> None:
        """Rewrites one of the Arbiter's comments."""
        self.unlocked(issue, lambda: api('--method', 'PATCH', f'repos/{PLAY}/issues/comments/{comment_id}',
                                         '--silent', body={'body': text}))

    @staticmethod
    def lock(issue: int) -> None:
        """Locks a move's issue, so nobody but the owner and the Arbiter writes there again."""
        try:
            api('--method', 'PUT', f'repos/{PLAY}/issues/{issue}/lock', '--silent', body={'lock_reason': 'resolved'})
        except GitHubError:
            print(f'::warning::#{issue} was left unlocked.')

    def unlocked(self, issue: int, act):
        """What `act` gives back, done on the issue as it is, or else unlocked for it and locked again."""
        try:
            return act()
        except GitHubError:
            pass  # a locked issue, perhaps: unlocked to speak, and locked again
        api('--method', 'DELETE', f'repos/{PLAY}/issues/{issue}/lock', '--silent')
        try:
            return act()
        finally:
            self.lock(issue)


# --- the run --------------------------------------------------------------------------------------------------------
def output(**values: object) -> None:
    """Step outputs, for the workflow's next steps."""
    path = os.environ.get('GITHUB_OUTPUT')
    if path:
        with open(path, 'a', encoding='utf-8') as handle_:
            handle_.writelines(f'{key}={value}\n' for key, value in values.items())


def flag(value: bool) -> str:
    return 'true' if value else 'false'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Draw, keep and post the replays of the games won on the profile.')
    parser.add_argument('step', choices=('plan', 'save', 'post'), help="the run's step: see this script's docstring")
    parser.add_argument('--profile', type=pathlib.Path, help="the profile's checkout: the facts and the page's theme")
    parser.add_argument('--kit', type=pathlib.Path, help="the kit's command line, its src/markdown-kit.py")
    parser.add_argument('--root', type=pathlib.Path, default=ROOT, help='the play repository (default: this one)')
    args = parser.parse_args(argv)
    env = os.environ
    work = pathlib.Path(env.get('RUNNER_TEMP') or tempfile.gettempdir()) / 'replays'
    work.mkdir(parents=True, exist_ok=True)
    if args.step in ('plan', 'save') and args.profile is None:
        parser.error(f'{args.step} reads the profile: name its checkout with --profile')

    if args.step == 'plan':
        found, passed = won(args.profile)
        for said in passed:
            print(f'::warning::{said}, so no replay was made of it.')
        accounts = env.get('ACCOUNTS') == 'true'
        owner_id = int(env['OWNER_ID']) if env.get('OWNER_ID', '').isdecimal() else None
        chosen = plan(load(args.root), found, theme_of(args.profile), account if accounts else None, owner_id)
        (work / 'plan.json').write_text(dump(chosen), encoding='utf-8')
        output(draw=flag(chosen['fresh'] or chosen['redraw']))
        print(f"{len(chosen['fresh'])} to draw in {chosen['theme']}, {len(chosen['redraw'])} to draw again and"
              f" {len(chosen['down'])} to take down; the accounts were {'' if accounts else 'not '}looked up.")
        return 0

    if args.step == 'save':
        if args.kit is None:
            parser.error("save draws with the kit: name its src/markdown-kit.py with --kit")
        chosen = json.loads((work / 'plan.json').read_text(encoding='utf-8'))
        saved = save(chosen, args.root, args.profile, functools.partial(draw, args.kit), face, work)
        (work / 'commit.txt').write_text(saved_message(saved, env.get('RUN_URL', '')), encoding='utf-8')
        entries = load(args.root)
        output(failed=len(saved.failed),
               record=flag(any(due(entry) or (entry['kept'] and entry['drawn'] is None) for entry in entries)),
               comment=flag(any(due(entry) for entry in entries)))
        for said in saved.failed:
            print(f'::error::{said} could not be drawn, so it waits for the next run.')
        print(f'{len(saved.added)} drawn, {len(saved.redrawn)} drawn again, {len(saved.down)} taken down and'
              f' {len(saved.left)} out of the folder.')
        return 0

    done = post(args.root, commits, Arbiter(), bool(env.get('GH_TOKEN')))
    (work / 'record.txt').write_text(recorded_message(done, env.get('RUN_URL', '')), encoding='utf-8')
    if done.waiting and not env.get('GH_TOKEN'):
        print(f"::warning::The Arbiter's token wasn't minted, so {len(done.waiting)} comments wait for the next run.")
    elif done.waiting:
        print(f'::warning::{len(done.waiting)} comments did not go through, and wait for the next run.')
    print(f'{len(done.saved)} commits filled in, {len(done.posted)} posted, {len(done.pointed)} pointed at a new'
          f' drawing and {len(done.down)} taken down.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
