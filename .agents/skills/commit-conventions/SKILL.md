---
name: commit-conventions
description: Use for commits, branch names, and pull requests.
---

# Commit and PR conventions

## Branches and versions

* Develop through PRs against `main`.
* Branches: `<prefix>/<issue>/<short-description>`, e.g. `fix/1234/querybuilder-improvements`.
* [SemVer](https://semver.org/); `.dev0` marks development toward the next version (`main` targets `v3.0.0`, so `3.0.0.dev0`).
* The plan for v3 is the `aiida._core`/user-API split: internals move to `aiida._core`, the user API delegates to it (see `AGENTS.md`). Breaking changes and schema migrations are acceptable while working toward v3 when they improve the design; record each in `CHANGELOG.md` under `Unreleased` → `Breaking changes`.

## Messages (not enforced)

* Subject: emoji, backticked scope, imperative description, e.g. `📚 \`Node\`: Store UUID on first save`. At most 50 characters, capitalized after the scope, no final period.
* Body: blank line after subject, 72-column wrapping, what and why.
* One issue per self-contained commit; supports bisecting and reverting.
* Issue links in PR description or GitHub UI; squash merges append `(#1234)`.

## Emoji prefixes (up for discussion)

Optional type prefixes; omit redundant labels such as `Fix:`.
May be formalized or dropped. Adapted from [MyST-Parser](https://github.com/executablebooks/MyST-Parser/blob/master/AGENTS.md#commit-message-format).

* `✨` New feature: `feature/`
* `🐛` Bug fix: `fix/`
* `👌` Improvement (no breaking changes): `improve/`
* `💥` Breaking change: `breaking/`
* `📚` Documentation: `docs/`
* `🧹` Maintenance and fixes: `chore/`
* `🧪` Tests: `test/`
* `🔧` CI: `ci/`
* `♻️` Refactoring: `refactor/`
* `📦` Dependencies: `deps/`
* `🚀` Release: `release/`
* `❌` Deprecation: `deprecate/`
* `⏪` Revert: `revert/`

## Pull requests

* Description and issue links; tests for features/fixes; docs for features/behavior changes.
* Passing `uv run pre-commit`.
* Merge: squash single-issue PRs; rebase individually significant multi-commit PRs.
* Bulk formatting: landed SHA in `.git-blame-ignore-revs`.
