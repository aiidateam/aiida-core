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

We first create a temporary profile containing an example provenance graph.

```{code-cell} ipython3
from aiida import load_profile, orm
from aiida.common import LinkType
from aiida.orm import LinkPair
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.visualization import Graph, pstate_node_styles

profile = load_profile(
    SqliteTempBackend.create_profile(
        'graph-visualization', options={'warnings.development_version': False}, debug=False
    ),
    allow_switch=True,
)

computer = orm.Computer(
    label='example-computer',
    hostname='localhost',
    transport_type='core.local',
    scheduler_type='core.direct',
).store()
code = orm.InstalledCode(computer=computer, filepath_executable='/bin/true', label='example-code').store()
dict1 = orm.Dict().store()
int1 = orm.Int(value=3).store()

workflow = orm.WorkChainNode()
for node, label in ((dict1, 'input1'), (int1, 'input2'), (code, 'code')):
    workflow.base.links.add_incoming(node, LinkType.INPUT_WORK, label)
workflow.store()

calc1 = orm.CalcJobNode(computer=computer, label='calc1')
for node, label in ((dict1, 'input1'), (int1, 'input2'), (code, 'code')):
    calc1.base.links.add_incoming(node, LinkType.INPUT_CALC, label)
calc1.base.links.add_incoming(workflow, LinkType.CALL_CALC, 'call1')
calc1.store()

remote = orm.RemoteData(computer=computer, remote_path='/x/y.py')
remote.base.links.add_incoming(calc1, LinkType.CREATE, 'output')
remote.store()

string = orm.Str(value='abc').store()
calcfunction = orm.CalcFunctionNode(label='calcf1')
for node, label in ((remote, 'input1'), (string, 'input2')):
    calcfunction.base.links.add_incoming(node, LinkType.INPUT_CALC, label)
calcfunction.base.links.add_incoming(workflow, LinkType.CALL_CALC, 'call2')
calcfunction.store()

for node, label in ((orm.Dict(), 'output1'), (orm.FolderData(), 'output2')):
    node.base.links.add_incoming(calcfunction, LinkType.CREATE, label)
    node.store()
    node.base.links.add_incoming(workflow, LinkType.RETURN, label)

calc1.seal()
calcfunction.seal()
workflow.seal()
```

```{code-cell} ipython3
dict1_uuid = dict1.uuid
calc1_uuid = calc1.uuid
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
