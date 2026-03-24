# Making a new release

## How releases reach users

Users install AiiDA from **PyPI** (or conda-forge, which also sources from PyPI):

```console
$ pip install aiida-core         # latest stable
$ pip install aiida-core==2.8.0  # exact version
$ pip install aiida-core~=2.8    # any 2.8.x patch release
```

Users never need to know about git branches or tags.
The release process creates a **git tag** (e.g., `v2.8.0`) that points to a specific commit.
Pushing the tag triggers a CI workflow that builds the package and publishes it to PyPI.
From there, `pip install` and conda-forge pick it up automatically.

## Branching strategy

As of v2.0, we have a simple branching strategy.
The main branch is called `main` and all development happens directly on that branch through pull requests.

### Branch types

There are three types of branches involved in the release process:

| Branch | Example | Purpose | Lifetime |
|---|---|---|---|
| `main` | `main` | All development happens here | Permanent |
| `release/X.Y.Z` | `release/2.8.0` | Prepares the release commit (changelog, version bump) | Temporary — deleted after squash-merge |
| `support/X.Y.x` | `support/2.8.x` | Collects cherry-picked fixes for patch releases | Long-lived — one per minor release series |

### How branches, tags, and PyPI fit together

The relationship between these concepts is:

```
main (development)
  │
  ├── release/2.8.0 (temporary branch for changelog + version bump)
  │     │
  │     └── squash-merged into main → creates commit abc123
  │
  ├── tag v2.8.0 → points to abc123 → triggers CI → published to PyPI
  │
  ├── support/2.8.x (created from tag v2.8.0, for future patch releases)
  │     │
  │     ├── cherry-pick fix from main
  │     ├── cherry-pick fix from main
  │     ├── release commit (bump to 2.8.1, update changelog)
  │     └── tag v2.8.1 → triggers CI → published to PyPI
  │
  └── development continues on main → eventually release/2.9.0 ...
```

Key points:

- **All development** (features and bug fixes) is done on `main` via pull requests.
- **Minor/major releases** (e.g., `v2.8.0`) are tagged on `main` after squash-merging the release PR.
- **Patch releases** (e.g., `v2.8.1`) are tagged on `support/2.8.x`. Bug fixes are first merged into `main`, then cherry-picked onto the support branch.
- **Tags are the source of truth** for releases. The tag triggers the CI workflow that publishes to PyPI. The branch a tag lives on does not matter — the release workflow builds from whatever commit the tag points to.
- **Users only interact with PyPI**. They never need to check out a branch or know about the support branch. `pip install aiida-core~=2.8` will install the latest 2.8.x patch release from PyPI, regardless of which branch the tag was created from.

### Remote naming conventions

In the following, we assume these naming conventions for remotes:

- `origin`: remote pointing to your personal fork
- `upstream`: remote pointing to `aiidateam/aiida-core`

Check your remotes with `git remote -v`.

## Semantic versioning

