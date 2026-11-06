# Contributing

See the [Contributor wiki](https://github.com/aiidateam/aiida-core/wiki) for setup and contribution instructions.

## Before merging substantial changes

- Walk through the design with another core developer. Both of you should be able to explain how it works and why it was designed that way.
- Keep the commit history reviewable: a small number of coherent changes, rather than lots of tiny commits or one large squash.
- Respect the compatibility guarantees for the user API, including re-exported interfaces. During v3 development, record breaking changes in `CHANGELOG.md`.
- Update the relevant [internals pages](docs/source/internals/). You must read them in detail and understand the design before merging.
- Link all related open issues in the PR. Keep track of unresolved questions and follow-up work in linked issues or PRs.
