---
name: commit-conventions
description: Use when making commits, creating branches, or preparing pull requests for aiida-core.
---

# Commit and PR conventions for aiida-core

## Branching and versioning

- All development happens on `main` through pull requests.
- Recommended branch naming convention: `<prefix>/<issue>/<short_description>`
  - Prefixes: `feature/`, `fix/`, `docs/`, `ci/`, `refactor/`
  - Example: `fix/1234/querybuilder-improvements`
- The `main` branch uses a `.post0` version suffix to indicate development after the last release (e.g., `2.6.0.post0` = development after `2.6.0`).
- Versioning follows [SemVer](https://semver.org/) (major.minor.patch).

## Commit style (not enforced)

Follow the **50/72 rule**:

- Subject line: max 50 characters, imperative mood ("Add feature", not "Added feature"), capitalized, no period
- Body: wrap at 72 characters, explain *what* and *why* (the code shows *how*)
- Merged PRs (via squash) append the PR number: `Fix bug in QueryBuilder (#1234)` (GH web UI automatically appends on squash-merge)
- Some contributors use emoji prefixes as a semantic type indicator (see below)

```
Short summary in imperative mood (50 chars)

More detailed explanation wrapped at 72 characters. Focus on
why the change was made, not how.
```

Guidelines:

- One issue per commit, self-contained changes: makes bisecting and reverting safe
- Link GitHub issues either via the PR description or the GH web UI.

## Emoji prefixes (up for discussion)

The following practices are used by some contributors but not consistently adopted.
They may be formalized or dropped in the future.

Some contributors use emojis as a one-character semantic type prefix.
The emoji *is* the type indicator, so the message after it should be just the description: write `🐛 QueryBuilder crashes on empty filter`, not `🐛 Fix: QueryBuilder crashes on empty filter`.
Emoji selection is adapted from [MyST-Parser](https://github.com/executablebooks/MyST-Parser/blob/master/AGENTS.md#commit-message-format):

| Emoji | Meaning | Branch Prefix |
|-------|---------|---------------|
| `✨` | New feature | `feature/` |
| `🐛` | Bug fix | `fix/` |
| `🚑` | Hotfix (urgent production fix) | `hotfix/` |
| `👌` | Improvement (no breaking changes) | `improve/` |
| `‼️` | Breaking change | `breaking/` |
| `📚` | Documentation | `docs/` |
| `🔧` | Maintenance (typos, etc.) | `chore/` |
| `🧪` | Tests or CI changes only | `test/` |
| `♻️` | Refactoring | `refactor/` |
| `⬆️` | Dependency upgrade | `deps/` |
| `🔖` | Release | `release/` |

## Pull request requirements

When submitting changes:

1. **Description**: Include a meaningful description explaining the change and link to related issues
2. **Tests**: Include test cases for new functionality or bug fixes
3. **Documentation**: Update docs if behavior changes or new features are added
4. **Code quality**: Ensure `uv run pre-commit` passes

Merging (maintainers): **Squash and merge** for single-issue PRs, **rebase and merge** for multi-commit PRs with individually significant commits.

## Git tooling

The `.git-blame-ignore-revs` file lists commits that should be ignored by `git blame` (e.g., bulk reformatting).
When landing a large-scale formatting-only commit, add its SHA to this file.
