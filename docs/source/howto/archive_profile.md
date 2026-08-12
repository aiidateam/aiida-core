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
This tutorial can be downloaded and run as a Jupyter Notebook: {nb-download}`archive_profile.ipynb` {octicon}`download`, together with the archive {download}`process.aiida`.
```

The AiiDA archive is a file format for long term storage of data from a particular profile.
See {ref}`how-to:share:archives` for information on how to create and migrate an archive.

The easiest way to inspect the contents of an archive is to create a profile that "mounts" the archive as its data storage:

```{code-cell} ipython3
!verdi profile setup core.sqlite_zip -n --profile-name archive --filepath process.aiida
```

The `--filepath` option also accepts a `http://` or `https://` URL of an archive hosted online:

```{code-block} console
verdi profile setup core.sqlite_zip -n --profile-name archive --filepath https://example.com/process.aiida
```

In this case, the archive is not downloaded in full: the profile stores the URL and AiiDA uses [HTTP range requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests) to fetch only the SQLite database (once per Python session, on first query) and to stream individual repository files on demand.
Note that the server hosting the archive must support range requests, and the archive must already be at the latest archive format version, since a remote archive cannot be migrated in place (download it and run `verdi archive migrate` on the local copy instead).
The HTTP requests use a timeout of 60 seconds by default, which can be changed via the `storage.remote_archive_timeout` configuration option, e.g. `verdi config set storage.remote_archive_timeout 120`.

Alternatively, if you do not want to create a profile at all, you can pass the location of the archive directly to the `verdi -p/--profile` option, as a `file:///absolute/path` URL of a local archive or an `http(s)://` URL of a remote one:

```{code-block} console
verdi -p file:///path/to/process.aiida process list -a
verdi -p https://example.com/process.aiida shell
```

This creates a temporary profile that mounts the archive for the duration of the command only: nothing is added to the AiiDA configuration file and any temporary files are cleaned up when the command finishes.

## Caching the database

By default, the SQLite database contained in the archive is extracted (and for remote archives, downloaded) again for every Python session.
For large or remote archives this can be avoided by caching the extracted database locally, in the `cache/sqlite_zip` subdirectory of the AiiDA configuration folder.
Cache entries are named after the checksum and size of the database recorded in the archive, so validating the cache only requires reading the table of contents of the archive (for remote archives, a small range request), never the database itself.

An existing valid cache entry is always used automatically.
The cache is only *written* when explicitly requested, either for a single invocation with the top-level `--use-cache` option:

```{code-block} console
verdi --use-cache -p https://example.com/process.aiida process list -a
```

or when creating a profile, in which case the cached database is also recorded for the profile in the configuration file:

```{code-block} console
verdi profile setup core.sqlite_zip -n --profile-name archive --filepath process.aiida --use-cache
```

For such profiles, a deleted cache entry is transparently recreated on the next load.
If instead the *archive itself* changed since the cache was created, loading the profile stops with an error, and the recorded cache can be updated explicitly with:

```{code-block} console
verdi profile cache-refresh archive
```

When the archive is unreachable (e.g. working offline with a remote archive), a profile with a recorded cached database can still be used by passing the top-level `--force-cache` option.
Note that in this case the data is not validated against the archive, and repository files, which are always read directly from the archive, may not be accessible.

The cache can be deleted at any time with `verdi profile cache-clear`: entries are recreated on the next load of a profile configured for caching.
Note however that recreating an entry requires access to the archive: if you rely on `--force-cache` to work with an unreachable archive, clearing the cache deletes your only usable copy of the data.

You can now inspect the contents of the `process.aiida` archive by using the `archive` profile in the same way you would a standard AiiDA profile.
For example, you can start an interactive shell using `verdi -p archive shell` or if you are already in a notebook simply load the profile:

```{code-cell} ipython3
from aiida import load_profile
load_profile('archive', allow_switch=True)
```

```{warning}
A profile using the `core.sqlite_zip` storage is read-only.
It is therefore possible to query data, but trying to modify existing data or store new data will raise an exception.
```

Just as with a normal profile, we can now use the {py:class}`~aiida.orm.QueryBuilder`, to [find and query for data](how-to:query):

```{code-cell} ipython3
from aiida import orm
process = orm.QueryBuilder().append(orm.ProcessNode).first(flat=True)
print(process)
```

and also use {py:class}`~aiida.tools.visualization.graph.Graph`, to [visualize data provenance](how-to:data:visualise-provenance):

```{code-cell} ipython3
from aiida import orm
from aiida.tools.visualization import Graph
process = orm.QueryBuilder().append(orm.ProcessNode).first(flat=True)
graph = Graph(graph_attr={'rankdir': 'LR'})
graph.add_incoming(process, annotate_links='both')
graph.add_outgoing(process, annotate_links='both')
graph.graphviz
```

Once you are done inspecting the archive and you no longer want to keep the profile around, you can delete it:
```{code-block} console
verdi profile delete archive
```
You will be prompted whether you also want to keep the data.
If you want to keep the `process.aiida` archive file, select not to delete the data.
