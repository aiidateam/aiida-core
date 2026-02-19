# AiiDA policy on AI-assisted contributions

This document defines the [aiidateam organization's](https://github.com/aiidateam/) policy regarding AI-generated content.
This policy applies to all aspects of the AiiDA project, including all GitHub repositories under the `aiidateam` organization.

We expect to periodically review and update this policy as the landscape changes, and we welcome feedback via our [discussion channels](https://aiida.discourse.group/).

## Core philosophy

We recognize that AI tools have become part of the modern developer's toolbox and, as users of these tools ourselves, we would be dishonest to prohibit their use.
However, contributions must reflect genuine effort and understanding from the author&mdash;submitting AI-generated code without meaningful human input, verification, and comprehension is not acceptable.

**Every contributor bears full responsibility for what they submit.** You must understand, verify, and be able to explain every line of code, every comment, and every design decision in your PR.

## Contributor expectations

### Understand what you submit

Contributors must demonstrate genuine understanding of their changes and how they fit into the broader codebase.
If reviewers perceive a lack of understanding&mdash;from the code itself, PR descriptions, or interactions during review&mdash;we reserve the right to close the PR.

Before contributing, we encourage you to:

- Engage with the project and familiarize yourself with the codebase.
- Discuss proposed changes with maintainers (via a [GitHub issue](https://github.com/aiidateam/aiida-core/issues) or [Discourse](https://aiida.discourse.group/)) before opening a PR.
- Ensure you understand every line of the changes you submit.

### Verify your code locally

Before requesting review, contributors must ensure that:

- All CI checks pass (`pre-commit`, `ruff`, `mypy`).
- All tests pass (e.g., `uv run pytest ...`).
- Documentation builds without errors, if applicable.

PRs that fail CI and show signs of being unverified AI output will be closed.

### Curate your PR

All PRs must be thoughtfully authored&mdash;this includes the title, description, and commit messages.
Copy-pasting raw LLM output into PR titles or descriptions is not acceptable.
The PR description should clearly explain what the change does, why it is needed, and reference a related [GitHub issue](https://github.com/aiidateam/aiida-core/issues).

### Solve real problems

All PRs must address real issues that have been previously raised or discussed.
We only accept contributions that stem from genuine use of or engagement with AiiDA; unsolicited refactors, style-only changes, or speculative features that were not discussed with maintainers are not welcome.

## Review capacity and prioritization

With modern AI tools, large changes to a codebase can be produced with just a few prompts. The actual effort lies in reviewing the generated output, understanding how it integrates with the rest of the codebase, and verifying its downstream effects. This is particularly relevant given that the reviewing capacity for this project is very limited.
Large PRs that appear to lack understanding of the codebase may not get reviewed and will eventually be closed.

Given these constraints, maintainer time and effort will be prioritized toward PRs of high initial quality and contributors whose interactions are constructive and demonstrate genuine engagement with the project.

## Automated and bot contributions

Fully automated contributions&mdash;PRs opened by AI agents or bots without meaningful human oversight&mdash;are not accepted.
Every PR must have a human author who takes responsibility for it, has actively driven the contribution, and is available to respond to review feedback.

## Consequences

PRs that violate this policy may be closed without detailed review.
Contributors who repeatedly submit low-effort AI-generated content may be restricted from future contributions.

## Additional resources

For comprehensive guidance on contributing to AiiDA, including code quality standards, development workflows, and testing practices, please refer to the [contributing guide](https://aiida.readthedocs.io/projects/aiida-core/en/latest/internals/contributing.html) and our `AGENTS.md`.

## Acknowledgements

We acknowledge the [Kornia AI policy](https://github.com/kornia/kornia/blob/main/AI_POLICY.md) and [MDAnalysis AI policy](https://github.com/MDAnalysis/mdanalysis/blob/develop/AI_POLICY.md) from which this document draws inspiration.
