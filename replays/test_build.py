#!/usr/bin/env python3
"""Tests for the replays: what is drawn, what is kept, what is said, and what an account that is gone takes down.

WHY THIS EXISTS. A replay is drawn once and kept for good: drawn twice, its
winning move's issue would carry two of the Arbiter's comments; taken out of
the folder wrongly, a page the profile links would be gone; and an account
judged gone on a bad minute would take a player's win off GitHub. So each of
those is pinned here: which facts are new, and that a replay is never drawn
twice; each game's newest 25, and the oldest leaving in the same commit; the
index; the gallery with none, one, twelve and more; the comment and its
pictures pinned to their commit; and what the daily look at the accounts
decides, when only GitHub's 404 says an account is gone.

GitHub, the kit and ImageMagick are each replaced by a stand-in, but for the
last test, which has the real kit draw every sample game when it is checked
out beside this repository, and is skipped when it is not. Nothing here reads
or writes outside a throwaway folder. Run it from the root of the repository:

    python3 -m unittest discover -s replays -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import functools
import io
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from unittest import mock

import build

HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures'
KIT = pathlib.Path(os.environ.get('MARKDOWN_KIT', pathlib.Path(__file__).resolve().parents[2] / 'markdown' / 'src'
                                  / 'markdown-kit.py'))  # the kit checked out beside this repository
OWNER_ID, OCTOCAT, HUBOT, MONALISA = 24684994, 583231, 480938, 2154
README = '# Play\n\nAbove.\n\n## 🎬 Replays\n\n<!-- replays:start -->\n<!-- replays:end -->\n\nBelow.\n'
MARKDOWN = "    with:\n      mode: profile\n      theme: {theme} # the page's one theme\n"


def facts(key: str = 'pentago', game: int = 3, winner: str = 'github', by: str = 'octocat', by_id: int = OCTOCAT,
          issue: int | None = 115, ended: str = '2026-10-21T16:00:00Z',
          others: tuple = ((MONALISA, 'monalisa'),)) -> dict:
    """The facts of a won game, shaped as the profile's engine writes them, with only what the folder, the index and
    the pages read: the owner's turn, a turn by each of GitHub's other players, and the winning move."""
    spec = build.GAMES[key]
    turn = {'notation': '1. a1', 'move': 'a1', 'words': 'A move', 'when': '20 Oct'}
    plies = [{**turn, 'side': 'house', 'by': 'tannergolden', 'by_id': OWNER_ID}]
    plies += [{**turn, 'side': 'github', 'by': login, 'by_id': uid} for uid, login in others]
    plies.append({**turn, 'notation': '9. c3#', 'side': winner, 'by': by, 'by_id': by_id, 'when': '21 Oct'})
    players = {uid: login for uid, login in others}
    if winner == 'github':
        players[by_id] = by
    return {'replay': 1, 'kind': key, 'game': game, 'winner': winner, 'by': by, 'by_id': by_id, 'issue': issue,
            'reason': spec.reason, 'line': None, 'started': '2026-10-13T12:00:00Z', 'ended': ended,
            'players': [{'player': login, 'player_id': uid, 'moves': 1} for uid, login in players.items()],
            'house_moves': 1, 'plies': plies}


def house_win(key: str = 'chess', game: int = 7, **more: object) -> dict:
    return facts(key, game, 'house', 'tannergolden', OWNER_ID, **more)


def ended(day: int, hour: int = 12) -> str:
    """A moment in October 2026, for games that end in order."""
    return f'2026-10-{day:02d}T{hour:02d}:00:00Z'


class Kit:
    """The kit, drawing each replay as a line that says what it was asked."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.fail: set[tuple[str, str]] = set()

    def __call__(self, facts_: pathlib.Path, out: pathlib.Path, name: str, theme: str, faces: pathlib.Path,
                 gone: list[int]) -> bool:
        key = facts_.parent.name
        self.calls.append((key, name, theme, list(gone)))
        if (key, name) in self.fail:
            return False
        for side in ('day', 'dark'):
            (out / f'{name}-{side}.svg').write_text(f'<svg>{key} {name} {side} {theme} {gone}</svg>\n',
                                                    encoding='utf-8')
        return True


class Arbiter:
    """The Official Arbiter on play's issues, keeping its comments by ID, and refusing everything while `down`."""

    def __init__(self) -> None:
        self.comments: dict[int, list] = {}
        self.calls: list[tuple] = []
        self.down = False
        self.last = 9000

    def check(self) -> None:
        if self.down:
            raise build.GitHubError('HTTP 502')

    def find(self, issue: int, mark: str) -> int | None:
        self.calls.append(('find', issue))
        self.check()
        return next((cid for cid, (on, text) in self.comments.items() if on == issue and mark in text), None)

    def say(self, issue: int, text: str) -> int:
        self.calls.append(('say', issue))
        self.check()
        self.last += 1
        self.comments[self.last] = [issue, text]
        return self.last

    def edit(self, issue: int, comment_id: int, text: str) -> None:
        self.calls.append(('edit', issue, comment_id))
        self.check()
        self.comments[comment_id] = [issue, text]


class Folder:
    """A throwaway play repository beside a throwaway profile, and a run's own folder."""

    def __init__(self) -> None:
        self.base = pathlib.Path(tempfile.mkdtemp(prefix='replays-test-'))
        self.root, self.profile, self.work = self.base / 'play', self.base / 'profile', self.base / 'work'
        (self.root / 'replays').mkdir(parents=True)
        (self.root / 'README.md').write_text(README, encoding='utf-8')
        self.theme('blackprint')
        self.kit, self.arbiter, self.fetched = Kit(), Arbiter(), []
        self.shas = (f'{n:040x}' for n in range(1, 1000))

    def theme(self, theme: str) -> None:
        workflows = self.profile / '.github' / 'workflows'
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / 'markdown.yml').write_text(MARKDOWN.format(theme=theme), encoding='utf-8')

    def won(self, *games: dict) -> None:
        for game in games:
            folder = self.profile / '.github' / game['kind'] / 'games'
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"game-{game['game']}.replay.json").write_text(build.dump(game), encoding='utf-8')

    def fetch(self, uid: int, faces: pathlib.Path) -> bool:
        self.fetched.append(uid)
        return True

    def plan(self, lookup=None) -> dict:
        found = build.won(self.profile)[0]
        return build.plan(build.load(self.root), found, build.theme_of(self.profile), lookup, OWNER_ID)

    def run(self, lookup=None, token: bool = True) -> tuple[dict, build.Saved, build.Posted, str]:
        """One run of 🎬 Replays as the workflow takes it: the plan, the save and its push, then the post."""
        chosen = self.plan(lookup)
        saved = build.save(chosen, self.root, self.profile, self.kit, self.fetch, self.work)
        sha = next(self.shas)
        posted = build.post(self.root, lambda root, path: [sha], self.arbiter, token)
        return chosen, saved, posted, sha

    def index(self) -> list[dict]:
        return build.load(self.root)

    def entry(self, key: str, game: int) -> dict:
        return next(entry for entry in self.index() if (entry['key'], entry['game']) == (key, game))

    def files(self, key: str, game: int) -> list[bool]:
        return [path.exists() for path in build.files(self.root / 'replays' / key, game)]

    def readme(self) -> str:
        return (self.root / 'README.md').read_text(encoding='utf-8')

    def cleanup(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)


class FolderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Folder()
        self.addCleanup(self.folder.cleanup)


