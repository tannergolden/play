#!/usr/bin/env python3
"""Enforce the five-differences contract between this template and the public one.

`README.md` states that this repository is permitted to differ from
`tannergolden/path` in exactly five ways, and that "any difference outside these
five is drift, and drift is a defect". That was held by prose alone, and prose
does not fail a check - so it drifted.

This reads `.github/template-parity.yml`, compares the two trees, and fails on
anything the contract does not permit.

It also writes the contract out as the mapping 📐 Template Parity's sync job
hands to the standards' template sync, so the check and the sync read one
contract through one parser and can never disagree about what it says.

Usage:

    python3 .github/scripts/template-parity.py <this-repo> <baseline-checkout>
    python3 .github/scripts/template-parity.py --sync-map <this-repo>
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import yaml

# Never part of the comparison: version control internals, and caches that
# only exist on a runner.
SKIP_PARTS = {".git", "__pycache__", ".ruff_cache", ".pytest_cache"}


def walk(root: pathlib.Path) -> set[str]:
    """Every file under `root`, as a POSIX path relative to it."""
    return {
        str(p.relative_to(root).as_posix())
        for p in root.rglob("*")
        if p.is_file() and not SKIP_PARTS.intersection(p.parts)
    }


def prefix_covering(path: str, prefixes: list[str]) -> str | None:
    """The entry in `prefixes` that `path` is, or sits underneath - else None."""
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + "/"):
            return prefix
    return None


def covered_by(path: str, prefixes: list[str]) -> bool:
    """True when `path` is one of `prefixes`, or sits underneath one."""
    return prefix_covering(path, prefixes) is not None


def strip_footer(text: str, markers: list[str]) -> str:
    """Blank out the licence footer so the rest of the document can be compared."""
    out = []
    for line in text.splitlines():
        out.append("" if any(marker in line for marker in markers) else line)
    return "\n".join(out)


def footer_of(text: str, markers: list[str]) -> list[str]:
    """The licence-footer lines alone - what difference 4 requires to differ."""
    return [line for line in text.splitlines() if any(m in line for m in markers)]


# Where the parity sync keeps its own record, and what it is called where
# people read it. The lock is enforcement-only-here like the contract itself.
SYNC_NAME = "📐 Template Parity Sync"
SYNC_LOCK = ".github/template-parity.lock"
SYNC_LIST = ".github/template-sync"
CONTRACT = ".github/template-parity.yml"


def sync_map(contract: dict) -> dict:
    """The contract as the mapping the standards' template sync reads.

    Nothing absent-here, inherited, enforcement-only or sync-never ever
    arrives; the relocated seeds move, and their footers swap from the
    baseline's marker to this repository's. Everything else is merged.
    """
    markers = list((contract.get("seeds") or {}).get("footer-markers") or [])
    if len(markers) != 2:
        raise ValueError(
            "seeds.footer-markers must name exactly two footers - the baseline's, then this "
            "repository's - for the sync to swap one for the other."
        )
    relocated = dict(contract.get("relocated") or {})
    exclude = sorted(
        set(contract.get("absent-here") or [])
        | set(contract.get("inherited-from-account") or [])
        | set(contract.get("enforcement-only-here") or [])
        | set(contract.get("sync-never") or {})
    )
    return {
        "format": 1,
        "name": SYNC_NAME,
        "source": CONTRACT,
        "lock": SYNC_LOCK,
        "list": SYNC_LIST,
        "exclude": exclude,
        "relocate": relocated,
        "replace": [{"under": src, "from": markers[0], "to": markers[1]} for src in sorted(relocated)],
    }


def emit_map(here: pathlib.Path) -> int:
    try:
        contract = yaml.safe_load((here / CONTRACT).read_text(encoding="utf-8"))
        if not isinstance(contract, dict):
            raise ValueError(f"{CONTRACT} did not parse to a mapping of contract terms.")
        print(json.dumps(sync_map(contract), indent=2, ensure_ascii=False))
    except (OSError, UnicodeDecodeError, yaml.YAMLError, ValueError) as exc:
        print(f"::error::Could not write the sync mapping from {here / CONTRACT}: {exc}", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--sync-map":
        return emit_map(pathlib.Path(sys.argv[2]).resolve())
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    here = pathlib.Path(sys.argv[1]).resolve()
    base = pathlib.Path(sys.argv[2]).resolve()

    # The step runs under `set -euo pipefail`, so an unguarded read ends the
    # run with a pathlib traceback and no verdict, no annotations and no step
    # summary. Naming the problem costs three lines. Passing the arguments the
    # other way round is the easy mistake, and lands here.
    contract_path = here / ".github/template-parity.yml"
    try:
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(
            f"::error::No contract at {contract_path}. The first argument must be THIS "
            f"repository's checkout and the second the baseline's, in that order."
        )
        return 2
    except UnicodeDecodeError as exc:
        print(f"::error::{contract_path} is not valid UTF-8: {exc}")
        return 2
    except yaml.YAMLError as exc:
        print(f"::error::{contract_path} is not valid YAML: {exc}")
        return 2
    if not isinstance(contract, dict):
        print(f"::error::{contract_path} did not parse to a mapping of contract terms.")
        return 2

    absent = list(contract.get("absent-here") or [])
    inherited = list(contract.get("inherited-from-account") or [])
    enforcement = list(contract.get("enforcement-only-here") or [])
    relocated = dict(contract.get("relocated") or {})
    may_differ = dict(contract.get("content-may-differ") or {})
    seeds = dict(contract.get("seeds") or {})
    markers = list(seeds.get("footer-markers") or [])
    seed_exceptions = dict(seeds.get("exceptions") or {})
    sync_never = dict(contract.get("sync-never") or {})

    problems: list[str] = []
    checked = 0

    # 0. What the sync leaves alone must be permitted to differ. A file held
    # identical by the contract that the sync never writes would drift on
    # the baseline's next change, with nothing to bring it back.
    for rel in sorted(sync_never):
        checked += 1
        if rel not in may_differ:
            problems.append(
                f"{rel}: listed in sync-never but not in content-may-differ. The sync leaves it "
                f"alone, so it must be permitted to differ - or synced like everything else."
            )

    here_files = walk(here)
    base_files = walk(base)

    # The relocated tree is compared on its own terms below, so lift both
    # sides out of the plain set comparison first.
    #
    # Keyed by (relocation, suffix) rather than suffix alone. With one
    # relocation the two are equivalent; with two, any document sharing a
    # suffix path - `README.md` under both - collided, the last write won, and
    # the check reported both trees as missing a file present in each. One
    # extra entry in `relocated:` is a one-line change that would have looked
    # like drift in a tree nobody had touched.
    reloc_here: dict[tuple[str, str], str] = {}
    reloc_base: dict[tuple[str, str], str] = {}
    for src, dest in relocated.items():
        for f in sorted(base_files):
            if covered_by(f, [src]):
                reloc_base[(src, f[len(src) :].lstrip("/"))] = f
        for f in sorted(here_files):
            if covered_by(f, [dest]):
                reloc_here[(src, f[len(dest) :].lstrip("/"))] = f
    here_files -= set(reloc_here.values())
    base_files -= set(reloc_base.values())

    # 1. Differences 1 and 3 are REQUIREMENTS, not merely permissions.
    #
    # `absent-here` and `inherited-from-account` used to be read in one place
    # only - as an excuse for a baseline file to be missing here. Nothing said
    # the converse, so copying one back in passed silently: the baseline's
    # `src/` tree, or a community health file, or an ISSUE_TEMPLATE form, all
    # byte-identical and therefore invisible to the shared-file comparison.
    # Two of the five differences had no gate at all.
    #
    # Checked first, and the offenders are lifted out, so the loops below
    # report each path once rather than twice.
    forbidden: set[str] = set()
    for f in sorted(here_files):
        prefix = prefix_covering(f, absent)
        if prefix is not None:
            forbidden.add(f)
            problems.append(
                f"{f}: difference 1 imposes no structure here, so `{prefix}` must not exist "
                f"in this repository. Remove it, or stop claiming difference 1."
            )
            continue
        prefix = prefix_covering(f, inherited)
        if prefix is not None:
            forbidden.add(f)
            problems.append(
                f"{f}: difference 3 inherits the community health files from the account, "
                f"and a local `{prefix}` OVERRIDES the inherited one - silently, for this "
                f"repository only. Remove it, or stop claiming difference 3."
            )
    checked += len(forbidden)
    here_files -= forbidden

    # 2. In the baseline, absent here: permitted only by difference 1 or 3.
    for f in sorted(base_files - here_files):
        checked += 1
        if not covered_by(f, absent) and not covered_by(f, inherited):
            problems.append(
                f"{f}: present in the baseline and missing here, and the contract does not "
                f"permit its absence."
            )

    # 3. Here but not in the baseline: only the contract's own enforcement.
    for f in sorted(here_files - base_files):
        checked += 1
        if not covered_by(f, enforcement):
            problems.append(
                f"{f}: present here and absent from the baseline. Only the relocated seed tree "
                f"and the contract's own enforcement may exist only in this repository."
            )

    # 4. Shared files must be byte-identical unless named.
    for f in sorted(here_files & base_files):
        checked += 1
        if (here / f).read_bytes() != (base / f).read_bytes() and f not in may_differ:
            problems.append(
                f"{f}: differs from the baseline and is not listed in content-may-differ. "
                f"Fix the drift, or add it with the reason it is permitted."
            )

    # 5. The relocated seeds: same set of documents, identical but for the footer.
    for key in sorted(set(reloc_base) - set(reloc_here)):
        checked += 1
        problems.append(f"{seed_path(relocated, key)}: seeded in the baseline, missing here.")
    for key in sorted(set(reloc_here) - set(reloc_base)):
        checked += 1
        problems.append(f"{seed_path(relocated, key)}: seeded here, absent from the baseline.")

    for key in sorted(set(reloc_here) & set(reloc_base)):
        src, rel = key
        checked += 1
        try:
            here_text = (here / reloc_here[key]).read_text(encoding="utf-8")
            base_text = (base / reloc_base[key]).read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            problems.append(
                f"{reloc_here[key]}: not valid UTF-8 ({exc.reason}), so it cannot be "
                f"compared against its baseline counterpart."
            )
            continue

        here_footer = footer_of(here_text, markers)
        base_footer = footer_of(base_text, markers)

        # Difference 4 applies to EVERY seed, exception or not. An exception
        # widens what a document may differ by; it does not waive what it must
        # differ by. This used to be a bare `continue` above the whole
        # comparison, so the two index documents - the first thing a new owner
        # reads - could be replaced wholesale, or carry the baseline's MIT
        # footer, and the check still printed "0 problem(s)".
        #
        # Absence is the case a "footers must differ" test misses: no footer
        # at all trivially differs from one. A seed that DROPPED its footer is
        # the more likely accident of the two, and the more expensive.
        if base_footer and not here_footer:
            problems.append(
                f"{reloc_here[key]}: the baseline carries a licence footer and this copy "
                f"carries none. Difference 4 requires a proprietary footer here, not the "
                f"absence of one."
            )
        elif here_footer and here_footer == base_footer:
            problems.append(
                f"{reloc_here[key]}: carries the same licence footer as its baseline "
                f"counterpart, which difference 4 requires to differ."
            )
        elif rel not in seed_exceptions and strip_footer(here_text, markers) != strip_footer(
            base_text, markers
        ):
            # What an exception waives, and all it waives: the body. Those two
            # documents name the seed path in prose, which is true on one side
            # and not the other.
            problems.append(
                f"{reloc_here[key]}: differs from its baseline counterpart by more than the "
                f"licence footer. Seed documents must be identical apart from it - use a "
                f"RELATIVE cross-link, which resolves the same at either depth."
            )

    # An exception that no longer differs is stale permission: report it, but
    # do not fail on it, since it describes a repository that got tidier.
    for rel, reason in sorted(seed_exceptions.items()):
        for key in sorted(k for k in reloc_here if k[1] == rel and k in reloc_base):
            if (here / reloc_here[key]).read_bytes() == (base / reloc_base[key]).read_bytes():
                print(
                    f"::notice title=Stale exception::{rel} is listed as a seed exception "
                    f"({reason}) but is now byte-identical. Remove the entry."
                )

    # The same courtesy for `content-may-differ`, which had none. Membership
    # alone exempted a file from comparison, so an entry could go on excusing
    # a difference that had stopped existing - and, worse, could excuse the
    # WRONG difference: nothing asserted that LICENSE still holds a
    # proprietary notice rather than the baseline's MIT text. Difference 4 is
    # the one README.md says "propagates to everything generated from here".
    #
    # A notice rather than a failure, matching the rule above: this file
    # describes a repository that got tidier, not one that broke.
    for rel, reason in sorted(may_differ.items()):
        here_path, base_path = here / rel, base / rel
        if here_path.is_file() and base_path.is_file():
            if here_path.read_bytes() == base_path.read_bytes():
                print(
                    f"::notice title=Stale permission::{rel} is listed in content-may-differ "
                    f"({reason}) but is now byte-identical to the baseline. Either the "
                    f"difference it names is gone - remove the entry - or it was lost by "
                    f"accident, which is the drift this check exists to catch."
                )
        elif not here_path.exists() and not base_path.exists():
            print(
                f"::notice title=Stale permission::{rel} is listed in content-may-differ "
                f"({reason}) but exists in neither tree. Remove the entry."
            )

    for p in problems:
        print(f"::error title=Template drift::{p}")

    verdict = (
        f"{checked} path(s) compared against {contract.get('baseline')}, {len(problems)} problem(s)."
    )
    print(f"\n{verdict}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("### 📐 Template parity\n\n" + verdict + "\n")
            for p in problems:
                handle.write(f"\n- ❌ {p}\n")
            if problems:
                handle.write(
                    "\n> [!NOTE]\n> The contract is `.github/template-parity.yml`. "
                    "Prefer fixing the drift over widening the allow-list.\n"
                )

    return 1 if problems else 0


def seed_path(relocated: dict[str, str], key: tuple[str, str]) -> str:
    """Where a relocated seed lives HERE, e.g. '.github/docs/templates/ADR.md'.

    Derived from the key's own relocation rather than from the first entry in
    the mapping, so a second relocation is labelled with its own destination
    instead of borrowing the first one's.
    """
    src, rel = key
    return f"{relocated.get(src, src)}/{rel}"


if __name__ == "__main__":
    sys.exit(main())
