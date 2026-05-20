# Policy of AiiDA on AI-assisted contributions

This document defines the [aiidateam organization's](https://github.com/aiidateam/) policy regarding AI-generated content.
This policy applies to all aspects of the AiiDA project, including all GitHub repositories under the `aiidateam` organization.

We expect to periodically review and update this policy as the landscape changes.

## Core philosophy

We recognize that AI tools have become part of the modern developer's toolbox and, as users of these tools ourselves, we would be dishonest to entirely prohibit their use.
However, contributions must reflect genuine effort and understanding from the author: submitting AI-generated code without meaningful human input, verification, and comprehension is not acceptable.

## Contributor expectations

### Understand what you submit

**Every contributor bears full responsibility for what they submit.**
You must understand, verify, and be able to explain every line of code, every comment, and every design decision in your PR.
If reviewers perceive a lack of understanding (from the code itself, PR descriptions, or interactions during review), we reserve the right to close the PR.

Before contributing, we expect you to engage with the project and familiarize yourself with the codebase.
Proposed changes should be discussed with maintainers (via a [GitHub issue](https://github.com/aiidateam/aiida-core/issues) or [Discourse](https://aiida.discourse.group/)) before opening a PR.

### Verify your code locally

Before requesting review, contributors must ensure that all CI checks pass (`uv run pre-commit ...`, including `ruff`, `mypy`, etc.), all added/modified tests pass (`uv run pytest ...`), and documentation builds (`uv run sphinx-build ...`) without errors, if applicable.
PRs that fail CI and receive no further attention from the contributor will be closed.
The same goes for PRs that show signs of being unverified AI output.

### Curate your PR

All PRs must be thoughtfully authored, including the title, description, and commit messages.
Copy-pasting raw LLM output into PR titles or descriptions is not acceptable.
The PR description should clearly explain what the change does, why it is needed, and reference the related [GitHub issue(s)](https://github.com/aiidateam/aiida-core/issues).
If no issue exists for the problem/improvement a PR addresses, **please create one first and reference it in the PR**.
If AI tools were used in preparing the contribution, contributors should disclose how and to what extent they were used.

### Solve real problems

Contributions should stem from genuine use of or engagement with AiiDA.
Unsolicited refactors, style-only changes, or speculative features are unlikely to be accepted; if in doubt, open a [GitHub issue](https://github.com/aiidateam/aiida-core/issues) or discuss on [Discourse](https://aiida.discourse.group/) before investing time in a PR.

## Review process and community impact

With modern AI tools, large changes to a codebase can be produced with a single prompt.
However, the real effort lies in reviewing the output, understanding how it integrates with the rest of the codebase, and verifying its downstream effects.
AI-generated content is easy to produce but *harder* for others to read, review, and interpret;mdash&do not shift that burden onto maintainers.

We expect contributors to engage meaningfully with reviewers and apply feedback thoughtfully.
Simply feeding reviewer comments back into an LLM to regenerate a PR is not acceptable; if you cannot engage with the review yourself, open a bug report or feature request instead.

Do not post AI-generated comments or summaries unless you genuinely agree with them and take full responsibility for their accuracy.
All LLM output *looks* plausible;mdash&it is your responsibility to ensure it is also correct.
Verbose or off-topic comments may be marked as spam.

The reviewing capacity of this project is limited, and maintainer time will be prioritized toward high-quality contributions from engaged contributors.
We are committed to mentoring new contributors, but a high volume of low-effort PRs makes this unsustainable.
PRs that appear to lack understanding of the codebase may not get reviewed and will eventually be closed.

## Enforcement

PRs opened or modified by unsupervised agentic tools or bots, without active human oversight, are not permitted.
Every PR must have a human author who takes responsibility for it, has actively driven the contribution, and is available to respond to review feedback.

PRs that violate this policy may be closed without detailed review.
Contributors who repeatedly submit low-effort AI-generated content may be restricted from future contributions.

## Legal considerations

There is ongoing legal uncertainty regarding the copyright status of LLM-generated content and its provenance.
Since this project does not have a formal [Contributor License Agreement](https://en.wikipedia.org/wiki/Contributor_license_agreement) (CLA), contributors retain copyright over their changes.
Allowing LLM-generated code into the codebase therefore has unpredictable consequences for the project's copyright status (even setting aside possible copyright violations due to plagiarism).

Every contribution must be backed by a human who holds the copyright for the changes submitted or has the legal right to contribute them under this project's license.
By submitting a PR, you certify that you are the author of the contribution and that you understand it.
"An LLM wrote it" is not an acceptable response to questions or critique.

This section is adapted from the [attrs AI policy](https://github.com/python-attrs/attrs/blob/main/.github/AI_POLICY.md).

## Acknowledgements

This document draws on and adapts text from the [Kornia AI policy](https://github.com/kornia/kornia/blob/main/AI_POLICY.md), the [MDAnalysis AI policy](https://github.com/MDAnalysis/mdanalysis/blob/develop/AI_POLICY.md), and the [attrs AI policy](https://github.com/python-attrs/attrs/blob/main/.github/AI_POLICY.md).
Many thanks to their authors.
