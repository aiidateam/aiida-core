# Issue triage

Good practices for [triaging](https://www.merriam-webster.com/dictionary/triage) issues on the AiiDA GitHub repository.

## First response

### Bugs

1. **Try to reproduce the bug** (this is not optional).
   If it is not obvious how, ask the issue creator for steps to reproduce.
2. If you cannot reproduce it, investigate whether it has already been fixed on `main`.
3. Comment with whether you managed to reproduce or not, including the steps you took.
4. Think about possible causes, solutions, and tests. Mention everything in the comments and `@mention` relevant developers.
5. If possible, estimate the time/effort required, or ask other developers.
6. If you know how to solve it and it is easy, assign it to yourself and solve it.

### Feature requests

1. Ensure the use case for the feature is clear. If not, ask for clarification.
2. Ensure the feature is limited in scope and clearly defined.
3. Estimate the effort required, or `@mention` people who might know.

### Questions

1. Respond to the question, or `@mention` developers who might know.
2. Point to the [Discourse forum](https://aiida.discourse.group/).
3. Consider reposting the question and answer on Discourse.

## Choosing labels

### Issue type

Assign one of the four types (mutually exclusive):

* **bug**: a defect in existing functionality
* **feature request**: a proposed new feature (not yet accepted for implementation)
* **accepted feature**: a feature request with allocated development time
* **question**: a question about usage or behavior

:::{note}
Do not label a feature request as "accepted feature" unless development time is allocated.
Ensure the scope and use case are clear before accepting.
:::

### Priority

* **critical-blocking**: only for bugs or missing features that absolutely must be in the next release
* **nice to have**: for things not crucial to stable, reliable, user-friendly operation
* **quality of life**: for changes that make it easier for developers to work on `aiida-core`

Always **comment on why you assign a specific priority**.

### Other labels

Attach additional labels as appropriate. Comment on why you are attaching them.

## Assigning a developer

Assign **one** developer only. `@mention` others who might know more or be able to help.

## Closing issues

Before closing, attach a label explaining why (see [issue labels](https://github.com/aiidateam/aiida-core/labels)).
Document your decision in a comment.

### Bugs

* Should be closed by a pull request.
* Exceptions: already fixed but forgotten to close, or cannot be reproduced by multiple developers and the reporter fails to provide additional information (label as `wontfix`).

### Feature requests

* Accepted features should be closed by a pull request.
* Feature requests can be closed with `wontfix` if the team decides the feature should not be implemented.

### Questions

* Close once the question is too outdated. Leave a comment with the reason.
