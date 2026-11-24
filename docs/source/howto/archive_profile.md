---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
execution:
  timeout: 120
---

(how-to:data:share:archive:profile)=

# How to inspect an archive

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`archive_profile.ipynb` {octicon}`download`
:::

The AiiDA archive is a file format for long term storage of data from a particular profile.
See {ref}`how-to:share:archives` for information on how to create and migrate an archive.

The easiest way to inspect the contents of an archive is to create a profile that "mounts" the archive as its data storage.
This example first sets up a scratch profile to generate an archive containing a small provenance graph at runtime, then mounts that archive in a temporary profile.

```{note}
An archive can only be mounted if its version matches the version expected by your installed AiiDA code.
If the archive was created by an older version of AiiDA, migrate it first with `verdi archive migrate`.
Migration is a one-way operation, so keep a copy of the original archive if you still need it.
See {ref}`how-to:share:migrate` for details.
```

```{code-cell} ipython3
:tags: [remove-cell]

from aiida import load_profile
from aiida.storage.sqlite_temp import SqliteTempBackend

load_profile(SqliteTempBackend.create_profile('howto-inspect-archive-source'), allow_switch=True)
```

```{code-cell} ipython3
:tags: [remove-cell]

from pathlib import Path
from tempfile import TemporaryDirectory

from aiida import orm
from aiida.engine import calcfunction
from aiida.tools.archive import create_archive


@calcfunction
def add(x, y):
    return x + y


@calcfunction
def multiply(x, y):
    return x * y


result = multiply(add(orm.Int(1), orm.Int(2)), orm.Int(3))
archive_dir = TemporaryDirectory()
archive_path = Path(archive_dir.name) / 'howto-inspect-archive.aiida'
create_archive([result], filename=archive_path)
```

```{code-cell} ipython3
from aiida import load_profile
from aiida.storage.sqlite_zip import SqliteZipBackend

load_profile(SqliteZipBackend.create_profile(archive_path), allow_switch=True)
```

To inspect your own archive, replace `archive_path` with the path to your archive file.

```{warning}
A profile using the `core.sqlite_zip` storage is read-only.
It is therefore possible to query data, but trying to modify existing data or store new data will raise an exception.
```

Just as with a normal profile, we can now use the {py:class}`~aiida.orm.QueryBuilder`, to [find and query for data](how-to:query):

```{code-cell} ipython3
from aiida import orm
process = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters=orm.CalcFunctionNode.fields.process_label == 'multiply',
).first(flat=True)
print(process)
```

and also use {py:class}`~aiida.tools.visualization.graph.Graph`, to [visualize data provenance](how-to:data:visualise-provenance):

```{code-cell} ipython3
from aiida import orm
from aiida.tools.visualization import Graph
process = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters=orm.CalcFunctionNode.fields.process_label == 'multiply',
).first(flat=True)
graph = Graph(graph_attr={'rankdir': 'LR'})
graph.recurse_ancestors(process, annotate_links='both', include_process_outputs=True)
graph.graphviz
```

The example archive and both profiles are temporary and do not need to be removed from your configuration.
