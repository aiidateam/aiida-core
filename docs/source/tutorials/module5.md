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

(tutorial:module5)=
# Module 5: Querying and analysis

:::{note}
This module reuses the tutorial profile created in {ref}`Module 1 <tutorial:module1>` and the F-sweep data created in {ref}`Module 2 <tutorial:module2>`.
If you are following along locally, run those modules first.
To use your own profile instead, replace the setup cell at the top of the downloaded notebook with:

```python
from aiida import load_profile

load_profile()
```
:::

## What you will learn

After this module, you will be able to:

- Build queries that filter, project, and aggregate over thousands of nodes without loading them into Python
- Walk the provenance graph from any node to its inputs, outputs, ancestors, or descendants
- Reconstruct an analysis directly from the database, without keeping Python references to the original results

```{code-cell} ipython3
# Set up the tutorial's isolated sandbox profile (same as Module 1).
# `%load_ext aiida` enables the `%verdi` magic; `%run` creates or loads the
# shared `tutorial-<hash>` profile, so data from earlier modules is available.
%load_ext aiida
%run -i include/setup_tutorial.py
```

## Why query the database?

In {ref}`Module 2 <tutorial:module2>` the sweep ended with a Python list called `enriched_results`: the F values and `Float` outputs of each `parse_output` calcfunction, conveniently in memory.
However, that list only exists because the sweep just ran in the same notebook.

In real work, the data you want to analyse is rarely the data you just produced.
You come back to last week's runs, you want to combine your sweep with a colleague's, you want to look at all `variance_V` values across every sweep you ever ran on this profile.

The good news: **AiiDA already stores all of this in a database, and you can query it directly.** {class}`~aiida.orm.QueryBuilder` is the API for that.

:::{important}
The provenance graph in the database, not the Python variables in your current session, is the source of truth for what you have computed.
A `QueryBuilder` query is a question you can ask of that graph at any time, from any session, without re-running anything.
:::

## Filtering and projecting

A query is built up by chaining `.append(...)` calls, one per node type you want, declaring filters on each, and asking for either a count, a list of results, or projected values.
Module 2 already showed a few small examples at the end; here we go a bit further.

Find every `Float` node in the database, and count them:

```{code-cell} ipython3
from aiida import orm

qb = orm.QueryBuilder().append(orm.Float)
print(f'Total Float nodes: {qb.count()}')
```

The number is higher than the eight `F` values we swept in Module 2.
Module 3's WorkGraph sweep produced its own set of `Float` outputs, and `parse_output` also stores `mean_V` alongside `variance_V`.
Every one of those is in the same database, indistinguishable from the others *until you constrain the query*.

You can add a **filter** to narrow the rows, and a **projection** to return only the column you care about so the database does not have to load full nodes:

```{code-cell} ipython3
qb = (
    orm.QueryBuilder()
    .append(
        orm.Float,
        filters={'attributes.value': {'>': 0.01}},
        project='attributes.value',
    )
)
values = sorted(row[0] for row in qb.all())
print(f'{len(values)} Float nodes with value > 0.01')
print(f'Values: {[round(v, 4) for v in values]}')
```

A few things to notice:

- `filters=` is a dict keyed by *column path*; `attributes.value` digs into the JSON `attributes` column of the node table.
- `project=` takes the same column path syntax and returns those columns instead of full node objects.
- `.all()` returns a list of rows, each row a list of projected columns.
- `.count()` skips materialisation entirely; the database returns just an integer.

The same column-path syntax works on **extras**, the mutable per-node metadata you can attach at any time.
Module 2 tagged each `parse_output` calcfunction with `F` (the feed rate) and `sweep='F_scan'`; we can pick out exactly those nodes now:

```{code-cell} ipython3
qb = (
    orm.QueryBuilder()
    .append(
        orm.CalcFunctionNode,
        filters={'extras.sweep': 'F_scan'},
        project=['extras.F', 'pk'],
    )
)
for f_val, pk in sorted(qb.all()):
    print(f'F={f_val:.3f}  (parse_output PK={pk})')
```

This returns only the Module 2 sweep, even though Module 3's WorkGraph ran the same sweep again: the WorkGraph's calcfunctions were never tagged with the `sweep` extra, so they are silently excluded.

:::{tip}
Reach for `project=` and `.count()` whenever you can.
They keep the work in SQL and avoid the cost of building full ORM objects in Python, which is what makes QueryBuilder fast at scale.
Once you have projected values, any aggregation (`min`, `max`, `statistics.mean`, NumPy, ...) is just plain Python on a list.
:::

:::{dropdown} Peeking at the SQL behind a query
QueryBuilder generates SQL under the hood, and exposes a few methods for inspecting it directly when you need to debug a slow or surprising query:

- `qb.as_sql(inline=True)` returns the generated SQL as a string, with parameters substituted, ready to paste into `psql` or an SQLite browser.
- `qb.analyze_query()` returns the database's query plan (`EXPLAIN ANALYZE` output on PostgreSQL).
  Useful for diagnosing slow queries on large profiles.
