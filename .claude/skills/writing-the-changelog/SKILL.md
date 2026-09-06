---
name: writing-the-changelog
description: Use when adding or editing entries in CHANGELOG.md for aiida-core — cutting a release, backporting changes to a patch release, categorizing entries, or fixing commit/PR references.
---

# Writing the CHANGELOG for aiida-core

## Anatomy of a release entry

```markdown
## v2.8.1 - 2026-07-25

<one or more short narrative paragraphs — see "Narrative intro" below>

### Full list of changes

#### Features
- <description> ([#7417](https://github.com/aiidateam/aiida-core/pull/7417)) [[fded1e6e0]](https://github.com/aiidateam/aiida-core/commit/fded1e6e0c31f5425650c8135ca5867e09e79d1a)

#### Fixes
- ...

#### Improvements
- ...
```

- Heading: `## v<X.Y.Z> - <YYYY-MM-DD>`.
- A narrative intro is expected for notable patches/releases; small patches can have a one-liner.
- `### Full list of changes` holds flat category sections (`#### <Category>`).

## Categorize by commit emoji (deterministic)

The **leading gitmoji of each source commit decides its category** — no human judgment about whether a change is "user-facing" or "developer-facing". This is intentional: it removes the ambiguous call and makes categorization reproducible. The emoji is a *routing key* and is **stripped from the rendered line** (the description does not start with the emoji — consistent with `commit-conventions`, where the emoji is the type indicator and the message is just the description).

**Emoji meanings are the single source of truth in the `commit-conventions` skill** (the MyST-Parser-derived table). Don't restate them here. This table only adds the changelog-specific routing (emoji → section) and section order:

| Emoji | Section heading | Notes |
|-------|-----------------|-------|
| `‼️`  | Breaking changes | first, if present |
| `✨`  | Features |
| `🐛` `🚑` | Fixes |
| `👌`  | Improvements |
| `♻️`  | Refactoring |
| `📚`  | Documentation |
| `🧪`  | Tests & CI |
| `🔧`  | Maintenance |
| `⬆️`  | Dependencies |
| `🔖`  | *(Release commit — exclude from the list)* |

Only emit sections that have entries.

### Commits with no emoji

If a source commit has no leading emoji, categorization isn't deterministic. Infer the category from the message (`Refactor …` → Refactoring, `Pin …`/dependency changes → Dependencies or Maintenance), **flag it** to the author, and prefer retagging the commit with the right emoji so the routing becomes deterministic next time.

## Referencing changes: PR link + commit hash

Each line ends with two references:

```
- <description> ([#<PR>](…/pull/<PR>)) [[<9-char sha>]](…/commit/<40-char sha>)
```

Two references, two jobs — let each do its own:

- **PR link** → the **original PR** (discussion, review, rationale). Version-agnostic; the same across every backport.
- **Commit hash** → the commit that **actually shipped in this release**, i.e. the one **reachable from this release's tag**. Display 9 chars, link the full 40-char SHA.

### The rules that avoid pain (learned the hard way)

1. **Link the release-branch commit, not the original `main` commit.** For a backport/cherry-pick the diff is often *edited* to fit the older base. The `main` commit's diff then does not match what shipped; the branch commit does. It's also the only one reachable from the release tag.
2. **Every hash in an entry must be reachable from that release's tag.** Verify: `git tag --contains <sha>` should list the release tag.
3. **Hashes drift on rebase.** A rebase rewrites every commit from the rebase point to the tip, giving new hashes (commits *below* the rebase point keep theirs). So **fill in / finalize hashes only after the release commit is created and the tag is pushed**, and don't rebase past the tag afterward. Writing hashes before the final rebase means chasing them.
4. **The real risk is rebasing, not garbage collection.** A commit reachable from a pushed tag (or long-lived support branch) is never GC'd. "Detached commit" fears don't apply once it's under a tag.
5. **PR numbers are stable; hashes are not.** If you want a zero-maintenance changelog, PR-links-only is a legitimate option — drop the `[[sha]]` part entirely.
6. **Backports can change the PR number too.** A cherry-pick often lands via a *new* PR on the release branch. Check the `(#NNNN)` in the commit subject and reconcile the PR link, not just the hash.

## Generating / refreshing the list

Always derive from the release branch, never by hand:

```bash
git log <previous-tag>.. --format="%H %s"
```

This yields exactly the commits that shipped since the last tag, with their **current** hashes and subjects. The subject carries both the routing emoji and the `(#PR)` suffix (appended on squash-merge — see `commit-conventions`). Use `%H` for the full SHA (URL) and its first 9 chars for the display. Exclude the `🔖 Release` commit.

When hashes have drifted (post-rebase) or you're adapting an entry to a new release line (e.g. the same changes re-cut for 2.8.x), re-run this and update each line by matching on the **PR number**.

## User vs developer changes

Two accepted layouts:

- **Flat emoji categories** (default, and what patch releases use): sections above, no user/developer split. The emoji-driven categories already segregate `Documentation` / `Tests & CI` / `Maintenance` / `Dependencies` from the user-facing ones. Order user-facing categories (Features, Fixes, Improvements) first.
- **Two-level split** (optional, for large minor/major releases): `### Full list of changes for users` and `### Full list of changes for developers`, each with `####` category sub-sections, plus curated highlight sections and a table-of-contents at the top. Only worth the overhead when the change set is large. Note this reintroduces a user/developer judgment call — keep it out of routine patches.

Don't drop developer-facing changes entirely — keep them, just segregated and last.

## Narrative intro guidance

- **One sentence per line**, no manual wrapping — same convention as `writing-and-building-docs`, and it keeps release-note diffs reviewable.
- Present tense, describe *what* and *why* ("This patch fixes … so that …").
- Call out compatibility implications explicitly (e.g. a downgrade migration that lets a newer schema be brought back to an older one — name both versions).
- Keep it to the headline changes; the full list carries the rest.

## Checklist for a release entry

1. `git log <previous-tag>.. --format="%H %s"` on the release branch.
2. Drop the `🔖 Release` commit; bucket the rest by leading emoji.
3. Write each line: description (emoji stripped) + original PR link + shipped-commit hash.
4. Order sections per the table; emit only non-empty ones.
5. Add/refresh the narrative intro; state compatibility impacts.
6. Verify a couple of hashes with `git tag --contains <sha>`.
7. Finalize hashes only after the tag is cut and pushed; never rebase past it afterward.
