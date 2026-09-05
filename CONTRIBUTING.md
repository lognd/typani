# Contributing to typani

Thanks for considering a contribution. This document has two paths
through it: a short summary if you already know how open-source
contribution works, and a full walkthrough if this is your first time.
Read whichever one applies; both point at the same commands.

## TL;DR for experienced contributors

- Fork the repo, clone your fork, add `lognd/typani` as `upstream`.
- `uv sync --all-groups` installs typani plus every dev dependency group.
- `uv run python scripts/develop.py` builds the optional native crate in
  place (`maturin develop`); optional, the pure-Python backend works
  without it.
- `uv run python scripts/check.py` is the gate: it runs `frob check`
  (when frob is installed) plus the test suite under both backends
  (the active backend, and again with `TYPANI_PURE=1`). Green here before you open a PR.
- ruff formats and lints (`uv run ruff format`, `uv run ruff check --fix`);
  ty type-checks (`uv run ty check`).
- Commit format: `<type>(<scope>): <imperative summary, 72 chars max>`.
  Types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `perf`,
  `ci`, `build`. No trailing period. One logical change per commit.
- ASCII only in every file, no exceptions.
- New modules start with `from __future__ import annotations` as the
  first import.
- Every public symbol gets a one-line docstring (WHY/WHAT, not a
  restatement of the name).
- Every fallible operation a caller must handle returns a typani
  `Result[T, E]`; exceptions are for programmer bugs, not expected
  failure.
- Tests are bound to the code they exercise with `# frob:tests
  path::Class.method` where frob is in use.
- Fill in every box of `.github/PULL_REQUEST_TEMPLATE.md`; an unchecked
  box with no explanation will slow down review.

## Your first contribution (step by step)

If you have never opened a pull request against someone else's project
before, this section is for you. None of the steps below are specific to
typani; they are the standard GitHub flow, spelled out.

### 1. Fork the repository

