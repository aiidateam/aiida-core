# Making a new release

## Branching strategy

As of v2.0, we have a simple branching strategy.
The main branch is called `main` and all development happens directly on that branch through pull requests.

In the following, we assume the following naming conventions for remotes:

* `origin`: remote pointing to `aiidateam/aiida-core`
* `fork`: remote pointing to your personal fork

Check your remotes with `git remote -v`.

## Semantic versioning

We use [semantic versioning](https://semver.org/), i.e., version labels have the form `vMAJOR.MINOR.PATCH`:

| Release type | Example | Contents |
|---|---|---|
| Major | `v1.0.0` to `v2.0.0` | Bug fixes, new features, and breaking changes |
| Minor | `v1.0.0` to `v1.1.0` | Bug fixes and new features (backwards compatible) |
| Patch | `v1.0.0` to `v1.0.1` | Bug fixes only |

## Release procedure

### 1. Create the release branch

The exact procedure depends on the release type and the current state of `main`.

If the release can be made directly from `main`:

```console
$ git checkout origin/main -b release/X.Y.Z
```

If `main` contains changes that should not be released, create the branch from the latest relevant tag:

```console
$ git checkout tags/vA.B.C -b release/X.Y.Z
```

### 2. Cherry-pick commits (if needed)

If the release branch was created from a tag (not `main`), cherry-pick the relevant commits:

```console
$ git cherry-pick <HASH>
$ git commit --amend  # add "Cherry-pick: <HASH>" to the end of the message
```

Or use the helper script for multiple commits:

```console
$ ./utils/patch-release.sh <HASH-0> <HASH-1> ... <HASH-N>
```

### 3. Create the release commit

The final commit on the release branch should contain:

* Updated `__version__` attribute in `src/aiida/__init__.py`
* Updated `CHANGELOG.md` with the changes (divided into relevant categories)
* Updated `AUTHORS.txt` if there are new contributors

Commit message: `Release vX.Y.Z`

:::{tip}
To automatically generate commit summaries for the changelog:

```console
$ git log --pretty="- %s [[%h]](https://github.com/aiidateam/aiida-core/commit/%H)" $(git describe --tags --abbrev=0)..HEAD
```

Remember to fetch the latest tags first with `git fetch --tags`.
:::

### 4. Create and merge pull request

Create a PR on GitHub to merge the release branch into `main` (if applicable).

:::{important}
The release branch must be merged using a **merge commit**.
It is crucial that the branch is **not rebased nor squashed**.
:::

### 5. Create the tag and release

Find the hash of the release commit and create a tag:

```console
$ git tag -a vX.Y.Z <HASH> -m 'Release `vX.Y.Z`'
$ git push --tags
```

The tag triggers the `release.yml` workflow, which runs tests and deploys to PyPI.

Create a [GitHub release](https://github.com/aiidateam/aiida-core/releases/new) with:
* Title: `AiiDA vX.Y.Z`
* Body: `See [CHANGELOG.md](https://github.com/aiidateam/aiida-core/blob/vX.Y.Z/CHANGELOG.md)`

### 6. Communication and dependent packages

1. Announce on the [AiiDA website](https://github.com/aiidateam/aiida-website), [Discourse](https://aiida.discourse.group/), and social media.
2. The [conda-forge feedstock](https://github.com/conda-forge/aiida-core-feedstock) should automatically create a PR.

## Post-release suffix

The `main` branch always uses a `.post0` version suffix (e.g., `2.0.0.post0`).
This warns users who are accidentally running from `main` that they are using a non-released version, as AiiDA displays a warning when loading a profile with a post-release version.
