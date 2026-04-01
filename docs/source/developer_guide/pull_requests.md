# Pull requests and git conventions

## Making a pull request

1. Ensure your bug fix or feature has a **corresponding [GitHub issue](https://github.com/aiidateam/aiida-core/issues)**.
   Search first to avoid duplicates; if no issue exists, open one.

1. Create a new branch using the naming convention `<prefix>/<issue>/<short_description>`:

   ```console
   $ git switch -c fix/1234/querybuilder_improvements
   ```

   Common prefixes: `feature/`, `fix/`, `docs/`, `ci/`, `refactor/`.

1. Add your changes and commit them:

   - If it's a bug fix, {doc}`add a test <writing_tests>`.
   - If it's a new feature, {doc}`document it <writing_documentation>` and {doc}`add tests <writing_tests>`.

1. Push your branch to your fork:

   ```console
   $ git push origin fix/1234/querybuilder_improvements
   ```

1. [Create a pull request](https://github.com/aiidateam/aiida-core/compare) from your fork to `main`:

   - Only open the PR when it is ready for review — each push triggers CI builds and, possibly, email notifications.
   - Use the PR title to describe its contents.
     **Bad:** "Fix issue 1234". **Good:** "Fix QueryBuilder ordering for `Group` entities".
   - If there is a related issue, link it in the PR description (e.g., write `Fixes #1234`) or use the GitHub UI sidebar to link it directly.
   - Aim for a reasonable number of lines changed for effective review.

1. Fix any failing CI checks until you get the green check mark.

### CI requirements

All PRs must:

- Pass pre-commit checks (`uv run pre-commit run`): coding style and static analysis
- Pass all tests
- Build the documentation without warnings

### After opening

- Address review feedback with new commits — they will be squashed on merge anyway.
- If you need to rewrite history (e.g., rebase or amend), use `git push --force-with-lease` instead of `--force` to avoid accidentally overwriting changes pushed by others.

## Commit guidelines

### Structure

A commit:

- Should ideally address **one issue**.
- Should be a **self-contained** change to the code base.
- Must **not** lump together unrelated changes.

### Commit messages

Follow the **50/72 rule**:

```text
Short summary in imperative mood (50 chars max)

More detailed explanatory text, if necessary. Wrap it to 72
characters. The blank line separating the summary from the body
is critical.

Explain the problem that this commit is solving. Focus on why
you are making this change as opposed to how (the code explains
that).

 * Bullet points are okay, too

Put references to issues in the description of your pull request,
not in the commit message.
```

Rules:

- Separate subject from body with a blank line
- Limit the subject line to **50 characters** — keeps `git log --oneline` readable without truncation
- Wrap the body at **72 characters** — matches the traditional terminal width for `git log` output
- Capitalize the subject line
- Do not end the subject line with a period
- Use the imperative mood in the subject line ("Add feature", not "Added feature") — reads as an instruction applied to the codebase ("if applied, this commit will...")
- Use the body to explain *what* and *why*, not *how*
- Merged PRs (via squash) append the PR number: `Fix bug in QueryBuilder (#1234)`

:::{tip}
Some contributors use emoji prefixes as a semantic type indicator in commit messages.
This saves characters in the subject line, gives a quick visual overview of the types of changes, and makes it easy to sort or filter commits.
The emoji replaces the type prefix, so write `🐛 QueryBuilder crashes on empty filter`, not `🐛 Fix: QueryBuilder crashes on empty filter`.

| Emoji | Meaning |
|-------|---------|
| `✨` | New feature |
| `🐛` | Bug fix |
| `👌` | Improvement (no breaking changes) |
| `‼️` | Breaking change |
| `📚` | Documentation |
| `🔧` | Maintenance (typos, etc.) |
| `🧪` | Tests or CI changes only |
| `♻️` | Refactoring |

This convention follows [MyST-Parser](https://github.com/executablebooks/MyST-Parser/blob/master/AGENTS.md#commit-message-format) and is optional.
:::

## Merging strategies (maintainers)

| Strategy | When to use |
|----------|-------------|
| **Squash and merge** | Single-issue PRs — one clean commit. Clean the commit message (title and body). |
| **Rebase and merge** | Multi-commit PRs with individually significant commits. |

In practice, most PRs are squash-merged, so a clean commit history on the branch is nice to have but not required — the squash takes care of it.
For rebase-and-merge, each commit should be self-contained and meaningful.
