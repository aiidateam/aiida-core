# Writing documentation

Improving the AiiDA documentation is both straightforward and valuable.

AiiDA uses [Sphinx](http://www.sphinx-doc.org) with [MyST Markdown](https://myst-parser.readthedocs.io/) and [reStructuredText](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

## Building docs locally

A convenient way to work on the documentation:

```console
$ pip install tox
$ tox -e py38-docs-live  # automatically recompiles when changes are detected
```

Or build manually:

```console
$ cd docs
$ make html
$ open build/html/index.html
```

:::{warning}
The CI tests on your PR will fail if warnings are encountered while building the documentation.
:::

## Useful resources

* [The Documentation System](https://www.divio.com/blog/documentation/) -- the framework AiiDA's docs are modeled after.
* [Google developer documentation style guide](https://developers.google.com/style) -- especially the notes about [tone](https://developers.google.com/style/tone).

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
2. File and directory names should be **alphanumeric, lowercase, with underscores** as separators (e.g., `entry_points.rst`).
3. Headers must be set in **sentence case** (e.g., "Entry points").
4. Section header hierarchy (for RST files):
   - `#` with overline for the global title
   - `*` with overline for chapters
   - `=` for sections
   - `-` for subsections
   - `^` for subsubsections
5. Separate paragraphs by one empty line, not more.
6. Use `*` for itemized lists.
7. Use the `code-block` directive instead of double-colon for code segments.

## Code segments

| Content | RST directive | Notes |
|---------|---------------|-------|
| Bash scripts | `.. code-block:: bash` | |
| Bash sessions | `.. code-block:: console` | Prefix commands with `$`, root with `#` |
| Python scripts | `.. code-block:: python` | |
| Python sessions | `.. code-block:: ipython` | For `verdi shell` examples |

## Docstring format

```python
"""Description of the function.

:param parameter: some notes on input parameter
:type parameter: str

:return returned: some note on what is returned
:rtype: str

:raises ValueError: Notes on the type of exception raised
"""
```

## Naming conventions

* *setup*: one word, not "set up"
* *Python*: capitalized
* *UUID*: block capitalized
