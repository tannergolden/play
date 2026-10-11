#!/usr/bin/env python3
"""Tests for the five-differences contract enforcement.

WHY THIS EXISTS. `template-parity.py` is the only thing standing between this
repository and silent drift from the public baseline, and it had no test of any
kind. The contract's own thesis is that a rule without a gate is a rule nobody
enforces; the gate itself was the unguarded rule.

Every test builds a throwaway pair of trees, runs the real script as a
subprocess exactly as the workflow does, and asserts on its exit code and
output. Nothing here reads or writes this repository.

Run it:

    python3 .github/scripts/test_template_parity.py

`.github/workflows/template-parity.yml` runs this BEFORE it runs the check
itself, so a broken enforcer fails ahead of the comparison it would perform.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent / 'template-parity.py'

MIT = 'Distributed under the MIT License.'
PROPRIETARY = 'Proprietary and confidential; all rights reserved.'

# The shape of the real contract, reduced to what a test needs. Individual
# tests override single keys rather than restating the whole thing.
CONTRACT = textwrap.dedent(
    f"""\
    baseline: tannergolden/path
    absent-here:
      - src
    inherited-from-account:
      - .github/SECURITY.md
    relocated:
      docs: .github/docs
    content-may-differ:
      LICENSE: 'Difference 4. Proprietary rather than MIT.'
    enforcement-only-here:
      - .github/template-parity.yml
    seeds:
      footer-markers:
        - '{MIT}'
        - '{PROPRIETARY}'
      exceptions:
        README.md: 'Names the seed path in prose.'
    """
)


def seed(body: str, footer: str) -> str:
    return f'# Title\n\n{body}\n\nBuilt with love. {footer}\n'


class Trees:
    """A baseline/here pair on disk, plus the run that compares them."""

    def __init__(self, contract: str = CONTRACT) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='parity-test-'))
        self.here = self.root / 'this'
        self.base = self.root / 'baseline'

        # The minimum that satisfies the contract: a licence that differs, a
        # shared file that does not, and one seed on each side.
        self.write_here('.github/template-parity.yml', contract)
        self.write_here('LICENSE', 'PROPRIETARY AND CONFIDENTIAL\n')
        self.write_base('LICENSE', 'MIT License\n')
        self.write_here('.gitignore', 'node_modules/\n')
        self.write_base('.gitignore', 'node_modules/\n')
        self.write_here('.github/docs/templates/ADR.md', seed('adr', PROPRIETARY))
        self.write_base('docs/templates/ADR.md', seed('adr', MIT))

    def _write(self, root: pathlib.Path, rel: str, text: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def write_here(self, rel: str, text: str) -> None:
        self._write(self.here, rel, text)

    def write_base(self, rel: str, text: str) -> None:
        self._write(self.base, rel, text)

    def run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.here), str(self.base)],
            capture_output=True, text=True,
        )

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class ParityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.trees = Trees()
        self.addCleanup(self.trees.cleanup)

    def assertClean(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(
            result.returncode, 0,
            f'expected a clean run, got exit {result.returncode}:\n'
            f'{result.stdout}\n{result.stderr}',
        )

    def assertDrift(
        self, result: subprocess.CompletedProcess[str], fragment: str
    ) -> None:
        self.assertEqual(
            result.returncode, 1,
            f'expected drift to fail the run, got exit {result.returncode}:\n'
            f'{result.stdout}\n{result.stderr}',
        )
        self.assertIn(fragment, result.stdout)


class TestTheBaselineFixtureIsSound(ParityTestCase):
    """Guards the fixture itself: everything else builds on a clean pair."""

    def test_a_conforming_pair_passes(self) -> None:
        self.assertClean(self.trees.run())


class TestDifferenceOne(ParityTestCase):
    """No imposed structure: src/ tests/ packages/ benchmarks/ (assets/ is shared)."""

    def test_absence_is_still_permitted(self) -> None:
        # Present in the baseline and missing here is exactly what difference
        # 1 asks for, and must stay permitted.
        self.trees.write_base('src/README.md', 'source lives here\n')
        self.assertClean(self.trees.run())

    def test_a_directory_named_in_absent_here_may_not_exist_here(self) -> None:
        # Copied from the baseline VERBATIM, so the trees agree byte for byte
        # and only the contract is violated. This is the case that passed.
        self.trees.write_base('src/README.md', 'source lives here\n')
        self.trees.write_here('src/README.md', 'source lives here\n')
        self.assertDrift(self.trees.run(), 'src/README.md')

    def test_the_message_names_the_difference_it_violates(self) -> None:
        self.trees.write_base('src/app/main.py', 'x = 1\n')
        self.trees.write_here('src/app/main.py', 'x = 1\n')
        self.assertDrift(self.trees.run(), 'difference 1')

    def test_a_file_merely_starting_with_the_prefix_is_untouched(self) -> None:
        # `src` must not match `srcutil.md`; covered_by() is prefix-based.
        self.trees.write_base('srcutil.md', 'not the src directory\n')
        self.trees.write_here('srcutil.md', 'not the src directory\n')
        self.assertClean(self.trees.run())


class TestDifferenceThree(ParityTestCase):
    """Community health files are inherited from the account, not local."""

    def test_inheritance_is_still_permitted(self) -> None:
        self.trees.write_base('.github/SECURITY.md', '# Security Policy\n')
        self.assertClean(self.trees.run())

    def test_a_health_file_may_not_reappear_here(self) -> None:
        # A local copy OVERRIDES the account-wide one, so the inherited policy
        # silently stops applying - and the trees still agree byte for byte.
        body = '# Security Policy\n'
        self.trees.write_base('.github/SECURITY.md', body)
        self.trees.write_here('.github/SECURITY.md', body)
        self.assertDrift(self.trees.run(), '.github/SECURITY.md')

    def test_the_message_names_the_difference_it_violates(self) -> None:
        body = '# Security Policy\n'
        self.trees.write_base('.github/SECURITY.md', body)
        self.trees.write_here('.github/SECURITY.md', body)
        self.assertDrift(self.trees.run(), 'difference 3')


class TestContentMayDiffer(ParityTestCase):
    """The four files difference 4 and 5 permit to diverge."""

    def test_a_listed_file_may_still_differ_freely(self) -> None:
        self.trees.write_here('LICENSE', 'PROPRIETARY, revised\n')
        self.assertClean(self.trees.run())

    def test_an_entry_that_no_longer_differs_is_reported_as_stale(self) -> None:
        # Difference 4 is the one that "propagates to everything generated
        # from here". A gate that would not notice the licence reverting to
        # the baseline's MIT is not gating difference 4 at all.
        self.trees.write_here('LICENSE', 'MIT License\n')
        result = self.trees.run()
        self.assertIn('Stale permission', result.stdout)
        self.assertIn('LICENSE', result.stdout)

    def test_a_stale_entry_does_not_fail_the_run(self) -> None:
        # Same treatment a stale seed exception already gets: it describes a
        # repository that got tidier, so it is a notice, not a failure.
        self.trees.write_here('LICENSE', 'MIT License\n')
        self.assertClean(self.trees.run())

    def test_an_entry_for_a_file_that_is_gone_is_reported_as_stale(self) -> None:
        (self.trees.here / 'LICENSE').unlink()
        (self.trees.base / 'LICENSE').unlink()
        result = self.trees.run()
        self.assertIn('Stale permission', result.stdout)


class TestSeedExceptions(ParityTestCase):
    """The two index documents name the seed path in prose."""

    def test_an_exception_may_not_lose_its_licence_footer(self) -> None:
        # An exception is permitted to differ by MORE than the footer. It is
        # not permitted to differ by LESS: difference 4 still applies, and a
        # bare `continue` waived that too.
        body = seed('index prose, identical on both sides', MIT)
        self.trees.write_base('docs/README.md', body)
        self.trees.write_here('.github/docs/README.md', body)
        self.assertDrift(self.trees.run(), 'licence footer')

    def test_an_exception_carrying_the_wrong_footer_fails(self) -> None:
        self.trees.write_base('docs/README.md', seed('public prose', MIT))
        self.trees.write_here('.github/docs/README.md', seed('private prose', MIT))
        self.assertDrift(self.trees.run(), 'licence footer')

    def test_an_exception_may_not_drop_its_footer_entirely(self) -> None:
        # No footer trivially "differs" from one, so a rule that only compares
        # footers waves this through - and it is the likelier accident.
        self.trees.write_base('docs/README.md', seed('public prose', MIT))
        self.trees.write_here('.github/docs/README.md', 'TOTALLY DIFFERENT\n')
        self.assertDrift(self.trees.run(), 'licence footer')

    def test_an_exception_may_differ_in_prose(self) -> None:
        self.trees.write_base('docs/README.md', seed('public prose', MIT))
        self.trees.write_here(
            '.github/docs/README.md',
            seed('private prose, quite different', PROPRIETARY),
        )
        self.assertClean(self.trees.run())


class TestSeedComparison(ParityTestCase):
    """Difference 2: same documents at a different depth, footer aside."""

    def test_a_seed_that_differs_beyond_its_footer_fails(self) -> None:
        self.trees.write_here(
            '.github/docs/templates/ADR.md', seed('adr, but rewritten', PROPRIETARY)
        )
        self.assertDrift(self.trees.run(), 'more than the')

    def test_a_seed_missing_here_fails(self) -> None:
        self.trees.write_base('docs/templates/User-Story.md', seed('story', MIT))
        self.assertDrift(self.trees.run(), 'missing here')

    def test_a_seed_only_here_fails(self) -> None:
        self.trees.write_here(
            '.github/docs/templates/Invented.md', seed('invented', PROPRIETARY)
        )
        self.assertDrift(self.trees.run(), 'absent from the baseline')

    def test_a_seed_pair_with_no_footer_is_judged_on_its_body(self) -> None:
        # A document carrying no licence line - a glossary, a diagram note -
        # cannot satisfy "the footer must differ", so it must not be judged
        # against that rule. Identical bodies are correct here, not drift.
        self.trees.write_base('docs/GLOSSARY.md', '# Glossary\n\nterm\n')
        self.trees.write_here('.github/docs/GLOSSARY.md', '# Glossary\n\nterm\n')
        self.assertClean(self.trees.run())

    def test_a_footerless_seed_that_really_drifted_still_fails(self) -> None:
        self.trees.write_base('docs/GLOSSARY.md', '# Glossary\n\nterm\n')
        self.trees.write_here('.github/docs/GLOSSARY.md', '# Glossary\n\nOTHER\n')
        self.assertDrift(self.trees.run(), 'more than the')


class TestSharedFiles(ParityTestCase):
    """Everything not named anywhere must be byte-identical."""

    def test_drift_in_a_shared_file_fails(self) -> None:
        self.trees.write_here('.gitignore', 'node_modules/\n.venv\n')
        self.assertDrift(self.trees.run(), 'not listed in content-may-differ')

    def test_an_unlisted_file_only_here_fails(self) -> None:
        self.trees.write_here('Makefile', 'all:\n')
        self.assertDrift(self.trees.run(), 'absent from the baseline')

    def test_an_unlisted_file_only_in_the_baseline_fails(self) -> None:
        self.trees.write_base('Makefile', 'all:\n')
        self.assertDrift(self.trees.run(), 'does not permit its absence')


class TestRelocation(ParityTestCase):
    """The seed tree moved wholesale; two moves must not collide."""

    TWO_TREES = CONTRACT.replace(
        'relocated:\n  docs: .github/docs\n',
        'relocated:\n  docs: .github/docs\n  notes: .github/notes\n',
    )

    def test_two_relocated_pairs_stay_independent(self) -> None:
        trees = Trees(self.TWO_TREES)
        self.addCleanup(trees.cleanup)
        # The SAME suffix path under both relocated trees. Keyed by suffix
        # alone, one entry silently overwrites the other and both trees are
        # then reported as missing a document that is present in each.
        trees.write_base('notes/templates/ADR.md', seed('note adr', MIT))
        trees.write_here(
            '.github/notes/templates/ADR.md', seed('note adr', PROPRIETARY)
        )
        self.assertClean(trees.run())

    def test_drift_in_the_second_relocated_tree_is_still_caught(self) -> None:
        trees = Trees(self.TWO_TREES)
        self.addCleanup(trees.cleanup)
        trees.write_base('notes/templates/ADR.md', seed('note adr', MIT))
        trees.write_here(
            '.github/notes/templates/ADR.md', seed('rewritten', PROPRIETARY)
        )
        self.assertDrift(trees.run(), 'more than the')

    def test_a_document_missing_from_the_second_tree_is_named_by_its_own_path(
        self,
    ) -> None:
        trees = Trees(self.TWO_TREES)
        self.addCleanup(trees.cleanup)
        trees.write_base('notes/Orphan.md', seed('orphan', MIT))
        self.assertDrift(trees.run(), '.github/notes/Orphan.md')


class TestDiagnostics(ParityTestCase):
    """A misuse must name the problem rather than raise."""

    def test_a_missing_contract_is_reported_not_raised(self) -> None:
        (self.trees.here / '.github/template-parity.yml').unlink()
        result = self.trees.run()
        self.assertNotIn('Traceback', result.stderr)
        self.assertIn('template-parity.yml', result.stdout)
        self.assertEqual(result.returncode, 2)

    def test_the_arguments_in_the_wrong_order_are_reported(self) -> None:
        # The baseline has no contract file, so this is the same failure as
        # above wearing an easier mistake.
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.trees.base), str(self.trees.here)],
            capture_output=True, text=True,
        )
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(result.returncode, 2)

    def test_a_malformed_contract_is_reported_not_raised(self) -> None:
        self.trees.write_here('.github/template-parity.yml', 'baseline: [unclosed\n')
        result = self.trees.run()
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(result.returncode, 2)

    def test_a_non_utf8_seed_is_reported_not_raised(self) -> None:
        (self.trees.here / '.github/docs/templates/ADR.md').write_bytes(b'\xff\xfe bad\n')
        result = self.trees.run()
        self.assertNotIn('Traceback', result.stderr)
        self.assertIn('UTF-8', result.stdout)
        self.assertEqual(result.returncode, 1)

    def test_wrong_argument_count_exits_two(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.trees.here)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


class TestTheSyncMapping(ParityTestCase):
    """The contract, written out for the sync: one parser, so the two never disagree."""

    def sync_map(self, contract: str = CONTRACT) -> subprocess.CompletedProcess[str]:
        self.trees.write_here('.github/template-parity.yml', contract)
        return subprocess.run(
            [sys.executable, str(SCRIPT), '--sync-map', str(self.trees.here)],
            capture_output=True, text=True,
        )

    def test_everything_the_contract_keeps_apart_is_left_out(self) -> None:
        contract = CONTRACT + "sync-never:\n  LICENSE: 'Difference 4.'\n"
        result = self.sync_map(contract)
        self.assertEqual(result.returncode, 0, result.stderr)
        mapping = json.loads(result.stdout)
        self.assertEqual(
            mapping['exclude'],
            ['.github/SECURITY.md', '.github/template-parity.yml', 'LICENSE', 'src'],
        )
        self.assertEqual(mapping['relocate'], {'docs': '.github/docs'})
        self.assertEqual(mapping['lock'], '.github/template-parity.lock')
        self.assertEqual(mapping['list'], '.github/template-sync')
        self.assertEqual(mapping['source'], '.github/template-parity.yml')

    def test_the_footer_swaps_from_the_baselines_to_this_ones(self) -> None:
        mapping = json.loads(self.sync_map().stdout)
        self.assertEqual(
            mapping['replace'], [{'under': 'docs', 'from': MIT, 'to': PROPRIETARY}]
        )

    def test_a_contract_without_two_footers_is_refused_with_a_sentence(self) -> None:
        contract = CONTRACT.replace(f"    - '{PROPRIETARY}'\n", '')
        result = self.sync_map(contract)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertIn('exactly two footers', result.stderr)


class TestTheSyncRunsOnlyWhenAsked(unittest.TestCase):
    """The parity sync writes to this repository, so nothing may start it but a person."""

    def test_only_a_dispatch_with_sync_ticked_reaches_the_sync_job(self) -> None:
        import yaml

        workflow = SCRIPT.parent.parent / 'workflows' / 'template-parity.yml'
        doc = yaml.safe_load(workflow.read_text(encoding='utf-8'))
        guard = doc['jobs']['sync']['if']
        self.assertIn("github.event_name == 'workflow_dispatch'", guard)
        self.assertIn('inputs.sync', guard)
        self.assertIn('github.event.repository.is_template', guard)
        self.assertNotIn('schedule', guard)
        # YAML 1.1 reads a bare `on` as true.
        dispatch = (doc.get('on') or doc.get(True))['workflow_dispatch']
        self.assertIs(dispatch['inputs']['sync']['default'], False)

    def test_a_sync_starts_from_the_default_branch_and_is_never_displaced(self) -> None:
        import yaml

        workflow = SCRIPT.parent.parent / 'workflows' / 'template-parity.yml'
        doc = yaml.safe_load(workflow.read_text(encoding='utf-8'))
        steps = doc['jobs']['sync']['steps']
        # The pull request targets the default branch, so the sync is worked
        # out there - never on whatever branch it was dispatched from.
        checkout = next(s for s in steps if s.get('uses', '').startswith('actions/checkout'))
        self.assertEqual(checkout['with']['ref'], '${{ github.event.repository.default_branch }}')
        # A token that cannot write workflows holds them back, not the push.
        sync = next(s for s in steps if s.get('id') == 'sync')
        self.assertEqual(sync['with']['workflow-files'], 'auto')
        self.assertEqual(sync['with']['workflow-token'], '${{ secrets.BOT_ACCESS_TOKEN }}')
        # The daily check queues apart, so it never takes a waiting sync's place.
        self.assertIn('${{ github.event_name }}', doc['concurrency']['group'])


class TestSyncNever(ParityTestCase):
    """What the sync leaves alone must be permitted to differ, or it would drift."""

    def test_an_entry_permitted_to_differ_passes(self) -> None:
        contract = CONTRACT + "sync-never:\n  LICENSE: 'Difference 4.'\n"
        trees = Trees(contract)
        self.addCleanup(trees.cleanup)
        self.assertClean(trees.run())

    def test_an_entry_held_identical_fails(self) -> None:
        contract = CONTRACT + "sync-never:\n  .gitignore: 'Left alone.'\n"
        trees = Trees(contract)
        self.addCleanup(trees.cleanup)
        self.assertDrift(trees.run(), 'listed in sync-never but not in content-may-differ')


class TestTheVerdict(ParityTestCase):
    """The summary line is read by a human; it must not overstate."""

    def test_the_baseline_named_in_the_verdict_comes_from_the_contract(self) -> None:
        contract = CONTRACT.replace(
            'baseline: tannergolden/path', 'baseline: tannergolden/other'
        )
        trees = Trees(contract)
        self.addCleanup(trees.cleanup)
        self.assertIn('tannergolden/other', trees.run().stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
