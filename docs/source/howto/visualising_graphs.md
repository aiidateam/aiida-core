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

(how-to:data:visualise-provenance)=

# How to visualize provenance

```{note}
This tutorial can be downloaded and run as a Jupyter Notebook: {nb-download}`visualising_graphs.ipynb` {octicon}`download`
```

The provenance graph of a database can be visually inspected, *via* [graphviz](https://www.graphviz.org/), using both the python API and command-line interface.

```{seealso}
`verdi graph generate -h`
```

We first load a profile, containing the provenance graph (in this case we load an archive as the profile).

```{code-cell} ipython3
from aiida import load_profile
from aiida.common import LinkType
from aiida.orm import LinkPair
from aiida.storage.sqlite_zip import SqliteZipBackend
from aiida.tools.visualization import Graph, pstate_node_styles

profile = load_profile(SqliteZipBackend.create_profile('include/graph1.aiida'))
```

```{code-cell} ipython3
dict1_uuid = '0ea79a16-501f-408a-8c84-a2704a778e4b'
calc1_uuid = 'b23e692e-4e01-48dd-b515-4c63877d73a4'
```

The {py:class}`~aiida.tools.visualization.graph.Graph` class is used to store visual representations of the nodes and edges, which can be added separately or cumulatively by one of the graph traversal methods.
The {py:attr}`~aiida.tools.visualization.graph.Graph.graphviz` attribute returns a [graphviz.Digraph](https://graphviz.readthedocs.io/en/stable/) instance, which will auto-magically render the graph in the notebook, or can be used to save the graph to file.

```{code-cell} ipython3
graph = Graph()
graph.add_node(dict1_uuid)
graph.add_node(calc1_uuid)
graph.graphviz
```

```{code-cell} ipython3
graph.add_edge(
    dict1_uuid, calc1_uuid,
    link_pair=LinkPair(LinkType.INPUT_CALC, "input1"))
graph.graphviz
```

```{code-cell} ipython3
graph.add_incoming(calc1_uuid)
graph.add_outgoing(calc1_uuid)
graph.graphviz
```

The {py:class}`~aiida.tools.visualization.graph.Graph` can also be initialized with global style attributes,
as outlined in the [graphviz attributes table](https://www.graphviz.org/doc/info/attrs.html).

```{code-cell} ipython3
graph = Graph(node_id_type="uuid",
              global_node_style={"penwidth": 1},
              global_edge_style={"color": "blue"},
              graph_attr={"rankdir": "LR"})
graph.add_incoming(calc1_uuid)
graph.add_outgoing(calc1_uuid)
graph.graphviz
```

Additionally functions can be parsed to the {py:class}`~aiida.tools.visualization.graph.Graph` initializer, to specify exactly how each node will be represented. For example, the {py:func}`~aiida.tools.visualization.graph.pstate_node_styles` function colors process nodes by their process state.

```{code-cell} ipython3
def link_style(link_pair, **kwargs):
    return {"color": "blue"}

graph = Graph(node_style_fn=pstate_node_styles,
              link_style_fn=link_style,
              graph_attr={"rankdir": "LR"})
graph.add_incoming(calc1_uuid)
graph.add_outgoing(calc1_uuid)
graph.graphviz
```

Edges can be annotated by one or both of their edge label and link type.

```{code-cell} ipython3
graph = Graph(graph_attr={"rankdir": "LR"})
graph.add_incoming(calc1_uuid,
                   annotate_links="both")
graph.add_outgoing(calc1_uuid,
                   annotate_links="both")
graph.graphviz
```

The {py:meth}`~aiida.tools.visualization.graph.Graph.recurse_descendants` and {py:meth}`~aiida.tools.visualization.graph.Graph.recurse_ancestors` methods can be used to construct a full provenance graph.

```{code-cell} ipython3
graph = Graph(graph_attr={"rankdir": "LR"})
graph.recurse_descendants(
    dict1_uuid,
    origin_style=None,
    include_process_inputs=True,
    annotate_links="both"
)
graph.graphviz
```

The link types can also be filtered, to view only the 'data' or 'logical' provenance.

```{code-cell} ipython3
graph = Graph(graph_attr={"rankdir": "LR"})
graph.recurse_descendants(
    dict1_uuid,
    origin_style=None,
    include_process_inputs=True,
    annotate_links="both",
    link_types=("input_calc", "create")
)
graph.graphviz
```

```{code-cell} ipython3
graph = Graph(graph_attr={"rankdir": "LR"})
graph.recurse_descendants(
    dict1_uuid,
    origin_style=None,
    include_process_inputs=True,
    annotate_links="both",
    link_types=("input_work", "return")
)
graph.graphviz
```

If you wish to highlight specific node classes,
then the `highlight_classes` option can be used
to only color specified nodes:

```{code-cell} ipython3
graph = Graph(graph_attr={"rankdir": "LR"})
graph.recurse_descendants(
    dict1_uuid,
    highlight_classes=['Dict']
)
graph.graphviz
```
