# Writing documentation

AiiDA uses [Sphinx](https://www.sphinx-doc.org) with [MyST Markdown](https://myst-parser.readthedocs.io/en/latest/) and [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

## Building docs locally

Build the documentation with:

```console
$ uv run sphinx-build -b html docs/source docs/build/html
```

For live rebuilds during editing, you can use `sphinx-autobuild` (included in the development dependencies):

```console
$ uv run sphinx-autobuild docs/source docs/build/html
```

To check for broken links:

```console
$ uv run sphinx-build -b linkcheck docs/source docs/build/linkcheck
```

:::{warning}
The CI tests on your PR will fail if warnings are encountered while building the documentation.
:::

## Useful resources

- [The Documentation System](https://docs.divio.com/documentation-system/) -- the framework AiiDA's docs are modeled after.
- [Google developer documentation style guide](https://developers.google.com/style) -- especially the notes about [tone](https://developers.google.com/style/tone).

## How the AiiDA documentation is organized

The documentation follows the [Divio documentation system](https://docs.divio.com/documentation-system/):

| Section | Directory | Purpose |
|---------|-----------|---------|
| Getting started | `intro/` | Landing page for new users with motivation, code snippets, and links |
| Tutorial | `tutorials/` | Teaches new users how to use AiiDA (learning-oriented) |
| How-to guides | `howto/` | Concrete recipes for specific tasks (goal-oriented) |
| Topics | `topics/` | In-depth explanations of AiiDA concepts (understanding-oriented) |
| Reference | `reference/` | Complete API reference (information-oriented) |
| Developer guide | `developer_guide/` | Guidelines for contributors |

## Style guide

1. Write **one sentence per line** and otherwise no manual line wrapping.
   This makes it easy to create and review diffs.
1. File and directory names should be **alphanumeric, lowercase, with underscores** as separators (e.g., `entry_points.md`).
1. Headers must be set in **sentence case** (e.g., "Entry points").
1. Separate paragraphs by one empty line, not more.
1. Use `-` or `*` for itemized lists.

### Markdown (MyST) files

Both MyST Markdown and RST are supported.
[MyST Markdown](https://myst-parser.readthedocs.io/en/latest/) is generally easier to read and write.
Use standard Markdown headers (`#`, `##`, `###`, etc.) and fenced code blocks:

````markdown
```python
print('hello')
```
````

### RST files

Many existing pages use reStructuredText.
When editing these, follow the existing RST conventions:

1. Section header hierarchy:
   - `#` with overline for the global title
   - `*` with overline for chapters
   - `=` for sections
   - `-` for subsections
   - `^` for subsubsections
1. Use the `code-block` directive instead of double-colon for code segments.

## Cross-references

MyST and RST use different syntax for cross-referencing:

| Purpose | MyST Markdown | reStructuredText |
|---------|---------------|------------------|
| Link to a document | `` {doc}`Link text <path/to/doc>` `` | `` :doc:`Link text <path/to/doc>` `` |
| Link to a label | `` {ref}`Link text <label-name>` `` | `` :ref:`Link text <label-name>` `` |
| Link to a class/function | `` {class}`aiida.orm.Node` `` | `` :class:`aiida.orm.Node` `` |

See the [MyST cross-referencing guide](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html) for full details.

## Code segments

For both formats, use the appropriate language identifier:

| Content | Language | Notes |
|---------|----------|-------|
| Bash scripts | `bash` | |
| Bash sessions | `console` | Prefix commands with `$`, root with `#` |
| Python scripts | `python` | |
| Python sessions | `ipython` | For `verdi shell` examples |

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
