---
name: writing-and-building-docs
description: Use for writing or building `.md` and `.rst` documentation under `docs/`.
---

# Documentation

* One sentence per line; no manual prose wrapping.
* Paths: lowercase alphanumeric with underscores; headings: sentence case.
* [Divio](https://www.divio.com/blog/documentation/): tutorials (learning), how-to guides (goals), topics (understanding), reference (information).

## Build

```bash
uv run sphinx-build -b html docs/source docs/build/html
```

Live reload (`sphinx-autobuild` is outside project dependencies):

```bash
uv pip install sphinx-autobuild
uv run sphinx-autobuild docs/source docs/build/html
```