class FreshTests(FolderTestCase):
    def test_every_won_game_the_index_does_not_list_is_new(self) -> None:
        self.folder.won(facts(game=3, ended=ended(21)), house_win(game=7, ended=ended(17)))
        chosen = self.folder.plan()
        self.assertEqual(chosen['fresh'], [['chess', 7], ['pentago', 3]], 'oldest first')
        self.assertEqual(chosen['theme'], 'blackprint')
        self.assertEqual((chosen['redraw'], chosen['down']), ([], []))
        self.assertEqual(chosen['faces'], sorted({OWNER_ID, OCTOCAT, MONALISA}))

    def test_a_replay_is_never_drawn_twice(self) -> None:
        self.folder.won(facts())
        self.folder.run()
        self.assertEqual(len(self.folder.kit.calls), 1)
        chosen, saved, posted, _ = self.folder.run()
        self.assertEqual(chosen['fresh'], [])
        self.assertEqual((saved.added, posted.posted), ([], []))
        self.assertEqual(len(self.folder.kit.calls), 1, 'no second drawing')
        self.assertEqual([call[0] for call in self.folder.arbiter.calls].count('say'), 1, 'no second comment')
        # Even a plan that names it again, as a run that read the index before another saved it would.
        build.save({'theme': 'blackprint', 'fresh': [['pentago', 3]], 'redraw': [], 'down': [], 'gone': [],
                    'faces': []}, self.folder.root, self.folder.profile, self.folder.kit, self.folder.fetch,
                   self.folder.work)
        self.assertEqual(len(self.folder.kit.calls), 1)
        self.assertEqual(len(self.folder.index()), 1)

    def test_facts_that_can_t_be_kept_are_passed_over_with_the_reason(self) -> None:
        folder = self.folder.profile / '.github' / 'pentago' / 'games'
        folder.mkdir(parents=True)
        (folder / 'game-1.replay.json').write_text('{not json', encoding='utf-8')
        (folder / 'game-2.replay.json').write_text(build.dump(facts(game=5)), encoding='utf-8')
        (folder / 'game-4.replay.json').write_text(build.dump({**facts(game=4), 'by': 'two words'}),
                                                   encoding='utf-8')
        (folder / 'game-6.replay.json').write_text(build.dump({**facts(game=6), 'winner': None}), encoding='utf-8')
        (folder / 'game-8.replay.json').write_text(build.dump({**facts(game=8), 'reason': 'checkmate'}),
                                                   encoding='utf-8')
        (folder / 'game-9.txt').write_text('a game record, not a replay', encoding='utf-8')
        self.folder.won(facts(game=10))
        found, passed = build.won(self.folder.profile)
        self.assertEqual(list(found), [('pentago', 10)])
        self.assertEqual(passed, [
            'Pentago game 1: its facts are not JSON',
            'Pentago game 2: they are not the facts of Pentago game 2',
            'Pentago game 4: they name nobody as the winner',
            'Pentago game 6: they name no side as the winner',
            'Pentago game 8: a game of Pentago is won by five in a row',
        ])

    def test_the_facts_a_page_is_written_from_are_checked_first(self) -> None:
        good = facts()
        self.assertEqual(build.problem(good, 'pentago', 3), '')
        self.assertEqual(build.problem({**good, 'issue': None}, 'pentago', 3), '', 'a win the owner ran by hand')
        last = good['plies'][-1]
        for broken, said in (
            ({**good, 'replay': 2}, "they are not the facts of a replay, as the profile's engine writes them"),
            ({**good, 'kind': 'chess'}, 'they are not the facts of Pentago game 3'),
            ({**good, 'game': True}, 'they are not the facts of Pentago game 3'),
            ({**good, 'by_id': True}, 'they name nobody as the winner'),
            ({**good, 'issue': '115'}, "the winning move's issue is not a number"),
            ({**good, 'ended': '21 Oct'}, 'they say no moment the game ended'),
            ({**good, 'players': [{'player': 'octocat'}]}, "GitHub's players are not each a login and an account"),
            ({**good, 'plies': []}, 'they hold no turns'),
            ({**good, 'plies': [*good['plies'][:-1], {**last, 'notation': '`9. c3#`'}]},
             'the winning move is not written as the score sheet writes it'),
            ({**good, 'plies': [*good['plies'][:-1], {**last, 'by_id': MONALISA}]},
             "the last turn is not the winner's own"),
        ):
            with self.subTest(said=said):
                self.assertEqual(build.problem(broken, 'pentago', 3), said)

    def test_the_theme_is_the_one_the_page_is_drawn_in(self) -> None:
        for written, theme in (('blackprint', 'blackprint'), ("'redprint'", 'redprint'), ('medieval', 'medieval'),
                               ('${{ inputs.theme }}', 'blackprint'), ("''", 'blackprint')):
            with self.subTest(written=written):
                self.folder.theme(written)
                self.assertEqual(build.theme_of(self.folder.profile), theme)
        (self.folder.profile / '.github' / 'workflows' / 'markdown.yml').unlink()
        self.assertEqual(build.theme_of(self.folder.profile), 'blackprint')

    def test_a_replay_is_drawn_in_the_theme_it_was_won_in_and_keeps_it(self) -> None:
        self.folder.theme('redprint')
        self.folder.won(facts())
        self.folder.run()
        self.assertEqual(self.folder.kit.calls[-1][2], 'redprint')
        self.folder.theme('greenprint')
        self.folder.run(lookup=lambda uid: uid != MONALISA)
        self.assertEqual(self.folder.kit.calls[-1], ('pentago', 'game-3', 'redprint', [MONALISA]))
        self.assertEqual(self.folder.entry('pentago', 3)['theme'], 'redprint')

    def test_a_drawing_that_fails_leaves_nothing_and_is_tried_again(self) -> None:
        self.folder.won(facts(), house_win())
        self.folder.kit.fail.add(('pentago', 'game-3'))
        _, saved, _, _ = self.folder.run()
        self.assertEqual(saved.failed, ['Pentago game 3'])
        self.assertEqual([saved.added[0]['key']], ['chess'])
        self.assertEqual(self.folder.files('pentago', 3), [False] * 4)
        self.assertFalse((self.folder.root / 'replays' / 'pentago').exists())
        self.folder.kit.fail.clear()
        self.assertEqual(self.folder.plan()['fresh'], [['pentago', 3]])
        self.folder.run()
        self.assertEqual(self.folder.files('pentago', 3), [True] * 4)

    def test_a_redrawing_that_fails_leaves_the_drawing_before_it(self) -> None:
        self.folder.won(facts())
        self.folder.run()
        day = self.folder.root / 'replays' / 'pentago' / 'game-3-day.svg'
        before = day.read_text(encoding='utf-8')
        self.folder.kit.fail.add(('pentago', 'game-3'))
        _, saved, _, _ = self.folder.run(lookup=lambda uid: uid != MONALISA)
        self.assertEqual(saved.failed, ['Pentago game 3'])
        self.assertEqual(day.read_text(encoding='utf-8'), before)
        self.assertEqual(self.folder.entry('pentago', 3)['gone'], [], 'tried again on the next daily run')


