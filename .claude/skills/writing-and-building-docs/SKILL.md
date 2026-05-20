---
name: writing-and-building-docs
description: Use when writing, editing, or building documentation files (`.md`, `.rst`) under `docs/`.
---

# Writing and building documentation for aiida-core

When writing or editing `.md` or `.rst` files under `docs/`:

- Write **one sentence per line** (no manual line wrapping): makes diffs easy to review.
- File/directory names: alphanumeric, lowercase, underscores as separators.
- Headers in **sentence case** (e.g., "Entry points", not "Entry Points").
- Documentation follows the [Divio documentation system](https://www.divio.com/blog/documentation/): tutorials (learning-oriented), how-to guides (goal-oriented), topics (understanding-oriented), reference (information-oriented).

## Building the docs

```bash
uv run sphinx-build -b html docs/source docs/build/html
```

For live-reloading during development, use `sphinx-autobuild` (not a project dependency, install manually):

```bash
uv pip install sphinx-autobuild
uv run sphinx-autobuild docs/source docs/build/html
```
