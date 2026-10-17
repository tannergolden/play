# Play: notes for Claude

Standing rules from the owner, for every session that works on this repository.

## Nothing private is ever named here

This repository is public, and so is everything it publishes: its issues, the intake's and the sweep's replies, and
every run's log. Apart from the template, tannergolden/repo, which these documents name by design, no private
repository of this account is ever named, linked or described here: not in a file, a commit message, a pull
request's title or description, an issue, a comment, a release note or a workflow's output.

- Speak of such a repository by its role, never by its name, and read every diff and message for one before it goes
  out.
- Name only the public repositories this one already works with: tannergolden/tannergolden, tannergolden/markdown and
  tannergolden/standards. When you can't tell whether a repository is public, leave it out.
- Should a private repository turn up named here, take it out at once and tell the owner. Rewriting history to purge
  it waits for the owner's word.

## The games are proprietary

- Everything here is proprietary under [LICENSE](LICENSE), all rights reserved
  ([ADR-0002](docs/adrs/ADR-0002-The-Games-Are-Proprietary.md)). Add nothing under an open licence; a third-party
  component keeps its own.

## Moves and their issues

- 🎲 Move Intake gives every issue it answers the Official Arbiter's 👀, sends each move on with a 🚀 and leaves its
  issue open, and the game's Arbiter answers it there, labels it `played` or `turned away`, files it in its game's
  milestone and closes it. A move turned away at the door is labelled `turned away` and closed here; one that never
  reaches its game is labelled `stranded`.
- ⏳ Move Sweep marks a move sent on but unruled after 15 minutes `overdue`, and sends stranded and overdue moves
  through the intake again once the outage notice is closed.
- Never open, comment on, label, lock or close an issue here, or start a workflow, from a test or by hand. The tests
  reach no network: stand-ins only.

## Working here

- The scripts are standard-library Python, with their tests beside them. Run Python with the tokens unset:
  `env -u GH_TOKEN -u GITHUB_TOKEN python3 -m unittest discover -s intake -p 'test_*.py'`, and the same for
  `replays` and `.github/scripts`.
- Before a push: those tests, `python3 .github/scripts/validate-repository.py`, and actionlint (with shellcheck) and
  zizmor on the workflows.
- Redraw the `AUTO-INDEX` tables in the same commit:
  `python3 <standards>/scripts/update-doc-indexes.py --tree --write`, from tannergolden/standards at `v1`.
- A change to how a move is answered updates everything that tells it, in the same commits: the README, the
  intake's README, the move form, `docs/GitHub-App.md`, and the header comments of the workflows and the scripts.

## Commits

- Conventional Commits with an emoji and a scope, such as `feat(intake): 👀 mark every issue seen`: a subject under 72
  characters, and a body wrapped at 72.
- The author is Tanner Golden <24684994+tannergolden@users.noreply.github.com>, and the last trailer signs it off as
  the owner: `Signed-off-by: Tanner Golden <24684994+tannergolden@users.noreply.github.com>`. The committer stays this
  environment's own, whose key signs the commit.
- Work lands on Development. Never force-push, and never rewrite its history.

## Writing

- No em or en dashes anywhere, chat replies included.
