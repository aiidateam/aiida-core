# Making a new release

## Branching strategy

As of v2.0, we have a simple branching strategy.
The main branch is called `main` and all development happens directly on that branch through pull requests.

In the following, we assume the following naming conventions for remotes:

- `origin`: remote pointing to your personal fork
- `upstream`: remote pointing to `aiidateam/aiida-core`

Check your remotes with `git remote -v`.

## Semantic versioning

We use [semantic versioning](https://semver.org/), i.e., version labels have the form `vMAJOR.MINOR.PATCH`:

| Release type | Example | Contents |
|---|---|---|
| Major | `v1.0.0` to `v2.0.0` | Bug fixes, new features, and breaking changes |
| Minor | `v1.0.0` to `v1.1.0` | Bug fixes and new features (backwards compatible) |
| Patch | `v1.0.0` to `v1.0.1` | Bug fixes only |

## Pre-release testing

Before every minor release, one or more release candidates (RCs) should be published to verify that nothing breaks for downstream packages.

### Publishing an RC

1. Create a branch for the RC (e.g., `support/2.8.0rc0`) off `main`.
2. Set `__version__` to the RC version (e.g., `2.8.0rc0`) in `src/aiida/__init__.py`.
3. Open a PR against `main` and add the **`test-release`** label.
   This triggers the release workflow, which publishes the RC to **TestPyPI** instead of PyPI.
4. To also publish the RC to conda-forge, manually open a feedstock PR with the RC version (see [conda-forge release process](#conda-forge-release-process)).

RC branches are **not** merged into `main` and are **not** ancestors of the final release tag.

### Testing downstream plugins

After publishing an RC, open PRs in key downstream repositories to test their test suites against the RC.
In each repo, update the `aiida-core` dependency to the RC version (e.g., `aiida-core>=2.8.0rc0`) and check whether CI passes.

Key repositories to test:

- [aiida-quantumespresso](https://github.com/aiidateam/aiida-quantumespresso)
- [aiidalab](https://github.com/aiidalab/aiidalab)
- [aiidalab-widgets-base](https://github.com/aiidalab/aiidalab-widgets-base)
- [aiidalab-qe](https://github.com/aiidalab/aiidalab-qe)
- [aiida-shell](https://github.com/aiidateam/aiida-shell)
- [aiida-pythonjob](https://github.com/aiidateam/aiida-pythonjob)
- [aiida-workgraph](https://github.com/aiidateam/aiida-workgraph)
- [aiida-firecrest](https://github.com/aiidateam/aiida-firecrest)
- [aiida-hyperqueue](https://github.com/aiidateam/aiida-hyperqueue)

Any failures found during RC testing should be fixed and a new RC published before proceeding with the final release.

<!-- TODO: uncomment once aiidateam/aiida-rc-testing is set up
The [aiida-rc-testing](https://github.com/aiidateam/aiida-rc-testing) repository automates this: it installs the RC from TestPyPI, clones each downstream package, and runs their test suites.
Trigger it via the GitHub Actions UI or the CLI:

```console
$ gh workflow run test-rc.yml -R aiidateam/aiida-rc-testing -f aiida_core_version=2.8.0rc2
```
-->

## Release procedure

### 1. Create the release branch

The exact procedure depends on the release type and the current state of `main`.

If the release can be made directly from `main`:

```console
$ git checkout upstream/main -b release/X.Y.Z
```

If `main` contains changes that should not be released, create the branch from the latest relevant tag:

```console
$ git checkout tags/vA.B.C -b release/X.Y.Z
```

### 2. Cherry-pick commits (if needed)

If the release branch was created from a tag (not `main`), cherry-pick the relevant commits:

```console
$ git cherry-pick -x <HASH>
```

The `-x` flag automatically appends `(cherry picked from commit <HASH>)` to the commit message.

Or use the helper script for multiple commits:

```console
$ ./utils/patch-release.sh <HASH-0> <HASH-1> ... <HASH-N>
```


### 3. Create the release commit

The final commit on the release branch should contain:

- Updated `__version__` attribute in `src/aiida/__init__.py` (e.g., `2.7.3.post0` → `2.8.0`)
- Updated `CHANGELOG.md` (see below)
- Updated `AUTHORS.txt` if there are new contributors

Commit message: `Release vX.Y.Z`

#### Changelog structure

The changelog entry for a release has two parts:

1. **Prose section** at the top: a short narrative describing the main changes, new features, and highlights of the release.
   If the release includes **behavior changes** — changes that may affect existing workflows but do not constitute API-breaking changes warranting a major version bump — these should be listed explicitly in the prose section so users are aware of them.

2. **Categorized commit list** below the prose: individual changes grouped by category (Features, Fixes, Deprecations, Dependencies, Documentation, Devops, etc.), each with a link to the commit and PR.

See `CHANGELOG.md` in the repository for examples of both sections.

:::{tip}
To automatically generate commit summaries for the categorized list:

```console
$ git log --pretty="- %s [[%h]](https://github.com/aiidateam/aiida-core/commit/%H)" $(git describe --tags --abbrev=0)..HEAD
```

Remember to fetch the latest tags first with `git fetch --tags`.
:::

### 4. Create and merge pull request

Create a PR on GitHub to merge the release branch into `main` (if applicable).
The release PR should always be **squash-merged** so that the release lands as a single commit on `main`.
If the PR contains multiple commits (e.g., from iterating on the changelog), squash-merge combines them into one.

### 5. Create the tag and release

Find the hash of the release commit **on `main`** (not the commit hash shown on the PR page — squash-merge creates a new commit) and create a tag:

```console
$ git tag -a vX.Y.Z <HASH> -m 'Release version X.Y.Z'
$ git push upstream vX.Y.Z
```

The tag push triggers the `.github/workflows/release.yml` workflow, which:

1. Verifies that the tag version matches `__version__` in `src/aiida/__init__.py` (via `check_release_tag.py`)
1. Runs pre-commit checks
1. Runs a subset of tests (RabbitMQ-requiring tests with SQLite backend)
1. Publishes to PyPI via `flit build` + trusted publisher (OIDC)
1. Triggers `.github/workflows/docker.yml` for Docker image builds

Create a [GitHub release](https://github.com/aiidateam/aiida-core/releases/new) with:

- Title: `AiiDA vX.Y.Z`
- Body: `See [CHANGELOG.md](https://github.com/aiidateam/aiida-core/blob/vX.Y.Z/CHANGELOG.md)`

### 6. Post-release version bump

After the release is published, bump `__version__` in `src/aiida/__init__.py` to `X.Y.Z.post0` on `main` and commit.
This ensures that development installs are distinguishable from the released version (see [Post-release suffix](#post-release-suffix) below).

### 7. conda-forge

Update the conda-forge feedstock (see [conda-forge release process](#conda-forge-release-process) below).

### 8. Communication

1. Post an announcement on [AiiDA Discourse](https://aiida.discourse.group/).
1. For minor and major releases, write a blog post on the [AiiDA website](https://github.com/aiidateam/aiida-website).
1. Announce the release (and the blog post, if applicable) on [LinkedIn](https://www.linkedin.com/company/aiida/).

## Post-release suffix

The `main` branch always uses a `.post0` version suffix (e.g., `2.0.0.post0`).
This warns users who are accidentally running from `main` that they are using a non-released version, as AiiDA displays a warning when loading a profile with a post-release version.

## conda-forge release process

The conda-forge feedstock is at [conda-forge/aiida-core-feedstock](https://github.com/conda-forge/aiida-core-feedstock).
Source is fetched from PyPI, not GitHub.

### Automated (patch releases)

The `regro-cf-autotick-bot` detects new stable PyPI releases and automatically opens PRs to update the feedstock.
For patch releases, this usually works without manual intervention.

### Manual (minor releases, release candidates)

For minor releases and release candidates, a maintainer manually creates a PR:

1. Fork `conda-forge/aiida-core-feedstock` (or use an existing fork)
1. Update `recipe/meta.yaml`: version string, sha256 hash, and any dependency changes
1. Add a comment: `@conda-forge-admin, please rerender`
1. Open a PR against the feedstock `main` branch
1. Feedstock CI builds and runs basic tests (`verdi --help`, `verdi --version`, `pip check`)
1. A feedstock maintainer reviews and merges
