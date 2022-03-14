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
---

(how-to:data:share:archive:profile)=

# How to inspect an archive

```{note}
This tutorial can be downloaded and run as a Jupyter Notebook: {nb-download}`archive_profile.ipynb` {octicon}`download`, together with the archive {download}`include/process.aiida`.
```

The AiiDA archive is a file format for long term storage of data from a particular profile.

See {ref}`how-to:share:archives` for information on how to create and migrate an archive.
Once you have an archive at the latest version, you can inspect its contents in the same way you would with a standard AiiDA profile.

We first create a profile instance from the archive path:

```{code-cell} ipython3
from aiida import manage, orm, profile_context
from aiida.storage.sqlite_zip.backend import SqliteZipBackend

archive_profile = SqliteZipBackend.create_profile('include/process.aiida')
print(archive_profile)
```

The {py:func}`~aiida.manage.configuration.profile_context` function works similarly to the {py:func}`~aiida.manage.configuration.load_profile` function,
but is used within a context manager, that insures that the storage is properly closed when the context is exited.
With this, we can load our archive as a profile:

```{code-cell} ipython3
with profile_context(archive_profile):
    print(manage.get_manager().get_profile())
```

To directly access the storage backend, and view information about it, we can use:

```{code-cell} ipython3
import json
with profile_context(archive_profile):
    storage = manage.get_manager().get_profile_storage()
    print(storage)
    print(json.dumps(storage.get_info(), indent=2))
```

This is directly equivalent to the command-line call:

```{code-cell} ipython3
!verdi archive info include/process.aiida
```

Note, that once the context manager is exited, the storage is closed, and will except on further calls.

```{code-cell} ipython3
print(storage)
```

As per a standard profile, we can now use the {py:class}`~aiida.orm.QueryBuilder`, to [find and query for data](how-to:query):

```{code-cell} ipython3
with profile_context(archive_profile):
    process = orm.QueryBuilder().append(orm.ProcessNode).first(flat=True)
    print(process)
```

and also use {py:class}`~aiida.tools.visualization.graph.Graph`, to [visualize data provenance](how-to:data:visualise-provenance):

```{code-cell} ipython3
from aiida.tools.visualization import Graph

with profile_context(archive_profile):
    process = orm.QueryBuilder().append(orm.ProcessNode).first(flat=True)
    graph = Graph(graph_attr={"size": "8!,8!", "rankdir": "LR"})
    graph.add_incoming(process, annotate_links="both")
    graph.add_outgoing(process, annotate_links="both")

graph.graphviz
```
