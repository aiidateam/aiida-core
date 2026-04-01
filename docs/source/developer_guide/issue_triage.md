# Issue triage

Good practices for [triaging](https://www.merriam-webster.com/dictionary/triage) issues on the AiiDA GitHub repository.

## First response

### Bugs

1. **Try to reproduce the bug** (this is not optional).
   If it is not obvious how, ask the issue creator for steps to reproduce.
1. If you cannot reproduce it, investigate whether it has already been fixed on `main`.
1. Comment with whether you managed to reproduce or not, including the steps you took.
1. Think about possible causes, solutions, and tests. Mention everything in the comments and `@mention` relevant developers.
1. If possible, estimate the time/effort required, or ask other developers.
1. If you know how to solve it and it is easy, assign it to yourself and solve it.

### Feature requests

1. Ensure the use case for the feature is clear. If not, ask for clarification.
1. Ensure the feature is limited in scope and clearly defined.
1. Estimate the effort required, or `@mention` people who might know.

### Questions

1. Respond to the question, or `@mention` developers who might know.
1. Point to the [Discourse forum](https://aiida.discourse.group/).
1. Consider reposting the question and answer on Discourse.

## Choosing labels

The full list of labels is at [github.com/aiidateam/aiida-core/labels](https://github.com/aiidateam/aiida-core/labels).
Labels are organized into the following categories.

### `type/` — issue type

Assign one `type/` label (mutually exclusive):

- `type/bug`: a defect in existing functionality
- `type/feature request`: a proposed new feature (status undecided)
- `type/accepted feature`: a feature request with allocated development time
- `type/enhancement`: an improvement to an existing feature
- `type/performance`: related to how quickly AiiDA works
- `type/refactoring`: internal restructuring without changing behavior
- `type/usability`: user experience improvements
- `type/task`: a concrete task (e.g., documentation, CI, cleanup)
- `type/question`: a question about usage or behavior
- `type/backwards-incompatible`: changes that are most likely backwards-incompatible

Closure labels (applied when closing without a PR):

- `type/wontfix`: the team decided not to fix or implement this
- `type/duplicate`: duplicates an existing issue (link to the original)

:::{note}
Do not label a feature request as `type/accepted feature` unless development time is allocated.
Ensure the scope and use case are clear before accepting.
:::

### `priority/` — priority

- `priority/critical-blocking`: must be resolved before the next release
- `priority/important`: significant impact, should be addressed soon
- `priority/nice-to-have`: not crucial to stable, reliable, user-friendly operation
- `priority/quality-of-life`: would simplify development of `aiida-core`

Always **comment on why you assign a specific priority**.

### `topic/` — area of the codebase

Use `topic/*` labels to categorize which area of the codebase is affected.
These help developers filter for issues in their area of expertise.
Common examples: `topic/engine`, `topic/orm`, `topic/verdi`, `topic/transports`, `topic/storage`, `topic/documentation`, `topic/daemon`, `topic/processes`, `topic/query-builder`.

### Contribution level

These labels indicate who should work on an issue ([#7226](https://github.com/aiidateam/aiida-core/issues/7226)):

- `good first issue`: issues that should be relatively easy to fix, also for beginning contributors. This is an [officially recognized GitHub label](https://github.com/topics/good-first-issue) that surfaces issues to new contributors.
- `help wanted`: more complex issues open for experienced external contributors
- `maintainer only`: fundamental, large, and/or technical changes reserved for internal contributions by the core team

### `pr/` — pull request workflow

These labels track the state of pull requests:

- `pr/ready-for-review`: PR is ready to be reviewed
- `pr/work-in-progress`: PR still in progress but already needs discussion
- `pr/blocked`: PR is blocked by another PR that should be merged first
- `pr/on-hold`: PR should not be merged
- `pr/next-to-merge`: PR is next in line to be merged

### Other labels

- `requires discussion`: needs team discussion before implementation
- `requires db-migration`: the fix or feature will require a database migration
- `design-issue`: a software design issue that needs architectural input
- `AEP`: connected to an existing [AiiDA Enhancement Proposal](https://github.com/aiidateam/AEP)
- `test-release`: triggers the release workflow to publish to TestPyPI
- `dependencies`: auto-applied by Dependabot for dependency update PRs
- `github_actions`: auto-applied by Dependabot for GitHub Actions update PRs

## Assigning a developer

Assign **one** developer only. `@mention` others who might know more or be able to help.

## Closing issues

Before closing, attach a label explaining why and document your decision in a comment.

### Bugs

- Should be closed by a pull request.
- Exceptions: already fixed but forgotten to close, or cannot be reproduced by multiple developers and the reporter fails to provide additional information (label as `type/wontfix`).

### Feature requests

- Accepted features should be closed by a pull request.
- Feature requests can be closed with `type/wontfix` if the team decides the feature should not be implemented.
- Use `type/duplicate` if the issue duplicates an existing one (link to the original).

### Questions

- Close once the question is answered or too outdated. Leave a comment with the reason.
