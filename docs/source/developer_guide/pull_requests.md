# Pull requests and git conventions

## Making a pull request

### Step-by-step

1. Ensure your bug fix or feature has a **corresponding GitHub issue**.
   If not, [open one](https://github.com/aiidateam/aiida-core/issues).

2. Create a new branch using the following naming convention:

   ```console
   $ git checkout -b issue_1234_short_description_of_issue
   ```

3. Add your changes and commit them:
   * If it's a bug fix, {doc}`add a test <writing_tests>`.
   * If it's a new feature, {doc}`document it <writing_documentation>` and {doc}`add tests <writing_tests>`.

4. Push your branch to your fork:

   ```console
   $ git push origin issue_1234_short_description_of_issue
   ```

5. [Create a pull request](https://github.com/aiidateam/aiida-core/compare) from your fork to the correct branch of `aiidateam/aiida-core`:
   * Only open the PR when you believe your changes are ready to merge.
     Each push to an open PR triggers email notifications and CI builds.
   * Use the PR title to describe its contents.
     **Bad:** "Fix issue 1234". **Good:** "quicksetup now works without sudo".
   * Mention the issue number in the PR *description*.

6. Fix any failing CI checks until you get the green check mark.

### CI requirements

All PRs must:

* Pass pre-commit checks (coding style and static analysis)
* Pass all tests
* Build the documentation without warnings

## Commit guidelines

### Structure

A commit:

* Should ideally address **one issue**.
* Should be a **self-contained** change to the code base.
* Must **not** lump together unrelated changes.

Use `git rebase` to clean up your commit history before opening a PR.
See tutorials on [git-scm.com](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) and [Atlassian](https://www.atlassian.com/git/tutorials/rewriting-history/git-rebase).

### Commit messages

```text
Summarize changes in 72 characters or less

More detailed explanatory text, if necessary. Wrap it to 72 characters.
The blank line separating the summary from the body is critical.

Explain the problem that this commit is solving. Focus on why you are
making this change as opposed to how (the code explains that).

 * Bullet points are okay, too

Put references to issues in the description of your pull request, not
in the commit message.
```

Rules:

* Separate subject from body with a blank line
* Limit the subject line and body to 72 characters
* Capitalize the subject line
* Do not end the subject line with a period
* Use the imperative mood in the subject line
* Use the body to explain *what* and *why*, not *how*
* No need to mention you added unit tests -- the diff makes that clear

## Pull request etiquette

* Open a PR only when it is ready for review.
  Each push triggers notifications and CI builds, consuming the organization's quota.
* Clean up commit history before opening (use `git rebase` and `git commit --amend`).
* Do **not** manually merge the base branch to bring your PR up to date.
  The reviewer will handle it after the review is completed.
* If a reviewer requests minor changes, use `git commit --amend` instead of creating new commits (unless the PR will be squashed anyway).

## Merging strategies

| Strategy | When to use |
|----------|-------------|
| **Squash and merge** | PR addresses a single issue, well-represented by one commit. Clean the commit message (title and body). |
| **Rebase and merge** | PR requires multiple individually significant commits, or has commits from different authors. |
| **Merge with merge commit** | Collaborative PRs with many commits where the merge commit adds clarity. |

If you are unsure what strategy to use, **do not merge**. Ask a maintainer.
