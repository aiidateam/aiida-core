# Writing documentation

Improving the AiiDA documentation is both straightforward and valuable.

AiiDA uses [Sphinx](http://www.sphinx-doc.org) with [MyST Markdown](https://myst-parser.readthedocs.io/) and [reStructuredText](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

## Building docs locally

Build the documentation with:

```console
$ uv run sphinx-build -b html docs/source docs/build/html
$ open docs/build/html/index.html
```

For live rebuilds during editing, you can use `sphinx-autobuild`:

```console
$ uv run sphinx-autobuild docs/source docs/build/html
```

:::{warning}
The CI tests on your PR will fail if warnings are encountered while building the documentation.
:::

## Useful resources

- [The Documentation System](https://www.divio.com/blog/documentation/) -- the framework AiiDA's docs are modeled after.
- [Google developer documentation style guide](https://developers.google.com/style) -- especially the notes about [tone](https://developers.google.com/style/tone).

## How the AiiDA documentation is organized

The documentation follows the [Divio documentation system](https://www.divio.com/blog/documentation/):

| Section | Directory | Purpose |
|---------|-----------|---------|
| Getting started | `intro/` | Landing page for new users with motivation, code snippets, and links |
| Tutorial | `tutorial/` | Teaches new users how to use AiiDA (learning-oriented) |
| How-to guides | `howto/` | Concrete recipes for specific tasks (goal-oriented) |
| Topics | `topics/` | In-depth explanations of AiiDA concepts (understanding-oriented) |
| Reference | `reference/` | Complete API reference (information-oriented) |
| Developer guide | `developer_guide/` | Guidelines for contributors |

## Style guide

1. Write **one sentence per line** and otherwise no manual line wrapping.
   This makes it easy to create and review diffs.
1. File and directory names should be **alphanumeric, lowercase, with underscores** as separators (e.g., `entry_points.rst`).
1. Headers must be set in **sentence case** (e.g., "Entry points").
1. Section header hierarchy (for RST files):
   - `#` with overline for the global title
   - `*` with overline for chapters
   - `=` for sections
   - `-` for subsections
   - `^` for subsubsections
1. Separate paragraphs by one empty line, not more.
1. Use `*` for itemized lists.
1. Use the `code-block` directive instead of double-colon for code segments.

## Code segments

| Content | RST directive | Notes |
|---------|---------------|-------|
| Bash scripts | `.. code-block:: bash` | |
| Bash sessions | `.. code-block:: console` | Prefix commands with `$`, root with `#` |
| Python scripts | `.. code-block:: python` | |
| Python sessions | `.. code-block:: ipython` | For `verdi shell` examples |

## Docstring format

Use Sphinx-style (reST) docstrings.
Types should be in type hints, not in docstrings — keeping them only in annotations avoids duplication that goes stale.

```python
def put_object_from_filelike(self, handle: BinaryIO) -> str:
    """Store the byte contents of a file in the repository.

    :param handle: filelike object with the byte content to be stored.
    :return: the generated fully qualified identifier for the object within the repository.
    :raises TypeError: if the handle is not a byte stream.
    """
```

## Naming conventions

- *setup*: one word, not "set up"
- *Python*: capitalized
- *UUID*: block capitalized