- `qb.as_dict()` and `QueryBuilder.from_dict(...)` serialise a query to a Python dict and back, so you can save, share, or rebuild queries later.
:::

## Joining across the graph

Every query so far asked about a *single* node type.
The interesting questions involve several nodes at once: which `Float` came from which `parse_output`, which `parse_output` belongs to which workflow, which workflow used which input file, etc.

You express those by chaining `.append(...)` calls and **declaring the relationship** between each appended node and an earlier one with `with_incoming=`, `with_outgoing=`, `with_ancestors=`, `with_descendants=`, or `with_group=`.
Each appended node gets an optional `tag=` so later appends can refer back to it.

The previous query returned the `parse_output` calcfunction nodes themselves. Extend it by one hop to also reach the `variance_V` `Float` output:

```{code-cell} ipython3
qb = (
    orm.QueryBuilder()
    .append(
        orm.CalcFunctionNode,
        tag='parse',
        filters={'extras.sweep': 'F_scan'},
        project='extras.F',
    )
    .append(
        orm.Float,
        with_incoming='parse',
        edge_filters={'label': 'variance_V'},
        project='attributes.value',
    )
)
for f_val, variance in sorted(qb.all()):
    print(f'F={f_val:.3f}  variance(V)={variance:.4e}')
```

What changed in the query:

- The second `.append` declares `with_incoming='parse'`: "the `Float` I want has an *incoming* link from the node tagged `parse`". From the `Float`'s point of view, `parse` is its creator.
- `edge_filters={'label': 'variance_V'}` filters on the *link* between the two nodes, picking just the output named `variance_V` and excluding `mean_V`.
- Both nodes contribute a projected column, so each result row is `[F, variance]`.