A "fork" is your own copy of the project on GitHub, which you can push
to freely without needing write access to the original. Open
[github.com/lognd/typani](https://github.com/lognd/typani) and click
"Fork" in the top right.

### 2. Clone your fork

```bash
git clone https://github.com/<your-username>/typani.git
cd typani
git remote add upstream https://github.com/lognd/typani.git
```

The `upstream` remote lets you pull in changes from the real project
later (`git fetch upstream`).

### 3. Install uv

typani uses [uv](https://docs.astral.sh/uv/) for dependency management
and running scripts. Install it following the instructions at
[docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/).
You do not need to install Python separately; uv manages that too.

### 4. Install dependencies

```bash
uv sync --all-groups
```

This creates a `.venv` and installs typani itself plus every group
needed for development (tests, linting, type checking).

### 5. Run the tests once, to see green

```bash
uv run pytest -q
```

Everything should pass on a clean checkout. If it does not, something is
wrong with your environment, not with your (not-yet-written) change --
worth checking before you go further.

### 6. Make a small change

Pick something small for your first PR: a typo in a docstring, a missing
test, a small bug. Big changes are much easier to review -- and much
more likely to be accepted -- once you have a merged PR or two behind
you. See ["What makes a good change"](#what-makes-a-good-change) below.

### 7. Run the local gate

```bash
uv run python scripts/check.py
```

On Windows, or any platform without `make`, every script under
`scripts/` runs the same way: `uv run python scripts/<name>.py`. There
is no separate Windows instruction set.

If you do not have `frob` installed, pass `--skip-frob`:

```bash
uv run python scripts/check.py --skip-frob
```

### 8. Commit your change

```bash
git add path/to/changed_file.py
git commit -m "fix(result): correct off-by-one in note ordering"
```

See the [commit format](#tldr-for-experienced-contributors) above. Small,
focused commits are easier to review than one giant commit at the end.

### 9. Push a branch and open the PR

```bash
git checkout -b fix/note-ordering
git push -u origin fix/note-ordering
```

Then open a pull request from your fork's branch against
`lognd/typani`'s `main` branch on GitHub. Fill in
`.github/PULL_REQUEST_TEMPLATE.md` completely -- it appears automatically
when you open the PR.

### 10. What review looks like

A maintainer will read the diff, run the gate, and either approve,
request changes, or ask questions in the PR thread. Expect comments even
on a good change -- that is normal review, not a sign something is
wrong. Push additional commits to the same branch to address feedback;
no need to open a new PR.

### 11. If CI is red

Click through to the failing check and read the log; it will point at
the failing test or lint rule. Fix it locally, re-run
`uv run python scripts/check.py`, and push again. If the failure looks
unrelated to your change (flaky test, infrastructure issue), say so in
the PR thread rather than guessing at a fix.

## What makes a good change

- **Small scope.** One logical change per PR. A PR that touches
  `Result`, the lint tool, and the release script at once is very hard
  to review and very easy to get wrong.
- **A test that fails before and passes after.** If you cannot write
  such a test, it is worth asking whether the change is well specified
  yet.
- **Docs updated in the same change.** If the change touches a
  documented symbol, update the matching page under `docs/*.md` and keep
  its `frob:doc` anchor comment pointed at the right symbol in the same
  commit, not a follow-up.
- **No new dependencies without discussion.** Open an issue first if you
  think typani needs one; the library's whole point is being small and
  dependency-light.
- **Performance changes come with numbers.** Run
  `bench/bench_result.py` under both backends
  (`uv run python bench/bench_result.py` and
  `TYPANI_PURE=1 uv run python bench/bench_result.py`) and include the
  before/after numbers in the PR description.

## How this repo is enforced: frob

This repository is enforced by [frob](https://github.com/lognd/frob), an
obligation graph over the code plus a git-tracked ticket ledger
(`tickets.md`) plus a set of gates that fail `frob check` when work is
unaccounted for -- a changed symbol with no ticket, a public function
with no test, a doc that drifted out of sync with the code it describes.

frob is pre-release and not yet on PyPI, so CI does **not** run it; the
maintainer runs `frob check` locally, and it is the actual merge gate
even though GitHub's checks will not show it.

You do not need frob installed to contribute. What you will see in the
code, and what you should do with it:

| Directive | Meaning | What to do as a contributor |
|-----------|---------|------------------------------|
| `# frob:doc docs/x.md#anchor` | This symbol is described at that doc anchor; if the doc drifts out of sync with the code, the gate fails. | Keep it pointed at the right anchor if you move or rename the symbol; update the doc in the same commit. |
| `# frob:ticket T-0042` | This code is accounted for by ticket T-0042 in `tickets.md`. | Leave it as-is; the maintainer files/updates the ticket at merge time. |
| `# frob:tests path::symbol` | This test is bound as evidence for the given source symbol. | Add the same style of binding on new tests you write, matching a neighboring example. |
| `# frob:todo T-0042 note` | A deliberately deferred piece of work, tracked against an open ticket. | Never write a bare `# TODO` in this repo; if you have no ticket id, describe the deferral in the PR and the maintainer adds the directive. |
| `# frob:waive RULE reason="..."` | An explicit, visible exception to a gate rule, with a stated reason. | Do not add one yourself unless you understand the rule being waived; ask in the PR if you think one is needed. |

The ticket ledger (`tickets.md`) has one section per ticket, each with a
`state` of `queued`, `planned`, `in-progress`, `done`, or `dropped`. As
an external contributor you do not need to touch `tickets.md` yourself
-- the maintainer files or closes the relevant ticket when your PR
lands. Your job is simpler: keep whatever `frob:` directives you find
intact, and mirror the neighboring style when you add a new public
symbol or test.

## AI-assisted contributions

AI-assisted contributions are welcome under the following policy, which
is deliberately strict. The rules exist so that AI assistance moves work
off reviewers rather than onto them: a generated diff nobody has read is
review work transferred to the maintainer, not a contribution.

**(a) Disclosure.** Say in the PR description which tool you used and
roughly how (drafted the initial patch, reviewed and edited an
AI-drafted patch, wrote tests with AI assistance, and so on). The PR
template has a line for this; fill it in honestly.

**(b) You are the author.** You are responsible for every line, whether
you or a model typed it. You must be able to explain any part of the
diff if asked in review. "The model said so" is not an acceptable answer
to a review question -- if you cannot explain why a line is there, it
should not be in the PR yet.

**(c) Not accepted:**

- An unreviewed, unedited AI-generated PR submitted as-is.
- A PR description that was clearly not written for this specific repo
  (generic boilerplate, wrong project name, invented capabilities).
- A bulk or sweeping change with no prior issue discussing it.
- Generated tests that only assert the current behavior of the code
  (a test that would pass on a buggy implementation just as easily as a
  correct one is not a test).

**(d) If you are an AI agent working in this repository:**

These are the house rules an agent must follow here, written directly to
the agent, not to whoever is dispatching it.

- Run `uv run python scripts/check.py` before claiming a task is done.
  A gate you did not run is not a gate you can claim passed.
- Use frob as the accounting layer whenever it is available on the
  host: `frob ticket doable` to find work, `frob ticket start` to claim
  a ticket, work strictly inside that ticket's declared scope, `frob
  check` to gate the change. Close a ticket in this exact order: record
  evidence first (test node ids bound to the ticket), then write the
  done report (it captures the evidence count that already exists at
  that point), then close the ticket. Doing this out of order produces a
  done report with a wrong or missing evidence count.
- Keep every `frob:` directive you encounter intact. Add matching
  directives (`frob:doc`, `frob:tests`, `frob:ticket`) on new public
  symbols you introduce, following the nearest existing example.
- Never leave a bare `# TODO`. Use `# frob:todo T-#### note` bound to
  an open ticket. If you have no ticket id, describe the deferred work
  in the PR and the maintainer files the ticket and adds the directive.
- Check for misuse of typani's own types in anything you write by
  running `python -m typani.lint` over the paths you touched.
- Every fallible operation returns a `Result`; raise exceptions only for
  programmer bugs (contract violations, unreachable states), never for
  expected failure paths.
- ASCII only, in every file you touch, no exceptions.
- Never read or write `.env` files, directly or indirectly.
- Never amend a commit that has already been pushed; create a new
  commit instead.
- Follow the commit format above exactly. Never add a `Co-Authored-By`
  trailer or any other attribution line to a commit message.
- Report honestly. If a gate is red, say so in the PR or the task
  report -- do not narrow the scope of what you claim to have done
  without saying that you did. A silently narrowed claim is worse than
  an honest "this part failed."
- An agent-authored PR still needs a named human contributor who takes
  authorship responsibility for it, per (b) above. An agent does not
  merge its own PR.

## Reporting bugs and proposing features

Use the issue forms:

- [Bug report](.github/ISSUE_TEMPLATE/bug_report.yml)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.yml)

For a `typani.lint` false positive specifically, please include the
minimal snippet that triggers it and the JSON finding
(`python -m typani.lint --json <path>`) in the bug report -- both make
it much faster to confirm and fix.

## Release process (maintainers)

Releases go through `.github/workflows/release.yml` (manual dispatch
only): it refuses to publish unless CI is green for the exact commit,
builds the pure wheel and the five-platform native wheel matrix with
maturin, and publishes both distributions through PyPI trusted
publishing. `uv run python scripts/release.py` is the local front door
(dirty-tree check, coupled version bump, build, `uv publish`, tag and
push; see its docstring for `--bump`, `--set`, `--tag`, `--push`,
`--dry-run`) and can only build this machine's native wheel.
`typani` and `typani-core` are version-coupled: the `native` extra pins
`typani-core==<typani's own version>` exactly, never `>=`/`~=`, because
the two are built and released together and a loose pin risks an ABI
mismatch that the backend selector would otherwise have to detect and
fall back around at runtime.

## License

By contributing to typani, you agree that your contributions are
licensed under the project's MIT license (see [LICENSE](LICENSE)).