We use [semantic versioning](https://semver.org/), i.e., version labels have the form `vMAJOR.MINOR.PATCH`:

| Release type | Example | Contents |
|---|---|---|
| Major | `v1.0.0` to `v2.0.0` | Bug fixes, new features, and breaking changes |
| Minor | `v2.0.0` to `v2.1.0` | Bug fixes and new features (backwards compatible) |
| Patch | `v2.0.0` to `v2.0.1` | Bug fixes only |

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

The procedure depends on the release type.

**Minor / major releases** — branch directly from `main`:

```console
$ git checkout upstream/main -b release/X.Y.0
```

**Patch releases** — use the persistent `support/X.Y.x` branch.
Bug fixes are always developed, reviewed, and merged into `main` first (via the normal PR workflow).
When a fix should be included in a patch release, it is cherry-picked from `main` onto the support branch.

Each minor release series has a long-lived support branch (e.g., `support/2.7.x`) that is created from the minor release tag and used for all subsequent patch releases in that series:

```console
# First patch release: create the support branch from the minor release tag
$ git checkout tags/vX.Y.0 -b support/X.Y.x
$ git push upstream support/X.Y.x

# Subsequent patch releases: work on the existing support branch
$ git checkout upstream/support/X.Y.x
```

### 2. Cherry-pick commits (patch releases)

Cherry-pick the relevant fixes from `main` onto the support branch:

```console
$ git cherry-pick -x <HASH>
```

The `-x` flag automatically appends `(cherry picked from commit <HASH>)` to the commit message, preserving traceability back to the original commit on `main`.

Or use the helper script for multiple commits:

```console
$ ./utils/patch-release.sh <HASH-0> <HASH-1> ... <HASH-N>
```

If a cherry-pick has conflicts, resolve them manually and commit.
If a fix does not apply cleanly (e.g., due to code that diverged significantly since the minor release), consider whether the fix is worth backporting or whether it should wait for the next minor release.


### 3. Create the release commit

The final commit on the release branch should contain:

- Updated `__version__` attribute in `src/aiida/__init__.py` (e.g., `2.7.3.post0` → `2.8.0`).
  The version string must **not** include the `v` prefix — use `2.8.0`, not `v2.8.0`.
  The `check_release_tag.py` CI job validates that the tag name matches `__version__`.
- Updated `CHANGELOG.md` (see below)
- Updated `AUTHORS.txt` if there are new contributors

Commit message: `Release vX.Y.Z`

#### Changelog structure

The changelog entry for a release has two parts:

1. **Prose section** at the top: a short narrative describing the main changes, new features, and highlights of the release.
   If the release includes **behavior changes** — changes that may affect existing workflows but do not constitute API-breaking changes warranting a major version bump — these should be listed explicitly in the prose section so users are aware of them.

2. **Categorized commit list** below the prose: individual changes grouped by category (Features, Fixes, Deprecations, Dependencies, Documentation, Devops, etc.), each with a link to the commit and PR.
   Within each category, entries should be sorted **newest to oldest** by merge time.

See `CHANGELOG.md` in the repository for examples of both sections.

:::{tip}
To automatically generate commit summaries for the categorized list:

```console
$ git log --pretty="- %s [[%h]](https://github.com/aiidateam/aiida-core/commit/%H)" $(git describe --tags --abbrev=0)..HEAD
```

Remember to fetch the latest tags first with `git fetch --tags`.
:::

#### Verifying changelog completeness

Before finalizing the changelog, verify that all relevant commits are included by comparing the git log against the changelog entries.
The following types of commits are typically **excluded** from the changelog:

- **Release mechanics**: version bumps, changelog updates
- **Revert pairs**: a commit and its subsequent revert cancel each other out and neither needs to be listed (unless a third commit re-introduces the change — in that case, only the final commit is listed)
- **Commits already in patch release sections**: for minor releases, commits that were cherry-picked into patch releases (e.g., v2.7.1, v2.7.2) and already appear in those sections should not be duplicated in the minor release section

### 4. Create and merge pull request

**Minor / major releases**: create a PR to merge the release branch into `main`.
The release must land as a **single commit** on `main`.
Use **squash-merge** (or rebase-merge if the PR already contains exactly one commit).
Do **not** use a merge commit.

**Patch releases**: create a PR to merge the release branch into the `support/X.Y.x` branch.
The same merge rules apply — single commit, no merge commits.

After the PR is merged, delete the release branch (GitHub offers this on the PR page).
The release branch is temporary and should not be kept around.

### 5. Create the tag and release

Tag the release commit.
For minor/major releases, find the hash **on `main`** (not the commit hash shown on the PR page — squash-merge creates a new commit):

```console
$ git fetch upstream
$ git log upstream/main -1 --format="%H %s"
```

For patch releases, tag the commit on the `support/X.Y.x` branch.

Then create and push the tag:

```console
$ git tag -a vX.Y.Z <HASH> -m 'Release `vX.Y.Z`'
$ git push upstream vX.Y.Z
```

The tag push triggers the `release.yml` workflow (see [Release CI workflows](#release-ci-workflows) below), which builds the package and publishes it to PyPI.
This is how releases reach users: they install from PyPI (or conda-forge, which also sources from PyPI), not from the git branch.
The tag can live on `main` (minor/major) or on a `support/X.Y.x` branch (patch) — it does not matter, since the release workflow builds from whatever commit the tag points to.

:::{note}
You may notice `release.yml` runs appearing in the Actions tab for pushes to the release PR branch (e.g., `release/2.8.0`).
These are expected and harmless — the `release.yml` workflow also triggers on PRs (to support the `test-release` label flow for RCs), but without that label it exits immediately (typically in 1–2 seconds).
The real release run is the one triggered by the tag push, which will show the tag name (e.g., `v2.8.0`) instead of a branch name.
:::

The release workflow requires **manual approval** before the "Publish to PyPI" job runs.
After the prerequisite jobs (`check-release-tag`, `pre-commit`, `tests`) pass, a member of the `@aiidateam/release-manager` team must approve the deployment:

1. Go to the workflow run page in the Actions tab (the run triggered by the tag push).
2. Click the **"Review deployments"** button.
3. Select the `release` environment and approve.

This is configured under **Settings → Environments → `release` → Required reviewers**.
The person who pushed the tag can self-approve (unless "Prevent self-review" is enabled).

It is recommended to wait for the release CI to pass before proceeding, but the remaining steps can also be done in parallel.
If the release CI fails, the package will not be published — you can then delete the tag, fix the issue, and re-tag.

Create a [GitHub release](https://github.com/aiidateam/aiida-core/releases/new) from the tag:

- Title: `AiiDA vX.Y.Z`
- Body: `See [CHANGELOG.md](https://github.com/aiidateam/aiida-core/blob/vX.Y.Z/CHANGELOG.md)`

Or use the `gh` CLI:

```console
$ gh release create vX.Y.Z --repo aiidateam/aiida-core --title "AiiDA vX.Y.Z" --notes "See [CHANGELOG.md](https://github.com/aiidateam/aiida-core/blob/vX.Y.Z/CHANGELOG.md)"
```

After the release is published to PyPI, verify it is installable:

```console
$ pip install aiida-core==X.Y.Z
```

### 6. Create the support branch (minor/major releases)

After a minor or major release, create the long-lived support branch for future patch releases in that series.
This branch is created from the release tag:

```console
$ git checkout tags/vX.Y.0 -b support/X.Y.x
$ git push upstream support/X.Y.x
```

This branch will be used for all subsequent patch releases (vX.Y.1, vX.Y.2, etc.) by cherry-picking fixes from `main` onto it.
See [How branches, tags, and PyPI fit together](#how-branches-tags-and-pypi-fit-together) for the full picture of how support branches relate to tags and PyPI releases.

### 7. Post-release version bump

After the release is published, bump `__version__` in `src/aiida/__init__.py` to `X.Y.Z.post0` and open a PR.
For minor/major releases, this bump happens on `main`.
For patch releases, this bump happens on the `support/X.Y.x` branch.
This ensures that development installs are distinguishable from the released version (see [Post-release suffix](#post-release-suffix) below).

```console
$ git checkout upstream/main -b post-release/X.Y.Z
# Edit src/aiida/__init__.py: set __version__ = 'X.Y.Z.post0'
$ git add src/aiida/__init__.py
$ git commit -m 'Post release: add the `.post0` qualifier to version attribute'
$ git push origin post-release/X.Y.Z
# Open a PR to main
```

### 8. conda-forge

Update the conda-forge feedstock (see [conda-forge release process](#conda-forge-release-process) below).

### 9. Communication

1. Post an announcement on [AiiDA Discourse](https://aiida.discourse.group/).
1. For minor and major releases, write a blog post on the [AiiDA website](https://github.com/aiidateam/aiida-website).
1. Announce the release (and the blog post, if applicable) on [LinkedIn](https://www.linkedin.com/company/aiida/).

## Post-release suffix

The `main` branch always uses a `.post0` version suffix (e.g., `2.0.0.post0`).
This warns users who are accidentally running from `main` that they are using a non-released version, as AiiDA displays a warning when loading a profile with a post-release version.

## conda-forge release process

The conda-forge feedstock is at [conda-forge/aiida-core-feedstock](https://github.com/conda-forge/aiida-core-feedstock).
Source is fetched from PyPI, not GitHub.

### Automated

The `regro-cf-autotick-bot` detects new stable PyPI releases and automatically opens PRs to update the feedstock.
For patch releases, this usually works without manual intervention.
The bot also detects minor releases, but these may require manual adjustments if dependencies have changed — review the bot's PR carefully before merging.

### Manual (release candidates, or if the bot PR needs changes)

For release candidates (or if the bot's auto-PR needs significant changes), a maintainer manually creates a PR:

1. Fork `conda-forge/aiida-core-feedstock` (or use an existing fork)
1. Update `recipe/meta.yaml`: version string, sha256 hash, and any dependency changes
1. Add a comment: `@conda-forge-admin, please rerender`
1. Open a PR against the feedstock `main` branch
1. Feedstock CI builds and runs basic tests (`verdi --help`, `verdi --version`, `pip check`)
1. A feedstock maintainer reviews and merges

## Release CI workflows

The release-related CI workflows live in `.github/workflows/`.

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| Release | `release.yml` | tag push (`v*`), or PR with `test-release` label | Validates tag vs `__version__` (via `check_release_tag.py`), runs pre-commit and a subset of tests, then publishes to **PyPI** (on tag) or **TestPyPI** (on `test-release` label). Uses `flit build` + trusted publisher (OIDC). |
| Docker | `docker.yml` | push to any branch/tag (excl. docs/tests changes), or manual | Orchestrates Docker image build, test, and publish via reusable workflows (`docker-build.yml`, `docker-test.yml`, `docker-publish.yml`). Publishes to GHCR on all pushes; to DockerHub only on tags and `main`. |