:::{tip}
Read multi-append queries **top to bottom, as a path through the graph**: the first `.append()` (the one without a `with_*=` keyword) picks the starting nodes, each later one follows a relationship to the next stop on the tour.
The order of projected columns in the result rows also follows the append order.
(The database itself doesn't execute the joins in this order; it picks whatever join plan it thinks is most selective. The top-to-bottom reading is just a mental model for you, not a description of the SQL.)
:::

The same `tutorial/F-sweep` Group from Module 2 can be the entry point of a join with `with_group=`: fetch every member of the Group and follow their links forward.

```{code-cell} ipython3
qb = (
    orm.QueryBuilder()
    .append(
        orm.Group,
        filters={'label': 'tutorial/F-sweep'},
        tag='grp',
    )
    .append(
        orm.CalcFunctionNode,
        with_group='grp',
        tag='parse',
        project='extras.F',
    )
    .append(
        orm.Float,
        with_incoming='parse',
        edge_filters={'label': 'mean_V'},
        project='attributes.value',
    )
)
for f_val, mean_v in sorted(qb.all()):
    print(f'F={f_val:.3f}  mean(V)={mean_v:.4e}')
```

Groups, extras, and graph traversal all compose: you can filter a query by any combination of them in a single call.

:::{dropdown} The full set of relationship keywords
| Keyword | Meaning |
|---|---|
| `with_incoming` | The appended node has an incoming link from the tagged node (i.e., the tagged node is its input or creator). |
| `with_outgoing` | The appended node has an outgoing link to the tagged node (i.e., the tagged node is its output). |
| `with_ancestors` | Anywhere upstream in the graph, not just one hop. |
| `with_descendants` | Anywhere downstream, not just one hop. |
| `with_group` | The appended node is a member of the tagged `Group`. |

Shorthand counterparts for one-off inspection live on `Node` itself: `node.base.links.get_incoming()`, `node.base.links.get_outgoing()`.
Those materialise full Python objects per link; QueryBuilder stays in SQL.
See {ref}`how-to:query:shortcuts:incoming-outgoing` for the side-by-side comparison.
:::

## At scale: querying vs opening files

Module 2 noted in passing that a query like *"all runs where `variance_V > 0.001`"* would otherwise mean opening every stdout node and re-running the regex.
Note that *both* paths parse those files; the difference is *when*.
AiiDA parses eagerly through `parse_output`, once per calculation, and stores the result as a `Float` node, so every subsequent query is plain SQL with no file I/O.
Without AiiDA, every new question against historical runs pays the full file-parsing cost again.
Since you typically read your data far more often than you write it, the amortised savings of eager parsing compound across all your future queries.

```{code-cell} ipython3
---
mystnb:
  code_prompt_show: 'Show file-based baseline: regex over every stdout (Module 1 / Module 2 pain)'
tags: [hide-cell]
---
# File-based baseline: the Module 1 / Module 2 regex on every stdout. Not
# AiiDA-related, hidden here to keep the comparison focused on the QB side.
import time

from include.constants import VARIANCE_RE

t0 = time.perf_counter()
stdout_qb = orm.QueryBuilder().append(
    orm.SinglefileData,
    filters={'attributes.filename': 'stdout'},
)
file_values = []
for (sfd,) in stdout_qb.iterall():
    with sfd.open(mode='r') as fh:
        match = VARIANCE_RE.search(fh.read())
        if match:
            file_values.append(float(match.group(1)))
t_files = time.perf_counter() - t0
```

```{code-cell} ipython3
---
mystnb:
  code_prompt_show: 'Show QueryBuilder version: project Float values from the database'
tags: [hide-input]
---
# Same answer through the database: project the Float.value attribute directly.
t0 = time.perf_counter()
db_qb = (
    orm.QueryBuilder()
    .append(orm.CalcFunctionNode, tag='parse')
    .append(
        orm.Float,
        with_incoming='parse',
        edge_filters={'label': 'variance_V'},
        project='attributes.value',
    )
)
db_values = [row[0] for row in db_qb.all()]
t_db = time.perf_counter() - t0

print(f'via stdout files: {len(file_values)} values in {t_files * 1e3:.1f} ms')
print(f'via QueryBuilder: {len(db_values)} values in {t_db * 1e3:.1f} ms')
print(f'speedup: ~{t_files / max(t_db, 1e-6):.1f}x')
```

At this scale the absolute numbers are small, but the *scaling* is what matters.
The file-based approach grows linearly with the number of runs and pays one filesystem round-trip per node; the QueryBuilder version stays one SQL query regardless.
A sweep of 10,000 runs flips this from "noticeable" to "the only viable path".

:::{dropdown} Does the speedup grow without bound as the database grows?
Mostly no, it stays roughly constant.
Both paths are linear in N; the ratio you measure reflects the **per-row cost difference**, not a "Python vs SQL" intuition.

- File path per row: filesystem `open()` + `read()` + regex match.
  Each open is a syscall in the 10-100 µs range (much more on a cold OS cache).
- QueryBuilder per row: one SQL roundtrip with a JOIN, then a few bytes marshaled per result row.
  Each marshaled row costs ~1-10 µs.

The constants depend on:

- **Loose vs packed repository.**
  Loose objects: one filesystem entry per object, every read is a syscall.
  Packed (`verdi storage maintain`): pack files mmap'd by the repository, reads become an offset and a memcpy. Loose degrades at large N; packed stays much closer to QueryBuilder.
- **OS file cache state.**
  Cold cache hugely punishes the file path; hot cache hides the asymptote.
- **Stdout size.**
  Bigger stdouts mean more read I/O and slower regex.

The "Python loop vs SQL" mental model where the speedup grows unboundedly applies when the database can answer the question **without touching every row**: `qb.count()` with a filter, a `SUM` over an indexed column, a top-N query, and so on.
In those cases the DB is O(1) (or O(log N) with an index) while Python stays O(N), so the speedup keeps growing as the database grows.
Our example here is not one of those: both paths walk every row, just via very different routes per row.
:::

## Rebuilding the transition curve from the database

Module 2 built its transition curve from `enriched_results`, a Python list it had just produced.
We can rebuild the same plot using only QueryBuilder, starting from nothing but the database.

```{code-cell} ipython3
from include.plotting import plot_transition_curve

qb = (
    orm.QueryBuilder()
    .append(
        orm.CalcFunctionNode,
        tag='parse',
        filters={'extras.sweep': 'F_scan'},
        project='extras.F',
    )
    .append(
        orm.Float,
        with_incoming='parse',
        edge_filters={'label': 'variance_V'},
        project='attributes.value',
    )
)
rows = sorted(qb.all())
f_values, variances = zip(*rows)

plot_transition_curve(list(f_values), list(variances))
```

This works tomorrow, next week, or on a fresh notebook with no prior cells.
You no longer need to hold Python references to the nodes you want to analyse: the question *"what is the transition curve of my F-sweep?"* lives in the database, not in your kernel state.

## Sharing your provenance

QueryBuilder reads the database; **archives** package a subset of it into a portable `.aiida` file.
A colleague can import that file into their own profile and re-run any of your queries against the imported nodes, with full provenance preserved.

The minimal recipe is one `verdi` command, here scoped to the F-sweep Group:

```bash
verdi archive create --groups tutorial/F-sweep f-sweep.aiida
```

`verdi archive create` accepts `--groups`, `--nodes`, `--computers`, and `--codes` to scope what is exported, and traverses the provenance graph from those entry points to include everything needed to make the archive self-contained.
For the round-trip side (importing an archive into a profile, querying across imported and local data), see {ref}`how-to:share`.

## Next steps

You can now ask structured questions of an AiiDA database at scale, and share the answers as portable archives.
The remaining tutorial modules each pick up an independent thread and can be tackled in any order:

- {ref}`Module 6 <tutorial:module6>`: more advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition)
- {ref}`Module 7 <tutorial:module7>`: handling failures and recovering from them

## Further reading

- The QueryBuilder how-to guide, covering filters, projections, relationships, shortcuts, and operators: {ref}`how-to:query`
- The QueryBuilder reference (column paths, relationship table, query-dict serialisation): {ref}`topics:database`
- Groups in depth: {ref}`how-to:data:organize`
- AiiDA archives and sharing: {ref}`how-to:share`
- Performance and scaling considerations for queries: {ref}`topics:performance`