class CapTests(FolderTestCase):
    def test_the_twenty_sixth_replay_of_a_game_takes_its_oldest_out_of_the_folder(self) -> None:
        self.folder.won(*(facts(game=n, ended=ended(1 + n // 2, n % 2 * 6)) for n in range(1, 26)), house_win())
        self.folder.run()
        self.assertEqual(sum(entry['kept'] for entry in self.folder.index()), 26)
        self.folder.won(facts(game=26, ended=ended(20)))
        _, saved, _, _ = self.folder.run()
        self.assertEqual([build.name(entry) for entry in saved.added], ['Pentago game 26'])
        self.assertEqual([build.name(entry) for entry in saved.left], ['Pentago game 1'])
        self.assertEqual(self.folder.files('pentago', 1), [False] * 4)
        self.assertEqual(self.folder.files('pentago', 2), [True] * 4)
        self.assertEqual(self.folder.files('chess', 7), [True] * 4, "another game's replays stay")
        oldest = self.folder.entry('pentago', 1)
        self.assertFalse(oldest['kept'])
        self.assertIsNotNone(oldest['comment'], 'listed still, with the comment that plays it from its commit')
        self.assertEqual(len(self.folder.index()), 27)
        self.assertNotIn('replays/pentago/game-1.md', self.folder.readme())
        message = build.saved_message(saved)
        self.assertTrue(message.startswith('chore(replays): 🎬 add the replay of Pentago game 26\n\n'), message)
        self.assertIn('Pentago game 1: out of the folder, as each game keeps its newest 25.', message)

    def test_a_replay_that_left_the_folder_is_never_drawn_again(self) -> None:
        self.folder.won(*(facts(game=n, ended=ended(n)) for n in range(1, 26)))
        self.folder.run()
        self.folder.won(facts(game=26, ended=ended(26)))
        self.folder.run()
        self.assertFalse(self.folder.entry('pentago', 1)['kept'])
        calls = len(self.folder.kit.calls)
        chosen, _, _, _ = self.folder.run()
        self.assertEqual(chosen['fresh'], [])
        self.assertEqual(len(self.folder.kit.calls), calls)

    def test_a_won_game_older_than_its_game_s_newest_25_is_never_drawn(self) -> None:
        self.folder.won(*(facts(game=n, ended=ended(n)) for n in range(2, 27)))
        self.folder.run()
        self.folder.won(facts(game=1, ended=ended(1)))
        self.assertEqual(self.folder.plan()['fresh'], [], 'it would only be drawn to leave in the same commit')

    def test_taken_down_replays_do_not_count_toward_the_25(self) -> None:
        self.folder.won(*(facts(game=n, ended=ended(n), by='hubot', by_id=HUBOT) for n in range(1, 25)),
                        facts(game=25, ended=ended(25)))
        self.folder.run()
        self.folder.run(lookup=lambda uid: uid != OCTOCAT)  # game 25's winner is gone
        self.folder.won(facts(game=26, ended=ended(26), by='hubot', by_id=HUBOT))
        _, saved, _, _ = self.folder.run()
        self.assertEqual(saved.left, [])
        self.assertTrue(self.folder.entry('pentago', 1)['kept'])


class IndexTests(FolderTestCase):
    def test_the_index_records_who_won_who_played_and_where_it_was_drawn(self) -> None:
        self.folder.theme('medieval')
        self.folder.won(facts(others=((MONALISA, 'monalisa'), (HUBOT, 'hubot'))))
        self.folder.run()
        entry = self.folder.entry('pentago', 3)
        self.assertEqual(list(entry), list(build.FIELDS))
        self.assertEqual({name: entry[name] for name in ('key', 'game', 'winner', 'by', 'by_id', 'issue', 'ended',
                                                         'theme', 'gone', 'kept')},
                         {'key': 'pentago', 'game': 3, 'winner': 'github', 'by': 'octocat', 'by_id': OCTOCAT,
                          'issue': 115, 'ended': '2026-10-21T16:00:00Z', 'theme': 'medieval', 'gone': [],
                          'kept': True})
        self.assertEqual(entry['players'], sorted([OWNER_ID, OCTOCAT, MONALISA, HUBOT]), "the owner's account too")

    def test_the_commit_and_the_comment_are_filled_in_after_the_push(self) -> None:
        self.folder.won(facts())
        chosen = self.folder.plan()
        build.save(chosen, self.folder.root, self.folder.profile, self.folder.kit, self.folder.fetch,
                   self.folder.work)
        entry = self.folder.entry('pentago', 3)
        self.assertEqual((entry['commit'], entry['drawn'], entry['comment'], entry['shows']), (None,) * 4,
                         'unknown until the push')
        sha = 'c0ffee' * 6 + 'c0de'
        asked = []
        done = build.post(self.folder.root, lambda root, path: asked.append(path) or [sha], self.folder.arbiter, True)
        self.assertEqual(asked, ['replays/pentago/game-3-day.svg'])
        entry = self.folder.entry('pentago', 3)
        self.assertEqual((entry['commit'], entry['drawn'], entry['shows']), (sha, sha, sha))
        self.assertEqual(entry['comment'], self.folder.arbiter.last)
        self.assertEqual([build.name(entry) for entry in done.posted], ['Pentago game 3'])
        message = build.recorded_message(done, 'https://example.test/run')
        self.assertEqual(message, 'chore(replays): 🔖 record the replay of Pentago game 3\n\n'
                                  f'Pentago game 3: saved in {sha[:12]} and posted as comment {entry["comment"]}.\n\n'
                                  'Run: https://example.test/run\n')

    def test_the_commit_a_replay_was_first_saved_in_stays_through_a_redrawing(self) -> None:
        self.folder.won(facts())
        _, _, _, first = self.folder.run()
        _, _, _, second = self.folder.run(lookup=lambda uid: uid != MONALISA)
        entry = self.folder.entry('pentago', 3)
        self.assertEqual((entry['commit'], entry['drawn'], entry['shows']), (first, second, second))

    def test_the_index_is_json_that_says_what_it_is(self) -> None:
        self.folder.won(facts())
        self.folder.run()
        text = (self.folder.root / 'replays' / 'index.json').read_text(encoding='utf-8')
        self.assertTrue(text.endswith('}\n'))
        index = json.loads(text)
        self.assertEqual(list(index), ['//', 'replays'])
        self.assertEqual(index['//'], build.NOTE)

    def test_the_index_refuses_a_row_it_does_not_hold_whole(self) -> None:
        build.write_index(self.folder.root, [])
        self.assertEqual(build.load(self.folder.root), [])
        path = self.folder.root / 'replays' / 'index.json'
        path.write_text(json.dumps({'replays': [{'key': 'go', 'game': 1}]}), encoding='utf-8')
        with self.assertRaises(ValueError):
            build.load(self.folder.root)


def kept(count: int) -> list[dict]:
    """Rows of the index for `count` replays, the games in turn, each ending an hour after the one before, ten a day
    from noon in UTC, which is the same day in EST."""
    keys = list(build.GAMES)
    return [{**build.entry_of(facts(keys[n % 4], n + 1, ended=f'2026-11-{1 + n // 10:02d}T{12 + n % 10}:00:00Z'),
                              'blackprint', []), 'kept': True} for n in range(count)]


class GalleryTests(unittest.TestCase):
    def test_no_replays_yet_is_said_in_one_line(self) -> None:
        said = build.gallery([])
        self.assertEqual(said, "_No game has been won by a player's own move yet, so there is no replay to show._")
        self.assertEqual(build.gallery([{**kept(1)[0], 'kept': False}]), said, 'one that left the folder shows not')

    def test_one_replay_is_one_picture_that_links_its_page(self) -> None:
        said = build.gallery(kept(1))
        self.assertEqual(said.count('<picture>'), 1)
        self.assertEqual(said.count('<tr>'), 1)
        self.assertIn('<a href="replays/chess/game-1.md"><picture><source media="(prefers-color-scheme: dark)"'
                      ' srcset="replays/chess/game-1-dark.svg"><img alt="The replay of game 1 of Chess, won by'
                      ' @octocat" src="replays/chess/game-1-day.svg" width="404"></picture></a><br>', said)
        self.assertIn('<sub><b>Chess, game 1</b>: @octocat for GitHub, 1 Nov 2026</sub>', said)
        self.assertNotIn('Every other replay', said)

    def test_twelve_replays_are_twelve_pictures_two_to_a_row_newest_first(self) -> None:
        said = build.gallery(kept(12))
        self.assertEqual(said.count('<picture>'), 12)
        self.assertEqual(said.count('<tr>'), 6)
        self.assertEqual(said.count('<td '), 12)
        self.assertNotIn('Every other replay', said)
        shown = re.findall(r'<a href="replays/(\w+)/game-(\d+)\.md">', said)
        self.assertEqual(shown[:2], [('tictac', '12'), ('pentago', '11')])
        self.assertEqual(shown[-1], ('chess', '1'))

    def test_from_the_thirteenth_on_the_rest_are_links_by_game(self) -> None:
        said = build.gallery(kept(15))
        self.assertEqual(said.count('<picture>'), 12)
        pictures, rest = said.split('</table>')
        self.assertNotIn('game-1.md', pictures)
        self.assertEqual(rest, '\n\n**Every other replay here**, newest first:\n\n'
                               '- **Chess**: [game 1](replays/chess/game-1.md)\n'
                               '- **Checkers**: [game 2](replays/checkers/game-2.md)\n'
                               '- **Pentago**: [game 3](replays/pentago/game-3.md)')
        many = build.gallery(kept(40))
        self.assertEqual(many.count('<picture>'), 12)
        self.assertIn('- **Chess**: [game 25](replays/chess/game-25.md), [game 21](replays/chess/game-21.md),', many)

    def test_a_house_win_names_the_owner_alone(self) -> None:
        entry = build.entry_of(house_win(ended='2026-10-17T15:00:00Z'), 'blackprint', [])
        self.assertIn('<sub><b>Chess, game 7</b>: @tannergolden, 17 Oct 2026</sub>', build.gallery([entry]))

    def test_the_day_is_the_page_s_own_in_est(self) -> None:
        early = build.entry_of(facts(ended='2026-10-22T03:00:00Z'), 'blackprint', [])
        self.assertIn('21 Oct 2026', build.gallery([early]))

    def test_the_gallery_goes_between_its_markers_and_nowhere_else(self) -> None:
        folder = Folder()
        self.addCleanup(folder.cleanup)
        readme = folder.root / 'README.md'
        build.write_gallery(readme, kept(2))
        text = readme.read_text(encoding='utf-8')
        self.assertTrue(text.startswith('# Play\n\nAbove.\n\n## 🎬 Replays\n\n<!-- replays:start -->\n\n<table>'))
        self.assertTrue(text.endswith('</table>\n\n<!-- replays:end -->\n\nBelow.\n'))
        build.write_gallery(readme, kept(2))
        self.assertEqual(readme.read_text(encoding='utf-8'), text, 'the same gallery is the same file')
        build.write_gallery(readme, [])
        self.assertEqual(readme.read_text(encoding='utf-8'), README.replace(
            '<!-- replays:start -->\n', "<!-- replays:start -->\n\n_No game has been won by a player's own move yet,"
                                        ' so there is no replay to show._\n\n'))
        readme.write_text('# Play\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            build.write_gallery(readme, [])

    def test_the_real_readme_has_the_gallery_s_markers_once_each_and_in_order(self) -> None:
        text = (HERE.parent / 'README.md').read_text(encoding='utf-8')
        self.assertEqual((text.count(build.START), text.count(build.END)), (1, 1))
        self.assertLess(text.index('## 🎬 Replays'), text.index(build.START))
        self.assertLess(text.index(build.START), text.index(build.END))


class PageTests(FolderTestCase):
    def test_a_page_says_who_won_which_game_and_when_and_links_the_move_and_the_record(self) -> None:
        self.folder.won(facts())
        self.folder.run()
        text = (self.folder.root / 'replays' / 'pentago' / 'game-3.md').read_text(encoding='utf-8')
        self.assertIn('# 🎬 PENTAGO, GAME 3\n', text)
        self.assertIn('**[@octocat](https://github.com/octocat) won game 3 of Pentago for GitHub, as Black, on'
                      ' 21 Oct 2026.**', text)
        self.assertIn('<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="game-3-dark.svg">\n'
                      '  <img alt="The replay of game 3 of Pentago, won by @octocat" src="game-3-day.svg">\n'
                      '</picture>', text)
        self.assertIn('- **The winning move**: `9. c3#`, five in a row, from'
                      ' [its issue](https://github.com/tannergolden/play/issues/115).', text)
        self.assertIn("- **The game's record**: [every finished game of Pentago]"
                      '(https://github.com/tannergolden/tannergolden/tree/HEAD/.github/pentago/games)', text)
        self.assertTrue(text.endswith('- **The board**: [the profile](https://github.com/tannergolden), where the next'
                                      ' game is played.\n'))
        self.assertEqual(json.loads((self.folder.root / 'replays' / 'pentago' / 'game-3.json').read_text(
            encoding='utf-8')), facts(), 'its facts, beside it')

    def test_a_house_win_and_a_win_with_no_issue(self) -> None:
        text = build.page(house_win(issue=None, ended='2026-10-17T15:00:00Z'))
        self.assertIn('**[@tannergolden](https://github.com/tannergolden) won game 7 of Chess as White, on'
                      ' 17 Oct 2026.**', text)
        self.assertIn('- **The winning move**: `9. c3#`, checkmate.\n', text)
        self.assertIn('won game 7 of Tic-Tac as X', build.page(house_win('tictac')))
        self.assertIn('won game 3 of Tic-Tac for GitHub, as O', build.page(facts('tictac')))


class CommentTests(unittest.TestCase):
    SHA = '0123456789abcdef0123456789abcdef01234567'

    def test_the_comment_pins_both_pictures_and_the_page_to_the_replay_s_commit(self) -> None:
        entry = build.entry_of(facts(), 'blackprint', [])
        said = build.comment(entry, self.SHA)
        raw = f'https://raw.githubusercontent.com/tannergolden/play/{self.SHA}/replays/pentago/game-3'
        page = f'https://github.com/tannergolden/play/blob/{self.SHA}/replays/pentago/game-3.md'
        self.assertEqual(said, '<!-- replay: pentago game 3 -->\n'
                               '🎬 **The replay of game 3 of Pentago**: every move of'
                               " [@octocat](https://github.com/octocat)'s win for GitHub, played again on the"
                               ' board.\n\n'
                               f'<a href="{page}"><picture><source media="(prefers-color-scheme: dark)"'
                               f' srcset="{raw}-dark.svg"><img alt="The replay of game 3 of Pentago"'
                               f' src="{raw}-day.svg"></picture></a>\n\n'
                               f"[Its page]({page}) names the winning move, and links the game's record.\n")
        self.assertNotIn('HEAD', said, 'it plays from its commit, after the replay has left the folder')

    def test_a_house_win_s_comment_names_the_owner(self) -> None:
        said = build.comment(build.entry_of(house_win(), 'blackprint', []), self.SHA)
        self.assertIn("every move of [@tannergolden](https://github.com/tannergolden)'s win, played again", said)

    def test_a_taken_down_comment_says_why_in_one_line(self) -> None:
        said = build.taken_down(build.entry_of(facts(), 'blackprint', []))
        self.assertEqual(said, '<!-- replay: pentago game 3 -->\n🎬 **The replay of game 3 of Pentago was taken'
                               ' down**, because the account that won it was deleted.\n')
        self.assertNotIn('octocat', said)


class AccountTests(FolderTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.folder.won(facts(game=3, ended=ended(21)),
                        house_win('chess', 7, ended=ended(17), others=((HUBOT, 'hubot'), (MONALISA, 'monalisa'))))
        self.folder.run()
        self.comments = {(entry['key'], entry['game']): entry['comment'] for entry in self.folder.index()}

    def test_a_winner_whose_account_is_gone_takes_the_replay_down(self) -> None:
        asked = []
        chosen, saved, posted, _ = self.folder.run(lookup=lambda uid: asked.append(uid) or uid != OCTOCAT)
        self.assertEqual(chosen['down'], [['pentago', 3, [OCTOCAT]]])
        self.assertEqual(chosen['redraw'], [])
        self.assertEqual([build.name(entry) for entry in saved.down], ['Pentago game 3'])
        self.assertEqual(self.folder.files('pentago', 3), [False] * 4)
        self.assertNotIn('replays/pentago/game-3', self.folder.readme())
        self.assertIn('replays/chess/game-7', self.folder.readme())
        entry = self.folder.entry('pentago', 3)
        self.assertEqual((entry['kept'], entry['gone'], entry['shows']), (False, [OCTOCAT], None))
        cid = self.comments['pentago', 3]
        self.assertEqual(self.folder.arbiter.comments[cid][1], build.taken_down(entry))
        self.assertEqual([build.name(entry) for entry in posted.down], ['Pentago game 3'])
        message = build.saved_message(saved)
        self.assertTrue(message.startswith('chore(replays): 🎬 take down the replay of Pentago game 3\n'))
        # Taken down for good: never looked up, drawn or said again.
        calls = (len(asked), len(self.folder.kit.calls), len(self.folder.arbiter.calls))
        chosen, _, _, _ = self.folder.run(lookup=lambda uid: asked.append(uid) or uid != OCTOCAT)
        self.assertEqual((chosen['fresh'], chosen['down'], chosen['redraw']), ([], [], []))
        self.assertEqual((len(self.folder.kit.calls), len(self.folder.arbiter.calls)), calls[1:])

    def test_a_player_whose_account_is_gone_is_drawn_again_as_an_empty_dial(self) -> None:
        chosen, saved, posted, sha = self.folder.run(lookup=lambda uid: uid != MONALISA)
        self.assertEqual(chosen['redraw'], [['chess', 7, [MONALISA]], ['pentago', 3, [MONALISA]]], 'as listed')
        self.assertEqual(chosen['down'], [])
        self.assertEqual(chosen['faces'], sorted({OWNER_ID, OCTOCAT, HUBOT}), 'no face for an account that is gone')
        self.assertEqual(self.folder.kit.calls[-2:], [('chess', 'game-7', 'blackprint', [MONALISA]),
                                                      ('pentago', 'game-3', 'blackprint', [MONALISA])])
        self.assertEqual(self.folder.files('pentago', 3), [True] * 4)
        for key, game in (('pentago', 3), ('chess', 7)):
            entry = self.folder.entry(key, game)
            self.assertEqual((entry['gone'], entry['drawn'], entry['shows']), ([MONALISA], sha, sha))
            self.assertEqual(entry['comment'], self.comments[key, game], 'the same comment, pointed anew')
            self.assertIn(f'/play/{sha}/replays/{key}/game-{game}-day.svg',
                          self.folder.arbiter.comments[entry['comment']][1])
        self.assertEqual([build.name(entry) for entry in posted.pointed], ['Chess game 7', 'Pentago game 3'])
        self.assertTrue(build.saved_message(saved).startswith('chore(replays): 🎬 redraw 2 replays\n\nChess game 7:'
                                                              ' drawn again, with every account deleted since as an'
                                                              ' empty dial.\n'))

    def test_nobody_gone_changes_nothing(self) -> None:
        before = (self.folder.root / 'replays' / 'index.json').read_text(encoding='utf-8')
        chosen, saved, posted, _ = self.folder.run(lookup=lambda uid: True)
        self.assertEqual((chosen['down'], chosen['redraw'], saved.down, saved.redrawn), ([], [], [], []))
        self.assertEqual((self.folder.root / 'replays' / 'index.json').read_text(encoding='utf-8'), before)
        self.assertEqual((posted.posted, posted.pointed, posted.down), ([], [], []))

    def test_a_lookup_that_fails_without_a_404_leaves_the_account_as_it_was(self) -> None:
        before = (self.folder.root / 'replays' / 'index.json').read_text(encoding='utf-8')
        chosen, saved, _, _ = self.folder.run(lookup=lambda uid: None)
        self.assertEqual((chosen['down'], chosen['redraw']), ([], []))
        self.assertEqual((self.folder.root / 'replays' / 'index.json').read_text(encoding='utf-8'), before)
        with mock.patch.object(build.subprocess, 'run') as run:
            for code, said, answer in ((0, '', True), (1, 'gh: Not Found (HTTP 404)', False),
                                       (1, 'gh: Forbidden (HTTP 403)', None), (1, 'API rate limit exceeded', None),
                                       (1, 'gh: Server Error (HTTP 502)', None)):
                run.return_value = subprocess.CompletedProcess([], code, '', said)
                with self.subTest(said=said):
                    self.assertIs(build.account(MONALISA), answer)
            run.side_effect = FileNotFoundError('gh')
            self.assertIsNone(build.account(MONALISA), 'no gh at all')
            run.side_effect = subprocess.TimeoutExpired('gh', 60)
            self.assertIsNone(build.account(MONALISA), 'no answer in time')
        self.assertEqual(run.call_args.args[0], ['gh', 'api', f'/user/{MONALISA}', '--silent'])

    def test_each_account_is_looked_up_once_and_the_owner_s_never(self) -> None:
        asked = []
        self.folder.run(lookup=lambda uid: asked.append(uid) or True)
        self.assertEqual(sorted(asked), sorted({OCTOCAT, MONALISA, HUBOT}))

    def test_accounts_are_looked_up_only_when_the_run_asks(self) -> None:
        with mock.patch.object(build, 'account', side_effect=AssertionError('looked up')):
            chosen, _, _, _ = self.folder.run()
        self.assertEqual((chosen['down'], chosen['redraw']), ([], []))

    def test_an_account_found_gone_stays_gone_for_every_replay_after(self) -> None:
        self.folder.run(lookup=lambda uid: uid != MONALISA)
        self.folder.won(facts(game=4, ended=ended(23)))
        chosen, _, _, _ = self.folder.run()
        self.assertEqual(self.folder.kit.calls[-1], ('pentago', 'game-4', 'blackprint', [MONALISA]))
        self.assertEqual(self.folder.entry('pentago', 4)['gone'], [MONALISA])
        self.assertNotIn(MONALISA, chosen['faces'])
        asked = []
        self.folder.run(lookup=lambda uid: asked.append(uid) or True)
        self.assertNotIn(MONALISA, asked, 'never looked up again')
        # A won game whose winner's account is already known to be gone is never drawn at all.
        self.folder.won(facts(game=5, ended=ended(24), by='monalisa', by_id=MONALISA))
        self.assertEqual(self.folder.plan()['fresh'], [])


class PostTests(FolderTestCase):
    def test_a_comment_already_posted_is_found_and_never_posted_twice(self) -> None:
        self.folder.won(facts())
        chosen = self.folder.plan()
        build.save(chosen, self.folder.root, self.folder.profile, self.folder.kit, self.folder.fetch,
                   self.folder.work)
        self.folder.arbiter.comments[42] = [115, '<!-- replay: pentago game 3 -->\nposted by a run whose record failed']
        sha = 'f' * 40
        done = build.post(self.folder.root, lambda root, path: [sha], self.folder.arbiter, True)
        self.assertNotIn('say', [call[0] for call in self.folder.arbiter.calls])
        self.assertEqual(self.folder.entry('pentago', 3)['comment'], 42)
        self.assertEqual(self.folder.arbiter.comments[42][1], build.comment(self.folder.entry('pentago', 3), sha))
        self.assertEqual([build.name(entry) for entry in done.posted], ['Pentago game 3'])

    def test_a_comment_that_does_not_go_through_waits_for_the_next_run(self) -> None:
        self.folder.won(facts())
        self.folder.arbiter.down = True
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            _, _, posted, sha = self.folder.run()
        self.assertEqual(printed.getvalue(), 'Pentago game 3: its comment did not go through (HTTP 502); the next run'
                                             ' tries again.\n')
        entry = self.folder.entry('pentago', 3)
        self.assertEqual((entry['drawn'], entry['comment'], entry['shows']), (sha, None, None))
        self.assertEqual([build.name(entry) for entry in posted.waiting], ['Pentago game 3'])
        self.assertIn(f'Pentago game 3: saved in {sha[:12]} and its comment waits for the next run.',
                      build.recorded_message(posted))
        self.assertEqual(build.due(entry), 'post')
        self.folder.arbiter.down = False
        _, _, posted, _ = self.folder.run()
        self.assertEqual([build.name(entry) for entry in posted.posted], ['Pentago game 3'])
        self.assertEqual(self.folder.entry('pentago', 3)['shows'], sha, 'pinned to the commit that saved it')

    def test_without_the_arbiter_s_token_the_commits_are_still_recorded(self) -> None:
        self.folder.won(facts())
        _, _, posted, sha = self.folder.run(token=False)
        self.assertEqual(self.folder.arbiter.calls, [])
        self.assertEqual(self.folder.entry('pentago', 3)['drawn'], sha)
        self.assertEqual([build.name(entry) for entry in posted.waiting], ['Pentago game 3'])

    def test_a_win_with_no_issue_has_nowhere_to_be_posted(self) -> None:
        self.folder.won(house_win(issue=None))
        _, _, posted, sha = self.folder.run()
        self.assertEqual(self.folder.arbiter.calls, [])
        self.assertEqual(self.folder.entry('chess', 7)['drawn'], sha)
        self.assertEqual((posted.posted, posted.waiting), ([], []))

    def test_what_the_post_step_has_to_do_is_known_before_it_runs(self) -> None:
        entry = build.entry_of(facts(), 'blackprint', [])
        self.assertEqual(build.due(entry), 'post')
        entry.update(drawn='a' * 40, comment=7, shows='a' * 40)
        self.assertIsNone(build.due(entry))
        self.assertEqual(build.due({**entry, 'drawn': 'b' * 40}), 'point')
        self.assertEqual(build.due({**entry, 'drawn': None}), 'point')
        self.assertEqual(build.due({**entry, 'gone': [OCTOCAT], 'kept': False}), 'down')
        self.assertIsNone(build.due({**entry, 'gone': [OCTOCAT], 'kept': False, 'shows': None}))
        self.assertIsNone(build.due({**entry, 'issue': None, 'comment': None}))
        self.assertIsNone(build.due({**entry, 'kept': False, 'drawn': None, 'comment': None}))


class MessageTests(unittest.TestCase):
    def test_each_commit_says_what_it_did_and_names_no_issue_and_pings_nobody(self) -> None:
        one, two = build.entry_of(facts(), 'blackprint', []), build.entry_of(house_win(), 'blackprint', [])
        for saved, subject in (
            (build.Saved(added=[one]), 'add the replay of Pentago game 3'),
            (build.Saved(added=[one, two]), 'add 2 replays'),
            (build.Saved(added=[one], down=[two]), 'add 1 replay and take down 1'),
            (build.Saved(redrawn=[one, two], down=[two]), 'redraw 2 replays and take down 1'),
            (build.Saved(), 'bring the replays and the gallery up to date'),
        ):
            with self.subTest(subject=subject):
                message = build.saved_message(saved, 'https://github.com/tannergolden/play/actions/runs/1')
                self.assertTrue(message.startswith(f'chore(replays): 🎬 {subject}\n'), message)
                self.assertTrue(message.endswith('\nRun: https://github.com/tannergolden/play/actions/runs/1\n'))
                self.assertNotRegex(message, r'#\d|@')
        self.assertIn('Pentago game 3: won by octocat for GitHub, as Black.\nChess game 7: won by tannergolden as'
                      ' White.', build.saved_message(build.Saved(added=[one, two])))


def png(width: int = 96, height: int = 96) -> bytes:
    """A grey gradient as a PNG, as an avatar might be served."""
    rows = b''.join(b'\x00' + bytes((x * 255 // width) for x in range(width)) for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


class Served(io.BytesIO):
    def __enter__(self) -> Served:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class FaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.faces = pathlib.Path(tempfile.mkdtemp(prefix='replays-faces-'))
        self.addCleanup(shutil.rmtree, self.faces, ignore_errors=True)

    def test_an_avatar_that_can_t_be_had_only_means_initials(self) -> None:
        heavy = Served(b'GIF89a' + b'\0' * 2_000_000)
        for served in (OSError('no network'), Served(b'<html>not an image</html>'), heavy):
            with self.subTest(served=type(served).__name__), mock.patch.object(build.urllib.request, 'urlopen',
                                                                               side_effect=[served]):
                self.assertFalse(build.face(OCTOCAT, self.faces))
                self.assertEqual(list(self.faces.iterdir()), [], 'nothing left behind')
        with mock.patch.object(build.urllib.request, 'urlopen', return_value=Served(png())), \
                mock.patch.object(build.shutil, 'which', return_value=None):
            self.assertFalse(build.face(OCTOCAT, self.faces), 'no ImageMagick')

    def test_the_avatar_is_asked_for_by_account_and_read_by_the_coder_its_bytes_name(self) -> None:
        self.assertEqual(build.AVATAR.format(uid=OCTOCAT), 'https://avatars.githubusercontent.com/u/583231?s=96')
        self.assertEqual([build.image(data) for data in (png(), b'\xff\xd8\xff\xe0', b'GIF87a', b'GIF89a',
                                                          b'RIFF\0\0\0\0WEBPVP8 ', b'<svg>', b'')],
                         ['png', 'jpeg', 'gif', 'gif', 'webp', None, None])

    @unittest.skipUnless(shutil.which('magick') or shutil.which('convert'), 'ImageMagick is not installed here')
    def test_an_avatar_becomes_a_48_by_48_grey_pgm(self) -> None:
        with mock.patch.object(build.urllib.request, 'urlopen', return_value=Served(png())) as urlopen:
            self.assertTrue(build.face(OCTOCAT, self.faces))
        self.assertEqual(urlopen.call_args.args[0], 'https://avatars.githubusercontent.com/u/583231?s=96')
        data = (self.faces / f'{OCTOCAT}.pgm').read_bytes()
        self.assertTrue(data.startswith(b'P5\n48 48\n255\n'), data[:20])
        self.assertEqual(len(data), len(b'P5\n48 48\n255\n') + 48 * 48)
        self.assertEqual(sorted(path.name for path in self.faces.iterdir()), [f'{OCTOCAT}.pgm'])


class Answers:
    """`gh api`, answering each call in turn from a script of answers: what it prints, or an error."""

    def __init__(self, *answers: str | Exception) -> None:
        self.answers, self.calls = list(answers), []

    def __call__(self, *args: str, body: dict | None = None) -> str:
        self.calls.append((args, body))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


class OutsideTests(unittest.TestCase):
    """The small functions between the script and the world outside it: gh, the kit and git."""

    def test_the_arbiter_posts_and_locks_an_issue_it_finds_unlocked(self) -> None:
        answers = Answers('123\n', 'false\n', '')
        with mock.patch.object(build, 'api', answers):
            self.assertEqual(build.Arbiter().say(115, 'hello'), 123)
        self.assertEqual([call[0][:3] for call in answers.calls], [
            ('--method', 'POST', 'repos/tannergolden/play/issues/115/comments'),
            ('repos/tannergolden/play/issues/115', '--jq', '.locked'),
            ('--method', 'PUT', 'repos/tannergolden/play/issues/115/lock'),
        ])
        self.assertEqual(answers.calls[0][1], {'body': 'hello'})
        self.assertEqual(answers.calls[2][1], {'lock_reason': 'resolved'})

    def test_the_arbiter_unlocks_a_locked_issue_to_speak_and_locks_it_again(self) -> None:
        answers = Answers(build.GitHubError('HTTP 403'), '', '124\n', '', 'true\n')
        with mock.patch.object(build, 'api', answers):
            self.assertEqual(build.Arbiter().say(115, 'hello'), 124)
        self.assertEqual([call[0][:3] for call in answers.calls], [
            ('--method', 'POST', 'repos/tannergolden/play/issues/115/comments'),
            ('--method', 'DELETE', 'repos/tannergolden/play/issues/115/lock'),
            ('--method', 'POST', 'repos/tannergolden/play/issues/115/comments'),
            ('--method', 'PUT', 'repos/tannergolden/play/issues/115/lock'),
            ('repos/tannergolden/play/issues/115', '--jq', '.locked'),
        ])
        answers = Answers(build.GitHubError('HTTP 403'), '', '', '')
        with mock.patch.object(build, 'api', answers):
            build.Arbiter().edit(115, 124, 'taken down')
        self.assertEqual([call[0][:3] for call in answers.calls], [
            ('--method', 'PATCH', 'repos/tannergolden/play/issues/comments/124'),
            ('--method', 'DELETE', 'repos/tannergolden/play/issues/115/lock'),
            ('--method', 'PATCH', 'repos/tannergolden/play/issues/comments/124'),
            ('--method', 'PUT', 'repos/tannergolden/play/issues/115/lock'),
        ])
        with mock.patch.object(build, 'api', Answers(build.GitHubError('HTTP 404'), build.GitHubError('HTTP 404'))):
            with self.assertRaises(build.GitHubError):
                build.Arbiter().say(115, 'hello')

    def test_the_arbiter_finds_its_own_comment_by_its_marker(self) -> None:
        answers = Answers('9001\n9002\n', '')
        with mock.patch.object(build, 'api', answers):
            self.assertEqual(build.Arbiter().find(115, '<!-- replay: pentago game 3 -->'), 9001)
            self.assertIsNone(build.Arbiter().find(115, '<!-- replay: pentago game 3 -->'))
        args = answers.calls[0][0]
        self.assertEqual(args[:2], ('repos/tannergolden/play/issues/115/comments', '--paginate'))
        self.assertEqual(args[-1], '.[] | select(.user.type == "Bot" and ((.body // "") | contains("<!-- replay:'
                                   ' pentago game 3 -->"))) | .id')

    def test_gh_is_asked_with_its_body_on_standard_input_and_a_refusal_is_an_error(self) -> None:
        with mock.patch.object(build.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, '42\n', '')
            self.assertEqual(build.api('--method', 'POST', 'repos/x/y', body={'body': 'hi'}), '42\n')
            self.assertEqual(run.call_args.args[0], ['gh', 'api', '--method', 'POST', 'repos/x/y', '--input', '-'])
            self.assertEqual(json.loads(run.call_args.kwargs['input']), {'body': 'hi'})
            run.return_value = subprocess.CompletedProcess([], 1, '', 'gh: Forbidden\ngh: Forbidden (HTTP 403)\n')
            with self.assertRaisesRegex(build.GitHubError, r'^gh: Forbidden \(HTTP 403\)$'):
                build.api('repos/x/y')
            run.side_effect = FileNotFoundError('gh')
            with self.assertRaises(build.GitHubError):
                build.api('repos/x/y')

    def test_the_kit_is_run_with_the_replay_s_theme_faces_and_gone_accounts_and_no_token(self) -> None:
        folder = pathlib.Path(tempfile.mkdtemp(prefix='replays-kit-'))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        env = {'GH_TOKEN': 'app', 'GITHUB_TOKEN': 'run', 'MARKDOWN_TOKEN': 'kit', 'PATH': os.environ.get('PATH', '')}
        with mock.patch.object(build.subprocess, 'run') as run, mock.patch.dict(os.environ, env):
            run.return_value = subprocess.CompletedProcess([], 0, '', '')
            self.assertTrue(build.draw(pathlib.Path('kit.py'), folder / 'game-3.json', folder, 'game-3', 'medieval',
                                       folder, [MONALISA, HUBOT]))
            self.assertEqual(run.call_args.args[0][1:], [
                'kit.py', 'replay', str(folder / 'game-3.json'), '--out', str(folder), '--name', 'game-3', '--tone',
                'medieval', '--faces', str(folder), '--gone', f'{MONALISA},{HUBOT}'])
            self.assertFalse({'GH_TOKEN', 'GITHUB_TOKEN', 'MARKDOWN_TOKEN'} & set(run.call_args.kwargs['env']))
            run.return_value = subprocess.CompletedProcess([], 2, '', '::set-output name=x::y\nfacts: bad\n')
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                self.assertFalse(build.draw(pathlib.Path('kit.py'), folder / 'game-3.json', folder / 'nowhere',
                                            'game-3', 'blackprint', folder / 'nowhere', []))
            self.assertNotIn('--faces', run.call_args.args[0], 'no faces folder, no faces')
            self.assertNotIn('--gone', run.call_args.args[0])
            self.assertEqual(printed.getvalue().splitlines()[1:],
                             ['  kit: ::set-output name=x::y', '  kit: facts: bad'],
                             "the kit's words never start a line, where they could be read as a workflow command")

    def test_each_drawing_s_commit_is_read_from_git_newest_first(self) -> None:
        root = pathlib.Path(tempfile.mkdtemp(prefix='replays-git-'))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)

        def git(*args: str) -> str:
            return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.test', *args], cwd=root,
                                  check=True, capture_output=True, text=True).stdout.strip()

        git('init', '-q')
        (root / 'day.svg').write_text('first\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'first')
        first = git('rev-parse', 'HEAD')
        (root / 'other').write_text('x\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'other')
        (root / 'day.svg').write_text('again\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'again')
        self.assertEqual(build.commits(root, 'day.svg'), [git('rev-parse', 'HEAD'), first])
        self.assertEqual(build.commits(root, 'missing.svg'), [])
        self.assertEqual(build.commits(root / 'nowhere', 'day.svg'), [])


class WorkflowTests(unittest.TestCase):
    """The workflow, the checks and the README agree with the script on what runs when, and where."""

    WORKFLOW = (HERE.parent / '.github' / 'workflows' / 'replay.yml').read_text(encoding='utf-8')

    def test_the_accounts_are_looked_up_daily_and_on_demand_and_never_hourly(self) -> None:
        crons = re.findall(r"^\s+- cron: '([^']+)'", self.WORKFLOW, re.M)
        self.assertEqual(len(crons), 2)
        hourly, daily = crons
        self.assertRegex(hourly, r'^[1-5]?[0-9] \* \* \* \*$')
        self.assertNotEqual(hourly.split()[0], '0', 'off the hour')
        self.assertRegex(daily, r'^[1-5]?[0-9] [12]?[0-9] \* \* \*$')
        self.assertIn(f"ACCOUNTS: ${{{{ github.event.schedule == '{daily}' || inputs.accounts == true }}}}",
                      self.WORKFLOW)
        self.assertNotIn(f"'{hourly}' ||", self.WORKFLOW)

    def test_a_scheduled_run_is_never_turned_away_for_the_repository_its_event_does_not_carry(self) -> None:
        guard = re.search(r'^    if: (.+)$', self.WORKFLOW, re.M)[1]
        self.assertIn("github.event_name == 'schedule' ||", guard)
        self.assertIn('github.ref_name == github.event.repository.default_branch', guard)

    def test_the_facts_are_read_where_the_profile_s_engine_writes_them(self) -> None:
        self.assertIn('.github/*/games/*.replay.json\n', self.WORKFLOW)
        self.assertIn('.github/workflows/markdown.yml\n', self.WORKFLOW)
        self.assertIn('repository: tannergolden/markdown\n          ref: v1\n', self.WORKFLOW)
        self.assertIn("printf '%s\\n' .markdown-kit/ .profile/ >> .git/info/exclude", self.WORKFLOW)

    def test_no_expression_reaches_a_script(self) -> None:
        script, indent = False, 0
        for number, line in enumerate(self.WORKFLOW.splitlines(), 1):
            stripped = line.lstrip()
            if script and stripped and len(line) - len(stripped) <= indent:
                script = False
            if script:
                self.assertNotIn('${{', line, f'line {number}')
            if stripped.startswith('run: |'):
                script, indent = True, len(line) - len(stripped)
            elif stripped.startswith('run: '):
                self.assertNotIn('${{', line, f'line {number}')

    def test_the_checks_run_these_tests(self) -> None:
        checks = (HERE.parent / '.github' / 'workflows' / 'checks.yml').read_text(encoding='utf-8')
        self.assertIn("python3 -m unittest discover -s replays -p 'test_*.py'", checks)


class MainTests(FolderTestCase):
    def test_a_whole_run_through_the_command_line(self) -> None:
        self.folder.won(facts())
        temp = self.folder.base / 'runner'
        temp.mkdir()
        out = temp / 'output'
        env = {'RUNNER_TEMP': str(temp), 'GITHUB_OUTPUT': str(out), 'ACCOUNTS': 'false', 'OWNER_ID': str(OWNER_ID),
               'RUN_URL': 'https://github.com/tannergolden/play/actions/runs/7', 'GH_TOKEN': ''}
        common = ['--root', str(self.folder.root)]
        printed = io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(printed), \
                mock.patch.object(build, 'draw', side_effect=lambda kit, *rest: self.folder.kit(*rest)), \
                mock.patch.object(build, 'face', side_effect=self.folder.fetch), \
                mock.patch.object(build, 'commits', return_value=['e' * 40]), \
                mock.patch.object(build, 'account', side_effect=AssertionError('looked up')):
            self.assertEqual(build.main(['plan', '--profile', str(self.folder.profile), *common]), 0)
            self.assertEqual(out.read_text(encoding='utf-8'), 'draw=true\n')
            self.assertEqual(build.main(['save', '--profile', str(self.folder.profile), '--kit', 'kit.py', *common]),
                             0)
            self.assertEqual(out.read_text(encoding='utf-8'), 'draw=true\nfailed=0\nrecord=true\ncomment=true\n')
            self.assertEqual(build.main(['post', *common]), 0)
        self.assertEqual((temp / 'replays' / 'commit.txt').read_text(encoding='utf-8'),
                         'chore(replays): 🎬 add the replay of Pentago game 3\n\n'
                         'Pentago game 3: won by octocat for GitHub, as Black.\n\n'
                         'Run: https://github.com/tannergolden/play/actions/runs/7\n')
        self.assertTrue((temp / 'replays' / 'record.txt').read_text(encoding='utf-8').startswith(
            'chore(replays): 🔖 record the replay of Pentago game 3\n\nPentago game 3: saved in eeeeeeeeeeee and'
            ' its comment waits for the next run.\n'))
        self.assertIn("::warning::The Arbiter's token wasn't minted, so 1 comments wait for the next run.",
                      printed.getvalue())
        self.assertEqual(self.folder.entry('pentago', 3)['drawn'], 'e' * 40)

    def test_the_profile_must_be_named_to_plan_or_save(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build.main(['plan', '--root', str(self.folder.root)])


def pgm(level: int) -> bytes:
    """A 48 by 48 grey face of one level, as a fetched avatar would be made."""
    return b'P5\n48 48\n255\n' + bytes((level + x) % 256 for x in range(48 * 48))


@unittest.skipUnless(KIT.is_file(), f'the kit is not checked out at {KIT}')
class EndToEndTests(unittest.TestCase):
    """The real kit draws every sample game, and draws them again when accounts go."""

    def setUp(self) -> None:
        self.folder = Folder()
        self.addCleanup(self.folder.cleanup)
        for key in build.GAMES:
            folder = self.folder.profile / '.github' / key / 'games'
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy(FIXTURES / f'{key}.replay.json', folder / 'game-1.replay.json')
        self.folder.theme('medieval')  # a collection's theme, which a replay is drawn in blackprint for
        self.kit = functools.partial(build.draw, KIT)

    def fetch(self, uid: int, faces: pathlib.Path) -> bool:
        (faces / f'{uid}.pgm').write_bytes(pgm(uid % 200))
        return True

    def run_once(self, lookup=None) -> tuple[build.Saved, str]:
        chosen = self.folder.plan(lookup)
        with contextlib.redirect_stdout(io.StringIO()):
            saved = build.save(chosen, self.folder.root, self.folder.profile, self.kit, self.fetch, self.folder.work)
        sha = next(self.folder.shas)
        build.post(self.folder.root, lambda root, path: [sha], self.folder.arbiter, True)
        return saved, sha

    def svg(self, key: str, side: str = 'day') -> str:
        return (self.folder.root / 'replays' / key / f'game-1-{side}.svg').read_text(encoding='utf-8')

    def test_the_kit_draws_every_sample_game_and_draws_again_without_a_deleted_account(self) -> None:
        saved, sha = self.run_once()
        self.assertEqual(saved.failed, [])
        self.assertEqual(sorted(entry['key'] for entry in saved.added), sorted(build.GAMES))
        first = {}
        for key in build.GAMES:
            with self.subTest(key=key):
                self.assertEqual(self.folder.files(key, 1), [True] * 4)
                for side in ('day', 'dark'):
                    svg = self.svg(key, side)
                    self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
                    self.assertIn(f'<!--markdown-kit v1 blackprint replay {key} wide {side}-->', svg)
                first[key] = self.svg(key)
                facts_ = json.loads((FIXTURES / f'{key}.replay.json').read_text(encoding='utf-8'))
                self.assertEqual(json.loads((self.folder.root / 'replays' / key / 'game-1.json').read_text(
                    encoding='utf-8')), facts_)
                self.assertEqual(self.folder.entry(key, 1)['theme'], 'medieval')
        self.assertIn('@hubot wins with 8... Nf3#', first['chess'], 'the chess sample, as its fixtures log says')
        self.assertEqual(self.folder.readme().count('<picture>'), 4)
        self.assertEqual(len(self.folder.arbiter.comments), 4)
        # The chess sample was won by @hubot; @monalisa played in every sample.
        _, second = self.run_once(lookup=lambda uid: uid not in (HUBOT, MONALISA))
        self.assertEqual(self.folder.files('chess', 1), [False] * 4)
        chess = self.folder.entry('chess', 1)
        self.assertEqual(self.folder.arbiter.comments[chess['comment']][1], build.taken_down(chess))
        for key in ('checkers', 'pentago', 'tictac'):
            with self.subTest(key=key):
                entry = self.folder.entry(key, 1)
                self.assertEqual(entry['gone'], sorted({HUBOT, MONALISA}))
                self.assertNotEqual(self.svg(key), first[key], 'drawn again, with two empty dials')
                self.assertEqual((entry['commit'], entry['drawn']), (sha, second))
                self.assertIn(f'/play/{second}/replays/{key}/game-1-dark.svg',
                              self.folder.arbiter.comments[entry['comment']][1])
        self.assertEqual(self.folder.readme().count('<picture>'), 3)


if __name__ == '__main__':
    unittest.main()
